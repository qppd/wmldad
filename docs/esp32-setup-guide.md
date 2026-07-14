# ESP32 Setup Guide — Complete Configuration for Water Meter Project

> **Target:** ESP32 NodeMCU-32S (38-pin) with Expansion Board  
> **OS:** Windows / Linux / Raspberry Pi OS (cross-platform)  
> **Audience:** Complete hardware/software setup from unboxing to first upload

---

## Table of Contents

1. [Hardware Overview](#hardware-overview)
2. [Driver Installation](#driver-installation)
3. [Arduino IDE / CLI Board Configuration](#arduino-ide--cli-board-configuration)
4. [Selecting the Correct Board](#selecting-the-correct-board)
5. [Selecting COM / ttyUSB Port](#selecting-com--ttyusb-port)
6. [Upload Process & Boot Modes](#upload-process--boot-modes)
7. [Boot Button & EN Button Usage](#boot-button--en-button-usage)
8. [Flash Button Usage](#flash-button-usage)
9. [Common Upload Errors & Fixes](#common-upload-errors--fixes)
10. [Verification Checklist](#verification-checklist)

---

## Hardware Overview

### ESP32 NodeMCU-32S (38-pin)

| Feature | Specification |
|---------|---------------|
| **MCU** | ESP32-WROOM-32D (Xtensa LX6 dual-core) |
| **USB-UART** | CP2102 (SiLabs) — requires CP210x driver |
| **GPIO** | 38 pins (34 usable) |
| **Flash** | 4 MB |
| **Voltage** | 3.3V logic, 5V USB input |
| **Pinout** | See [Block Diagram](../docs/block-diagram.md#pinout-reference-esp32-38-pin) |

### Expansion Board (38-pin)

- Screw terminals for all GPIOs
- 5V and 3.3V power rails
- Reset (EN) and Boot buttons accessible
- Mounting holes for enclosure

> 📸 **Screenshot Placeholder:** *Photo of ESP32 NodeMCU-32S mounted on expansion board with labeled pins*

---

## Driver Installation

### Windows (CP210x Driver)

1. **Download:** [Silicon Labs CP210x Universal Windows Driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
   - Direct: `CP210x_Universal_Windows_Driver.zip`
2. **Extract** and run `CP210xVCPInstaller_x64.exe` (or x86 for 32-bit)
3. **Restart** computer
4. **Verify:** Device Manager → Ports (COM & LPT) → **Silicon Labs CP210x USB to UART Bridge (COMx)**

> 📸 **Screenshot Placeholder:** *Windows Device Manager showing CP210x under Ports with COM port number*

### Linux (Raspberry Pi / Ubuntu / Debian)

```bash
# CP210x driver is built into kernel (>= 3.x)
# No installation needed

# Verify device appears
ls /dev/ttyUSB*
# Should show: /dev/ttyUSB0

# Check kernel messages
dmesg -w
# Plug in ESP32, watch for:
# cp210x 1-1.2:1.0: cp210x converter detected
# usb 1-1.2: cp210x converter now attached to ttyUSB0
```

### macOS

```bash
# Option 1: Official driver
# Download from: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
# Install .pkg, restart

# Option 2: Homebrew (community)
brew install --cask silicon-labs-vcp-driver
```

### Verify Driver Installation

| OS | Command / Check |
|----|-----------------|
| **Windows** | Device Manager → Ports → CP210x (COM3) |
| **Linux** | `ls /dev/ttyUSB*` → `/dev/ttyUSB0` |
| **macOS** | `ls /dev/tty.*` → `/dev/tty.SLAB_USBtoUART` |

---

## Arduino IDE Board Configuration

### Arduino IDE 2.x

1. **File** → **Preferences** (`Ctrl+,`)
2. **Additional Boards Manager URLs:**
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. **OK**
4. **Tools** → **Board** → **Boards Manager...** (`Ctrl+Shift+B`)
5. Search **"esp32"**
6. Install **"esp32 by Espressif Systems"** (latest version)
7. Wait for download (~200 MB)

---

## Selecting the Correct Board

### For Water Meter Project: **NodeMCU-32S**

| Interface | Selection |
|-----------|-----------|
| **Arduino IDE** | Tools → Board → ESP32 Arduino → **NodeMCU-32S** |

### Board Variants (Choose Correct One)

| Board | FQBN | Use Case |
|-------|------|----------|
| **NodeMCU-32S** | `esp32:esp32:nodemcu-32s` | **This project** — 38-pin, CP2102 |
| ESP32 Dev Module | `esp32:esp32:esp32dev` | Generic 30-pin dev board |
| ESP32-S3 DevKitC-1 | `esp32:esp32:esp32s3devkitc-1` | ESP32-S3 (different chip) |
| TTGO T-Display | `esp32:esp32:ttgo-tdisplay` | With built-in screen |
| M5Stack Core2 | `esp32:esp32:m5stack-core2` | M5Stack device |

> ⚠️ **Critical:** Selecting wrong board = wrong pin mapping, wrong flash size, upload failures.

> 📸 **Screenshot Placeholder:** *Arduino IDE Tools → Board menu with NodeMCU-32S highlighted*

---

## Selecting COM / ttyUSB Port

### Windows

1. **Tools** → **Port** → Select **COMx (Silicon Labs CP210x)**
2. Note the COM number (e.g., COM3, COM4)

### Linux / Raspberry Pi

```bash
# List available ports
ls /dev/ttyUSB* /dev/ttyACM*

# Typical output:
# /dev/ttyUSB0  (CP2102 on NodeMCU-32S)

# In Arduino IDE:
# Tools → Port → /dev/ttyUSB0
```

### macOS

```bash
ls /dev/tty.*
# /dev/tty.SLAB_USBtoUART  (CP2102)
# /dev/tty.wchusbserial     (CH340)
```

### Persistent Port Naming (Linux)

```bash
# Create udev rule for consistent naming
sudo tee /etc/udev/rules.d/99-esp32.rules <<'EOF'
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyESP32", MODE="0666"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger

# Now always available as:
ls -l /dev/ttyESP32
# /dev/ttyESP32 -> /dev/ttyUSB0
```

---

## Upload Process & Boot Modes

### Normal Upload (Automatic)

1. Connect ESP32 via USB
2. Select correct board and port
3. Click **Upload** (`Ctrl+U`)
4. Arduino IDE automatically:
   - Resets ESP32 into bootloader mode
   - Uploads firmware via esptool.py
   - Resets into application mode

### Manual Bootloader Mode (If Auto Fails)

**When to use:** Upload fails with "Failed to connect to ESP32" or "Timed out waiting for packet header"

#### Method: BOOT + EN Button Sequence

```
1. Hold BOOT button (GPIO 0 low)
2. Press and release EN (Reset) button
3. Release BOOT button
4. ESP32 is now in bootloader mode (waiting for upload)
5. Click Upload immediately
```

> 📸 **Screenshot Placeholder:** *Photo of ESP32 expansion board with BOOT and EN buttons labeled*

### Boot Mode Pin States

| Mode | GPIO 0 (BOOT) | GPIO 2 | EN (Reset) | Use Case |
|------|---------------|--------|------------|----------|
| **Normal Boot** | High (1) | Don't care | Running | Application runs |
| **Bootloader** | Low (0) | Don't care | Pulse low | Firmware upload |
| **Download Boot** | Low (0) | Low (0) | Pulse low | Factory test (avoid) |

---

## Boot Button & EN Button Usage

### Buttons on Expansion Board

| Button | GPIO | Function |
|--------|------|----------|
| **BOOT** | GPIO 0 | Hold during reset → bootloader mode |
| **EN** (Reset) | EN (CHIP_PU) | Hardware reset |

### Common Scenarios

| Scenario | Action |
|----------|--------|
| **Normal upload** | Just click Upload (auto-reset works) |
| **Upload fails** | Hold BOOT → Press EN → Release BOOT → Upload |
| **Stuck in bootloader** | Press EN (reset) alone |
| **Need clean boot** | Press EN alone |
| **Factory reset** | Hold BOOT + EN for 5s → Release both |

---

## Flash Button Usage

> **Note:** The "Flash" button is typically the **BOOT button** (GPIO 0). There is no separate "Flash" button on standard NodeMCU-32S.

### Terminology Clarification

| Term | Actual Button | Purpose |
|------|---------------|---------|
| **Boot Button** | BOOT (GPIO 0) | Enters bootloader for flashing |
| **Flash Button** | Same as BOOT | Colloquial term for "button to flash firmware" |
| **EN / Reset** | EN (RST) | Hardware reset |

### Flash Procedure Summary

```
To flash new firmware:
1. Connect ESP32 via USB
2. Select Board: NodeMCU-32S
3. Select Port: COMx / /dev/ttyUSB0
4. Click Upload (Ctrl+U)
5. If fails: Hold BOOT → Press EN → Release BOOT → Retry Upload
```

---

## Common Upload Errors & Fixes

### Error 1: "Failed to connect to ESP32: Timed out waiting for packet header"

| Cause | Fix |
|-------|-----|
| Not in bootloader mode | Hold BOOT → Press EN → Release BOOT → Upload |
| Wrong port selected | Verify port in Device Manager / `ls /dev/ttyUSB*` |
| Charge-only USB cable | Use **data cable** (test with phone file transfer) |
| Driver not installed | Install CP210x driver (see Driver Installation) |
| Port busy (Serial Monitor open) | Close Serial Monitor / Plotter before upload |

### Error 2: "A fatal error occurred: Could not open /dev/ttyUSB0: Permission denied"

```bash
# Linux fix:
sudo usermod -a -G dialout $USER
newgrp dialout
# Or logout/login
```

### Error 3: "esptool.py not found" / "python3: not found"

```bash
# Install esptool
pip3 install esptool

# Ensure python3 in PATH
which python3
```

### Error 4: "Property 'upload.speed' undefined" / Wrong baud rate

```bash
# In Arduino IDE: Tools → Upload Speed → 921600 (or 115200 for reliability)
# In CLI: --upload-speed 921600
```

### Error 5: "Flash size mismatch" / "Invalid head of packet"

| Cause | Fix |
|-------|-----|
| Wrong board selected | Select **NodeMCU-32S** (not ESP32 Dev Module) |
| Corrupt flash | Erase flash: `esptool.py --port /dev/ttyUSB0 erase_flash` |
| Partition scheme mismatch | Tools → Partition Scheme → Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS) |

### Error 6: "Brownout detector triggered" (Random resets)

| Cause | Fix |
|-------|-----|
| Insufficient power | Use 5V 2A+ supply; add 1000µF capacitor on 5V rail |
| Thin USB cable | Use thick, short, quality USB cable |
| Powered via laptop USB | Use powered hub or wall adapter |

### Error 7: "MD5 of file does not match data in flash!"

```bash
# Erase and re-flash
esptool.py --port /dev/ttyUSB0 erase_flash
# Then upload again
```

### Error 8: Upload succeeds but Serial Monitor shows garbage

| Cause | Fix |
|-------|-----|
| Wrong baud rate | Set Serial Monitor to **115200** (match `Serial.begin(115200)`) |
| Line ending | Set to "Both NL & CR" or "Newline" |
| Corrupt firmware | Erase flash and re-upload |

---

## Verification Checklist

After successful upload, verify:

### 1. Serial Output (115200 baud)

```
ets Jun  8 2016 00:22:57
rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)
configsip: 0, SPIWP:0xee
clk_drv:0x00,q_drv:0x00,d_drv:0x00,cs0_drv:0x00,hd_drv:0x00,wp_drv:0x00
mode:DIO, clock div:2
load:0x3fff0030,len:1184
load:0x40078000,len:13424
load:0x40080400,len:3600
entry 0x400805e0
Connecting to WiFi...
WiFi connected! IP: 192.168.1.100
Firebase initialized successfully
Starting stream on: /commands/wm_001
Sensor 0 (inlet): ISR attached on GPIO 26
Sensor 1 (fix1): ISR attached on GPIO 25
Sensor 2 (fix2): ISR attached on GPIO 33
Sensor 3 (fix3): ISR attached on GPIO 32
Reading: inlet=0.00 L/min fix1=0.00 L/min fix2=0.00 L/min fix3=0.00 L/min
Data uploaded to Firebase
```

### 2. Firebase Console

1. Open Firebase Console → Realtime Database
2. Check `/readings/wm_001/` — should see timestamped data every 5s

### 3. LED Indicators (Built-in LED on GPIO 2)

| Pattern | Meaning |
|---------|---------|
| Solid green | Normal operation |
| Blink green (1s) | WiFi connecting |
| Blink blue (fast) | Transmitting to Firebase |
| Solid yellow | Minor leak detected |
| Solid red | Major leak detected |
| Red flash | Upload failed |
| White blink (3x) | Upload success |
| Off | Deep sleep / no power |

### 4. Sensor Test

1. Blow into inlet sensor → Should show flow rate > 0
2. Tap each fixture sensor → Individual readings change
3. Check `inlet ≈ fix1 + fix2 + fix3` (within 10%)

---

## Quick Reference Card

| Task | Arduino IDE |
|------|-------------|
| Board | Tools → Board → ESP32 → **NodeMCU-32S** |
| Port | Tools → Port → COMx / ttyUSB0 |
| Upload Speed | Tools → Upload Speed → 921600 |
| Compile | `Ctrl+R` |
| Upload | `Ctrl+U` |
| Monitor | `Ctrl+Shift+M` |
| Bootloader | Hold BOOT → Press EN → Release BOOT |
| Erase Flash | N/A (use esptool) |

---

## Official References

- [ESP32 Arduino Core Installation](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)
- [Espressif Board Manager JSON](https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json)
- [ESP32 Technical Reference Manual](https://www.espressif.com/sites/default/files/documentation/esp32_technical_reference_manual_en.pdf)
- [NodeMCU-32S Pinout](https://github.com/nodemcu/nodemcu-devkit-v1.0)
- [CP210x Drivers](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
- [esptool.py Documentation](https://docs.espressif.com/projects/esptool/en/latest/esp32/)
- [Arduino Forum - ESP32](https://forum.arduino.cc/c/hardware/esp32/61)

---

## Next Steps

Proceed to:
1. [Firebase ESP Client Guide](./firebase-esp-client-guide.md) — Library setup and usage
2. [Project Setup Guide](./setup.md) — Full system deployment
3. [Calibration Guide](./calibration.md) — Sensor K-factor calibration

---

*Last updated: July 2026 | Tested with ESP32 NodeMCU-32S, Arduino IDE 2.3.2, Arduino CLI 1.0.4, ESP32 Core 2.0.14 | Compatible with Windows 10/11, Linux, macOS, Raspberry Pi OS*