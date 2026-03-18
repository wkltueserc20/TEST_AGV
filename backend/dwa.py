import numpy as np
import math
from typing import List, Dict, Any
from shapely.geometry import Point, box
from shapely.affinity import rotate, translate

class DWA:
    def __init__(self, config: Dict[str, Any]):
        self.max_speed = config.get("max_speed", 600.0)
        self.min_speed = -50.0
        self.max_yaw_rate = 1.2
        self.max_accel = 800.0 
        self.max_dyaw_rate = 3.5
        
        # 搜尋空間解析度
        self.v_resolution = 20.0 
        self.yaw_rate_resolution = 0.1
        self.dt = 0.1
        self.predict_time = 2.5 # 局部預測時間
        
        self.robot_width = 1000.0
        self.robot_height = 1000.0

    def calc_dynamic_window(self, v, omega):
        Vd = [v - self.max_accel * self.dt, v + self.max_accel * self.dt,
              omega - self.max_dyaw_rate * self.dt, omega + self.max_dyaw_rate * self.dt]
        return [max(self.min_speed, Vd[0]), min(self.max_speed, Vd[1]),
                max(-self.max_yaw_rate, Vd[2]), min(self.max_yaw_rate, Vd[3])]

    def predict_trajectory(self, x_init, v, omega):
        x = np.array(x_init, dtype=float)
        traj = [x.copy()]
        # 模擬軌跡
        for _ in range(8):
            x[0] += v * math.cos(x[2]) * self.dt * 2.0
            x[1] += v * math.sin(x[2]) * self.dt * 2.0
            x[2] += omega * self.dt * 2.0
            traj.append(x.copy())
        return np.array(traj)

    def check_safety(self, traj, obstacles):
        """檢查整條預測軌跡是否安全"""
        for p in traj:
            # 1.05m 嚴格碰撞箱
            poly = translate(rotate(box(-525, -525, 525, 525), p[2], use_radians=True), xoff=p[0], yoff=p[1])
            
            # 地圖邊界
            if p[0] < 550 or p[0] > 49450 or p[1] < 550 or p[1] > 49450: return False

            for ob in obstacles:
                if (p[0]-ob['x'])**2 + (p[1]-ob['y'])**2 > 3500**2: continue
                ob_geom = Point(ob['x'], ob['y']).buffer(ob['radius']) if ob['type'] == 'circle' else \
                          translate(rotate(box(-ob['width']/2, -ob['height']/2, ob['width']/2, ob['height']/2), ob.get('angle', 0), use_radians=True), xoff=ob['x'], yoff=ob['y'])
                if poly.intersects(ob_geom): return False
        return True

    def filter_commands(self, x_curr, v_curr, omega_curr, target_v, target_omega, obstacles):
        """
        核心邏輯：給定一個理想指令 (target_v, target_omega)，
        尋找動態窗口內最接近該指令且安全的替代方案。
        """
        dw = self.calc_dynamic_window(v_curr, omega_curr)
        best_u = [0.0, 0.0]
        min_diff = float("inf")
        
        v_samples = np.arange(dw[0], dw[1] + 1, self.v_resolution)
        w_samples = np.arange(dw[2], dw[3] + 0.01, self.yaw_rate_resolution)
        
        found_safe = False
        for v in v_samples:
            for w in w_samples:
                traj = self.predict_trajectory(x_curr, v, w)
                
                # 僅篩選安全的指令
                if not self.check_safety(traj, obstacles): continue
                found_safe = True
                
                # 計算與「理想指令」的差距 (加權歐幾里德距離)
                diff = (v - target_v)**2 + (w * 500 - target_omega * 500)**2 
                
                if diff < min_diff:
                    min_diff = diff
                    best_u = [v, w]
        
        # 脫困：如果完美指令不安全且找不到路
        if not found_safe:
            # 往遠離障礙物的方向緩慢旋轉
            return [0.0, 0.5 if omega_curr >= 0 else -0.5]
            
        return best_u
