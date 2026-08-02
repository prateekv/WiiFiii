"""
sensor-backend/ws_server.py
───────────────────────────
Standalone WebSocket Server for Live Device Scanning.
Imports logic from device_scanner.py and broadcasts results to HTML clients.
"""

import asyncio
import json
import logging
import datetime
import websockets
from websockets.exceptions import ConnectionClosed

# Import the scanning logic we built in Step 1
from device_scanner import (
    get_network_info, 
    scan_network_scapy, 
    scan_network_fallback, 
    check_admin_privileges
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Keep track of connected clients
connected_clients = set()

async def register(websocket):
    """Registers a new client connection."""
    connected_clients.add(websocket)
    log.info(f"Client connected. Total clients: {len(connected_clients)}")

async def unregister(websocket):
    """Unregisters a client connection gracefully."""
    connected_clients.remove(websocket)
    log.info(f"Client disconnected. Total clients: {len(connected_clients)}")

async def broadcast_device_list():
    """
    Background task that scans the network every 5 seconds and 
    sends the results to all connected WebSocket clients.
    """
    log.info("Starting background device scanner loop...")
    is_admin = check_admin_privileges()
    
    while True:
        try:
            # 1. Get network info
            net_info = get_network_info()
            
            if net_info.subnet_cidr == "Unknown":
                log.error("Could not detect network subnet. Retrying in 5s...")
                await asyncio.sleep(5)
                continue

            # 2. Perform the scan
            if is_admin:
                try:
                    devices = scan_network_scapy(net_info.subnet_cidr)
                except ImportError:
                    devices = scan_network_fallback(net_info.subnet_cidr)
            else:
                devices = scan_network_fallback(net_info.subnet_cidr)

            # 3. Format the data payload as JSON
            device_list = []
            for d in devices:
                device_list.append({
                    "ip": d.ip,
                    "mac": d.mac,
                    "name": d.hostname
                })

            payload = {
                "type": "device_list",
                "timestamp": datetime.datetime.now().isoformat(),
                "devices": device_list
            }
            message = json.dumps(payload)

            # 4. Broadcast to all active clients
            if connected_clients:
                # Use asyncio.gather to send to all clients concurrently
                tasks = []
                for client in connected_clients:
                    tasks.append(asyncio.create_task(client.send(message)))
                
                # We catch exceptions internally in the handler so wait for them here
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        pass # The unregister handler will clean up disconnected clients
                        
        except Exception as e:
            log.error(f"Error during scan/broadcast: {e}")

        # Wait 5 seconds before scanning again
        await asyncio.sleep(5)

async def connection_handler(websocket, path):
    """Handles individual client connections."""
    await register(websocket)
    try:
        # Keep the connection open and listen for messages (even if we ignore them)
        # This is necessary to detect client disconnects properly.
        async for message in websocket:
            pass
    except ConnectionClosed:
        pass
    finally:
        await unregister(websocket)

async def main():
    """Entry point: starts the WebSocket server and the broadcast loop."""
    log.info("Starting WebSocket Server on ws://localhost:8765...")
    
    # Start the WebSocket server on port 8765
    server = await websockets.serve(connection_handler, "localhost", 8765)
    
    # Start the background broadcast loop
    broadcast_task = asyncio.create_task(broadcast_device_list())
    
    # Keep the server running forever
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Server stopped by user.")
