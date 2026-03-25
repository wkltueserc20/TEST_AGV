import json
import time
import math
import requests
import subprocess
import os

def test_three_agvs():
    print("Starting Multi-AGV Yield List Test (3 AGVs)...")
    
    # 1. 準備環境
    agvs = [
        {"id": "AGV_01", "x": 10000, "y": 25000, "theta": 0}, # Prio High
        {"id": "AGV_02", "x": 40000, "y": 25000, "theta": math.pi}, # Prio Med
        {"id": "AGV_03", "x": 25000, "y": 10000, "theta": math.pi/2} # Prio Low
    ]
    obstacles = [
        {"id": "Station_A", "type": "equipment", "x": 5000, "y": 25000, "radius": 1000, "docking_angle": 180},
        {"id": "Station_B", "type": "equipment", "x": 45000, "y": 25000, "radius": 1000, "docking_angle": 0},
        {"id": "Station_C", "type": "equipment", "x": 25000, "y": 45000, "radius": 1000, "docking_angle": 90},
        {"id": "Station_D", "type": "equipment", "x": 25000, "y": 5000, "radius": 1000, "docking_angle": 270}
    ]
    
    with open("agvs.json", "w") as f: json.dump(agvs, f)
    with open("obstacles.json", "w") as f: json.dump(obstacles, f)
    if os.path.exists("task_history.json"): os.remove("task_history.json")

    # 2. 啟動後端
    process = subprocess.Popen(["python", "main.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    try:
        # 3. 發布任務
        requests.post("http://localhost:5000/api/tasks", json={"source_id": "Station_A", "target_id": "Station_B", "priority": 1})
        requests.post("http://localhost:5000/api/tasks", json={"source_id": "Station_B", "target_id": "Station_A", "priority": 5})
        requests.post("http://localhost:5000/api/tasks", json={"source_id": "Station_D", "target_id": "Station_C", "priority": 10})

        print("Tasks assigned. AGV_03 should yield to both AGV_01 and AGV_02.")
        
        # 4. 監控 40 秒
        for i in range(80):
            res = requests.get("http://localhost:5000/api/telemetry")
            data = res.json()
            
            agv3 = next((a for a in data["agvs"] if a["id"] == "AGV_03"), None)
            
            status_line = []
            for a in data["agvs"]:
                yielding = a.get("yielding_to_ids", [])
                status_line.append(f"{a['id']}: {a['status']} (Yielding to: {yielding})")
            
            print(f"[{i*0.5}s] " + " | ".join(status_line))
            
            if agv3 and len(agv3.get("yielding_to_ids", [])) >= 2:
                print(">>> SUCCESS: AGV_03 is yielding to multiple vehicles!")
            
            time.sleep(0.5)

    finally:
        process.terminate()
        print("Test finished.")

if __name__ == "__main__":
    test_three_agvs()
