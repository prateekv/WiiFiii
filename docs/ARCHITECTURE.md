# Architecture Document: WiFi CSI Home Sensing

This document provides the detailed architecture and handoff instructions for building the live WiFi CSI sensing pipeline.

## 1. Data Flow Diagram

```
[ESP32 CSI Nodes]
       │ (UDP Broadcast Packets on Port 5005)
       ▼
[Python Backend (sensor-backend)]
       ├── csi_reader.py       (Listens for UDP CSI frames)
       ├── device_scanner.py   (Scans network via ARP for connected devices)
       └── ws_server.py        (Bundles CSI + Device data every second)
       │
       │ (WebSocket Connection)
       ▼
[Next.js Frontend (web-app)]
       └── components/LiveMap.tsx  (Consumes JSON stream and renders heatmap/Three.js)
```

## 2. Stub File Responsibilities

- **`sensor-backend/main.py`**: The FastAPI entry point. Manages background tasks and ties everything together.
- **`sensor-backend/device_scanner.py`**: Scans the local network (via `scapy` or `arp -a`) to find connected devices.
- **`sensor-backend/csi_reader.py`**: Sets up the `asyncio` UDP listener to catch broadcast CSI packets from ESP32 nodes.
- **`sensor-backend/ws_server.py`**: Manages active WebSocket connections and broadcasts the combined data stream.
- **`web-app/src/components/LiveMap.tsx`**: The frontend React component that will eventually render the Three.js 3D map.
- **`firmware/main/main.c`**: The ESP-IDF firmware for the ESP32 nodes to collect and transmit CSI.

## 3. Expected Input/Output Formats

**ESP32 UDP Output (JSON string over UDP):**
```json
{
  "node_id": "esp32-node-01",
  "mac": "64:fb:92:b6:07:7e",
  "rssi": -42,
  "payload_preview": "00 11 22 33"
}
```

**WebSocket Output (Combined Pipeline Stream):**
```json
{
  "type": "live_pipeline_frame",
  "tick": 124,
  "connected_devices": [
    { "ip": "192.168.1.1", "mac": "aa:bb:cc...", "hostname": "router" }
  ],
  "csi_nodes": {
    "esp32-node-01": {
      "mac": "64:fb:92:b6:07:7e",
      "rssi": -42,
      "payload_preview": "00 11 22 33",
      "last_seen": 1690001234.5
    }
  }
}
```

## 4. CSI Extraction Integration

We are basing the CSI extraction on the **official `espressif/esp-csi` methodology** natively available in ESP-IDF v5.x.
- **How to integrate:** Use the `esp_wifi_set_csi_rx_cb()` function in the firmware to intercept raw CSI bytes. Extract the MAC, RSSI, and buffer from `wifi_csi_info_t`, serialize it into JSON, and send it over a UDP socket (`sendto`) to the network broadcast address `255.255.255.255:5005`.

## 5. Router Device Scanning Integration

We are using **`scapy` (with an `arp -a` fallback)** for network device scanning.
- **How to integrate:** Use `subprocess.run("ipconfig")` to get the subnet gateway, then actively ping the subnet and read the local ARP cache (`arp -a`) to get the IP and MAC mapping. This runs in a background thread in the Python backend so it doesn't block the WebSocket.

## 6. Coding Conventions

- **Keep it simple:** Use plain functions and dataclasses. Avoid over-engineering (no complex OOP hierarchies).
- **Extensive Comments:** The user is non-technical. Explain all WiFi/signal concepts (e.g., what RSSI means, why we need active traffic) in plain English comments above the relevant code blocks.
- **Async Python:** Use `asyncio` for the backend to prevent blocking on network operations.

## 7. Explicit Note on Storage

> **CRITICAL:** No data storage/database. Everything is live/in-memory only. Do not add SQLite, Redis, or file logging.

## 8. Step-by-Step Build Order

Gemini should follow this exact order:
1. **`sensor-backend/device_scanner.py`**: Get the ARP network scanner working first.
2. **`sensor-backend/csi_reader.py`**: Build the UDP listener to catch the ESP32 data.
3. **`sensor-backend/ws_server.py`**: Create the WebSocket broadcaster to merge and send the data.
4. **`web-app/src/components/LiveMap.tsx`**: Build the Next.js frontend to consume and display the data.
