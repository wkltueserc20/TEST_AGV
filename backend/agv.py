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

class AGVMode(str, Enum):
    SIMULATION = "SIMULATION"
    HARDWARE = "HARDWARE"

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
        self.mode = AGVMode.SIMULATION 
        self.is_running = False 
        self.is_planning = False
        
        self.max_rpm = 3000.0
        self.replan_needed = True
        self.culprit_id = None 
        self.wait_start_time = None
        self.stuck_start_time = None 
        self.recovery_nudge_time = 0.0

        self.kinematics = Kinematics(wheel_base=800.0)
        self.controller = AGVController({"dt": 0.1, "wheel_base": 800.0})
        self.planner = AStarPlanner(grid_size=200)
        self._last_compute_time = 0.0
        self._last_conflict_check_time = 0.0
        self.target_v = 0.0
        self.target_omega = 0.0
        self.evasion_target: Optional[Dict[str, float]] = None

    def get_priority_score(self) -> float:
        base = 0.0
        if self.status == AGVStatus.EXECUTING: base = 50.0
        elif self.status == AGVStatus.EVADING: base = 25.0
        id_weight = (hash(self.id) % 100) / 100.0
        return base + id_weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "x": self.x, "y": self.y, "theta": self.theta,
            "v": self.v, "omega": self.omega,
            "l_rpm": self.l_rpm, "r_rpm": self.r_rpm,
            "target": self.target, "status": self.status,
            "is_running": self.is_running, "is_planning": self.is_planning,
            "path": self.global_path, "visited": self.visited_nodes,
            "max_rpm": self.max_rpm, "culprit_id": self.culprit_id,
            "evasion_target": self.evasion_target
        }

    def _async_replan(self, obstacles, static_costmap, world=None, original_status=None, is_evasion_search=False):
        self.is_planning = True
        # 規劃期間不改變狀態，除非是剛從 IDLE 啟動
        if self.status == AGVStatus.IDLE: self.status = AGVStatus.PLANNING
        
        try:
            if is_evasion_search:
                all_threat_paths = [p for oid, p in world.path_occupancy.items() if oid != self.id]
                # 定向排斥向量
                repulsion_vec = None
                for oid, points in world.path_occupancy.items():
                    if oid != self.id:
                        other = world.agvs.get(oid)
                        if other: repulsion_vec = (self.x - other.x, self.y - other.y)
                        break
                if repulsion_vec:
                    mag = math.sqrt(repulsion_vec[0]**2 + repulsion_vec[1]**2)
                    if mag > 0: repulsion_vec = (repulsion_vec[0]/mag, repulsion_vec[1]/mag)

                # 尋找安全點
                safe_spot = self.planner.find_nearest_safe_spot((self.x, self.y), static_costmap, all_threat_paths, repulsion_vec)
                if safe_spot:
                    self.evasion_target = {"x": safe_spot[0], "y": safe_spot[1]}
                    self.target = self.evasion_target
                    world.reserve_haven(self.id, (safe_spot[0], safe_spot[1]))
                    # 計算路徑
                    path, visited = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles, static_costmap=static_costmap, world=world)
                    self.global_path = path
                    self.is_running = True
                    self.status = AGVStatus.EVADING
                else:
                    self.status = AGVStatus.STUCK
                return

            # 一般 A* 規劃
            path, visited = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles, static_costmap=static_costmap, world=world)
            if not path:
                self.global_path = []; return

            self.global_path = path
            self.visited_nodes = visited
            # 只有當目前不是避讓狀態時，才更新為任務執行狀態
            if self.status != AGVStatus.EVADING:
                self.status = AGVStatus.EXECUTING if self.is_running else AGVStatus.IDLE
        finally:
            self.is_planning = False
            self.replan_needed = False

    def is_conflicted(self, world) -> bool:
        # 只要目前位置在別人的預留路徑內，就算衝突 (1.2m 範圍)
        for other_id, points in world.path_occupancy.items():
            if other_id == self.id: continue
            for px, py in points:
                if math.sqrt((px - self.x)**2 + (py - self.y)**2) < 1200:
                    return True
        return False

    def update(self, dt: float, world):
        if self.replan_needed and not self.is_planning:
            world.release_haven(self.id)
            all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
            thread = threading.Thread(target=self._async_replan, args=(all_obs, world.static_costmap, world, self.status), daemon=True)
            thread.start()

        # 廣播意圖 (Mission 或 Evading 都廣播)
        if self.global_path:
            min_dist = float("inf"); closest_idx = 0
            for i, wp in enumerate(self.global_path):
                d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
                if d < min_dist: min_dist = d; closest_idx = i
            # 廣播整條路徑 (全量意圖廣播)
            projection = self.global_path[closest_idx :]
            world.update_path_occupancy(self.id, projection)
        else:
            world.clear_path_occupancy(self.id)

        if self.is_planning:
            self.v = 0; self.omega = 0; self.l_rpm, self.r_rpm = 0, 0; return

        if not self.is_running:
            self.status = AGVStatus.IDLE; self.v = 0; self.omega = 0
            world.release_haven(self.id) 
            # 只有 IDLE 狀態下才主動檢查避讓，避免頻繁閃避
            self._last_compute_time += dt
            if self._last_compute_time >= 0.05:
                self.check_proactive_evasion(world)
                self._last_compute_time = 0.0
            self.l_rpm, self.r_rpm = 0, 0; return
        
        # 核心優化：如果已經在避讓(EVADING)，就絕對不重新觸發搜尋，直到抵達目標
        # 這保證了「一次到位」
        if self.status == AGVStatus.EVADING:
            pass # 這裡不再執行 check_proactive_evasion

        if not self.global_path: 
            self.l_rpm, self.r_rpm = 0, 0; return

        # 1. 決策層
        self._last_compute_time += dt
        if self._last_compute_time >= 0.05:
            all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
            min_dist = float("inf"); closest_idx = 0
            for i, wp in enumerate(self.global_path):
                d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
                if d < min_dist: min_dist = d; closest_idx = i
            
            lookahead = max(4, int(4 + abs(self.v) / 100.0))
            target_wp = self.global_path[min(closest_idx + lookahead, len(self.global_path)-1)]

            margin = 505 if self.status == AGVStatus.EVADING else 525
            max_speed_mms = self.max_rpm * self.kinematics.rpm_to_mms
            
            # 社交禮讓停機
            current_max_speed = max_speed_mms
            if self.status == AGVStatus.EXECUTING:
                for other_id, other_agv in world.agvs.items():
                    if other_id == self.id: continue
                    # 只要前方有人在閃避，我就死等
                    if other_agv.status == AGVStatus.EVADING:
                        dist = math.sqrt((other_agv.x - self.x)**2 + (other_agv.y - self.y)**2)
                        if dist < 5000:
                            current_max_speed = 0.0; break
                    
                    # 標準路徑禮讓
                    dist = math.sqrt((other_agv.x - self.x)**2 + (other_agv.y - self.y)**2)
                    if dist < 4000:
                        is_on_my_path = False
                        path_projection = world.path_occupancy.get(self.id, [])
                        for px, py in path_projection[:20]:
                            if math.sqrt((other_agv.x - px)**2 + (other_agv.y - py)**2) < 1500:
                                is_on_my_path = True; break
                        if is_on_my_path:
                            if dist < 2000: current_max_speed = 0.0 
                            else: current_max_speed = 100.0 

            ignore_id = self.culprit_id if self.status == AGVStatus.EVADING else None
            bv, bo, culprit = self.controller.compute_command(
                self.x, self.y, self.theta, self.v, self.omega, 
                target_wp, current_max_speed, all_obs, margin=margin, dt=0.05, ignore_id=ignore_id, status=self.status
            )
            self.target_v, self.target_omega = bv, bo
            self.culprit_id = culprit
            self._last_compute_time = 0.0

            if self.target_v == 0 and self.target_omega == 0:
                self.status = AGVStatus.STUCK
            else:
                # 恢復狀態，但絕不覆蓋 EVADING
                if self.status != AGVStatus.EVADING:
                    self.status = AGVStatus.EXECUTING

        # 物理積分...
        remaining_dt = dt
        sub_dt = 0.05 if dt > 0.1 else 0.01 
        max_speed_mms = self.max_rpm * self.kinematics.rpm_to_mms
        all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
        while remaining_dt > 0:
            step = min(remaining_dt, sub_dt)
            if self.mode == AGVMode.SIMULATION:
                if self.recovery_nudge_time > 0:
                    self.v = -100.0; self.omega = 0.0
                    self.x, self.y, self.theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, step)
                    self.recovery_nudge_time -= step
                else:
                    self.v, self.omega = self.controller.limit_physics(self.target_v, self.target_omega, self.v, self.omega, max_speed_mms, step, status=self.status)
                    new_x, new_y, new_theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, step)
                    if dt < 0.1:
                        margin = 505 if self.status == AGVStatus.EVADING else 525
                        safe, _ = self.controller.is_pose_safe(new_x, new_y, new_theta, all_obs, margin=margin)
                        if not safe: self.v = 0; self.omega = 0; break
                    self.x, self.y, self.theta = new_x, new_y, new_theta
            remaining_dt -= step

        # 抵達終點檢查
        if math.sqrt((self.x - self.target["x"])**2 + (self.y - self.target["y"])**2) < 300:
            self.is_running = False
            self.status = AGVStatus.IDLE
            self.v = 0; self.omega = 0
            self.evasion_target = None
            world.release_haven(self.id)
            
        self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)

    def check_proactive_evasion(self, world) -> bool:
        # 如果已經在閃了，就閉嘴跑完它
        if self.status == AGVStatus.EVADING: return False
        
        for other_id, other_agv in world.agvs.items():
            if other_id == self.id: continue
            path_points = world.path_occupancy.get(other_id, [])
            if not path_points: continue
            # 感應半徑 5 公尺
            for px, py in path_points:
                if math.sqrt((px - self.x)**2 + (py - self.y)**2) < 5000:
                    self.trigger_evasion(world, threat_pos=(other_agv.x, other_agv.y))
                    return True
        return False

    def trigger_evasion(self, world, threat_pos=None):
        all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
        thread = threading.Thread(target=self._async_replan, args=(all_obs, world.static_costmap, world, self.status, True), daemon=True)
        thread.start()

    def _is_haven_safe(self, tx, ty, world) -> bool:
        # 避開牆壁 (嚴格 2m)
        safe, _ = self.controller.is_pose_safe(tx, ty, self.theta, world.obstacles, margin=505)
        if not safe: return False
        # 避開預約
        for oid, hpos in world.reserved_havens.items():
            if oid != self.id and math.sqrt((tx-hpos[0])**2 + (ty-hpos[1])**2) < 1000: return False
        # 避開別人的全量路徑意圖 (2.0m 禁區)
        for oid, points in world.path_occupancy.items():
            if oid == self.id: continue
            for px, py in points:
                if math.sqrt((tx-px)**2 + (ty-py)**2) < 2000: return False
        return True

