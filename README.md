# WiFi CSI Home Sensing

> **Status:** Environment setup in progress — skeleton only, no sensing logic yet.

A real-time home presence and movement sensing system using WiFi Channel State Information (CSI) with an ESP32 sensor network.

## Monorepo Structure

```
wifi/
├── firmware/          # ESP32 C firmware (ESP-IDF v5.x)
│   ├── main/
│   │   ├── main.c     # WiFi STA + CSI callback skeleton
│   │   └── CMakeLists.txt
│   └── CMakeLists.txt
│
├── sensor-backend/    # Python — processes CSI + ARP scan, serves WebSocket
│   ├── main.py        # FastAPI app with WebSocket broadcaster
│   └── requirements.txt
│
├── web-app/           # Next.js + Three.js — live dashboard
│   └── src/
│
├── docs/              # Architecture notes, wiring diagrams, references
│
├── .gitignore
└── README.md
```

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.9+ | Backend runtime |
| Node.js | 18+ | Frontend tooling |
| Git | 2.x | Version control |
| ESP-IDF | v5.2+ | ESP32 firmware build |
| Npcap | Latest | ARP scanning on Windows |

## Quick Start

### Backend
```bash
cd sensor-backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python main.py
# → http://localhost:8000
```

### Frontend
```bash
cd web-app
npm install
npm run dev
# → http://localhost:3000
```

### Firmware (requires ESP-IDF)
```bash
cd firmware
idf.py set-target esp32s3
idf.py build
idf.py -p COM<N> flash monitor
```

## Architecture

```
[ESP32 nodes × 3-4]  ──UDP──►  [Python FastAPI Backend]  ──WS──►  [Next.js Dashboard]
                                      │
                                 [ARP Scanner]
                                 (Scapy / Npcap)
```

## Docs
See [`/docs`](./docs/) for hardware wiring, ESP-IDF setup guide, and CSI processing notes.
