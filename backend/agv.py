import math
import numpy as np
import threading
import time
import logging
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
from kinematics import Kinematics
from controller import AGVController
from planner import AStarPlanner

logger = logging.getLogger(__name__)

class AGVStatus(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    EVADING = "EVADING"
    STUCK = "STUCK"

class AGV:
    def __init__(self, id: str, x: float, y: float, theta: float = 0.0):
        self.id = id
        self.x = x; self.y = y; self.theta = theta
        self.v = 0.0; self.omega = 0.0
        self.l_rpm = 0.0; self.r_rpm = 0.0
        
        self.target = {"x": x, "y": y}
        self.global_path: List[Tuple[float, float]] = []
        self.visited_nodes: List[Tuple[int, int]] = []
        
        self.status = AGVStatus.IDLE
        self.is_running = False 
        self.is_planning = False
        
        self.max_rpm = 3000.0
        self.replan_needed = True
        self.culprit_id = None 
        self.wait_start_time = None
        self.stuck_start_time = None # 新增：卡住計時器
        self.recovery_nudge_time = 0.0

        self.kinematics = Kinematics(wheel_base=800.0)
        self.controller = AGVController({"dt": 0.1, "wheel_base": 800.0})
        self.planner = AStarPlanner(grid_size=200)
        self._last_compute_time = 0.0
        self.target_v = 0.0
        self.target_omega = 0.0

    def get_priority_score(self) -> float:
        base = 50.0 if self.is_running else 0.0
        id_weight = (hash(self.id) % 100) / 100.0
        wait_bonus = 0.0
        if self.wait_start_time:
            wait_bonus = (time.time() - self.wait_start_time) * 0.1
        return base + id_weight + wait_bonus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "x": self.x, "y": self.y, "theta": self.theta,
            "v": self.v, "omega": self.omega,
            "l_rpm": self.l_rpm, "r_rpm": self.r_rpm,
            "target": self.target, 
            "status": self.status,
            "is_running": self.is_running,
            "is_planning": self.is_planning,
            "path": self.global_path,
            "visited": self.visited_nodes,
            "max_rpm": self.max_rpm,
            "culprit_id": self.culprit_id
        }

    def _async_replan(self, obstacles, static_costmap):
        self.is_planning = True
        self.status = AGVStatus.PLANNING
        try:
            path, visited = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles, static_costmap=static_costmap)
            self.global_path = path
            self.visited_nodes = visited
        finally:
            self.is_planning = False
            self.status = AGVStatus.EXECUTING if self.is_running else AGVStatus.IDLE
            self.replan_needed = False

    def update(self, dt: float, world):
        if self.replan_needed and not self.is_planning:
            all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
            thread = threading.Thread(target=self._async_replan, args=(all_obs, world.static_costmap), daemon=True)
            thread.start()

        if self.is_planning:
            self.v = 0; self.omega = 0; return

        if not self.is_running:
            self.status = AGVStatus.IDLE
            self.v = 0; self.omega = 0
            world.clear_path_occupancy(self.id)
            self.check_proactive_evasion(world)
            return

        if not self.global_path: 
            world.clear_path_occupancy(self.id)
            return

        # 1. 決策層：更新目標指令 (20Hz 決策頻率)
        self._last_compute_time += dt
        if self._last_compute_time >= 0.05:
            all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
            min_dist = float("inf"); closest_idx = 0
            for i, wp in enumerate(self.global_path):
                d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
                if d < min_dist: min_dist = d; closest_idx = i
            
            # 更新路徑預演 (未來 3公尺)
            projection = self.global_path[closest_idx : closest_idx + 15]
            world.update_path_occupancy(self.id, projection)
            
            lookahead = max(4 if abs(self.v) < 10 else 1, int(2 + abs(self.v) / 150.0))
            target_wp = self.global_path[min(closest_idx + lookahead, len(self.global_path)-1)]

            # 簡化邊際：避讓時稍微通融
            margin = 480 if self.status == AGVStatus.EVADING else 525
            max_speed_mms = self.max_rpm * self.kinematics.rpm_to_mms
            
            # 核心優化：如果在避讓中，忽略對該對象的碰撞檢查
            ignore_id = self.culprit_id if self.status == AGVStatus.EVADING else None

            bv, bo, culprit = self.controller.compute_command(
                self.x, self.y, self.theta, self.v, self.omega, 
                target_wp, max_speed_mms, all_obs, margin=margin, dt=0.05, ignore_id=ignore_id
            )
            
            self.target_v, self.target_omega = bv, bo
            self.culprit_id = culprit
            self._last_compute_time = 0.0

            if self.target_v == 0 and self.target_omega == 0:
                if not self.wait_start_time: self.wait_start_time = time.time()
                self.status = AGVStatus.STUCK
            else:
                self.wait_start_time = None
                self.status = AGVStatus.EXECUTING if self.status != AGVStatus.EVADING else AGVStatus.EVADING

        # 物理積分：每幀都執行，且使用正確的 dt
        # 3. 緊急恢復邏輯 (Recovery Nudge)
        if self.status == AGVStatus.STUCK and self.v == 0:
            if not self.stuck_start_time: self.stuck_start_time = time.time()
            if time.time() - self.stuck_start_time > 2.0: # 卡住超過 2 秒
                self.recovery_nudge_time = 0.5 # 啟動 0.5 秒的強制後退
                self.stuck_start_time = None 
        else:
            self.stuck_start_time = None

        remaining_dt = dt
        sub_dt = 0.01 
        max_speed_mms = self.max_rpm * self.kinematics.rpm_to_mms

        # 2. 執行層：子步長物理積分
        # 效能關鍵：預先準備好障礙物，且加速時簡化物理檢查
        all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
        
        remaining_dt = dt
        sub_dt = 0.05 if dt > 0.1 else 0.01 # 加速時使用更大的物理步長
        max_speed_mms = self.max_rpm * self.kinematics.rpm_to_mms
        
        while remaining_dt > 0:
            step = min(remaining_dt, sub_dt)
            
            if self.recovery_nudge_time > 0:
                self.v = -100.0; self.omega = 0.0
                self.recovery_nudge_time -= step
                self.x, self.y, self.theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, step)
            else:
                self.v, self.omega = self.controller.limit_physics(self.target_v, self.target_omega, self.v, self.omega, max_speed_mms, step)
                new_x, new_y, new_theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, step)
                
                # 僅在正常速度下或子步長較大時才進行精細碰撞檢查
                if dt < 0.1:
                    safe, _ = self.controller.is_pose_safe(new_x, new_y, new_theta, all_obs)
                    if not safe:
                        self.v = 0; self.omega = 0; break
                
                self.x, self.y, self.theta = new_x, new_y, new_theta
                
            remaining_dt -= step

        if math.sqrt((self.x - self.target["x"])**2 + (self.y - self.target["y"])**2) < 300:
            self.is_running = False; self.status = AGVStatus.IDLE; self.v = 0; self.omega = 0
            
        self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)

    def check_proactive_evasion(self, world):
        # 核心優化：大幅擴大預警半徑 (3000mm)
        for other_id, path_points in world.path_occupancy.items():
            if other_id == self.id: continue
            
            # 只要別人的預演路徑進入我 3公尺範圍，就啟動避讓
            for px, py in path_points:
                if math.sqrt((px - self.x)**2 + (py - self.y)**2) < 3000:
                    self.trigger_evasion(world)
                    return

    def trigger_evasion(self, world):
        """主動避讓策略：優先倒車，其次找路口。"""
        # 1. 優先策略：深度倒車 (退後 5公尺)
        if self.global_path and len(self.global_path) > 10:
            # 找到距離目前位置約 5公尺前的路徑點 (假設節點間距 200mm，25個節點)
            target_idx = max(0, len(self.global_path) - 40)
            tx, ty = self.global_path[target_idx]
            
            if self._is_haven_safe(tx, ty, world):
                self.set_escape_target(tx, ty)
                return

        # 2. 備選策略：搜尋最近路口 (Haven)
        intersection = self.planner.find_nearest_intersection((self.x, self.y), world.static_costmap)
        if intersection:
            if self._is_haven_safe(intersection[0], intersection[1], world):
                self.set_escape_target(intersection[0], intersection[1])
                return
                
        self.status = AGVStatus.STUCK

    def _is_haven_safe(self, tx, ty, world) -> bool:
        """檢查避難點是否真正安全 (無人佔用且離別人路徑足夠遠)。"""
        # 檢查是否離其他 AGV 太近
        for oid, oagv in world.agvs.items():
            if oid != self.id and math.sqrt((tx-oagv.x)**2 + (ty-oagv.y)**2) < 2000:
                return False
        
        # 檢查是否離別人的路徑太近 (加大到 1500mm 以策安全)
        for oid, points in world.path_occupancy.items():
            if oid == self.id: continue
            for px, py in points:
                if math.sqrt((tx-px)**2 + (ty-py)**2) < 1500:
                    return False
        return True

    def set_escape_target(self, tx, ty):
        self.target = {"x": tx, "y": ty}
        self.is_running = True
        self.replan_needed = True
        self.status = AGVStatus.EVADING
