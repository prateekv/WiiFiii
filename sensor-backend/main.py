"""
sensor-backend/main.py
─────────────────────
WiFi CSI Home Sensing — Live Pipeline Backend
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Set, Dict, Any
import time

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Import our scanner logic
from network_scanner import get_network_info, read_arp_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Global State ──────────────────────────────────────────────────────────────
connected_clients: Set[WebSocket] = set()

# In-memory stores for our live data
latest_devices: list = []
latest_csi_nodes: Dict[str, dict] = {}


# ── UDP Listener (CSI Data) ───────────────────────────────────────────────────
class CsiUdpProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        log.info("UDP Server listening on port 5005 for CSI broadcasts...")

    def datagram_received(self, data, addr):
        try:
            payload = data.decode("utf-8")
            csi_data = json.loads(payload)
            node_id = csi_data.get("node_id", "unknown_node")
            
            # Keep track of the latest frame per node, adding a timestamp
            csi_data["last_seen"] = time.time()
            latest_csi_nodes[node_id] = csi_data
        except Exception as e:
            # Drop malformed packets silently to avoid log spam
            pass


async def start_udp_server():
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: CsiUdpProtocol(),
        local_addr=("0.0.0.0", 5005)
    )
    return transport


# ── Background Tasks ──────────────────────────────────────────────────────────
async def device_scanner_loop():
    """Periodically scan the network for connected devices."""
    log.info("Starting network device scanner loop...")
    while True:
        try:
            # We use the ARP cache read (fallback path) because it doesn't require admin
            # and is fast enough for a live dashboard.
            devices = read_arp_cache()
            
            global latest_devices
            latest_devices = [d.to_dict() for d in devices]
        except Exception as e:
            log.error(f"Device scanner error: {e}")
            
        await asyncio.sleep(5)  # Scan every 5 seconds


async def pipeline_broadcast_loop():
    """Broadcasts the combined live data to all WebSocket clients."""
    log.info("Starting WebSocket broadcast loop...")
    tick = 0
    while True:
        await asyncio.sleep(1) # Broadcast at 1Hz
        tick += 1
        
        # Clean up stale CSI nodes (not seen in 3 seconds)
        current_time = time.time()
        stale_nodes = [node_id for node_id, data in latest_csi_nodes.items() 
                       if current_time - data["last_seen"] > 3]
        for node_id in stale_nodes:
            del latest_csi_nodes[node_id]
            
        payload = {
            "type": "live_pipeline_frame",
            "tick": tick,
            "connected_devices": latest_devices,
            "csi_nodes": latest_csi_nodes
        }
        
        await broadcast(payload)


# ── Lifespan: start background tasks on startup ───────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 Sensor backend starting…")
    
    udp_transport = await start_udp_server()
    scanner_task = asyncio.create_task(device_scanner_loop())
    broadcast_task = asyncio.create_task(pipeline_broadcast_loop())
    
    yield
    
    udp_transport.close()
    scanner_task.cancel()
    broadcast_task.cancel()
    log.info("👋 Sensor backend shutting down.")


app = FastAPI(title="WiFi CSI Sensor Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST endpoints ────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "clients": len(connected_clients)}

@app.get("/pipeline/state")
async def get_pipeline_state():
    return {
        "connected_devices": latest_devices,
        "csi_nodes": latest_csi_nodes
    }


# ── WebSocket endpoint ────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)
    log.info(f"Client connected. Total: {len(connected_clients)}")
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(ws)
        log.info(f"Client disconnected. Total: {len(connected_clients)}")


async def broadcast(payload: dict):
    if not connected_clients:
        return
    msg = json.dumps(payload)
    dead = set()
    for client in connected_clients:
        try:
            await client.send_text(msg)
        except Exception:
            dead.add(client)
    connected_clients -= dead

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
