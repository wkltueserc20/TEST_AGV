import numpy as np
import math
from dwa import DWA

def run_test():
    dwa = DWA({"max_speed": 600.0})
    
    x_curr = [5000.0, 5000.0, 0.0] # 面向右方
    v_curr = 0.0
    omega_curr = 0.0
    goal = [45000.0, 45000.0] # 右上方
    
    obstacles = [
        {"id": "1", "type": "rectangle", "x": 6000.0, "y": 5000.0, "width": 1000.0, "height": 5000.0, "angle": 0.0}
    ]
    
    print("--- DWA Test ---")
    for i in range(10):
        best_u = dwa.dw_search(x_curr, v_curr, omega_curr, goal, obstacles)
        print(f"Step {i}: v={best_u[0]:.2f}, omega={best_u[1]:.2f}, x={x_curr[0]:.2f}, y={x_curr[1]:.2f}, theta={x_curr[2]:.2f}")
        
        # 簡單更新位置
        dt = 0.1
        v_curr, omega_curr = best_u[0], best_u[1]
        x_curr[0] += v_curr * math.cos(x_curr[2]) * dt
        x_curr[1] += v_curr * math.sin(x_curr[2]) * dt
        x_curr[2] += omega_curr * dt

if __name__ == "__main__":
    run_test()
