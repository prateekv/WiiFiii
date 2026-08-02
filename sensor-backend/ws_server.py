"""
sensor-backend/ws_server.py
───────────────────────────
Final Live Pipeline WebSocket Server (Step 6)
Combines device scanning, raw CSI reading, and signal processing 
into a single live JSON stream.
"""

import asyncio
import json
import logging
import datetime
import websockets
from websockets.exceptions import ConnectionClosed

# Import modules
from device_scanner import (
    get_network_info, 
    scan_network_scapy, 
    scan_network_fallback, 
    check_admin_privileges
)
from csi_reader import CsiUdpProtocol, start_udp_server
from signal_processor import CSISignalProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Global state
connected_clients = set()
csi_raw_state = {}  # Holds raw CSI packets
processor = CSISignalProcessor()
latest_device_list = []

async def register(websocket):
    connected_clients.add(websocket)
    log.info(f"Client connected. Total clients: {len(connected_clients)}")

async def unregister(websocket):
    connected_clients.discard(websocket)
    log.info(f"Client disconnected. Total clients: {len(connected_clients)}")

async def device_scanner_task():
    """Background task to continuously scan for connected devices every 5 seconds."""
    log.info("Starting background device scanner...")
    is_admin = check_admin_privileges()
    
    global latest_device_list
    
    while True:
        try:
            net_info = get_network_info()
            if net_info.subnet_cidr == "Unknown":
                await asyncio.sleep(5)
                continue

            if is_admin:
                try:
                    devices = scan_network_scapy(net_info.subnet_cidr)
                except ImportError:
                    devices = scan_network_fallback(net_info.subnet_cidr)
            else:
                devices = scan_network_fallback(net_info.subnet_cidr)

            latest_device_list = [{"ip": d.ip, "mac": d.mac, "name": d.hostname} for d in devices]
        except Exception as e:
            log.error(f"Scanner error: {e}")
            
        await asyncio.sleep(5)

async def pipeline_broadcast_task():
    """
    Core pipeline loop running at 1Hz. 
    Pulls raw CSI data, runs the signal processor, merges with device list,
    and broadcasts to the frontend dashboard.
    """
    log.info("Starting WebSocket broadcast pipeline...")
    
    while True:
        try:
            # 1. Feed the latest raw CSI packets into the processor
            for node_id, data in list(csi_raw_state.items()):
                rssi = data.get('rssi', 0)
                processor.add_data_point(node_id, rssi)
                # clear it so we don't process stale data multiple times
                del csi_raw_state[node_id]
                
            # 2. Process to get movement and zone estimates
            processor.process()
            
            # 3. Construct the combined payload
            payload = {
                "type": "live_pipeline_frame",
                "timestamp": datetime.datetime.now().isoformat(),
                "devices": latest_device_list,
                "analytics": processor.get_state()
            }
            message = json.dumps(payload)

            # 4. Broadcast
            if connected_clients:
                tasks = [asyncio.create_task(client.send(message)) for client in connected_clients]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                # Client disconnects will be cleaned up by the handler loop
                
        except Exception as e:
            log.error(f"Pipeline error: {e}")
            
        await asyncio.sleep(1) # Broadcast at 1Hz

async def connection_handler(websocket, path):
    await register(websocket)
    try:
        async for message in websocket:
            pass
    except ConnectionClosed:
        pass
    finally:
        await unregister(websocket)

async def main():
    """Main entry point for the entire backend."""
    log.info("=======================================")
    log.info(" WiFi CSI Home Sensing Backend         ")
    log.info("=======================================")
    
    # 1. Start the UDP server to listen for ESP32 broadcasts
    udp_transport = await start_udp_server(csi_raw_state)
    
    # 2. Start WebSocket server for frontend
    server = await websockets.serve(connection_handler, "localhost", 8765)
    log.info("WebSocket Server listening on ws://localhost:8765")
    
    # 3. Start background loops
    scanner_task = asyncio.create_task(device_scanner_task())
    broadcast_task = asyncio.create_task(pipeline_broadcast_task())
    
    # Run forever
    await server.wait_closed()
    
    # Cleanup
    udp_transport.close()
    scanner_task.cancel()
    broadcast_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Backend stopped.")
