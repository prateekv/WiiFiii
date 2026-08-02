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

async def main():
    """Standalone test mode for Step 3: Just read and print raw CSI data to the terminal."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("==================================================")
    print(" STEP 3: LIVE CSI STREAM READER (Terminal Output) ")
    print("==================================================")
    
    test_state = {}
    transport = await start_udp_server(test_state)
    
    try:
        while True:
            await asyncio.sleep(1)
            # Print whatever is in the state dict
            if test_state:
                print("\n--- Live Raw CSI Data ---")
                for node_id, data in test_state.items():
                    print(f"Node: {node_id} | MAC: {data.get('mac')} | RSSI: {data.get('rssi')} | Payload Preview: {data.get('payload_preview')}")
            else:
                print("Waiting for ESP32 UDP packets on port 5005...")
    except KeyboardInterrupt:
        pass
    finally:
        transport.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")
