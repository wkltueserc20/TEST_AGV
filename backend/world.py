import math
import json
import os
import logging
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class World:
    def __init__(self, width=50000.0, height=50000.0):
        self.width = width
        self.height = height
        self.obstacles: List[Dict[str, Any]] = []
        self.agvs: Dict[str, Any] = {}
        self.storage_file = "obstacles.json"
        
        # 效能優化：預處理代價地圖 (解析度 200mm)
        self.grid_res = 200.0
        self.nx = int(width // self.grid_res)
        self.ny = int(height // self.grid_res)
        self.static_costmap = None # 會在 load_obstacles 後計算
        
        self.load_obstacles()

    def save_obstacles(self):
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.obstacles, f, indent=2)
            self.update_static_costmap() # 每次儲存後更新地圖
        except Exception as e:
            logger.error(f"Failed to save obstacles: {e}")

    def load_obstacles(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.obstacles = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load obstacles: {e}")
                self.obstacles = []
        self.update_static_costmap()

    def update_static_costmap(self):
        """
        預計算靜態障礙物的勢場代價。
        這讓 A* 搜尋從 O(N*M) 變為 O(N) 的查表運算。
        """
        logger.info("Computing static costmap...")
        # 初始化為邊界斥力
        costmap = np.zeros((self.nx, self.ny))
        
        # 預處理障礙物邊界以加快內部循環
        obs_rects = []
        for ob in self.obstacles:
            if ob['type'] == 'rectangle':
                w, h = ob.get('width', 1000), ob.get('height', 1000)
                obs_rects.append((ob['x'] - w/2, ob['y'] - h/2, ob['x'] + w/2, ob['y'] + h/2))
        
        for gx in range(self.nx):
            wx = gx * self.grid_res
            for gy in range(self.ny):
                wy = gy * self.grid_res
                
                # 1. 邊界距離
                min_d = min(wx, self.width - wx, wy, self.height - wy)
                
                # 2. 靜態障礙物距離
                for r in obs_rects:
                    dx = max(r[0] - wx, 0, wx - r[2])
                    dy = max(r[1] - wy, 0, wy - r[3])
                    d = math.sqrt(dx**2 + dy**2)
                    if d < min_d: min_d = d
                
                # 3. 計算代價 (使用與 Planner 一致的公式)
                if min_d < 550: 
                    costmap[gx, gy] = 1000000.0
                elif min_d < 2000:
                    costmap[gx, gy] = (2000.0 / min_d) ** 4
                else:
                    costmap[gx, gy] = 0
        
        self.static_costmap = costmap
        logger.info("Static costmap update complete.")

    def add_obstacle(self, ob: Dict[str, Any]):
        self.obstacles.append(ob); self.save_obstacles()

    def remove_obstacle(self, ob_id: str):
        self.obstacles = [o for o in self.obstacles if o.get("id") != ob_id]; self.save_obstacles()

    def update_obstacle(self, ob_data: Dict[str, Any]):
        for ob in self.obstacles:
            if ob.get("id") == ob_data.get("id"):
                ob.update(ob_data); break
        self.save_obstacles()

    def clear_obstacles(self):
        self.obstacles = []; self.save_obstacles()

    def get_dynamic_obstacles(self, exclude_agv_id: str) -> List[Dict[str, Any]]:
        dyn_obs = [] # 這裡只回傳其他 AGV，因為靜態障礙物已在 costmap 中
        for oid, o_agv in self.agvs.items():
            if oid != exclude_agv_id:
                dyn_obs.append({
                    "id": oid, "type": "circle", "x": o_agv.x, "y": o_agv.y, "radius": 850.0 
                })
        return dyn_obs
