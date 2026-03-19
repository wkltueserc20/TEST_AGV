import math
import numpy as np
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
        self.max_rpm = 3000.0
        self.replan_needed = True

        self.kinematics = Kinematics(wheel_base=800.0)
        self.controller = AGVController({})
        self.planner = AStarPlanner(grid_size=100) # 使用高解析度規劃

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "x": self.x, "y": self.y, "theta": self.theta,
            "v": self.v, "omega": self.omega,
            "l_rpm": self.l_rpm, "r_rpm": self.r_rpm,
            "target": self.target, "is_running": self.is_running,
            "path": self.global_path, "max_rpm": self.max_rpm
        }

    def update(self, dt: float, world):
        if not self.is_running: return

        # 1. 自動重規劃
        if self.replan_needed:
            self.global_path = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], world.obstacles)
            self.replan_needed = False

        if not self.global_path: return

        # 2. 精確尋找路徑點 (解決切西瓜關鍵)
        # 尋找離車子最近的紅線索引
        min_dist = float("inf")
        closest_idx = 0
        for i, wp in enumerate(self.global_path):
            d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
            if d < min_dist:
                min_dist = d
                closest_idx = i
        
        # 核心優化：極短的前瞻距離 (300mm ~ 600mm)
        # 這強迫 AGV 必須精確地跟著紅線走，而不是瞄準遠方
        lookahead_steps = max(1, int(3 + self.v / 100.0))
        target_idx = min(closest_idx + lookahead_steps, len(self.global_path)-1)
        target_wp = self.global_path[target_idx]

        # 3. 呼叫控制器算速度
        bv, bo = self.controller.compute_command(
            self.x, self.y, self.theta, 
            self.v, self.omega, 
            target_wp, self.max_rpm, 
            world.obstacles
        )

        # 4. 物理執行與強制剎車
        self.v, self.omega = bv, bo
        if self.v == 0 and self.omega == 0:
            # 如果控制器因為安全理由停下，強制歸零，防止數值滑行
            pass 
            
        self.x, self.y, self.theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, dt)
        
        # 5. 到達判定
        if math.sqrt((self.x - self.target["x"])**2 + (self.y - self.target["y"])**2) < 300:
            self.is_running = False
            self.v = 0; self.omega = 0
            
        self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)
