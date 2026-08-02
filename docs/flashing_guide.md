# ⚡ ESP32 Firmware Flashing Guide (Windows)

This guide walks you through compiling the CSI firmware and flashing it onto your ESP32 boards using the ESP-IDF toolchain.

## Prerequisites

1. **ESP-IDF Installed**: You must have installed ESP-IDF using the official Windows Installer (`esp-idf-tools-setup-online.exe`).
2. **USB Data Cable**: Ensure your USB cable is capable of data transfer (not just a charging cable).

---

## Step 1: Open the ESP-IDF Environment

You cannot use a standard PowerShell or VS Code terminal for this step. The ESP-IDF requires a specialized environment with all its build tools on the PATH.

1. Open your Windows **Start Menu**.
2. Search for and click **"ESP-IDF X.X PowerShell Environment"**.
3. A black terminal window will open and initialize the toolchain (it may take a few seconds).
4. Navigate to your firmware directory:
   ```powershell
   cd c:\Users\prate\Documents\code\wifi\firmware
   ```

## Step 2: Configure WiFi Credentials

Before flashing, you must tell the ESP32 how to connect to your router:

1. Open `firmware/main/main.c` in VS Code.
2. Find lines 17-18 and enter your actual WiFi network details:
   ```c
   #define WIFI_SSID      "YOUR_WIFI_NAME"
   #define WIFI_PASS      "YOUR_WIFI_PASSWORD"
   ```
3. Save the file.

> [!CAUTION]
> Do not commit your real WiFi password to GitHub! We will eventually move this into a configuration menu (`menuconfig`), but hardcoding it is easiest for this initial validation.

## Step 3: Find Your COM Port

1. Plug your ESP32 board into your laptop.
2. Right-click the Windows Start button and open **Device Manager**.
3. Expand the **Ports (COM & LPT)** section.
4. Note the COM port number of your ESP32 (e.g., `COM3`, `COM5`). It will typically be named something like "Silicon Labs CP210x" or "USB-SERIAL CH340".

## Step 4: Build, Flash, and Monitor

In your ESP-IDF PowerShell window (make sure you are inside the `firmware/` directory), run the following command. Replace `COM3` with your actual COM port from Step 3:

```powershell
idf.py -p COM3 build flash monitor
```

### What this command does:
- **`build`**: Compiles the C code into a binary payload. (This takes 1-2 minutes the first time).
- **`flash`**: Uploads the binary payload to the ESP32 over USB.
- **`monitor`**: Opens a live serial console so you can see what the ESP32 is printing.

> [!IMPORTANT]
> If the flashing process gets stuck at `Connecting...`, you may need to **hold down the "BOOT" button** on your ESP32 board until flashing begins.

## Step 5: Verify the CSI Stream

Once the monitor starts, you should see logs indicating the ESP32 is booting, connecting to WiFi, and getting an IP address.

Once connected, you will see a rapid, continuous stream of data like this:

```
I (2450) wifi-csi: Got IP: 192.168.1.50
I (2450) wifi-csi: CSI collection successfully enabled!
I (2460) wifi-csi: Traffic generator task started.
I (2510) wifi-csi: [CSI] MAC: 64:fb:92:b6:07:7e | RSSI: -42 dBm | Bytes: 128 | First 4 bytes: 00 00 00 00
I (2560) wifi-csi: [CSI] MAC: 64:fb:92:b6:07:7e | RSSI: -41 dBm | Bytes: 128 | First 4 bytes: 00 00 00 00
...
```

**If you see this data scrolling rapidly, congratulations! Your hardware is successfully extracting raw CSI data.**

## Step 6: Exiting the Monitor

To stop viewing the live stream and return to your prompt, press:

**`Ctrl + ]`** (Control + Right Bracket)

---

## Repeat for Other Boards

Unplug the flashed board, plug in the next one, and repeat Step 4. You may want to change `#define NODE_ID "esp32-node-02"` in `main.c` before flashing the second board to tell them apart later.
