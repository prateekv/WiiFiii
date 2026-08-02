# WiFi CSI Home Sensing — Pre-Build Research Report
*Generated: August 2026 | Portfolio project scoping only — no code yet*

---

## 1. Best Open-Source CSI Extraction Tools (ESP32-focused, 2025–2026)

### 🥇 Tier 1 — Actively Maintained, Recommended

#### `espressif/esp-csi`
- **Repo:** https://github.com/espressif/esp-csi
- **Maintained by:** Espressif Systems (chip manufacturer — first-party support)
- **Status:** ✅ Actively maintained through 2025–2026 with ESP-IDF v5.x support
- **What it does:** Official Espressif toolkit. Provides firmware examples for CSI capture, human detection, and radar-style sensing. CSI is accessed via the official `esp_wifi_set_csi_rx_cb()` API. Supports ESP32, ESP32-S3, ESP32-C3, ESP32-C6.
- **Key strength:** This is the most future-proof option because it's first-party. As new ESP32 variants ship, this gets updated first.
- **Limitation:** Examples are more "starter kit" than turnkey. You still build the visualization layer.

#### `StevenMHernandez/ESP32-CSI-Tool`
- **Repo:** https://github.com/StevenMHernandez/ESP32-CSI-Tool
- **Status:** ✅ Widely cited in 2024–2025 research; community-maintained
- **What it does:** The de facto community "gold standard." Supports **Active mode** (ESP32 sends WiFi packets to itself and reads CSI) and **Passive mode** (sniffer, reads CSI from all nearby WiFi traffic). Exports via USB serial or SD card.
- **Key strength:** Extensively documented, most GitHub stars of any ESP32 CSI tool, large issue tracker full of solved problems.
- **Limitation:** Serial/SD output is less convenient than wireless; you need a laptop tethered via USB to receive data live.

#### `Rui-Chun/ESP32-CSI-Collection-and-Display`
- **Repo:** https://github.com/Rui-Chun/ESP32-CSI-Collection-and-Display
- **Status:** ✅ Community-maintained, recommended for wireless setups
- **What it does:** Transmits CSI wirelessly via **mDNS + UDP** instead of USB serial. Has a built-in real-time display. Avoids the cable tethering problem of ESP32-CSI-Tool.
- **Key strength:** Most convenient for a home sensing deployment where ESP32s are mounted on walls and you want to receive data over WiFi.
- **Limitation:** Less comprehensive documentation than ESP32-CSI-Tool.

### 🥈 Tier 2 — Useful but Situational

#### `HKU-COMP3516-ESP32-CSI-Tool`
- **Repo:** https://github.com/HKU-COMP3516-ESP32-CSI-Tool
- **Status:** ✅ Maintained for newer chips (ESP32-S3)
- **What it does:** Fork of the main ESP32-CSI-Tool, adapted for modern ESP-IDF (v5.x) and ESP32-S3. Good if you use S3 boards and the original tool gives IDF version conflicts.
- **Use when:** Your build environment is on ESP-IDF v5.x.

#### Nexmon CSI (Raspberry Pi / Broadcom)
- **Repo:** https://github.com/seemoo-lab/nexmon_csi
- **Status:** ⚠️ **Not recommended for new projects (2025–2026).** Community-maintained but highly sensitive to Linux kernel versions. Raspberry Pi 5 and recent Bookworm/Trixie kernels are not well-supported; requires manual patching and older kernel pinning.
- **What it does:** Patches Broadcom WiFi firmware on Raspberry Pi to expose raw CSI. More subcarriers than ESP32, making it attractive for research.
- **Verdict:** Only use if you specifically need Raspberry Pi AND you're comfortable with kernel hacking. For a portfolio project, ESP32 is much lower friction.

---

## 2. GitHub Repos: Real-Time CSI Movement Detection + Live Visualization

