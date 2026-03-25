import json
import time
import math
import requests
import subprocess
import os

def test_priority():
    print("Starting Priority Traffic Control Test...")
    
    # 1. 準備環境
    agvs = [
        {"id": "AGV_01", "x": 10000, "y": 25000, "theta": 0}, # 從左往右
        {"id": "AGV_02", "x": 40000, "y": 25000, "theta": math.pi} # 從右往左
    ]
    obstacles = [
        {"id": "Station_A", "type": "equipment", "x": 5000, "y": 25000, "radius": 1000, "docking_angle": 180},
        {"id": "Station_B", "type": "equipment", "x": 45000, "y": 25000, "radius": 1000, "docking_angle": 0}
    ]
    
    with open("agvs.json", "w") as f: json.dump(agvs, f)
    with open("obstacles.json", "w") as f: json.dump(obstacles, f)
    if os.path.exists("task_history.json"): os.remove("task_history.json")

    # 2. 啟動後端
    process = subprocess.Popen(["python", "main.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    try:
        # 3. 發布任務
        # AGV_01: Prio 1 (High)
        requests.post("http://localhost:5000/api/tasks", json={
            "source_id": "Station_A", "target_id": "Station_B", "priority": 1
        })
        # AGV_02: Prio 10 (Low)
        requests.post("http://localhost:5000/api/tasks", json={
            "source_id": "Station_B", "target_id": "Station_A", "priority": 10
        })

        print("Tasks assigned. Monitoring intersection...")
        
        # 4. 監控 30 秒
        for i in range(60):
            res = requests.get("http://localhost:5000/api/telemetry")
            data = res.json()
            
            yield_agv = next((a for a in data["agvs"] if a["id"] == "AGV_02"), None)
            high_agv = next((a for a in data["agvs"] if a["id"] == "AGV_01"), None)
            
            if yield_agv and high_agv:
                print(f"[{i*0.5}s] AGV_01: {high_agv['status']} @ ({int(high_agv['x'])}, {int(high_agv['y'])}) | "
                      f"AGV_02: {yield_agv['status']} @ ({int(yield_agv['x'])}, {int(yield_agv['y'])})")
                
                if yield_agv["status"] in ["THINKING", "YIELDING", "WAITING"]:
                    print(">>> SUCCESS: AGV_02 (Low Prio) is yielding!")
            
            time.sleep(0.5)

    finally:
        process.terminate()
        print("Test finished.")

if __name__ == "__main__":
    test_priority()
