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

with world_lock:
    init_id = f"AGV-{str(uuid.uuid4())[:4].upper()}"
    world.agvs[init_id] = AGV(init_id, 5000.0, 5000.0)

def get_snapshot():
    with world_lock:
        agvs_data = [a.to_dict() for a in world.agvs.values()]
        
        # 建立社交連結 (誰在等誰，或是誰在讓誰)
        links = []
        for a in world.agvs.values():
            if a.culprit_id and a.culprit_id.startswith("AGV"):
                links.append({
                    "from": a.id, 
                    "to": a.culprit_id, 
                    "type": a.status
                })
        
        return {
            "agvs": agvs_data,
            "obstacles": list(world.obstacles),
            "multiplier": SIM_MULTIPLIER,
            "social_links": links,
            "path_occupancy": {k: v for k, v in world.path_occupancy.items()}
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
                    # 容錯解析 ID
                    ob_id = msg.get("id") or (msg.get("data") if not isinstance(msg.get("data"), dict) else msg.get("data").get("id"))
                    if ob_id:
                        world.remove_obstacle(str(ob_id))
                        for a in world.agvs.values(): a.replan_needed = True
                elif target_id and target_id in world.agvs:
                    a = world.agvs[target_id]
                    if t == "start": a.is_running = True; a.replan_needed = True
                    elif t == "pause": a.is_running = False
                    elif t == "remove_agv": del world.agvs[target_id]
                    elif t == "reset":
                        a.x, a.y, a.theta = 5000.0, 5000.0, 0.0
                        a.v, a.omega, a.l_rpm, a.r_rpm = 0.0, 0.0, 0.0, 0.0
                        a.is_running = False; a.global_path = []
                    elif t == "set_target":
                        a.target = msg.get("data"); a.replan_needed = True
                    elif t == "set_speed":
                        a.max_rpm = float(msg.get("data", 3000))
        except Exception as e:
            logger.error(f"Error processing command {t}: {e}")

def physics_engine_thread():
    # 採用穩定的 60Hz 運算 (約 0.0166s 每幀)
    real_dt = 0.0166 
    while True:
        cycle_start = time.time()
        process_commands()
        
        # 計算模擬步長：現實時間 * 倍速
        sim_dt = real_dt * SIM_MULTIPLIER
        
        with world_lock:
            for a in world.agvs.values():
                # 告訴 AGV：模擬世界過了 sim_dt 秒
                a.update(sim_dt, world)
        
        elapsed = time.time() - cycle_start
        if real_dt > elapsed:
            time.sleep(real_dt - elapsed)

async def telemetry_broadcaster():
    while True:
        # 維持 30Hz 的廣播即可，這對人類視覺已足夠流暢
        await manager.broadcast({"type": "telemetry", "data": get_snapshot()})
        await asyncio.sleep(0.033)

@app.on_event("startup")
async def startup():
    threading.Thread(target=physics_engine_thread, daemon=True).start()
    asyncio.create_task(telemetry_broadcaster())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
