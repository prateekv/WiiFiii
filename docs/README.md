# WiFi CSI Home Sensing — Documentation

## Contents

- [Architecture Overview](./architecture.md) *(coming soon)*
- [ESP32 Hardware Setup & Wiring](./hardware-setup.md) *(coming soon)*
- [ESP-IDF Installation Guide (Windows)](./esp-idf-windows.md) *(coming soon)*
- [CSI Signal Processing Notes](./csi-processing.md) *(coming soon)*
- [Research References](./references.md) *(coming soon)*

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| CSI firmware | `espressif/esp-csi` | First-party, tracks ESP-IDF v5.x |
| CSI parsing library | `CSIKit` (pip) | Handles raw byte parsing, supports ESP32 |
| Backend framework | FastAPI + uvicorn | Async WebSocket support, fast, typed |
| Frontend | Next.js + Three.js | Modern SSR + 3D/WebGL for heatmap |
| Device discovery | Scapy ARP scan | Layer 2, no router API needed |
| Hardware | ESP32-S3-DevKitC-1 | Dual-core, 8MB PSRAM, AI acceleration |
