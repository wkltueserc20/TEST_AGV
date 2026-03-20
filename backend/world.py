import math
import json
import os
import logging
import threading
import numpy as np
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class World:
    def __init__(self, width=50000.0, height=50000.0):
        self.width = width
        self.height = height
        self.obstacles: List[Dict[str, Any]] = []
        self.agvs: Dict[str, Any] = {}
        self.path_occupancy: Dict[str, List[Tuple[float, float]]] = {}
        self.storage_file = "obstacles.json"
        
        self.grid_res = 200.0
        self.nx = int(width // self.grid_res)
        self.ny = int(height // self.grid_res)
        
        self.static_costmap = np.zeros((self.nx, self.ny))
        self._map_lock = threading.Lock()
        self._is_updating = False
        self._needs_recompute = False # 記錄是否在計算中又有新的變動
        
        self.load_obstacles()

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

    def update_static_costmap(self):
        """觸發地圖重算，支援併發請求"""
        if self._is_updating:
            # 如果正在算，標記「算完後要再算一次最新版」
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
                            d = math.sqrt((data[0] - wx)**2 + (data[1] - wy)**2) - data[2]
                        if d < min_d: min_d = d
                    if min_d < 550: new_map[gx, gy] = 1000000.0
                    elif min_d < 2000: new_map[gx, gy] = (2000.0 / min_d) ** 4
            
            with self._map_lock:
                self.static_costmap = new_map
            logger.info("Costmap computation complete.")
        except Exception as e:
            logger.error(f"Costmap failed: {e}")
        finally:
            self._is_updating = False
            # 核心修正：如果計算期間又有新變動，立刻再啟動一輪
            if self._needs_recompute:
                self.update_static_costmap()

    def add_obstacle(self, ob: Dict[str, Any]):
        self.obstacles.append(ob); self.save_obstacles()

    def remove_obstacle(self, ob_id: str):
        # 修正：更安全的 ID 比對
        if not ob_id: return
        original_count = len(self.obstacles)
        self.obstacles = [o for o in self.obstacles if str(o.get("id")) != str(ob_id)]
        if len(self.obstacles) < original_count:
            logger.info(f"Obstacle {ob_id} removed from data list.")
            self.save_obstacles()

    def update_obstacle(self, ob_data: Dict[str, Any]):
        for ob in self.obstacles:
            if str(ob.get("id")) == str(ob_data.get("id")):
                ob.update(ob_data); break
        self.save_obstacles()

    def clear_obstacles(self):
        self.obstacles = []
        self.save_obstacles()

    def update_path_occupancy(self, agv_id: str, path_points: List[Tuple[float, float]]):
        self.path_occupancy[agv_id] = path_points

    def clear_path_occupancy(self, agv_id: str):
        if agv_id in self.path_occupancy:
            del self.path_occupancy[agv_id]

    def get_dynamic_obstacles(self, exclude_agv_id: str) -> List[Dict[str, Any]]:
        dyn_obs = []
        for oid, o_agv in self.agvs.items():
            if oid != exclude_agv_id:
                dyn_obs.append({"id": oid, "type": "circle", "x": o_agv.x, "y": o_agv.y, "radius": 850.0})
        return dyn_obs
