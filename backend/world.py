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
        self.agvs: Dict[str, Any] = {}
        self.storage_file = "obstacles.json"
        self.load_obstacles() # 啟動時自動讀取

    def save_obstacles(self):
        """將目前障礙物存入檔案"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.obstacles, f, indent=2)
            logger.info(f"Obstacles saved to {self.storage_file}")
        except Exception as e:
            logger.error(f"Failed to save obstacles: {e}")

    def load_obstacles(self):
        """從檔案讀取障礙物"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.obstacles = json.load(f)
                logger.info(f"Loaded {len(self.obstacles)} obstacles from {self.storage_file}")
            except Exception as e:
                logger.error(f"Failed to load obstacles: {e}")
                self.obstacles = []

    def add_obstacle(self, ob: Dict[str, Any]):
        self.obstacles.append(ob)
        self.save_obstacles()

    def remove_obstacle(self, ob_id: str):
        self.obstacles = [o for o in self.obstacles if o.get("id") != ob_id]
        self.save_obstacles()

    def update_obstacle(self, ob_data: Dict[str, Any]):
        for ob in self.obstacles:
            if ob.get("id") == ob_data.get("id"):
                ob.update(ob_data)
                break
        self.save_obstacles()

    def clear_obstacles(self):
        self.obstacles = []
        self.save_obstacles()

    def is_safe(self, x: float, y: float, theta: float, margin: float = 525.0, exclude_agv_id: str = None) -> bool:
        if x < margin or x > self.width - margin or y < margin or y > self.height - margin:
            return False
        poly = translate(rotate(box(-margin, -margin, margin, margin), theta, use_radians=True), xoff=x, yoff=y)
        for ob in self.obstacles:
            if (x - ob['x'])**2 + (y - ob['y'])**2 > 3500**2: continue
            if ob['type'] == 'circle':
                ob_geom = Point(ob['x'], ob['y']).buffer(ob['radius'])
            else:
                ob_geom = translate(rotate(box(-ob['width']/2, -ob['height']/2, ob['width']/2, ob['height']/2), ob.get('angle', 0), use_radians=True), xoff=ob['x'], yoff=ob['y'])
            if poly.intersects(ob_geom): return False
        for other_id, other_agv in self.agvs.items():
            if other_id == exclude_agv_id: continue
            if (x - other_agv.x)**2 + (y - other_agv.y)**2 > 2000**2: continue
            other_geom = Point(other_agv.x, other_agv.y).buffer(800)
            if poly.intersects(other_geom): return False
        return True

    def get_dynamic_obstacles(self, exclude_agv_id: str) -> List[Dict[str, Any]]:
        dyn_obs = list(self.obstacles)
        for oid, o_agv in self.agvs.items():
            if oid != exclude_agv_id:
                dyn_obs.append({"type": "circle", "x": o_agv.x, "y": o_agv.y, "radius": 800})
        return dyn_obs
