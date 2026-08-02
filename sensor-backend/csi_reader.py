"""
sensor-backend/csi_reader.py
────────────────────────────
Handles receiving raw CSI data over UDP from the ESP32 boards.
"""

import asyncio
import json
import logging
import time
from typing import Dict

log = logging.getLogger(__name__)

class CsiUdpProtocol(asyncio.DatagramProtocol):
    def __init__(self, csi_nodes_state: Dict[str, dict]):
        self.csi_nodes_state = csi_nodes_state

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
            self.csi_nodes_state[node_id] = csi_data
        except Exception as e:
            pass

async def start_udp_server(csi_nodes_state: Dict[str, dict]):
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: CsiUdpProtocol(csi_nodes_state),
        local_addr=("0.0.0.0", 5005)
    )
    return transport
