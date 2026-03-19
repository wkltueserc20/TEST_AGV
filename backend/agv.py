import math
import numpy as np
import threading
from typing import Dict, Any, List, Tuple
from kinematics import Kinematics
from controller import AGVController
from planner import AStarPlanner

class AGV:
    def __init__(self, id: str, x: float, y: float, theta: float = 0.0):
        self.id = id
        self.x = x; self.y = y; self.theta = theta
        self.v = 0.0; self.omega = 0.0
        self.l_rpm = 0.0; self.r_rpm = 0.0
        
        self.target = {"x": x, "y": y}
        self.global_path: List[Tuple[float, float]] = []
        self.is_running = False
        self.is_planning = False
        self.max_rpm = 3000.0
        self.replan_needed = True

        self.kinematics = Kinematics(wheel_base=800.0)
        self.controller = AGVController({})
        self.planner = AStarPlanner(grid_size=200)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "x": self.x, "y": self.y, "theta": self.theta,
            "v": self.v, "omega": self.omega,
            "l_rpm": self.l_rpm, "r_rpm": self.r_rpm,
            "target": self.target, 
            "is_running": self.is_running,
            "is_planning": self.is_planning,
            "path": self.global_path, "max_rpm": self.max_rpm
        }

    def _async_replan(self, obstacles):
        self.is_planning = True
        try:
            # 規劃時考慮當前所有動態障礙物
            new_path = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles)
            self.global_path = new_path
        finally:
            self.is_planning = False
            self.replan_needed = False

    def update(self, dt: float, world):
        if not self.is_running: return

        # 1. 觸發非同步重規劃
        if self.replan_needed and not self.is_planning:
            # 獲取包含其他 AGV 的最新快照
            dynamic_obs = world.get_dynamic_obstacles(exclude_agv_id=self.id)
            thread = threading.Thread(target=self._async_replan, args=(dynamic_obs,), daemon=True)
            thread.start()

        # 2. 如果正在規劃，嘗試原地轉向對準目標，不移動
        if self.is_planning:
            dx, dy = self.target["x"] - self.x, self.target["y"] - self.y
            target_angle = math.atan2(dy, dx)
            alpha = math.atan2(math.sin(target_angle - self.theta), math.cos(target_angle - self.theta))
            if abs(alpha) > 0.4:
                w = 1.2 if alpha > 0 else -1.2
                if self.controller.is_pose_safe(self.x, self.y, self.theta + w * 0.1, world.obstacles, margin=515):
                    self.v = 0
                    self.omega = np.clip(w, self.omega - 5.0*dt, self.omega + 5.0*dt)
                    self.x, self.y, self.theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, dt)
                    self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)
                    return
            self.v = 0; self.omega = 0; return

        if not self.global_path: return

        # 3. 獲取動態障礙物 (包含其他正在移動的 AGV)
        dynamic_obs = world.get_dynamic_obstacles(exclude_agv_id=self.id)

        # 4. 尋找最近點並執行控制
        min_dist = float("inf"); closest_idx = 0
        for i, wp in enumerate(self.global_path):
            d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
            if d < min_dist: min_dist = d; closest_idx = i
        
        lookahead = max(1, int(2 + self.v / 150.0))
        target_wp = self.global_path[min(closest_idx + lookahead, len(self.global_path)-1)]

        # 核心：傳遞動態障礙物給控制器，實現即時避撞
        bv, bo = self.controller.compute_command(
            self.x, self.y, self.theta, self.v, self.omega, 
            target_wp, self.max_rpm, dynamic_obs
        )

        self.v, self.omega = bv, bo
        self.x, self.y, self.theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, dt)
        
        if math.sqrt((self.x - self.target["x"])**2 + (self.y - self.target["y"])**2) < 300:
            self.is_running = False; self.v = 0; self.omega = 0
            
        self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)
