import math
import json
import os
import logging
from typing import List, Dict, Any
from shapely.geometry import Point, box
from shapely.affinity import rotate, translate

logger = logging.getLogger(__name__)

class World:
    def __init__(self, width=50000.0, height=50000.0):
        self.width = width
        self.height = height
        self.obstacles: List[Dict[str, Any]] = []
        self.agvs: Dict[str, Any] = {} # 這裡存儲 AGV 實例
        self.storage_file = "obstacles.json"
        self.load_obstacles()

    def save_obstacles(self):
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.obstacles, f, indent=2)
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
        """
        獲取所有障礙物，包括目前正在移動的其他 AGV。
        """
        dyn_obs = list(self.obstacles)
        for oid, o_agv in self.agvs.items():
            if oid != exclude_agv_id:
                # 將其他車輛視為 850mm 圓形障礙物，留出 1m 通道的安全餘裕
                dyn_obs.append({
                    "id": oid,
                    "type": "circle",
                    "x": o_agv.x,
                    "y": o_agv.y,
                    "radius": 850.0 
                })
        return dyn_obs
