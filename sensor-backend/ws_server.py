"""
sensor-backend/ws_server.py
───────────────────────────
Manages active WebSocket connections and broadcasts the live combined data stream.
"""

import json
import logging
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect

log = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.add(ws)
        log.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, ws: WebSocket):
        self.active_connections.discard(ws)
        log.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, payload: dict):
        if not self.active_connections:
            return
        msg = json.dumps(payload)
        dead = set()
        for client in self.active_connections:
            try:
                await client.send_text(msg)
            except Exception:
                dead.add(client)
        self.active_connections -= dead

manager = ConnectionManager()
