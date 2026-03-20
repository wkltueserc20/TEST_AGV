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
        self.visited_nodes: List[Tuple[int, int]] = [] # 儲存 A* 搜尋痕跡
        
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
            "path": self.global_path,
            "visited": self.visited_nodes, # 傳送搜尋過程
            "max_rpm": self.max_rpm
        }

    def _async_replan(self, obstacles, static_costmap):
        self.is_planning = True
        try:
            path, visited = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles, static_costmap=static_costmap)
            self.global_path = path
            self.visited_nodes = visited
        finally:
            self.is_planning = False
            self.replan_needed = False

    def update(self, dt: float, world):
        if not self.is_running: return

        if self.replan_needed and not self.is_planning:
            dynamic_obs = world.get_dynamic_obstacles(exclude_agv_id=self.id)
            thread = threading.Thread(target=self._async_replan, args=(dynamic_obs, world.static_costmap), daemon=True)
            thread.start()

        if self.is_planning:
            self.v = 0; self.omega = 0
            self.l_rpm = 0; self.r_rpm = 0
            return

        if not self.global_path: return

        dynamic_obs = world.get_dynamic_obstacles(exclude_agv_id=self.id)

        min_dist = float("inf"); closest_idx = 0
        for i, wp in enumerate(self.global_path):
            d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
            if d < min_dist: min_dist = d; closest_idx = i
        
        if abs(self.v) < 10.0:
            lookahead = max(4, int(2 + self.v / 150.0))
        else:
            lookahead = max(1, int(2 + self.v / 150.0))
            
        target_idx = min(closest_idx + lookahead, len(self.global_path)-1)
        target_wp = self.global_path[target_idx]

        bv, bo = self.controller.compute_command(
            self.x, self.y, self.theta, self.v, self.omega, 
            target_wp, self.max_rpm, dynamic_obs
        )

        self.v, self.omega = bv, bo
        self.x, self.y, self.theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, dt)
        
        if math.sqrt((self.x - self.target["x"])**2 + (self.y - self.target["y"])**2) < 300:
            self.is_running = False; self.v = 0; self.omega = 0
            
        self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)
