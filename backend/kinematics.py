import math

class Kinematics:
    def __init__(self, wheel_base=800.0):
        self.L = wheel_base
        # 根據 3000 RPM = 600 mm/s 推算出的轉換係數 (mm/s per RPM)
        self.rpm_to_mms = 0.2 

    def rpm_to_velocity(self, l_rpm, r_rpm):
        """轉換左右 RPM 為線速度 v (mm/s) 與角速度 omega (rad/s)"""
        v_l = l_rpm * self.rpm_to_mms
        v_r = r_rpm * self.rpm_to_mms
        
        v = (v_r + v_l) / 2.0
        # omega = (v_r - v_l) / L
        omega = (v_r - v_l) / self.L
        return v, omega

    def velocity_to_rpm(self, v, omega):
        """轉換線速度與角速度回左右 RPM"""
        # v_l = v - (omega * L / 2)
        v_l = v - (omega * self.L / 2.0)
        v_r = v + (omega * self.L / 2.0)
        
        l_rpm = v_l / self.rpm_to_mms
        r_rpm = v_r / self.rpm_to_mms
        return l_rpm, r_rpm

    def update_pose(self, x, y, theta, v, omega, dt):
        """使用線速度與角速度直接更新姿勢 (更精確)"""
        new_x = x + v * math.cos(theta) * dt
        new_y = y + v * math.sin(theta) * dt
        new_theta = theta + omega * dt
        
        # 規範化角度
        new_theta = math.atan2(math.sin(new_theta), math.cos(new_theta))
        return new_x, new_y, new_theta
