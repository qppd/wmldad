# Arduino IDE Installation on Raspberry Pi OS Trixie (64-bit)

> **Target:** Raspberry Pi OS Trixie (64-bit) on Pi 3B+/4/5  
> **Purpose:** GUI-based ESP32 firmware development and upload  
> **Audience:** Users who prefer graphical interface over CLI

---

## Table of Contents

1. [Installation Methods](#installation-methods)
2. [Method 1: Flatpak (Recommended)](#method-1-flatpak-recommended)
3. [Method 2: Official AppImage](#method-2-official-appimage)
4. [Method 3: Arduino IDE 1.x (Legacy)](#method-3-arduino-ide-1x-legacy)
5. [ESP32 Board Support Setup](#esp32-board-support-setup)
6. [Library Installation](#library-installation)
7. [Serial Port Permissions](#serial-port-permissions)
8. [Testing the Installation](#testing-the-installation)
9. [Troubleshooting](#troubleshooting)
10. [Quick Reference](#quick-reference)

---

## Installation Methods

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Flatpak** | Auto-updates, sandboxed, native integration | Slightly slower startup | Most users |
| **AppImage** | Single file, portable, latest version | Manual updates, no desktop integration by default | Portable use |
| **apt (1.x)** | System integrated | **Outdated** (1.8.x), no ESP32 support | Legacy only |

> **Recommendation:** Use **Flatpak** for Arduino IDE 2.x on Raspberry Pi OS Trixie.

---

## Method 1: Flatpak (Recommended)

### Install Flatpak (if not present)

```bash
# Raspberry Pi OS Trixie includes Flatpak by default
# Verify:
flatpak --version
# Flatpak 1.15.x

# If missing:
sudo apt update && sudo apt install -y flatpak
```

### Install Arduino IDE 2.x via Flatpak

```bash
# Add Flathub repository (if not added)
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install Arduino IDE
flatpak install flathub cc.arduino.IDE2

# Run
flatpak run cc.arduino.IDE2
```

### Create Desktop Shortcut (Auto-created)

Flatpak automatically creates `.desktop` entry in Applications → Programming → Arduino IDE 2

> 📸 **Screenshot Placeholder:** *Application menu showing "Arduino IDE 2" under Programming*

### Update Arduino IDE

```bash
# Update all Flatpaks
flatpak update

# Or just Arduino IDE
flatpak update cc.arduino.IDE2
```

---

## Method 2: Official AppImage

### Download and Install

```bash
# Create directory for AppImages
mkdir -p ~/Applications
cd ~/Applications

# Download latest Arduino IDE 2.x AppImage for ARM64
# Check: https://www.arduino.cc/en/software#ide2
wget https://downloads.arduino.cc/arduino-ide/arduino-ide_2.3.2_Linux_ARM64.AppImage

# Make executable
chmod +x arduino-ide_2.3.2_Linux_ARM64.AppImage

# Optional: Integrate with desktop
# Install appimaged for auto-integration
sudo apt install -y libfuse2
# Run once to register:
~/Applications/arduino-ide_2.3.2_Linux_ARM64.AppImage --appimage-extract-and-run
```

### Run

```bash
# Direct execution
~/Applications/arduino-ide_2.3.2_Linux_ARM64.AppImage

# Or create symlink in ~/.local/bin
mkdir -p ~/.local/bin
ln -sf ~/Applications/arduino-ide_2.3.2_Linux_ARM64.AppImage ~/.local/bin/arduino-ide
# Then run: arduino-ide
```

### Update

```bash
# Download new version, replace file
# No automatic updates - check https://www.arduino.cc/en/software
```

---

## Method 3: Arduino IDE 1.x (Legacy - Not Recommended)

> ⚠️ **Warning:** Arduino IDE 1.8.x is **end-of-life**. No ESP32 core updates, no modern features.

```bash
# Only if you specifically need 1.x
sudo apt update && sudo apt install -y arduino

# Version will be ~1.8.19 (very old)
arduino --version
```

---

## ESP32 Board Support Setup

### Step 1: Open Preferences

1. Launch Arduino IDE
2. **File** → **Preferences** (or `Ctrl+,`)
3. Find **"Additional Boards Manager URLs"**

> 📸 **Screenshot Placeholder:** *Arduino IDE Preferences dialog with Additional Boards Manager URLs field highlighted*

### Step 2: Add ESP32 Board Manager URL

```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```

- Paste the URL into the field
- Click **OK**

> 📸 **Screenshot Placeholder:** *Preferences dialog with ESP32 URL pasted in*

### Step 3: Install ESP32 Core

1. **Tools** → **Board** → **Boards Manager...** (or `Ctrl+Shift+B`)
2. Search: **esp32**
3. Click **Install** on **"esp32 by Espressif Systems"**
4. Wait for download (~200 MB toolchain)

> 📸 **Screenshot Placeholder:** *Boards Manager showing "esp32 by Espressif Systems" installing*

### Step 4: Select Your Board

1. **Tools** → **Board** → **ESP32 Arduino** → **NodeMCU-32S**
   - Or your specific board: **ESP32 Dev Module**, **ESP32-S3 DevKitC-1**, etc.

> 📸 **Screenshot Placeholder:** *Tools → Board menu showing ESP32 options with NodeMCU-32S selected*

---

## Library Installation

### Required Libraries for Water Meter Project

| Library | Install Method | Version |
|---------|----------------|---------|
| **Firebase ESP Client** | Library Manager | ≥ 4.4.x |
| **ArduinoJson** | Library Manager | ≥ 7.x |

### Via Library Manager (GUI)

1. **Tools** → **Manage Libraries...** (or `Ctrl+Shift+I`)
2. Search each library name
3. Click **Install** on correct result

> 📸 **Screenshot Placeholder:** *Library Manager showing "Firebase ESP Client" by mobizt installing*

### Via CLI (Alternative)

```bash
# If using Arduino CLI alongside IDE
arduino-cli lib install "Firebase ESP Client"
arduino-cli lib install "ArduinoJson"
```

---

## Serial Port Permissions

### Add User to dialout Group

```bash
# Required for USB serial access
sudo usermod -a -G dialout $USER

# Apply immediately (or log out/in)
newgrp dialout

# Verify
groups $USER
# Should include: dialout
```

### udev Rules for ESP32 (Optional but Recommended)

```bash
# Create udev rule for consistent device naming
sudo tee /etc/udev/rules.d/99-esp32.rules > /dev/null <<'EOF'
# CP2102/CP2104 (NodeMCU-32S)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout", SYMLINK+="ttyESP32"
# CH340/CH341
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="dialout", SYMLINK+="ttyESP32"
# ESP32-S3 native USB
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", MODE="0666", GROUP="dialout", SYMLINK+="ttyESP32"
EOF

# Reload rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

> Now your ESP32 will appear as `/dev/ttyESP32` consistently.

---

## Testing the Installation

### 1. Blink Test Sketch

```cpp
// File → Examples → 01.Basics → Blink
// Or create new sketch:

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
  while (!Serial) delay(10);  // Wait for serial monitor
  Serial.println("ESP32 Blink Test");
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("ON");
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("OFF");
  delay(500);
}
```

### 2. Connect ESP32

- Plug ESP32 via USB (data cable, not charge-only!)
- Check port: **Tools** → **Port** → Select `/dev/ttyUSB0` or `/dev/ttyESP32`

> 📸 **Screenshot Placeholder:** *Tools → Port menu showing /dev/ttyUSB0 selected*

### 3. Upload

1. Click **Upload** (right arrow icon) or `Ctrl+U`
2. Watch output window for progress

> 📸 **Screenshot Placeholder:** *Upload progress bar and "Done uploading" message*

### 4. Open Serial Monitor

1. Click **Serial Monitor** (magnifying glass icon) or `Ctrl+Shift+M`
2. Set baud rate: **115200**
3. Should see "ON"/"OFF" every 500ms

> 📸 **Screenshot Placeholder:** *Serial Monitor showing "ON"/"OFF" output at 115200 baud*

---

## Troubleshooting

### Issue: "Board not found" / "No device found on /dev/ttyUSB0"

| Check | Fix |
|-------|-----|
| USB cable | Use **data cable** (not charge-only) |
| Driver | CP210x: `sudo apt install -y linux-modules-extra-$(uname -r)` |
| Port permissions | `sudo usermod -a -G dialout $USER && newgrp dialout` |
| Board in bootloader | Hold **BOOT**, press **EN**, release **BOOT**, upload |
| Wrong port | Check `ls /dev/tty*` and `dmesg -w` on connect |

### Issue: "Error compiling for board NodeMCU-32S"

```bash
# Reinstall ESP32 core
# In Arduino IDE: Boards Manager → esp32 → Remove → Install

# Or via CLI:
arduino-cli core uninstall esp32:esp32
arduino-cli core update-index
arduino-cli core install esp32:esp32
```

### Issue: Slow IDE startup / High memory usage

```bash
# Increase swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Issue: Flatpak Arduino IDE can't access serial ports

```bash
# Grant serial port access to Flatpak
flatpak permission-set device serial cc.arduino.IDE2 yes

# Or use CLI:
flatpak override --device=all cc.arduino.IDE2
# (Less secure but works)
```

### Issue: Library not found after install

- Restart Arduino IDE after library install
- Check **Sketch** → **Include Library** → Library appears in list
- Verify library path: **File** → **Preferences** → **Sketchbook location**

### Issue: "esptool.py not found" during upload

```bash
# Install globally
pip3 install esptool

# Or ensure Arduino IDE can find it (restart IDE after core install)
```

---

## Quick Reference

| Task | Menu / Shortcut |
|------|-----------------|
| Open Preferences | File → Preferences (`Ctrl+,`) |
| Boards Manager | Tools → Board → Boards Manager (`Ctrl+Shift+B`) |
| Library Manager | Tools → Manage Libraries (`Ctrl+Shift+I`) |
| Select Board | Tools → Board → ESP32 Arduino → NodeMCU-32S |
| Select Port | Tools → Port → /dev/ttyUSB0 |
| Verify/Compile | Sketch → Verify/Compile (`Ctrl+R`) |
| Upload | Sketch → Upload (`Ctrl+U`) |
| Serial Monitor | Tools → Serial Monitor (`Ctrl+Shift+M`) |
| Serial Plotter | Tools → Serial Plotter (`Ctrl+Shift+L`) |
| Board Manager URL | Preferences → Additional Boards Manager URLs |

---

## Official References

- [Arduino IDE Download](https://www.arduino.cc/en/software)
- [Arduino IDE 2.x Documentation](https://docs.arduino.cc/arduino-ide/)
- [ESP32 Arduino Core Installation](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)
- [Flatpak Arduino IDE](https://flathub.org/apps/cc.arduino.IDE2)
- [Raspberry Pi Arduino Forum](https://forums.raspberrypi.com/viewforum.php?f=107)

---

## Next Steps

Proceed to:
1. [ESP32 Setup Guide](./esp32-setup-guide.md) — Detailed board config, drivers, upload
2. [Firebase ESP Client Guide](./firebase-esp-client-guide.md) — Library usage
3. [Project Setup Guide](./setup.md) — Full deployment

---

*Last updated: July 2026 | Tested on Raspberry Pi OS Trixie (64-bit) with Arduino IDE 2.3.2 (Flatpak) | Compatible with Pi 3B+/4/5*