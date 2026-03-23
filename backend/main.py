import asyncio
import json
import logging
import time
import threading
import queue
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from world import World
from agv import AGV

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SIM_MULTIPLIER = 1
world = World()
world_lock = threading.Lock()
cmd_queue = queue.Queue()

# 注意：World 初始化時會呼叫 load_agvs()，所以這裡不需要 init_id 的手動創建，除非是全新環境
with world_lock:
    if not world.agvs:
        init_id = f"AGV-{str(uuid.uuid4())[:4].upper()}"
        world.agvs[init_id] = AGV(init_id, 5000.0, 5000.0)
        world.save_agvs()

def get_snapshot():
    with world_lock:
        agvs_data = []
        for a in world.agvs.values():
            d = a.to_dict()
            if d.get("path"):
                d["path"] = d["path"][::3]
            agvs_data.append(d)
        
        return {
            "agvs": agvs_data,
            "obstacles": list(world.obstacles),
            "multiplier": SIM_MULTIPLIER,
            "path_occupancy": {k: v[::5] for k, v in world.path_occupancy.items()},
            "reserved_havens": {k: v for k, v in world.reserved_havens.items()}
        }

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

def process_commands():
    global SIM_MULTIPLIER
    while not cmd_queue.empty():
        msg = cmd_queue.get_nowait()
        t = msg.get("type")
        target_id = msg.get("agv_id")
        
        try:
            with world_lock:
                if t == "set_multiplier":
                    SIM_MULTIPLIER = int(msg.get("data", 1))
                elif t == "add_agv":
                    new_id = f"AGV-{str(uuid.uuid4())[:4].upper()}"
                    world.agvs[new_id] = AGV(new_id, msg.get("x", 5000), msg.get("y", 5000))
                    world.save_agvs()
                elif t == "add_obstacle":
                    world.add_obstacle(msg.get("data"))
                    for a in world.agvs.values(): a.replan_needed = True
                elif t == "update_obstacle":
                    world.update_obstacle(msg.get("data"))
                    for a in world.agvs.values(): a.replan_needed = True
                elif t == "clear_obstacles":
                    world.clear_obstacles()
                    for a in world.agvs.values(): a.replan_needed = True
                elif t == "remove_obstacle":
                    ob_id = msg.get("id") or (msg.get("data") if not isinstance(msg.get("data"), dict) else msg.get("data").get("id"))
                    if ob_id:
                        world.remove_obstacle(str(ob_id))
                        for a in world.agvs.values(): a.replan_needed = True
                elif target_id and target_id in world.agvs:
                    a = world.agvs[target_id]
                    if t == "start": 
                        a.is_running = True; a.replan_needed = True; world.save_agvs()
                    elif t == "pause": 
                        a.is_running = False; world.save_agvs()
                    elif t == "remove_agv": 
                        del world.agvs[target_id]
                        world.save_agvs()
                    elif t == "reset":
                        a.x, a.y, a.theta = 5000.0, 5000.0, 0.0
                        a.v, a.omega, a.l_rpm, a.r_rpm = 0.0, 0.0, 0.0, 0.0
                        a.is_running = False; a.global_path = []
                        world.save_agvs()
                    elif t == "set_target":
                        a.target = msg.get("data"); a.replan_needed = True; world.save_agvs()
                    elif t == "set_speed":
                        a.max_rpm = float(msg.get("data", 3000)); world.save_agvs()
        except Exception as e:
            logger.error(f"Error processing command {t}: {e}")

def physics_engine_thread():
    real_dt = 0.0166 
    while True:
        cycle_start = time.time()
        process_commands()
        sim_dt = real_dt * SIM_MULTIPLIER
        with world_lock:
            for a in world.agvs.values():
                a.update(sim_dt, world)
        elapsed = time.time() - cycle_start
        if real_dt > elapsed:
            time.sleep(real_dt - elapsed)

async def telemetry_broadcaster():
    last_save_time = time.time()
    while True:
        start_time = asyncio.get_event_loop().time()
        snapshot = get_snapshot()
        await manager.broadcast({"type": "telemetry", "data": snapshot})
        
        # 每 5 秒自動儲存一次 AGV 位置 (記憶功能)
        if time.time() - last_save_time > 5.0:
            world.save_agvs()
            last_save_time = time.time()

        elapsed = asyncio.get_event_loop().time() - start_time
        await asyncio.sleep(max(0.01, 0.033 - elapsed))

@app.on_event("startup")
async def startup():
    threading.Thread(target=physics_engine_thread, daemon=True).start()
    asyncio.create_task(telemetry_broadcaster())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