### Repo A — `espressif/esp-csi` (examples folder)
- **URL:** https://github.com/espressif/esp-csi
- **What it does:** Includes a `human_detection` example that streams CSI from ESP32-S3, processes amplitude variance across subcarriers, and flags movement/presence. Has a simple Python-based serial plotter.
- **Stack:** C (ESP-IDF firmware) + Python (matplotlib live plot)
- **Last updated:** Actively updated through 2025–2026
- **Relevance:** Best starting point for firmware. You'd replace the matplotlib plot with your own WebSocket dashboard.

### Repo B — `RS2002/ESP32-Realtime-System`
- **URL:** https://github.com/RS2002/ESP32-Realtime-System
- **What it does:** Comprehensive sensing system featuring live CSI amplitude, phase, and spectrum display. Supports movement detection, fall detection, and gesture recognition modes. Has a web-based dashboard component.
- **Stack:** C (ESP-IDF) + Python (FastAPI backend) + HTML/JS frontend via WebSocket
- **Last updated:** 2024–2025 (active)
- **Relevance:** ⭐ This is the closest to what you want. The architecture (ESP32 → Python server → WebSocket → browser) is exactly what your project needs.

### Repo C — `Gi-z/CSIKit`
- **URL:** https://github.com/Gi-z/CSIKit
- **What it does:** Python framework for parsing and visualizing raw CSI files from multiple hardware sources: ESP32, Intel 5300, Atheros, Nexmon, PicoScenes. Includes CLI tools, matplotlib graphs for amplitude/phase/spectrogram, and integrates with TensorFlow/PyTorch.
- **Stack:** Python (pure), pip-installable
- **Last updated:** Active as of early 2024; pip package is still maintained
- **Relevance:** ⭐ Best library to **build on top of** for your Python backend. Parse/clean raw CSI bytes from ESP32, then forward processed data to your dashboard.

### Repo D — `xyanchen/WiFi-CSI-Sensing-Benchmark` (SenseFi)
- **URL:** https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark
- **What it does:** The industry-standard benchmark suite for deep learning on CSI data. Includes datasets, preprocessing pipelines, and baseline ML models (CNN, LSTM, Transformer) for activity recognition and localization.
- **Stack:** Python (PyTorch + NumPy + SciPy)
- **Last updated:** 2024–2025 (research community active)
- **Relevance:** Reference this to borrow preprocessing code (phase sanitization, subcarrier selection). You don't need its ML components initially — the signal processing utilities are the gem.

### Repo E — `GitHub topic: #wifi-csi`
- **URL:** https://github.com/topics/wifi-csi
- **What it does:** Aggregates 30+ repos tagged with `wifi-csi`. Notable ones include WebSocket-based 3D Three.js tracking visualizations and Doppler radar views.
- **Stack:** Various
- **Last updated:** Topic is actively populated in 2025–2026
- **Relevance:** Use as a discovery hub. Filter by "recently updated" to find fresh projects when you begin building.

---

## 3. Device Discovery Tools (ARP Scan — Easier First Step)

This is independent of CSI and simpler. It answers "who is on my network right now?"

### Python Libraries

| Library | Install | How it works | Quality |
|---|---|---|---|
| **`scapy`** | `pip install scapy` | Crafts raw ARP packets, parses replies. Returns IP + MAC. Cross-platform. Needs admin/sudo. | ⭐ Best — full control |
| **`python-nmap`** | `pip install python-nmap` | Python wrapper for `nmap`. Supports OS detection, port scanning, richer output. | Good for richer data |
| **`getmac`** | `pip install getmac` | Simpler — reads the OS ARP cache, no active scan. Fast but misses silent devices. | Lightweight/limited |

**Recommended for your project:** `scapy` — it gives you clean IP + MAC + hostname (via a follow-up DNS lookup), is well-maintained, and works on Windows with Npcap installed.

### Node.js Libraries

| Library | Install | Notes |
|---|---|---|
| **`arpscan`** | `npm install arpscan` | Wraps the system `arp-scan` binary. Simple callback interface. Requires `arp-scan` on PATH. |
| **`network-list`** | `npm install network-list` | Pure JS, no binary dependency. Less reliable on Windows. |
| **Child process `arp-scan`** | No install needed | `exec('sudo arp-scan -l')` and parse stdout. Dirty but effective on Linux/macOS. |

