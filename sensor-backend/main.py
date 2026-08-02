"""
sensor-backend/main.py
─────────────────────
WiFi CSI Home Sensing — Skeleton Backend
No sensing logic yet — just skeleton routes + WebSocket broadcaster.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Set

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Active WebSocket connections ──────────────────────────────────────────────
connected_clients: Set[WebSocket] = set()


# ── Lifespan: start background tasks on startup ───────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 Sensor backend starting…")
    # TODO: start CSI listener task here
    # TODO: start ARP scanner task here
    task = asyncio.create_task(mock_broadcast_loop())
    yield
    task.cancel()
    log.info("👋 Sensor backend shutting down.")


app = FastAPI(title="WiFi CSI Sensor Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Basic health check — confirms server is running."""
    return {"status": "ok", "clients": len(connected_clients)}


@app.get("/devices")
async def list_devices():
    """
    Returns devices found on the local network via ARP scan.
    TODO: replace stub with real scapy ARP scanner.
    """
    return {
        "devices": [
            {"ip": "192.168.1.1",   "mac": "aa:bb:cc:dd:ee:ff", "hostname": "router"},
            {"ip": "192.168.1.100", "mac": "11:22:33:44:55:66", "hostname": "my-laptop"},
        ]
    }


@app.get("/csi/status")
async def csi_status():
    """
    Returns status of the CSI listener.
    TODO: replace stub with real CSI listener state.
    """
    return {"listening": False, "nodes_connected": 0, "packets_per_sec": 0}


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)
    log.info(f"Client connected. Total: {len(connected_clients)}")
    try:
        while True:
            # Keep connection alive; actual data is pushed by broadcast loop
            await ws.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(ws)
        log.info(f"Client disconnected. Total: {len(connected_clients)}")


async def broadcast(payload: dict):
    """Send a JSON payload to all connected WebSocket clients."""
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


# ── Mock broadcast loop (remove when real CSI data arrives) ──────────────────

async def mock_broadcast_loop():
    """
    Sends fake CSI heatmap data every second so the frontend has something
    to render during skeleton / UI development.
    """
    import random
    tick = 0
    while True:
        await asyncio.sleep(1)
        tick += 1
        await broadcast({
            "type": "csi_frame",
            "tick": tick,
            "heatmap": [[round(random.random(), 3) for _ in range(10)] for _ in range(10)],
            "devices": 2,
        })


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
