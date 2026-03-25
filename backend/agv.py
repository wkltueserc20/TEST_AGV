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
    WAITING = "WAITING"
    THINKING = "THINKING"
    YIELDING = "YIELDING"

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
        self._last_closest_idx = 0
        
        # Traffic Control 擴充
        self.original_target: Optional[Dict[str, float]] = None
        self.yielding_to_id: Optional[str] = None

        if state_dict:
            self.x = state_dict.get("x", self.x); self.y = state_dict.get("y", self.y)
            self.theta = state_dict.get("theta", self.theta)
            self.target = state_dict.get("target", self.target)
            self.mode = AGVMode(state_dict.get("mode", self.mode))
            self.max_rpm = state_dict.get("max_rpm", self.max_rpm)
            self.has_goods = state_dict.get("has_goods", False)
            self.current_task = state_dict.get("current_task")
            # 修正 1：重啟程式時，強制回歸 IDLE，並將目標設為當前位置，防止非同步規劃誤啟動
            self.status = AGVStatus.IDLE
            self.is_running = False 
            self.target = {"x": self.x, "y": self.y}
            self.replan_needed = False

    def get_priority(self) -> int:
        # 數字越小優先級越高。沒任務為 100，有任務預設為 5。
        if not self.current_task:
            return 100
        return self.current_task.get("priority", 5)

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

    def _async_replan(self, obstacles, static_costmap, world=None, original_status=None, is_evasion_search=False, yielding_to_id=None):
        self.is_planning = True
        try:
            if is_evasion_search:
                # 獲取威脅路徑 (特別是對方的高優先級路徑)
                all_threat_paths = []
                if yielding_to_id and yielding_to_id in world.path_occupancy:
                    all_threat_paths.append(world.path_occupancy[yielding_to_id])
                else:
                    all_threat_paths = [p for oid, p in world.path_occupancy.items() if oid != self.id]
                
                safe_spot = self.planner.find_nearest_safe_spot((self.x, self.y), static_costmap, all_threat_paths)
                if safe_spot:
                    # 進入避讓模式，記錄原始目標
                    if self.status not in [AGVStatus.YIELDING, AGVStatus.EVADING]:
                        self.original_target = {"x": self.target["x"], "y": self.target["y"]}
                    
                    self.evasion_target = {"x": safe_spot[0], "y": safe_spot[1]}
                    self.target = self.evasion_target
                    self.yielding_to_id = yielding_to_id
                    
                    path, visited = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles, static_costmap=static_costmap, world=world)
                    self.global_path = path; self._last_closest_idx = 0; self.is_running = True
                    self.status = AGVStatus.YIELDING
                else:
                    self.status = AGVStatus.STUCK
                return

            path, visited = self.planner.get_path([self.x, self.y], [self.target["x"], self.target["y"]], obstacles, static_costmap=static_costmap, world=world)
            if not path: self.global_path = []; self._last_closest_idx = 0; return
            self.global_path = path; self._last_closest_idx = 0; self.visited_nodes = visited
            
            # 安全更新狀態：避免蓋掉裝卸料、避讓或等待狀態
            if self.status in [AGVStatus.PLANNING, AGVStatus.EXECUTING, AGVStatus.IDLE]:
                # 如果有目標要移動，就設為 EXECUTING，否則設為 IDLE
                self.status = AGVStatus.EXECUTING if (self.is_running or self.target != {"x": self.x, "y": self.y}) else AGVStatus.IDLE
            elif self.status in [AGVStatus.YIELDING, AGVStatus.WAITING]:
                # 避讓路徑規劃完畢，繼續執行避讓任務，確保 is_running 為 True
                self.is_running = True
        finally:
            self.is_planning = False; self.replan_needed = False

    def update(self, dt: float, world):
        # 1. 狀態速度鎖定：裝卸料、等待中、思考中或受困時，強制禁止移動並立即回傳
        if self.status in [AGVStatus.LOADING, AGVStatus.UNLOADING, AGVStatus.WAITING, AGVStatus.THINKING, AGVStatus.STUCK]:
            self.v = 0; self.omega = 0; self.target_v = 0; self.target_omega = 0
            self.l_rpm, self.r_rpm = 0, 0
            
            # --- Traffic Control: WAITING 狀態下的任務恢復偵測 ---
            if self.status == AGVStatus.WAITING:
                # 修正：如果完全沒有任務，則不應待在 WAITING，直接轉為 IDLE
                if not self.current_task:
                    logger.info(f"AGV {self.id} has no task. Resetting from WAITING to IDLE.")
                    self.status = AGVStatus.IDLE
                    self.is_running = False
                    self.yielding_to_id = None
                    self.original_target = None
                    return

                if self.yielding_to_id:
                    # 強制至少等待 15 秒再重新規劃，避免震盪
                    if self.wait_start_time and (time.time() - self.wait_start_time > 15.0):
                        if self.original_target:
                            other_path = world.path_occupancy.get(self.yielding_to_id, [])
                            conflict_cleared = True
                            if other_path:
                                for ox, oy in other_path[:100]:
                                    if (ox - self.x)**2 + (oy - self.y)**2 < 6250000: # 2.5m
                                        conflict_cleared = False; break
                            
                            if conflict_cleared:
                                logger.info(f"AGV {self.id} conflict with {self.yielding_to_id} cleared. Resuming task.")
                                self.target = self.original_target
                                self.original_target = None
                                self.yielding_to_id = None
                                self.is_running = True
                                self.replan_needed = True
                                self.status = AGVStatus.PLANNING
                                return # 立即回傳，讓下一幀啟動規劃

            # 裝卸料計時處理
            if self.status in [AGVStatus.LOADING, AGVStatus.UNLOADING]:
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
            return

        # 2. 路徑規劃與避讓檢查
        if self.replan_needed and not self.is_planning:
            all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
            threading.Thread(target=self._async_replan, args=(all_obs, world.static_costmap, world), daemon=True).start()

        self._last_compute_time += dt
        # 定期檢查避讓
        if self._last_compute_time >= 0.05:
            # 移除 status 限制，允許裝卸料時也能偵測並執行避讓
            self.check_proactive_evasion(world)
        # --- 效能優化：單次 O(1) 路徑索引搜尋 ---
        closest_idx = self._last_closest_idx
        if self.global_path:
            min_dist = float("inf")
            # 只在上次最近點附近往前尋找 (窗口大小 20)
            search_end = min(len(self.global_path), self._last_closest_idx + 20)
            for i in range(self._last_closest_idx, search_end):
                d = (self.global_path[i][0] - self.x)**2 + (self.global_path[i][1] - self.y)**2
                if d < min_dist:
                    min_dist = d
                    closest_idx = i
            # 更新快取
            self._last_closest_idx = closest_idx

        # 3. 路徑佔用發布
        if self.global_path and self.is_running:
            world.update_path_occupancy(self.id, self.global_path[closest_idx :])
        else: world.clear_path_occupancy(self.id)

        if not self.is_running or not self.global_path:
            self.v = 0; self.omega = 0; self.l_rpm, self.r_rpm = 0, 0; return

        # 4. 控制指令計算
        if self._last_compute_time >= 0.05:
            self._last_compute_time = 0.0
            all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
            
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
                bv, bo, culprit = self.controller.compute_command(self.x, self.y, self.theta, self.v, self.omega, target_wp, max_speed, all_obs, dt=0.05, force_forward=force_forward, ignore_id=ignore_id, obstacle_geoms=world.obstacle_geoms)
                self.target_v, self.target_omega = bv, bo; self.culprit_id = culprit

        # 5. 物理更新與安全檢查
        self.v, self.omega = self.controller.limit_physics(self.target_v, self.target_omega, self.v, self.omega, self.max_rpm * self.kinematics.rpm_to_mms, dt)
        new_x, new_y, new_theta = self.kinematics.update_pose(self.x, self.y, self.theta, self.v, self.omega, dt)
        
        # 安全檢查
        all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
        margin = 505 if self.status == AGVStatus.EVADING else 525
        safe, _ = self.controller.is_pose_safe(new_x, new_y, new_theta, all_obs, margin=margin, obstacle_geoms=world.obstacle_geoms)
        if safe:
            self.x, self.y, self.theta = new_x, new_y, new_theta
        else:
            self.v = 0; self.omega = 0; self.target_v = 0; self.target_omega = 0

        # 6. 任務完成判定
        dist_final = math.sqrt((self.x - self.target["x"])**2 + (self.y - self.target["y"])**2)
        if dist_final < 300:
            if self.status in [AGVStatus.YIELDING, AGVStatus.EVADING]:
                # 到達避讓點，進入等待狀態
                self.status = AGVStatus.WAITING
                self.wait_start_time = time.time() # 記錄開始等待時間
                self.v = 0; self.omega = 0
            elif self.current_task and self.status not in [AGVStatus.WAITING, AGVStatus.THINKING]:
                # 只有在非避讓狀態下，才允許檢查是否到達任務工位
                source_x = next((o["x"] for o in world.obstacles if o["id"] == self.current_task.get("source_id")), None)
                source_y = next((o["y"] for o in world.obstacles if o["id"] == self.current_task.get("source_id")), None)
                target_x = next((o["x"] for o in world.obstacles if o["id"] == self.current_task.get("target_id")), None)
                target_y = next((o["y"] for o in world.obstacles if o["id"] == self.current_task.get("target_id")), None)

                # 判定是到達取貨點還是卸貨點
                is_at_source = (abs(self.target["x"] - source_x) < 10 and abs(self.target["y"] - source_y) < 10) if source_x else False
                is_at_target = (abs(self.target["x"] - target_x) < 10 and abs(self.target["y"] - target_y) < 10) if target_x else False

                if is_at_source and not self.has_goods:
                    self.status = AGVStatus.LOADING; self.task_timer = 5.0
                elif is_at_target and self.has_goods:
                    self.status = AGVStatus.UNLOADING; self.task_timer = 5.0
                else:
                    # 如果到達的地方既不是取貨點也不是卸貨點 (例如避讓點)
                    # 且目前不是 IDLE，則應維持目前狀態或進入 WAITING
                    if self.status != AGVStatus.IDLE:
                        self.status = AGVStatus.WAITING
                        self.wait_start_time = time.time()
                self.v = 0; self.omega = 0; self.is_running = (self.status != AGVStatus.IDLE)
            elif self.status not in [AGVStatus.WAITING, AGVStatus.YIELDING, AGVStatus.EVADING]:
                # 只有在非任務、非避讓且非等待的情況下，才停止運行並轉為 IDLE
                self.is_running = False; self.status = AGVStatus.IDLE; self.v = 0; self.omega = 0
        self.l_rpm, self.r_rpm = self.kinematics.velocity_to_rpm(self.v, self.omega)

    def check_proactive_evasion(self, world) -> bool:
        if self.status in [AGVStatus.EVADING, AGVStatus.YIELDING, AGVStatus.THINKING]:
            return False
        
        # --- 設備安全區保護：如果 AGV 還在設備中心附近（尚未完全出門），暫不觸發避讓 ---
        if self.current_task:
            source_ob = next((o for o in world.obstacles if o["id"] == self.current_task.get("source_id")), None)
            if source_ob:
                dist_to_source = math.sqrt((self.x - source_ob["x"])**2 + (self.y - source_ob["y"])**2)
                # 距離起點設備中心 2.5 米內，視為「尚在設備內部/出門跑道上」
                if dist_to_source < 2500:
                    return False

        my_prio = self.get_priority()
        my_path = self.global_path[self._last_closest_idx : self._last_closest_idx + 100]
        if not my_path: # 如果沒路徑，獲取當前位置作為佔用
            my_path = [(self.x, self.y)]

        for other_id, other_agv in world.agvs.items():
            if other_id == self.id: continue
            
            other_path = world.path_occupancy.get(other_id, [])
            if not other_path: continue
            
            # 1. 偵測路徑衝突 (未來 100 點)
            has_conflict = False
            for mx, my in my_path:
                for ox, oy in other_path[:100]:
                    if (mx - ox)**2 + (my - oy)**2 < 6250000: # 2.5m
                        has_conflict = True; break
                if has_conflict: break
            
            if not has_conflict: continue

            # 2. 優先級與 ID 仲裁
            other_prio = other_agv.get_priority()
            should_i_yield = False
            
            if my_prio > other_prio:
                should_i_yield = True # 優先級低 (數字大) 的讓行
            elif my_prio == other_prio:
                if self.id < other_id:
                    should_i_yield = True # 優先級相同，ID 小的讓行
            
            if should_i_yield:
                logger.info(f"AGV {self.id} (Prio {my_prio}) yields to {other_id} (Prio {other_prio}). Conflict detected.")
                self.status = AGVStatus.THINKING
                self.trigger_evasion(world, other_id)
                return True
                
        return False

    def trigger_evasion(self, world, other_id=None):
        if self.is_planning:
            return 
        all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
        threading.Thread(target=self._async_replan, args=(all_obs, world.static_costmap, world, self.status, True, other_id), daemon=True).start()
