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

SIM_MULTIPLIER = 10

class AGV:
    def __init__(self, id, x, y, theta=0):
        self.id = id
        self.x = x; self.y = y; self.theta = theta
        self.v = 0.0; self.omega = 0.0
        self.l_rpm = 0.0; self.r_rpm = 0.0
        self.target = {"x": x + 5000, "y": y + 5000}
        self.global_path = []
        self.is_running = False
        self.max_rpm = 3000.0
        self.replan_needed = True

    def to_dict(self):
        return {
            "id": self.id, "x": self.x, "y": self.y, "theta": self.theta,
            "v": self.v, "omega": self.omega,
            "l_rpm": self.l_rpm, "r_rpm": self.r_rpm,
            "target": self.target, "is_running": self.is_running,
            "path": self.global_path, "max_rpm": self.max_rpm
        }

class SimulationState:
    def __init__(self):
        self.lock = threading.Lock()
        self.agvs: Dict[str, AGV] = {}
        self.obstacles = []
        self.add_agv(5000, 5000)

    def add_agv(self, x, y):
        with self.lock:
            id = f"AGV-{str(uuid.uuid4())[:4].upper()}"
            self.agvs[id] = AGV(id, x, y)
            return id

    def remove_agv(self, id):
        with self.lock:
            if id in self.agvs: del self.agvs[id]

    def get_snapshot(self):
        with self.lock:
            return {"agvs": [a.to_dict() for a in self.agvs.values()], "obstacles": list(self.obstacles), "multiplier": SIM_MULTIPLIER}

sim = SimulationState()
cmd_queue = queue.Queue()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, ws: WebSocket):
        await ws.accept(); self.active_connections.append(ws)
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
    dwa_filter = DWA({"max_speed": 600.0})
    planner = AStarPlanner(grid_size=500)
    dt = 0.1
    
    while True:
        cycle_start = time.time()
        while not cmd_queue.empty():
            try:
                msg = cmd_queue.get_nowait()
                t, target_id = msg.get("type"), msg.get("agv_id")
                with sim.lock:
                    if t == "add_agv": sim.add_agv(msg.get("x", 5000), msg.get("y", 5000))
                    elif t == "add_obstacle":
                        sim.obstacles.append(msg.get("data"))
                        for a in sim.agvs.values(): a.replan_needed = True
                    elif t == "update_obstacle":
                        d = msg.get("data")
                        for ob in sim.obstacles:
                            if ob.get("id") == d.get("id"): ob.update(d); break
                        for a in sim.agvs.values(): a.replan_needed = True
                    elif t == "clear_obstacles":
                        sim.obstacles = []; 
                        for a in sim.agvs.values(): a.replan_needed = True
                    elif t == "remove_obstacle":
                        sim.obstacles = [o for o in sim.obstacles if o.get("id") != msg.get("id")]
                        for a in sim.agvs.values(): a.replan_needed = True
                    elif target_id in sim.agvs:
                        a = sim.agvs[target_id]
                        if t == "start": a.is_running = True; a.replan_needed = True
                        elif t == "pause": a.is_running = False
                        elif t == "remove_agv": sim.remove_agv(target_id)
                        elif t == "reset":
                            a.x, a.y, a.theta = 5000.0, 5000.0, 0.0
                            a.v, a.omega, a.l_rpm, a.r_rpm = 0, 0, 0, 0
                            a.is_running = False; a.replan_needed = True
                        elif t == "set_target": a.target = msg.get("data"); a.replan_needed = True
                        elif t == "set_speed": a.max_rpm = float(msg.get("data", 3000))
            except: break

        with sim.lock:
            for agv_id, a in sim.agvs.items():
                if a.replan_needed and a.is_running:
                    a.global_path = planner.get_path([a.x, a.y], [a.target["x"], a.target["y"]], sim.obstacles)
                    a.replan_needed = False
                
                if a.is_running:
                    for _ in range(SIM_MULTIPLIER):
                        # --- 核心改進：Pure Pursuit 指令預估 ---
                        # 1. 尋找紅線上距離約 1.2 米的目標點
                        target_wp = [a.target["x"], a.target["y"]]
                        if a.global_path:
                            min_d, idx = float("inf"), 0
                            for i, wp in enumerate(a.global_path):
                                d = (wp[0]-a.x)**2 + (wp[1]-a.y)**2
                                if d < min_d: min_d, idx = d, i
                            # 前瞻距離設為 1.2m
                            target_wp = a.global_path[min(idx + 2, len(a.global_path)-1)]

                        # 2. 計算理想的 v 和 omega
                        dx, dy = target_wp[0] - a.x, target_wp[1] - a.y
                        alpha = math.atan2(dy, dx) - a.theta
                        alpha = math.atan2(math.sin(alpha), math.cos(alpha))
                        
                        # 理想速度：直道快，彎道慢
                        ideal_v = (a.max_rpm * 0.2) * math.cos(alpha)
                        ideal_v = max(50.0, ideal_v) # 保持最低推進力
                        
                        # 理想角速度 (Pure Pursuit 公式: omega = 2*v*sin(alpha) / L)
                        ideal_omega = (2.0 * ideal_v * math.sin(alpha)) / 1200.0 # L=1.2m 虛擬前瞻半徑
                        ideal_omega = max(-1.2, min(1.2, ideal_omega))

                        # 3. 使用 DWA 作為安全護盾進行過濾
                        dynamic_obs = list(sim.obstacles)
                        for oid, o_a in sim.agvs.items():
                            if oid != agv_id: dynamic_obs.append({"type": "circle", "x": o_a.x, "y": o_a.y, "radius": 800})
                        
                        dwa_filter.max_speed = a.max_rpm * 0.2
                        bv, bo = dwa_filter.filter_commands([a.x, a.y, a.theta], a.v, a.omega, ideal_v, ideal_omega, dynamic_obs)
                        
                        a.v += (bv - a.v) * 0.7
                        a.omega += (bo - a.omega) * 0.7
                        a.x, a.y, a.theta = kin.update_pose(a.x, a.y, a.theta, a.v, a.omega, dt)
                        a.x = max(500, min(49500, a.x)); a.y = max(500, min(49500, a.y))
                        
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
