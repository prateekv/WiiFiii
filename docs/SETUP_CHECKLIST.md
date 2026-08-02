# 📋 Pre-Flight Setup Checklist

Complete this checklist *before* asking Gemini to start writing code for the WiFi CSI project.

## 1. Local Software & Drivers
- [ ] **Python**: Installed (v3.9 or higher).
- [ ] **Node.js**: Installed (v18 or higher) for the frontend dashboard.
- [ ] **ESP-IDF**: Installed via the official [Windows Online Installer](https://dl.espressif.com/dl/idf-installer/esp-idf-tools-setup-online.exe) (v5.2 or later). *Required for compiling firmware.*
- [ ] **Npcap**: Installed via [npcap.com](https://npcap.com). *Required on Windows for the Python backend to perform ARP scans.*
- [ ] **Git**: Installed and initialized in the project root.

## 2. Hardware Ready
- [ ] **ESP32 Boards**: At least 2–3 ESP32 boards (e.g., ESP32-WROOM-32 or ESP32-S3).
- [ ] **Data Cables**: USB cables tested for data transfer (not charge-only).
- [ ] **Power**: A powered USB hub or wall adapters if deploying boards away from your laptop.

## 3. Network & API Access
- [ ] **WiFi Credentials**: Know your 2.4GHz network SSID and password (the ESP32s will need this hardcoded).
- [ ] **Admin Rights**: Ensure you can run PowerShell as Administrator (needed for the `scapy` ARP scanner).
- [ ] *(Optional)* **Router Admin**: Router login is *not* required since we are using ARP scanning, but keep it handy in case you need to isolate the ESP32s on a guest network.

---

## 🤖 Initial Prompt for Gemini

Copy and paste this exact paragraph to Gemini to kick off the coding phase:

> "I have completed the local hardware and software setup for my WiFi CSI home sensing project. Please read `/docs/ARCHITECTURE.md` and `/docs/research.md` to understand the full scope of the project. Then, following the architecture strictly, begin building the project in order, starting exclusively with the `sensor-backend/device_scanner.py` component. Do not move on to the next component until I confirm this one is working."
