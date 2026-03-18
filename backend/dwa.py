import numpy as np
import math
from typing import List, Dict, Any
from shapely.geometry import Point, box
from shapely.affinity import rotate, translate

class DWA:
    def __init__(self, config: Dict[str, Any]):
        self.max_speed = config.get("max_speed", 600.0)
        self.min_speed = -50.0
        self.max_yaw_rate = 1.2 # 穩定轉速
        self.max_accel = 800.0 
        self.max_dyaw_rate = 3.0
        
        self.v_resolution = 20.0 
        self.yaw_rate_resolution = 0.1
        self.dt = 0.1
        self.predict_time = 3.0 
        
        # 權重優化：提高 heading 權重，確保緊跟紅線
        self.to_goal_cost_gain = 0.3    # 提高導航點引導權重
        self.speed_cost_gain = 1.0
        self.obstacle_cost_gain = 4.5   # 保持足夠的避障距離
        
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
        # 精確預測 10 步
        for _ in range(10):
            x[0] += v * math.cos(x[2]) * self.dt
            x[1] += v * math.sin(x[2]) * self.dt
            x[2] += omega * self.dt
            traj.append(x.copy())
        return np.array(traj)

    def get_score(self, x, y, theta, obstacles):
        # 碰撞箱 1.1m (550mm 半徑)
        robot_poly = translate(rotate(box(-550, -550, 550, 550), theta, use_radians=True), xoff=x, yoff=y)
        min_d = 5000.0
        for ob in obstacles:
            if (x - ob['x'])**2 + (y - ob['y'])**2 > 4000**2: continue
            
            if ob['type'] == 'circle':
                ob_geom = Point(ob['x'], ob['y']).buffer(ob['radius'])
            else:
                ob_geom = translate(rotate(box(-ob['width']/2, -ob['height']/2, ob['width']/2, ob['height']/2), ob.get('angle', 0), use_radians=True), xoff=ob['x'], yoff=ob['y'])
            
            d = robot_poly.distance(ob_geom)
            if d <= 0: return -1.0 # 碰撞
            if d < min_d: min_d = d
        return min_d

    def dw_search(self, x_curr, v_curr, omega_curr, goal, obstacles):
        dist_to_final_goal = math.sqrt((x_curr[0]-goal[0])**2 + (x_curr[1]-goal[1])**2)
        
        # 終點停靠保護
        if dist_to_final_goal < 800:
            if dist_to_final_goal < 400: return [0.0, 0.0]
            return [50.0, 0.0]

        dw = self.calc_dynamic_window(v_curr, omega_curr)
        best_u = [0.0, 0.0]
        min_cost = float("inf")
        found_safe = False

        for v in np.arange(dw[0], dw[1] + 1, self.v_resolution):
            for omega in np.arange(dw[2], dw[3] + 0.01, self.yaw_rate_resolution):
                traj = self.predict_trajectory(x_curr, v, omega)
                
                min_d_traj = 5000.0
                collision = False
                for p in traj[::2]:
                    d = self.get_score(p[0], p[1], p[2], obstacles)
                    if d < 0:
                        collision = True
                        break
                    if d < min_d_traj: min_d_traj = d
                
                if collision: continue
                found_safe = True
                
                # 計算成本
                dx, dy = goal[0] - traj[-1, 0], goal[1] - traj[-1, 1]
                t_theta = math.atan2(dy, dx)
                cost_goal = abs(math.atan2(math.sin(t_theta - traj[-1, 2]), math.cos(t_theta - traj[-1, 2])))
                cost_speed = self.max_speed - v
                cost_ob = 1.0 / (min_d_traj + 1.0)

                total_cost = (self.to_goal_cost_gain * cost_goal + 
                              self.speed_cost_gain * cost_speed + 
                              self.obstacle_cost_gain * cost_ob)
                
                if total_cost < min_cost:
                    min_cost = total_cost
                    best_u = [v, omega]
        
        # 脫困行為：如果計算出速度接近 0，強制轉向目標方向
        if best_u[0] < 30:
            dx, dy = goal[0] - x_curr[0], goal[1] - x_curr[1]
            target_angle = math.atan2(dy, dx)
            diff = math.atan2(math.sin(target_angle - x_curr[2]), math.cos(target_angle - x_curr[2]))
            best_u = [0.0, 0.5 if diff > 0 else -0.5]
            
        return best_u
