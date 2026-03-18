import asyncio
import json
import logging
import math
import time
import threading
import queue
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from kinematics import Kinematics
from dwa import DWA
from planner import AStarPlanner

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- AGV 物件類別 ---
class AGV:
    def __init__(self, id, x, y, theta=0):
        self.id = id
        self.x = x
        self.y = y
        self.theta = theta
        self.v = 0.0
        self.omega = 0.0
        self.l_rpm = 0.0
        self.r_rpm = 0.0
        self.target = {"x": x + 5000, "y": y + 5000} # 預設目標在附近
        self.global_path = []
        self.is_running = False
        self.max_rpm = 3000.0
        self.replan_needed = True

    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x, "y": self.y, "theta": self.theta,
            "v": self.v, "omega": self.omega,
            "l_rpm": self.l_rpm, "r_rpm": self.r_rpm,
            "target": self.target,
            "is_running": self.is_running,
            "path": self.global_path,
            "max_rpm": self.max_rpm
        }

# --- 執行緒安全的共享狀態 ---
class SimulationState:
    def __init__(self):
        self.lock = threading.Lock()
        self.agvs: Dict[str, AGV] = {}
        self.obstacles = []
        # 初始化第一台 AGV
        self.add_agv(5000, 5000)

    def add_agv(self, x, y):
        with self.lock:
            id = str(uuid.uuid4())[:8]
            self.agvs[id] = AGV(id, x, y)
            return id

    def remove_agv(self, id):
        with self.lock:
            if id in self.agvs: del self.agvs[id]

    def get_snapshot(self):
        with self.lock:
            return {
                "agvs": [a.to_dict() for a in self.agvs.values()],
                "obstacles": list(self.obstacles)
            }

sim = SimulationState()
cmd_queue = queue.Queue()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections: self.active_connections.remove(ws)
    async def broadcast(self, data: dict):
        msg = json.dumps(data)
        for conn in self.active_connections[:]:
            try: await conn.send_text(msg)
            except: 
                if conn in self.active_connections: self.active_connections.remove(conn)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            raw_data = await websocket.receive_text()
            cmd_queue.put(json.loads(raw_data))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def physics_engine_thread():
    kin = Kinematics(wheel_base=800.0)
    dwa_engine = DWA({"max_speed": 600.0})
    planner = AStarPlanner(grid_size=1500)
    dt = 0.1
    multiplier = 10 
    
    while True:
        cycle_start = time.time()
        
        # 1. 指令處理
        while not cmd_queue.empty():
            try:
                msg = cmd_queue.get_nowait()
                t = msg.get("type")
                target_id = msg.get("agv_id")
                
                with sim.lock:
                    if t == "add_agv":
                        sim.add_agv(msg.get("x", 5000), msg.get("y", 5000))
                    elif t == "remove_agv":
                        sim.remove_agv(target_id)
                    elif t == "add_obstacle":
                        sim.obstacles.append(msg.get("data"))
                        for a in sim.agvs.values(): a.replan_needed = True
                    elif t == "clear_obstacles":
                        sim.obstacles = []
                        for a in sim.agvs.values(): a.replan_needed = True
                    elif target_id in sim.agvs:
                        a = sim.agvs[target_id]
                        if t == "start": a.is_running = True; a.replan_needed = True
                        elif t == "pause": a.is_running = False
                        elif t == "set_target": a.target = msg.get("data"); a.replan_needed = True
                        elif t == "set_speed": 
                            a.max_rpm = float(msg.get("data", 3000))
            except: break

        # 2. 全局規劃與物理更新
        with sim.lock:
            for agv_id, a in sim.agvs.items():
                if a.replan_needed and a.is_running:
                    a.global_path = planner.get_path([a.x, a.y], [a.target["x"], a.target["y"]], sim.obstacles)
                    a.replan_needed = False

                if a.is_running:
                    for _ in range(multiplier):
                        # --- 核心：互碰避障 ---
                        # 將「其他 AGV」也當作障礙物傳給 DWA
                        dynamic_obs = list(sim.obstacles)
                        for other_id, other_a in sim.agvs.items():
                            if other_id != agv_id:
                                dynamic_obs.append({"type": "circle", "x": other_a.x, "y": other_a.y, "radius": 600})

                        target_wp = [a.target["x"], a.target["y"]]
                        if a.global_path:
                            min_d = float("inf")
                            idx = 0
                            for i, wp in enumerate(a.global_path):
                                d = (wp[0]-a.x)**2 + (wp[1]-a.y)**2
                                if d < min_d: min_d = d; idx = i
                            target_wp = a.global_path[min(idx + 3, len(a.global_path)-1)]

                        # 更新 DWA 極限
                        dwa_engine.max_speed = a.max_rpm * 0.2
                        bv, bo = dwa_engine.dw_search([a.x, a.y, a.theta], a.v, a.omega, target_wp, dynamic_obs)
                        
                        a.v += (bv - a.v) * 0.6
                        a.omega += (bo - a.omega) * 0.6
                        a.x, a.y, a.theta = kin.update_pose(a.x, a.y, a.theta, a.v, a.omega, dt)
                        
                        a.x = max(500, min(49500, a.x))
                        a.y = max(500, min(49500, a.y))
                        
                        if math.sqrt((a.x - a.target["x"])**2 + (a.y - a.target["y"])**2) < 600:
                            a.is_running = False; a.v = a.omega = 0; break
                    
                    a.l_rpm, a.r_rpm = kin.velocity_to_rpm(a.v, a.omega)

        elapsed = time.time() - cycle_start
        if dt > elapsed: time.sleep(dt - elapsed)

async def telemetry_broadcaster():
    while True:
        await manager.broadcast({"type": "telemetry", "data": sim.get_snapshot()})
        await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup():
    threading.Thread(target=physics_engine_thread, daemon=True).start()
    asyncio.create_task(telemetry_broadcaster())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
