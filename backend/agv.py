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
    def __init__(self, id: str, x: float, y: float, theta: float = 0.0, state_dict: Optional[Dict[str, Any]] = None):
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

        if state_dict:
            self.x = state_dict.get("x", self.x)
            self.y = state_dict.get("y", self.y)
            self.theta = state_dict.get("theta", self.theta)
            self.target = state_dict.get("target", self.target)
            self.mode = AGVMode(state_dict.get("mode", self.mode))
            self.max_rpm = state_dict.get("max_rpm", self.max_rpm)
            self.status = AGVStatus(state_dict.get("status", self.status))
            self.is_running = False 
            self.replan_needed = True if self.target != {"x": self.x, "y": self.y} else False

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
            "mode": self.mode,
            "is_running": self.is_running, "is_planning": self.is_planning,
            "path": self.global_path, "visited": self.visited_nodes,
            "max_rpm": self.max_rpm, "culprit_id": self.culprit_id,
            "evasion_target": self.evasion_target
        }

    def _async_replan(self, obstacles, static_costmap, world=None, original_status=None, is_evasion_search=False):
        self.is_planning = True
        if self.status == AGVStatus.IDLE: self.status = AGVStatus.PLANNING
        try:
            if is_evasion_search:
                all_threat_paths = [p for oid, p in world.path_occupancy.items() if oid != self.id]
                repulsion_vec = None
                for oid, points in world.path_occupancy.items():
                    if oid != self.id:
                        other = world.agvs.get(oid)
                        if other: repulsion_vec = (self.x - other.x, self.y - other.y)
                        break
                if repulsion_vec:
                    mag = math.sqrt(repulsion_vec[0]**2 + repulsion_vec[1]**2)
                    if mag > 0: repulsion_vec = (repulsion_vec[0]/mag, repulsion_vec[1]/mag)

                safe_spot = self.planner.find_nearest_safe_spot((self.x, self.y), static_costmap, all_threat_paths, repulsion_vec)
                if safe_spot:
                    self.evasion_target = {"x": safe_spot[0], "y": safe_spot[1]}
                    self.target = self.evasion_target
                    world.reserve_haven(self.id, (safe_spot[0], safe_spot[1]))
                    path, visited = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles, static_costmap=static_costmap, world=world)
                    self.global_path = path
                    self.is_running = True; self.status = AGVStatus.EVADING
                else: self.status = AGVStatus.STUCK
                return

            path, visited = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles, static_costmap=static_costmap, world=world)
            if not path:
                self.global_path = []; return
            self.global_path = path; self.visited_nodes = visited
            if self.status != AGVStatus.EVADING:
                self.status = AGVStatus.EXECUTING if self.is_running else AGVStatus.IDLE
        finally:
            self.is_planning = False; self.replan_needed = False

    def update(self, dt: float, world):
        if self.replan_needed and not self.is_planning:
            world.release_haven(self.id)
            all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
            thread = threading.Thread(target=self._async_replan, args=(all_obs, world.static_costmap, world, self.status), daemon=True)
            thread.start()

        if self.global_path and self.is_running:
            min_dist = float("inf"); closest_idx = 0
            for i, wp in enumerate(self.global_path):
                d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
                if d < min_dist: min_dist = d; closest_idx = i
            projection = self.global_path[closest_idx :]
            world.update_path_occupancy(self.id, projection)
        else: world.clear_path_occupancy(self.id)

        if self.is_planning:
            self.v = 0; self.omega = 0; self.l_rpm, self.r_rpm = 0, 0; return

        if not self.is_running:
            self.status = AGVStatus.IDLE; self.v = 0; self.omega = 0
            world.release_haven(self.id) 
            self._last_compute_time += dt
            if self._last_compute_time >= 0.05:
                self.check_proactive_evasion(world); self._last_compute_time = 0.0
            self.l_rpm, self.r_rpm = 0, 0; return
        
        if self.status == AGVStatus.EVADING:
            self._last_compute_time += dt
            if self._last_compute_time >= 0.1:
                if not self._is_haven_safe(self.target["x"], self.target["y"], world):
                    self.check_proactive_evasion(world)
                self._last_compute_time = 0.0

        if not self.global_path: 
            self.l_rpm, self.r_rpm = 0, 0; return

        self._last_compute_time += dt
        if self._last_compute_time >= 0.05:
            if self.is_planning: 
                self._last_compute_time = 0.0; return

            all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
            min_dist = float("inf"); closest_idx = 0
            for i, wp in enumerate(self.global_path):
                d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
                if d < min_dist: min_dist = d; closest_idx = i
            lookahead = max(4 if abs(self.v) < 10 else 1, int(4 + abs(self.v) / 100.0))
            target_wp = self.global_path[min(closest_idx + lookahead, len(self.global_path)-1)]
            margin = 505 if self.status == AGVStatus.EVADING else 525
            max_speed_mms = self.max_rpm * self.kinematics.rpm_to_mms
            
            current_max_speed = max_speed_mms
            if self.status == AGVStatus.EXECUTING:
                for other_id, other_agv in world.agvs.items():
                    if other_id == self.id: continue
                    if other_agv.status == AGVStatus.EVADING:
                        dist = math.sqrt((other_agv.x - self.x)**2 + (other_agv.y - self.y)**2)
                        if dist < 5000: current_max_speed = 0.0; break
                    dist = math.sqrt((other_agv.x - self.x)**2 + (other_agv.y - self.y)**2)
                    if dist < 4000:
                        is_on_my_path = False
                        path_projection = world.path_occupancy.get(self.id, [])
                        for px, py in path_projection[:20]:
                            if math.sqrt((other_agv.x - px)**2 + (other_agv.y - py)**2) < 1200:
                                is_on_my_path = True; break
                        if is_on_my_path:
                            if dist < 2000: current_max_speed = 0.0 
                            else: current_max_speed = 100.0 

            # --- 智慧對接：進入設備前先對齊角度 ---
            is_docking_approach = False
            target_docking_angle = None
            if len(self.global_path) > 0:
                final_wp = self.global_path[-1]
                for ob in world.obstacles:
                    if ob.get('type') == 'equipment' and ob['x'] == final_wp[0] and ob['y'] == final_wp[1]:
                        target_docking_angle = ob.get('docking_angle')
                        dist_to_final = math.sqrt((self.x - final_wp[0])**2 + (self.y - final_wp[1])**2)
                        # 如果距離終點 2200mm 以內，視為進入「門口對齊區」
                        if dist_to_final < 2200:
                            is_docking_approach = True
                        break

            goto_controller = True
            force_forward_val = False

            if is_docking_approach and target_docking_angle is not None:
                target_rad = (target_docking_angle * math.pi) / 180.0
                angle_error = math.atan2(math.sin(target_rad - self.theta), math.cos(target_rad - self.theta))
                dist_to_final = math.sqrt((self.x - final_wp[0])**2 + (self.y - final_wp[1])**2)
                
                # 提前減速區：從 4000mm 開始 (跑道入口)
                if dist_to_final < 4000:
                    if abs(angle_error) > 0.15: 
                        current_max_speed = min(current_max_speed, 100.0) # 角度差太大，強迫極低速
                    elif abs(angle_error) > 0.05: 
                        current_max_speed = min(current_max_speed, 200.0)

                # 門口停靠點：2000mm 處 (給予一點緩衝 1950-2050)
                if dist_to_final > 1950:
                    if dist_to_final < 2100:
                        # 快到 2 米點了，減速準備停下
                        current_max_speed = min(current_max_speed, 80.0)
                else:
                    # 在 2000mm 處強制停下對齊
                    if dist_to_final > 1000 and abs(angle_error) > 0.04: 
                        if abs(self.v) > 20.0:
                            current_max_speed = 0.0 
                        else:
                            self.target_v = 0.0
                            self.target_omega = np.clip(angle_error * 2.5, -1.2, 1.2)
                            goto_controller = False 
                    else:
                        force_forward_val = True

            if goto_controller:
                ignore_id = self.culprit_id if self.status == AGVStatus.EVADING else None
                bv, bo, culprit = self.controller.compute_command(
                    self.x, self.y, self.theta, self.v, self.omega, 
                    target_wp, current_max_speed, all_obs, margin=margin, dt=0.05, 
                    ignore_id=ignore_id, status=self.status, force_forward=force_forward_val
                )
                self.target_v, self.target_omega = bv, bo; self.culprit_id = culprit; self._last_compute_time = 0.0
            
            if self.target_v == 0 and self.target_omega == 0 and not is_docking_approach:
                self.status = AGVStatus.STUCK
            else:
                self.status = AGVStatus.EXECUTING if self.status != AGVStatus.EVADING else AGVStatus.EVADING

        if self.status == AGVStatus.STUCK and self.v == 0:
            if not self.stuck_start_time: self.stuck_start_time = time.time()
            if time.time() - self.stuck_start_time > 2.0: 
                self.recovery_nudge_time = 0.5; self.stuck_start_time = None 
        else: self.stuck_start_time = None

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

        if self.mode == AGVMode.SIMULATION:
            dist_to_target = math.sqrt((self.x - self.target["x"])**2 + (self.y - self.target["y"])**2)
            target_docking_angle = None
            for ob in world.obstacles:
                if ob.get('type') == 'equipment' and ob['x'] == self.target["x"] and ob['y'] == self.target["y"]:
                    target_docking_angle = ob.get('docking_angle')
                    break
            angle_error = 0.0
            if target_docking_angle is not None:
                target_rad = (target_docking_angle * math.pi) / 180.0
                angle_error = math.atan2(math.sin(target_rad - self.theta), math.cos(target_rad - self.theta))

            if dist_to_target < 300:
                if target_docking_angle is not None and abs(angle_error) > 0.05: 
                    self.v = 0.0; self.target_v = 0.0
                    self.target_omega = np.clip(angle_error * 2.0, -1.0, 1.0)
                    self.status = AGVStatus.EXECUTING
                else:
                    self.is_running = False; self.status = AGVStatus.IDLE
                    self.v = 0; self.omega = 0; self.evasion_target = None; world.release_haven(self.id)
            
        self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)

    def check_proactive_evasion(self, world) -> bool:
        if self.status == AGVStatus.EVADING: return False
        for other_id, other_agv in world.agvs.items():
            if other_id == self.id: continue
            path_points = world.path_occupancy.get(other_id, [])
            if not path_points: continue
            for px, py in path_points:
                if math.sqrt((px - self.x)**2 + (py - self.y)**2) < 2000:
                    self.trigger_evasion(world, threat_pos=(other_agv.x, other_agv.y))
                    return True
        return False

    def trigger_evasion(self, world, threat_pos=None):
        all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
        thread = threading.Thread(target=self._async_replan, args=(all_obs, world.static_costmap, world, self.status, True), daemon=True)
        thread.start()

    def _is_haven_safe(self, tx, ty, world) -> bool:
        safe, _ = self.controller.is_pose_safe(tx, ty, self.theta, world.obstacles, margin=505)
        if not safe: return False
        for oid, hpos in world.reserved_havens.items():
            if oid != self.id and math.sqrt((tx-hpos[0])**2 + (ty-hpos[1])**2) < 1000: return False
        for oid, points in world.path_occupancy.items():
            if oid == self.id: continue
            for px, py in points:
                if math.sqrt((tx-px)**2 + (ty-py)**2) < 2000: return False
        return True
