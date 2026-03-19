import numpy as np
import math
from typing import List, Dict, Any
from shapely.geometry import Point, box
from shapely.affinity import rotate, translate

class AGVController:
    def __init__(self, config: Dict[str, Any]):
        self.max_rpm = 3000.0
        self.rpm_to_mms = 0.2
        self.wheel_base = 800.0
        self.max_accel = 1200.0 
        self.max_dyaw_rate = 5.0 
        self.dt = 0.02 
        self.robot_width = 1000.0
        self.robot_height = 1000.0

    def is_pose_safe(self, x, y, theta, obstacles, margin=525):
        poly = translate(rotate(box(-margin, -margin, margin, margin), theta, use_radians=True), xoff=x, yoff=y)
        if x < 550 or x > 49450 or y < 550 or y > 49450: return False
        for ob in obstacles:
            if (x - ob['x'])**2 + (y - ob['y'])**2 > 3000**2: continue
            if ob['type'] == 'rectangle':
                ob_geom = box(ob['x']-500, ob['y']-500, ob['x']+500, ob['y']+500)
            else:
                ob_geom = Point(ob['x'], ob['y']).buffer(ob['radius'])
            if poly.intersects(ob_geom): return False
        return True

    def compute_command(self, x, y, theta, v_curr, omega_curr, target_wp, max_rpm, obstacles):
        max_speed = min(max_rpm, 3000.0) * self.rpm_to_mms
        
        dx, dy = target_wp[0] - x, target_wp[1] - y
        distance = math.sqrt(dx**2 + dy**2)
        target_angle = math.atan2(dy, dx)
        alpha = math.atan2(math.sin(target_angle - theta), math.cos(target_angle - theta))
        
        # --- 核心優化：外擺補償 (Swing-out) ---
        if abs(alpha) > 0.1:
            swing_dir = theta - (math.pi/2 if alpha > 0 else -math.pi/2)
            swing_offset = min(150.0, 300.0 * math.sin(abs(alpha)))
            comp_target_x = target_wp[0] + math.cos(swing_dir) * swing_offset
            comp_target_y = target_wp[1] + math.sin(swing_dir) * swing_offset
            dx, dy = comp_target_x - x, comp_target_y - y
            distance = math.sqrt(dx**2 + dy**2)
            target_angle = math.atan2(dy, dx)
            alpha = math.atan2(math.sin(target_angle - theta), math.cos(target_angle - theta))

        # --- 1. 原地旋轉 (方案 B & C) ---
        # 如果速度很低 (剛起步或卡住)，啟動「無敵星模式」與「強制轉向」
        if abs(v_curr) < 50.0:
            if abs(alpha) > 0.4: # 超過 23 度強制轉正
                w = 1.5 if alpha > 0 else -1.5
                # 方案 B：放寬起步安全邊距到 502mm (1m 車體半寬 500mm + 2mm 極限餘裕)
                # 讓 AGV 即使沒停正也能擠出空間旋轉
                if self.is_pose_safe(x, y, theta + w * 0.1, obstacles, margin=502):
                    return self.limit_physics(0.0, w, v_curr, omega_curr, max_speed)
                else:
                    return self.limit_physics(-100.0, 0.0, v_curr, omega_curr, max_speed)
        else:
            # 行進中的常規旋轉檢查
            if abs(alpha) > 0.4:
                w = 1.5 if alpha > 0 else -1.5
                if self.is_pose_safe(x, y, theta + w * 0.1, obstacles, margin=515):
                    return self.limit_physics(0.0, w, v_curr, omega_curr, max_speed)
                else:
                    return self.limit_physics(-100.0, 0.0, v_curr, omega_curr, max_speed)

        # --- 2. 精確追蹤 ---
        speed = max_speed * (math.cos(alpha) ** 2)
        if abs(alpha) > 0.2: speed = min(speed, 250.0) 
        speed = max(50.0, speed)
        
        lookahead = max(distance, 400)
        omega = (2.0 * speed * math.sin(alpha)) / lookahead
        
        cmd_v, cmd_w = self.limit_physics(speed, omega, v_curr, omega_curr, max_speed)
        
        # 安全層
        if self.is_path_safe(x, y, theta, cmd_v, cmd_w, obstacles):
            return cmd_v, cmd_w
            
        return 0.0, 0.0

    def is_path_safe(self, x, y, theta, v, w, obstacles):
        tx, ty, tt = x, y, theta
        for _ in range(4):
            tx += v * math.cos(tt) * 0.2
            ty += v * math.sin(tt) * 0.2
            tt += w * 0.2
            if not self.is_pose_safe(tx, ty, tt, obstacles, margin=525): return False
        return True

    def limit_physics(self, v, w, v_curr, w_curr, max_speed):
        v = np.clip(v, v_curr - self.max_accel * self.dt, v_curr + self.max_accel * self.dt)
        w = np.clip(w, w_curr - self.max_dyaw_rate * self.dt, w_curr + self.max_dyaw_rate * self.dt)
        
        v_l = v - (w * self.wheel_base / 2.0); v_r = v + (w * self.wheel_base / 2.0)
        max_wheel_v = max(abs(v_l), abs(v_r))
        if max_wheel_v > max_speed:
            ratio = max_speed / max_wheel_v
            v *= ratio; w *= ratio
        return v, w