**For your web dashboard (Node backend):** Use `arpscan` npm package. If your backend is Python (FastAPI), use `scapy`.

### Detecting Which Router You're On
Use `netifaces` (Python: `pip install netifaces`) to get the current default gateway (your router's IP). Then use `scapy` or `socket` to query the router. This gives you the exact subnet to ARP-scan.

---

## 4. Fork vs. Build From Scratch — Recommendations

### ✅ Reference (don't fork, study and adapt)
- **`StevenMHernandez/ESP32-CSI-Tool`** — flash this firmware first to validate your ESP32 hardware outputs CSI correctly before writing a line of Python.
- **`xyanchen/WiFi-CSI-Sensing-Benchmark`** — steal the CSI preprocessing pipeline (phase sanitization, amplitude normalization). Don't use its full ML stack.

### ✅ Build on top of (fork or install as library)
- **`Gi-z/CSIKit`** — install as a pip library. It handles the dirty parsing of raw ESP32 CSI bytes so you don't have to write a binary parser.
- **`RS2002/ESP32-Realtime-System`** — fork this. Its architecture (ESP32 → Python → WebSocket → browser) matches your goal. You'll want to replace the visualization layer with something better, but the data pipeline is solid.

### ✅ Use as firmware base
- **`espressif/esp-csi`** — use the official repo's `get-started` example as your ESP32 firmware foundation. It's first-party and tracks ESP-IDF v5.x.

### ❌ Avoid for this project
- **Nexmon CSI** — kernel maintenance burden too high for a portfolio project.
- **Intel 5300 / Linux 802.11n CSI Tool** — requires old laptop hardware, discontinued NIC, patched kernels. Not practical in 2025+.

### Summary Architecture Recommendation

```
[ESP32 nodes × 3–4, wall-mounted]
    │ UDP packets over WiFi
    ▼
[Python backend — FastAPI]
    ├── CSIKit: parse raw CSI bytes
    ├── NumPy/SciPy: variance, Doppler, heatmap
    └── WebSocket: stream to browser
    ▼
[Browser dashboard — Vanilla JS or React]
    ├── Floor plan SVG overlay
    ├── Heatmap.js or D3: live heatmap
    └── ARP table panel: connected devices
```

---

## 5. Hardware Required

### ESP32 Nodes (CSI Sensors)

| Board | Purpose | Quantity | Est. Price (USD) | Est. Price (INR) | Buy From |
|---|---|---|---|---|---|
| **ESP32-WROOM-32 DevKit** | Primary CSI node — good for getting started | 2–3 | ~$5–8 each | ₹350–450 each | AliExpress, Robu.in, Amazon |
| **ESP32-S3-DevKitC-1** | Upgraded node — faster CPU, AI acceleration, more RAM | 2–3 (optional upgrade) | ~$8–12 each | ₹650–950 each | AliExpress, Mouser |
| **ESP32-WROOM-32U** (external antenna variant) | Better range / through-wall penetration | 1–2 | ~$6–10 each | ₹400–600 each | AliExpress |
| **2.4GHz external antennas** (3dBi dipole) | Improves sensing range | 1 per -U board | ~$1–2 each | ₹80–150 each | AliExpress |
| **USB-C cables** (data, not charge-only) | Flashing firmware | 3–4 | ~$2–4 each | ₹100–200 each | Local |
| **USB power adapters or powered USB hub** | Powering nodes during deployment | 1 hub or adapters | ~$10–20 total | ₹800–1500 | Amazon |

### Minimum viable setup: **3× ESP32-WROOM-32** — one as transmitter (AP/ping mode), two as receivers in opposite corners of a room. Total cost: ~$20–25 USD (₹1,500–2,000).

### Recommended setup for multi-room mapping: **4× ESP32-S3-DevKitC-1** deployed in a cross-floor-plan pattern. Total cost: ~$40–50 USD (₹3,200–4,000).

### Your Laptop
No special hardware needed. Your laptop connects to the same WiFi network, runs the Python backend, and serves the browser dashboard. The ARP scanner also runs on your laptop.

---

## 6. Software Dependencies (Dev Machine)

### Firmware Side (ESP32 Flashing)

| Dependency | Version | Install |
|---|---|---|
| **ESP-IDF** (Espressif IoT Dev Framework) | v5.2+ (latest stable) | https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/ |
| **Python** (IDF dependency) | 3.9–3.12 | Required by IDF build system |
| **CMake** | 3.16+ | Bundled with IDF installer on Windows |
| **Ninja build** | Latest | Bundled with IDF installer |
| **Git** | 2.x | Required by IDF component manager |
| **esptool.py** | Auto-installed with IDF | Flashing tool |
| **VS Code + ESP-IDF extension** | Latest | Optional but highly recommended for Windows |

> **Windows Note:** Use the official IDF Windows installer (`esp-idf-tools-setup-online.exe`). Do NOT try to manually install IDF on Windows — the installer handles all PATH and toolchain issues automatically.

### Backend (Python)

| Package | Purpose | Install |
|---|---|---|
| **`fastapi`** | WebSocket + REST API server | `pip install fastapi uvicorn` |
| **`uvicorn`** | ASGI server for FastAPI | `pip install uvicorn[standard]` |
| **`websockets`** | Low-level WebSocket support | `pip install websockets` |
| **`CSIKit`** | Parse raw ESP32 CSI bytes | `pip install csikit` |
| **`numpy`** | Signal math — variance, FFT | `pip install numpy` |
| **`scipy`** | Filters, spectrograms, signal cleanup | `pip install scipy` |
| **`scapy`** | ARP scanning for connected devices | `pip install scapy` |
| **`netifaces`** | Get gateway/router IP, subnet | `pip install netifaces` |
| **`python-nmap`** | Optional: richer device info | `pip install python-nmap` |
| **`asyncio`** | Concurrent UDP listening + WebSocket | stdlib (built in) |

> **Windows Note:** `scapy` on Windows requires **Npcap** (https://npcap.com) — install this first, it's free.

### Frontend (Browser Dashboard)

| Dependency | Purpose | Install |
|---|---|---|
| **Vanilla HTML/JS** or **React + Vite** | Dashboard UI | No install for vanilla; `npm create vite@latest` for React |
| **Heatmap.js** | Live 2D heatmap overlay on floor plan | CDN: `https://cdn.jsdelivr.net/npm/heatmap.js` |
| **D3.js** | SVG floor plan + data binding | CDN |
| **Chart.js** | RSSI/amplitude time series charts | CDN |
| **Socket.IO or native WebSocket** | Receive live data from Python server | CDN or `npm install socket.io-client` |

### System Tools

| Tool | Purpose | Install |
|---|---|---|
| **Npcap** (Windows) | Required by Scapy for raw packet access | https://npcap.com |
| **Nmap** | Optional: richer device discovery | https://nmap.org/download |
| **Wireshark** | Optional: debug WiFi packet captures | https://wireshark.org |
| **Git** | Version control | https://git-scm.com |
| **Node.js 18+** | If using JS tooling / Vite frontend | https://nodejs.org |

---

## Key Caveats & Gotchas

> [!IMPORTANT]
> **CSI is not GPS.** You cannot get sub-meter XY coordinates directly from raw CSI without training a location-specific ML model. Your "map" will initially be a heatmap of **movement probability** or **presence score** — not an exact person position. This is still impressive and useful, but calibrate expectations.

> [!WARNING]
> **Windows ARP scanning requires Npcap AND running as Administrator.** Test your scapy ARP scanner in a PowerShell Admin window from day one to avoid confusing permission errors later.

> [!NOTE]
> **Start with 1 room, 1 transmitter, 2 receivers.** CSI sensing accuracy degrades rapidly across walls. Multi-room mapping is a hard problem that even research papers solve only approximately. Get single-room detection working first, then expand.

> [!TIP]
> **2.4GHz only for ESP32.** Standard ESP32 boards only support 2.4GHz WiFi. This is fine for CSI sensing but means your sensing nodes must share the band with your router. If your home network is congested on 2.4GHz, consider isolating the ESP32s on a separate 2.4GHz-only SSID.
