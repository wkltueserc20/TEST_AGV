import math
import json
import os
import logging
import threading
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from agv import AGV

logger = logging.getLogger(__name__)

class World:
    def __init__(self, width=50000.0, height=50000.0):
        self.width = width
        self.height = height
        self.obstacles: List[Dict[str, Any]] = []
        self.agvs: Dict[str, AGV] = {}
        self.path_occupancy: Dict[str, List[Tuple[float, float]]] = {}
        self.reserved_havens: Dict[str, Tuple[float, float]] = {} 
        self.storage_file = "obstacles.json"
        self.agvs_storage_file = "agvs.json"
        
        self.grid_res = 200.0
        self.nx = int(width // self.grid_res)
        self.ny = int(height // self.grid_res)
        
        self.static_costmap = np.zeros((self.nx, self.ny))
        self._map_lock = threading.Lock()
        self._is_updating = False
        self._needs_recompute = False 
        
        self.load_obstacles()
        self.load_agvs()

    def save_obstacles(self):
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.obstacles, f, indent=2)
            self.update_static_costmap()
        except Exception as e:
            logger.error(f"Failed to save obstacles: {e}")

    def load_obstacles(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.obstacles = json.load(f)
                for i, ob in enumerate(self.obstacles):
                    if not ob.get("id"):
                        ob["id"] = f"ob-{i}-{int(ob['x'])}-{int(ob['y'])}"
            except Exception as e:
                logger.error(f"Failed to load obstacles: {e}")
                self.obstacles = []
        self.update_static_costmap()

    def save_agvs(self):
        """將所有 AGV 狀態儲存至 JSON (記憶功能)"""
        try:
            data = {}
            for aid, a in self.agvs.items():
                data[aid] = a.to_dict()
            with open(self.agvs_storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save AGVs: {e}")

    def load_agvs(self):
        """從 JSON 恢復 AGV 狀態"""
        if os.path.exists(self.agvs_storage_file):
            try:
                with open(self.agvs_storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for aid, state in data.items():
                    self.agvs[aid] = AGV(aid, state["x"], state["y"], state["theta"], state_dict=state)
                logger.info(f"Loaded {len(self.agvs)} AGVs from memory.")
            except Exception as e:
                logger.error(f"Failed to load AGVs: {e}")
                self.agvs = {}

    def update_static_costmap(self):
        if self._is_updating:
            self._needs_recompute = True
            return
        
        self._needs_recompute = False
        current_obs = list(self.obstacles)
        thread = threading.Thread(target=self._compute_costmap_task, args=(current_obs,), daemon=True)
        thread.start()

    def _compute_costmap_task(self, obs_list):
        self._is_updating = True
        try:
            new_map = np.zeros((self.nx, self.ny))
            obs_geoms = []
            for ob in obs_list:
                if ob['type'] == 'rectangle':
                    w, h = ob.get('width', 1000), ob.get('height', 1000)
                    obs_geoms.append(('rect', ob['x'] - w/2, ob['y'] - h/2, ob['x'] + w/2, ob['y'] + h/2))
                elif ob['type'] == 'equipment':
                    # 設備為 2m x 2m，半徑 1000mm
                    obs_geoms.append(('equipment', ob['x'], ob['y'], ob.get('radius', 1000)))
                else:
                    obs_geoms.append(('circle', ob['x'], ob['y'], ob.get('radius', 500)))
            
            for gx in range(self.nx):
                wx = gx * self.grid_res
                for gy in range(self.ny):
                    wy = gy * self.grid_res
                    min_d = min(wx, self.width - wx, wy, self.height - wy)
                    
                    for kind, *data in obs_geoms:
                        if kind == 'rect':
                            dx = max(data[0] - wx, 0, wx - data[2])
                            dy = max(data[1] - wy, 0, wy - data[3])
                            d = math.sqrt(dx**2 + dy**2)
                        else:
                            # 圓形、設備都統一處理為圓形幾何
                            d = math.sqrt((data[0] - wx)**2 + (data[1] - wy)**2) - data[2]
                        
                        if d < min_d: min_d = d
                    
                    # 恢復最簡單的障礙物邏輯：離任何障礙物邊緣 550mm 以內都是無限成本 (牆壁)
                    if min_d < 550: 
                        new_map[gx, gy] = 1000000.0
                    elif min_d < 2000: 
                        new_map[gx, gy] = (2000.0 / min_d) ** 4
                    else:
                        new_map[gx, gy] = 0.0
            
            with self._map_lock:
                self.static_costmap = new_map
            logger.info("Costmap computation complete.")
        except Exception as e:
            logger.error(f"Costmap failed: {e}")
        finally:
            self._is_updating = False
            if self._needs_recompute:
                self.update_static_costmap()

    def add_obstacle(self, ob: Dict[str, Any]):
        self.obstacles.append(ob); self.save_obstacles()

    def remove_obstacle(self, ob_id: str):
        if not ob_id: return
        original_count = len(self.obstacles)
        self.obstacles = [o for o in self.obstacles if str(o.get("id")) != str(ob_id)]
        if len(self.obstacles) < original_count:
            logger.info(f"Obstacle {ob_id} removed from data list.")
            self.save_obstacles()

    def update_obstacle(self, ob_data: Dict[str, Any]):
        # 支援 ID 重新命名：old_id -> new_id
        target_id = ob_data.get("old_id") or ob_data.get("id")
        new_id = ob_data.get("new_id")
        
        for ob in self.obstacles:
            if str(ob.get("id")) == str(target_id):
                if new_id:
                    ob["id"] = new_id
                # 更新其他屬性
                for k, v in ob_data.items():
                    if k not in ["id", "old_id", "new_id"]:
                        ob[k] = v
                break
        self.save_obstacles()

    def clear_obstacles(self):
        self.obstacles = []
        self.save_obstacles()

    def update_path_occupancy(self, agv_id: str, path_points: List[Tuple[float, float]]):
        self.path_occupancy[agv_id] = path_points

    def clear_path_occupancy(self, agv_id: str):
        if agv_id in self.path_occupancy:
            del self.path_occupancy[agv_id]

    def reserve_haven(self, agv_id: str, pos: Tuple[float, float]):
        self.reserved_havens[agv_id] = pos

    def release_haven(self, agv_id: str):
        if agv_id in self.reserved_havens:
            del self.reserved_havens[agv_id]

    def get_dynamic_obstacles(self, exclude_agv_id: str) -> List[Dict[str, Any]]:
        dyn_obs = []
        for oid, o_agv in self.agvs.items():
            if oid != exclude_agv_id:
                dyn_obs.append({"id": oid, "type": "circle", "x": o_agv.x, "y": o_agv.y, "radius": 850.0})
        return dyn_obs
