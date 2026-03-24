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
    LOADING = "LOADING"     
    UNLOADING = "UNLOADING" 

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
        self.target_v = 0.0
        self.target_omega = 0.0
        self.evasion_target: Optional[Dict[str, float]] = None
        
        self.has_goods = False
        self.current_task: Optional[Dict[str, Any]] = None
        self.task_timer = 0.0

        if state_dict:
            self.x = state_dict.get("x", self.x); self.y = state_dict.get("y", self.y)
            self.theta = state_dict.get("theta", self.theta)
            self.target = state_dict.get("target", self.target)
            self.mode = AGVMode(state_dict.get("mode", self.mode))
            self.max_rpm = state_dict.get("max_rpm", self.max_rpm)
            self.status = AGVStatus(state_dict.get("status", self.status))
            self.has_goods = state_dict.get("has_goods", False)
            self.current_task = state_dict.get("current_task")
            self.is_running = state_dict.get("is_running", False)
            self.replan_needed = True if self.target != {"x": self.x, "y": self.y} else False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "x": self.x, "y": self.y, "theta": self.theta,
            "v": self.v, "omega": self.omega, "l_rpm": self.l_rpm, "r_rpm": self.r_rpm,
            "target": self.target, "status": self.status, "mode": self.mode, "has_goods": self.has_goods,
            "is_running": self.is_running, "is_planning": self.is_planning,
            "path": self.global_path, "visited": self.visited_nodes,
            "max_rpm": self.max_rpm, "culprit_id": self.culprit_id,
            "evasion_target": self.evasion_target, "current_task": self.current_task
        }

    def _async_replan(self, obstacles, static_costmap, world=None, original_status=None, is_evasion_search=False):
        self.is_planning = True
        try:
            if is_evasion_search:
                all_threat_paths = [p for oid, p in world.path_occupancy.items() if oid != self.id]
                safe_spot = self.planner.find_nearest_safe_spot((self.x, self.y), static_costmap, all_threat_paths)
                if safe_spot:
                    self.evasion_target = {"x": safe_spot[0], "y": safe_spot[1]}
                    self.target = self.evasion_target
                    path, visited = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles, static_costmap=static_costmap, world=world)
                    self.global_path = path; self.is_running = True; self.status = AGVStatus.EVADING
                else: self.status = AGVStatus.STUCK
                return
            path, visited = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles, static_costmap=static_costmap, world=world)
            if not path: self.global_path = []; return
            self.global_path = path; self.visited_nodes = visited
            if self.status != AGVStatus.EVADING:
                self.status = AGVStatus.EXECUTING if self.is_running else AGVStatus.IDLE
        finally:
            self.is_planning = False; self.replan_needed = False

    def update(self, dt: float, world):
        # 1. 裝卸料計時處理
        if self.status in [AGVStatus.LOADING, AGVStatus.UNLOADING]:
            self.v = 0; self.omega = 0; self.target_v = 0; self.target_omega = 0
            self.task_timer -= dt
            if self.task_timer <= 0:
                if self.status == AGVStatus.LOADING:
                    self.has_goods = True
                    if self.current_task:
                        source = next((o for o in world.obstacles if o["id"] == self.current_task["source_id"]), None)
                        if source: source["has_goods"] = False; world.save_obstacles()
                        tid = self.current_task.get("target_id")
                        if tid:
                            target_ob = next((o for o in world.obstacles if o["id"] == tid), None)
                            if target_ob:
                                self.target = {"x": target_ob["x"], "y": target_ob["y"]}
                                self.status = AGVStatus.EXECUTING; self.is_running = True; self.replan_needed = True
                            else: world.complete_task(self.current_task["source_id"], None); self.status = AGVStatus.IDLE; self.is_running = False; self.current_task = None
                        else: world.complete_task(self.current_task["source_id"], None); self.status = AGVStatus.IDLE; self.is_running = False; self.current_task = None
                else:
                    self.has_goods = False
                    if self.current_task:
                        target_ob = next((o for o in world.obstacles if o["id"] == self.current_task["target_id"]), None)
                        if target_ob: target_ob["has_goods"] = True; world.save_obstacles()
                        world.complete_task(self.current_task.get("source_id"), self.current_task["target_id"])
                    self.status = AGVStatus.IDLE; self.is_running = False; self.current_task = None
            self.l_rpm, self.r_rpm = 0, 0; return

        # 2. 路徑規劃與避讓檢查
        if self.replan_needed and not self.is_planning:
            all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
            threading.Thread(target=self._async_replan, args=(all_obs, world.static_costmap, world), daemon=True).start()

        self._last_compute_time += dt
        # 定期檢查避讓
        if self._last_compute_time >= 0.05:
            if self.status != AGVStatus.LOADING and self.status != AGVStatus.UNLOADING:
                self.check_proactive_evasion(world)

        # 3. 路徑佔用發布
        if self.global_path and self.is_running:
            min_dist = float("inf"); closest_idx = 0
            for i, wp in enumerate(self.global_path):
                d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
                if d < min_dist: min_dist = d; closest_idx = i
            world.update_path_occupancy(self.id, self.global_path[closest_idx :])
        else: world.clear_path_occupancy(self.id)

        if not self.is_running or not self.global_path:
            self.v = 0; self.omega = 0; self.l_rpm, self.r_rpm = 0, 0; return

        # 4. 控制指令計算
        if self._last_compute_time >= 0.05:
            self._last_compute_time = 0.0
            all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
            
            min_dist = float("inf"); closest_idx = 0
            for i, wp in enumerate(self.global_path):
                d = (wp[0]-self.x)**2 + (wp[1]-self.y)**2
                if d < min_dist: min_dist = d; closest_idx = i
            
            lookahead = max(1, int(4 + abs(self.v) / 100.0))
            target_wp = self.global_path[min(closest_idx + lookahead, len(self.global_path)-1)]
            
            is_docking = False; target_angle = None; final_wp = self.global_path[-1]
            for ob in world.obstacles:
                if ob.get('type') == 'equipment' and ob['x'] == final_wp[0] and ob['y'] == final_wp[1]:
                    target_angle = ob.get('docking_angle')
                    if math.sqrt((self.x - final_wp[0])**2 + (self.y - final_wp[1])**2) < 3200:
                        is_docking = True; break

            force_forward = False; goto_ctrl = True; max_speed = self.max_rpm * self.kinematics.rpm_to_mms
            if is_docking and target_angle is not None:
                target_rad = (target_angle * math.pi) / 180.0
                err = math.atan2(math.sin(target_rad - self.theta), math.cos(target_rad - self.theta))
                dist = math.sqrt((self.x - final_wp[0])**2 + (self.y - final_wp[1])**2)
                if dist < 4000: max_speed = min(max_speed, 200.0 if abs(err) > 0.1 else 400.0)
                if 1950 < dist < 2100:
                    if abs(err) > 0.04:
                        if abs(self.v) > 20: self.target_v = 0; self.target_omega = 0
                        else: self.target_v = 0; self.target_omega = np.clip(err * 2.5, -1.2, 1.2)
                        goto_ctrl = False
                    else: force_forward = True
                elif dist <= 1950: force_forward = True

            if goto_ctrl:
                ignore_id = self.culprit_id if self.status == AGVStatus.EVADING else None
                bv, bo, culprit = self.controller.compute_command(self.x, self.y, self.theta, self.v, self.omega, target_wp, max_speed, all_obs, dt=0.05, force_forward=force_forward, ignore_id=ignore_id)
                self.target_v, self.target_omega = bv, bo; self.culprit_id = culprit

        # 5. 物理更新與安全檢查
        self.v, self.omega = self.controller.limit_physics(self.target_v, self.target_omega, self.v, self.omega, self.max_rpm * self.kinematics.rpm_to_mms, dt)
        new_x, new_y, new_theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, dt)
        
        # 安全檢查
        all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
        margin = 505 if self.status == AGVStatus.EVADING else 525
        safe, _ = self.controller.is_pose_safe(new_x, new_y, new_theta, all_obs, margin=margin)
        if safe:
            self.x, self.y, self.theta = new_x, new_y, new_theta
        else:
            self.v = 0; self.omega = 0; self.target_v = 0; self.target_omega = 0

        # 6. 任務完成判定
        dist_final = math.sqrt((self.x - self.target["x"])**2 + (self.y - self.target["y"])**2)
        if dist_final < 300:
            if self.current_task:
                source_x = next((o["x"] for o in world.obstacles if o["id"] == self.current_task.get("source_id")), None)
                source_y = next((o["y"] for o in world.obstacles if o["id"] == self.current_task.get("source_id")), None)
                is_at_source = (abs(self.target["x"] - source_x) < 10 and abs(self.target["y"] - source_y) < 10) if source_x else False
                if is_at_source and not self.has_goods:
                    self.status = AGVStatus.LOADING; self.task_timer = 5.0
                else:
                    self.status = AGVStatus.UNLOADING; self.task_timer = 5.0
                self.v = 0; self.omega = 0
            else:
                self.is_running = False; self.status = AGVStatus.IDLE; self.v = 0; self.omega = 0
        self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)

    def check_proactive_evasion(self, world) -> bool:
        # --- 關鍵修正 2：正在執行物流任務的車輛擁有最高優先權，不進行避讓 ---
        if self.current_task is not None:
            return False
            
        if self.status == AGVStatus.EVADING: return False
        
        for other_id, other_agv in world.agvs.items():
            if other_id == self.id: continue
            
            # 獲取其他車輛的規劃路徑投影
            path_points = world.path_occupancy.get(other_id, [])
            if not path_points: continue
            
            # --- 關鍵修正 1：擴大掃描範圍，實現「提前閃車」 ---
            # 檢查對方前方 100 個路徑點 (約 20 米) 是否會經過我目前的位置
            # 只要對方路徑會穿過我 2.5 米內，我就必須讓路
            for px, py in path_points[:100]: 
                if math.sqrt((px - self.x)**2 + (py - self.y)**2) < 2500:
                    logger.info(f"AGV {self.id} is in the way of {other_id}'s path. Triggering proactive evasion.")
                    self.trigger_evasion(world)
                    return True
        return False

    def trigger_evasion(self, world):
        all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
        threading.Thread(target=self._async_replan, args=(all_obs, world.static_costmap, world, self.status, True), daemon=True).start()
