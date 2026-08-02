# sensor-backend

Python backend for the WiFi CSI Home Sensing project.

## Responsibilities (when complete)
- Listen for raw CSI data from ESP32 nodes over UDP
- Parse CSI bytes using CSIKit
- Run signal processing (amplitude variance, Doppler)
- ARP-scan the network to list connected devices
- Stream processed data to the web-app via WebSocket

## Running (skeleton)

```bash
# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Start server
python main.py
# or: uvicorn main:app --reload --port 8000
```

## Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Server health check |
| GET | `/devices` | ARP-scanned device list (stub) |
| GET | `/csi/status` | CSI listener status (stub) |
| WS | `/ws` | WebSocket — live CSI frames |

## Windows: Npcap Required
Before running ARP scanning, install Npcap from https://npcap.com  
Run the backend as Administrator for raw packet access.
