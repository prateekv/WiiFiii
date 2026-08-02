"""
sensor-backend/device_server.py
─────────────────────────────────
Live "who's on my network" WebSocket server.

Run:
  python device_server.py             (uses ping-sweep + arp -a, no admin)
  python device_server.py --interval 10   (scan every 10 seconds)

Then open: http://localhost:8765
"""

import argparse
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Set

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from network_scanner import Device, NetworkInfo, get_network_info, scan_network

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Shared state (in-memory only, no persistence) ─────────────────────────────
class AppState:
    network_info: NetworkInfo = NetworkInfo()
    devices: list[Device] = []
    last_scan_at: float = 0.0
    scan_duration_ms: float = 0.0
    scan_count: int = 0
    # Track first_seen across scans within this session
    _first_seen_map: dict[str, float] = {}

state = AppState()
clients: Set[WebSocket] = set()

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(title="WiFi Device Scanner", version="1.0.0")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_dashboard():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/status")
async def api_status():
    return JSONResponse({
        "network": state.network_info.to_dict(),
        "device_count": len(state.devices),
        "last_scan_at": state.last_scan_at,
        "scan_duration_ms": state.scan_duration_ms,
        "scan_count": state.scan_count,
    })


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    log.info(f"Client connected ({len(clients)} total)")
    # Send current state immediately on connect
    try:
        await ws.send_text(_build_payload())
        while True:
            await ws.receive_text()          # keep-alive; data flows server→client
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)
        log.info(f"Client disconnected ({len(clients)} total)")


# ── Broadcast helpers ──────────────────────────────────────────────────────────

def _build_payload() -> str:
    return json.dumps({
        "type": "update",
        "network": state.network_info.to_dict(),
        "devices": [d.to_dict() for d in state.devices],
        "last_scan_at": state.last_scan_at,
        "scan_duration_ms": round(state.scan_duration_ms),
        "scan_count": state.scan_count,
        "server_time": time.time(),
    })


async def _broadcast():
    if not clients:
        return
    payload = _build_payload()
    dead = set()
    for ws in clients:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    clients -= dead


# ── Background scan loop ───────────────────────────────────────────────────────

async def scan_loop(interval: int):
    """Runs the network scan every `interval` seconds and broadcasts results."""
    log.info(f"Scanner starting — interval={interval}s")
    loop = asyncio.get_event_loop()

    while True:
        t0 = time.time()
        try:
            # Network info (fast — just netsh + netifaces)
            info = await loop.run_in_executor(None, get_network_info)
            state.network_info = info

            if info.gateway_ip:
                log.info(f"Scanning {info.subnet_cidr()} (SSID: {info.ssid})")
                raw_devices = await loop.run_in_executor(None, scan_network, info)

                # Preserve first_seen across scans
                now = time.time()
                for d in raw_devices:
                    if d.ip not in state._first_seen_map:
                        state._first_seen_map[d.ip] = now
                    d.first_seen = state._first_seen_map[d.ip]
                    d.last_seen = now

                # Prune first_seen map for IPs no longer seen > 5 mins
                cutoff = now - 300
                state._first_seen_map = {
                    ip: t for ip, t in state._first_seen_map.items()
                    if t > cutoff or any(d.ip == ip for d in raw_devices)
                }

                state.devices = raw_devices
            else:
                log.warning("No gateway detected — is WiFi connected?")
                state.devices = []

        except Exception as e:
            log.error(f"Scan error: {e}", exc_info=True)

        state.scan_duration_ms = (time.time() - t0) * 1000
        state.last_scan_at = time.time()
        state.scan_count += 1

        log.info(
            f"Scan #{state.scan_count}: {len(state.devices)} devices "
            f"in {state.scan_duration_ms:.0f}ms"
        )
        await _broadcast()
        await asyncio.sleep(interval)


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    # Read interval from app state (set by __main__ before starting uvicorn)
    interval = getattr(app.state, "scan_interval", 8)
    asyncio.create_task(scan_loop(interval))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live network device scanner")
    parser.add_argument(
        "--interval", type=int, default=8,
        help="Scan interval in seconds (default: 8)"
    )
    parser.add_argument(
        "--port", type=int, default=8765,
        help="HTTP/WebSocket port (default: 8765)"
    )
    args = parser.parse_args()

    app.state.scan_interval = args.interval

    print(f"""
╔══════════════════════════════════════════════════════╗
║        WiFi Device Scanner — Live Dashboard          ║
╠══════════════════════════════════════════════════════╣
║  Dashboard  →  http://localhost:{args.port:<5}               ║
║  Scan interval: every {args.interval}s                         ║
║                                                      ║
║  Tip: Run as Administrator for full ARP scan         ║
║       (otherwise uses ping-sweep + arp -a)           ║
╚══════════════════════════════════════════════════════╝
""")

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")
