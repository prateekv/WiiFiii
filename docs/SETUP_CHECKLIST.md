# Final Setup Checklist

Before switching over to Gemini, ensure the following steps are complete on your local machine.

## 1. Local Installations

- **Python**: Version 3.9+ is installed and on your PATH.
- **Node.js**: Version 18+ is installed and on your PATH.
- **ESP-IDF**: Installed via the official Windows Installer (v5.2+).
- **Npcap**: Installed (required for `scapy` on Windows).

## 2. Hardware Ready

- **ESP32 Boards**: At least 3 ESP32 boards (WROOM or S3).
- **USB Cables**: Data-capable USB cables for each board.
- **Power**: Wall adapters or a powered USB hub to run the boards once flashed.

## 3. Accounts & API Access

- No router admin login is required (we are using passive ARP scanning).
- No external APIs are used (everything is local).

## 4. Gemini Handoff Summary

**Copy and paste the following paragraph to Gemini as your very first message:**

> I am building a live WiFi CSI home sensing project. Please review `/docs/ARCHITECTURE.md` and `/docs/research.md` to understand the full scope. I want you to build the implementation exactly in the order specified in the architecture document, starting with `sensor-backend/device_scanner.py`. Remember: no data storage or databases—everything must be live and in-memory only.
