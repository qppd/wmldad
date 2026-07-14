# Arduino CLI Installation on Raspberry Pi OS Trixie (64-bit)

> **Target:** Raspberry Pi OS Trixie (64-bit) on Pi 3B+/4/5  
> **Purpose:** Headless ESP32 firmware compilation and upload via command line  
> **Audience:** Developers who prefer CLI over Arduino IDE GUI

---

## Table of Contents

1. [Why Arduino CLI?](#why-arduino-cli)
2. [Prerequisites](#prerequisites)
3. [Installation Methods](#installation-methods)
4. [Post-Install Configuration](#post-install-configuration)
5. [ESP32 Board Support](#esp32-board-support)
6. [Compiling and Uploading](#compiling-and-uploading)
7. [PATH Configuration](#path-configuration)
8. [Testing Installation](#testing-installation)
9. [Troubleshooting](#troubleshooting)
10. [Quick Reference](#quick-reference)

---

## Why Arduino CLI?

| Feature | Arduino CLI | Arduino IDE 2.x |
|---------|-------------|-----------------|
| **Headless/SSH** | ✅ Native | ❌ Requires GUI/X11 |
| **Automation/CI** | ✅ Scriptable | ❌ Manual only |
| **Resource usage** | Low (~10 MB) | High (~500 MB) |
| **ARM64 native** | ✅ Official binary | ⚠️ Via Flatpak/AppImage |
| **Scripting** | ✅ Full control | Limited |

> **Best for:** Raspberry Pi headless servers, CI/CD pipelines, automated builds

---

## Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Required for Arduino CLI and ESP32 compilation
sudo apt install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libusb-1.0-0 \
    libudev-dev \
    udev
```

> **Note:** `libusb-1.0-0` and `libudev-dev` are required for ESP32 USB upload (esptool.py).

---

## Installation Methods

### Method 1: Official Install Script (Recommended)

```bash
# Download and run official installer
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# This installs to ~/.local/bin/arduino-cli
# Add to PATH (see PATH Configuration section)
```

### Method 2: Download Binary Directly

```bash
# Go to releases: https://github.com/arduino/arduino-cli/releases/latest
# For Raspberry Pi OS Trixie (ARM64):
cd /tmp
wget https://github.com/arduino/arduino-cli/releases/download/v1.0.4/arduino-cli_1.0.4_Linux_ARM64.tar.gz
tar -xzf arduino-cli_1.0.4_Linux_ARM64.tar.gz
sudo mv arduino-cli /usr/local/bin/
arduino-cli version
# arduino-cli  Version: 1.0.4 Commit: ...
```

### Method 3: Via Go (If Go Installed)

```bash
# Only if you have Go 1.21+ installed
go install github.com/arduino/arduino-cli@latest
# Binary in ~/go/bin/arduino-cli
```

### Method 4: Package Manager (May Be Outdated)

```bash
# Check version first
apt show arduino-cli

# If recent enough (≥ 1.0):
sudo apt install -y arduino-cli
```

---

## Post-Install Configuration

### Initialize Configuration

```bash
# Create default config file
arduino-cli config init

# Creates: ~/.arduino15/arduino-cli.yaml
# View config:
cat ~/.arduino15/arduino-cli.yaml
```

### Update Board Index

```bash
# Update to latest board definitions
arduino-cli core update-index

# Add ESP32 board manager URL (CRITICAL for ESP32)
arduino-cli config add board_manager.additional_urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

# Verify URL added
arduino-cli config dump | grep additional_urls
```

> 📸 **Screenshot Placeholder:** *Terminal showing `arduino-cli config dump` output with ESP32 URL*

---

## ESP32 Board Support

### Install ESP32 Core

```bash
# Search for ESP32 core
arduino-cli core search esp32

# Install latest ESP32 core (from Espressif)
arduino-cli core install esp32:esp32

# Or install specific version
arduino-cli core install esp32:esp32@2.0.14

# Verify installation
arduino-cli core list
# Should show: esp32:esp32  2.0.14  installed
```

> ⏱ **Time:** 2-5 minutes on Pi 4/5 (downloads ~200 MB toolchain)

### Verify Board Definitions

```bash
# List all ESP32 boards available
arduino-cli board listall esp32:esp32 | grep -E "(nodemcu|esp32dev|esp32s3)"

# Common boards for this project:
# esp32:esp32:nodemcu-32s     = NodeMCU-32S (used in this project)
# esp32:esp32:esp32dev        = Generic ESP32 Dev Module
# esp32:esp32:esp32s3devkitc  = ESP32-S3 DevKitC
```

---

## Compiling and Uploading

### Project Structure

```
water-meter-firmware/
├── water-meter.ino          # Main sketch
├── config.h                 # Configuration (gitignored)
├── config.example.h         # Template
├── sensor_manager.h
├── flow_sensor.h
├── firebase_client.h
├── local_rules.h
├── wifi_manager.h
├── data_logger.h
├── ntp_sync.h
├── ota_updater.h
└── led_indicator.h
```

### Compile (Verify)

```bash
cd ~/wmldad/src   # Or wherever your .ino file is

# Compile for NodeMCU-32S
arduino-cli compile --fqbn esp32:esp32:nodemcu-32s .

# With verbose output
arduino-cli compile --fqbn esp32:esp32:nodemcu-32s -v .

# Specify build path (optional)
arduino-cli compile --fqbn esp32:esp32:nodemcu-32s --build-path ./build .
```

> 📸 **Screenshot Placeholder:** *Terminal showing successful compilation output with memory usage*

### Upload to ESP32

```bash
# Find serial port
arduino-cli board list
# Or:
ls /dev/ttyUSB* /dev/ttyACM*
# Typical: /dev/ttyUSB0 (CP2102) or /dev/ttyACM0 (native USB)

# Upload (adjust port and FQBN)
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:nodemcu-32s .

# With verbose output
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:nodemcu-32s -v .
```

### Compile + Upload in One Command

```bash
arduino-cli compile --fqbn esp32:esp32:nodemcu-32s --upload -p /dev/ttyUSB0 .
```

---

## PATH Configuration

### Temporary (Current Session)

```bash
export PATH=$PATH:~/.local/bin
# Or if installed to /usr/local/bin (already in PATH)
```

### Permanent (Add to ~/.bashrc)

```bash
# For install script method (~/.local/bin)
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc

# For binary method (/usr/local/bin) - already in PATH by default
# No action needed

# Reload
source ~/.bashrc

# Verify
which arduino-cli
arduino-cli version
```

### For Systemd Services / Cron Jobs

```bash
# Use full path in scripts
/usr/local/bin/arduino-cli compile --fqbn esp32:esp32:nodemcu-32s /home/pi/wmldad/src
```

---

## Testing Installation

### Complete Test Workflow

```bash
# 1. Check version
arduino-cli version

# 2. List connected boards
arduino-cli board list

# 3. Create test sketch
mkdir -p ~/test_blink && cd ~/test_blink
cat > blink.ino <<'EOF'
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
}
void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);
  Serial.println("Blink");
}
EOF

# 4. Compile
arduino-cli compile --fqbn esp32:esp32:nodemcu-32s .

# 5. Upload (connect ESP32 via USB first)
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:nodemcu-32s .

# 6. Monitor serial
arduino-cli monitor -p /dev/ttyUSB0 -c baudrate=115200
# Press Ctrl+C to exit monitor
```

> 📸 **Screenshot Placeholder:** *Serial monitor output showing "Blink" every second*

---

## Troubleshooting

### Issue: `arduino-cli: command not found`

```bash
# Check install location
ls ~/.local/bin/arduino-cli
ls /usr/local/bin/arduino-cli

# Add to PATH (see PATH Configuration section)
export PATH=$PATH:~/.local/bin
```

### Issue: `Error: could not find board definition`

```bash
# Update index and reinstall core
arduino-cli core update-index
arduino-cli core install esp32:esp32

# Verify
arduino-cli core list
```

### Issue: `Permission denied` on serial port

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and back in, or:
newgrp dialout

# Verify
groups $USER
# Should show: dialout
```

### Issue: `esptool.py not found` / Upload fails

```bash
# Install esptool via pip (Arduino CLI uses it)
pip3 install esptool

# Or use Arduino CLI's bundled tool (should work automatically)
arduino-cli core install esp32:esp32  # Reinstalls toolchain
```

### Issue: Compilation fails with `xtensa-esp32-elf-gcc: not found`

```bash
# ESP32 toolchain not installed properly
arduino-cli core uninstall esp32:esp32
arduino-cli core update-index
arduino-cli core install esp32:esp32
```

### Issue: Slow compilation on Pi

```bash
# Use ccache to speed up rebuilds
sudo apt install -y ccache
export PATH="/usr/lib/ccache:$PATH"

# Or increase swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue: "Board not found" for custom board

```bash
# List ALL boards
arduino-cli board listall

# Search for your board
arduino-cli board listall | grep -i nodemcu
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Check version | `arduino-cli version` |
| Update board index | `arduino-cli core update-index` |
| Install ESP32 core | `arduino-cli core install esp32:esp32` |
| List installed cores | `arduino-cli core list` |
| List all boards | `arduino-cli board listall` |
| List connected boards | `arduino-cli board list` |
| Compile sketch | `arduino-cli compile --fqbn esp32:esp32:nodemcu-32s .` |
| Upload sketch | `arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:nodemcu-32s .` |
| Compile + Upload | `arduino-cli compile --fqbn esp32:esp32:nodemcu-32s --upload -p /dev/ttyUSB0 .` |
| Serial monitor | `arduino-cli monitor -p /dev/ttyUSB0 -c baudrate=115200` |
| Create new sketch | `arduino-cli sketch new MySketch` |
| Install library | `arduino-cli lib install "ArduinoJson"` |
| List libraries | `arduino-cli lib list` |
| Search library | `arduino-cli lib search "Firebase"` |
| Config file location | `~/.arduino15/arduino-cli.yaml` |
| Data directory | `~/.arduino15/` |

---

## ESP32 Board FQBN Reference

| Board | FQBN (Fully Qualified Board Name) |
|-------|-----------------------------------|
| **NodeMCU-32S** (this project) | `esp32:esp32:nodemcu-32s` |
| Generic ESP32 Dev Module | `esp32:esp32:esp32dev` |
| ESP32-S3 DevKitC-1 | `esp32:esp32:esp32s3devkitc-1` |
| ESP32-C3 DevKitM-1 | `esp32:esp32:esp32c3devkitm-1` |
| TTGO T-Display | `esp32:esp32:ttgo-tdisplay` |
| M5Stack Core2 | `esp32:esp32:m5stack-core2` |

### Common FQBN Options for NodeMCU-32S

```bash
# Full FQBN with options
esp32:esp32:nodemcu-32s:PartitionScheme=default,CPUFreq=240,FlashMode=qio,FlashFreq=80,FlashSize=4M,UploadSpeed=921600,DebugLevel=none

# Minimal (uses defaults)
esp32:esp32:nodemcu-32s
```

---

## Official References

- [Arduino CLI GitHub](https://github.com/arduino/arduino-cli)
- [Arduino CLI Documentation](https://arduino.github.io/arduino-cli/)
- [ESP32 Arduino Core](https://github.com/espressif/arduino-esp32)
- [ESP32 Board Manager URL](https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json)
- [Arduino CLI Releases](https://github.com/arduino/arduino-cli/releases)
- [Raspberry Pi Forums - Arduino](https://forums.raspberrypi.com/viewforum.php?f=107)

---

## Next Steps

Proceed to:
1. [Arduino IDE Installation Guide](./arduino-ide-installation.md) — If you prefer GUI
2. [ESP32 Setup Guide](./esp32-setup-guide.md) — Drivers, board selection, upload
3. [Project Setup Guide](./setup.md) — Full deployment

---

*Last updated: July 2026 | Tested on Raspberry Pi OS Trixie (64-bit) with Arduino CLI 1.0.4 | Compatible with Pi 3B+/4/5*