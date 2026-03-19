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
            new_path = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles)
            self.global_path = new_path
        finally:
            self.is_planning = False
            self.replan_needed = False

    def update(self, dt: float, world):
        if not self.is_running: return

        # 1. 觸發非同步重規劃
        if self.replan_needed and not self.is_planning:
            thread = threading.Thread(target=self._async_replan, args=(list(world.obstacles),), daemon=True)
            thread.start()

        # 2. 核心優化：即時旋轉響應 (先轉再說)
        # 如果正在規劃路徑，且目標在車頭 45 度以外，先執行原地旋轉
        if self.is_planning:
            dx, dy = self.target["x"] - self.x, self.target["y"] - self.y
            target_angle = math.atan2(dy, dx)
            alpha = math.atan2(math.sin(target_angle - self.theta), math.cos(target_angle - self.theta))
            
            if abs(alpha) > 0.4: # 大於 23 度就啟動預轉向
                w = 1.2 if alpha > 0 else -1.2
                # 旋轉安全檢查
                if self.controller.is_pose_safe(self.x, self.y, self.theta + w * 0.1, world.obstacles, margin=515):
                    self.v = 0
                    self.omega = np.clip(w, self.omega - 5.0*dt, self.omega + 5.0*dt) # 加速度限制
                    self.x, self.y, self.theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, dt)
                    self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)
                    return
            
            # 如果不適合旋轉或角度已對準，則保持靜止等待 A*
            self.v = 0; self.omega = 0
            self.l_rpm, self.r_rpm = 0, 0
            return

        # 3. 正常追蹤邏輯 (A* 算完後銜接)
        if not self.global_path: return

        min_dist = float("inf")
        closest_idx = 0
        for i, wp in enumerate(self.global_path):
            d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
            if d < min_dist: min_dist = d; closest_idx = i
        
        lookahead_steps = max(1, int(2 + self.v / 150.0))
        target_idx = min(closest_idx + lookahead_steps, len(self.global_path)-1)
        target_wp = self.global_path[target_idx]

        bv, bo = self.controller.compute_command(self.x, self.y, self.theta, self.v, self.omega, target_wp, self.max_rpm, world.obstacles)

        self.v, self.omega = bv, bo
        self.x, self.y, self.theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, dt)
        
        if math.sqrt((self.x - self.target["x"])**2 + (self.y - self.target["y"])**2) < 300:
            self.is_running = False; self.v = 0; self.omega = 0
            
        self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)
