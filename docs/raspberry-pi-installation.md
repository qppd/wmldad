# Raspberry Pi OS Installation Guide (Trixie 64-bit)

> **Target:** Raspberry Pi 3B+ / 4 / 5  
> **OS:** Raspberry Pi OS (64-bit) Trixie (Debian 13)  
> **Audience:** Students, researchers, developers — no prior Linux experience required

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Download Raspberry Pi Imager](#download-raspberry-pi-imager)
3. [Select OS: Raspberry Pi OS (64-bit) Trixie](#select-os-raspberry-pi-os-64-bit-trixie)
4. [Choose Storage Device](#choose-storage-device)
5. [Configure OS Settings (Critical Step)](#configure-os-settings-critical-step)
6. [Write Image to SD Card](#write-image-to-sd-card)
7. [First Boot](#first-boot)
8. [Post-Install System Update](#post-install-system-update)
9. [Verification Checklist](#verification-checklist)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Item | Specification | Notes |
|------|---------------|-------|
| **Raspberry Pi** | 3B+, 4 (2GB/4GB/8GB), or 5 | Pi 5 recommended for ML workloads |
| **microSD Card** | ≥ 32 GB, Class 10 / A1 / A2 | Samsung EVO Plus, SanDisk Extreme recommended |
| **SD Card Reader** | USB-A or USB-C | Built-in laptop slot works too |
| **Power Supply** | 5V 3A (Pi 4), 5V 5A (Pi 5) USB-C | Official Raspberry Pi PSU strongly recommended |
| **Network** | Ethernet or WiFi | Ethernet preferred for initial setup |
| **Computer** | Windows / macOS / Linux | For running Raspberry Pi Imager |

> ⚠️ **Warning:** Do NOT use phone chargers or low-quality power supplies. Undervoltage causes instability, SD card corruption, and throttling.

---

## Download Raspberry Pi Imager

1. Go to: **https://www.raspberrypi.com/software/**
2. Download the version for your host OS:
   - **Windows:** `Raspberry Pi Imager.exe` (~120 MB)
   - **macOS:** `Raspberry Pi Imager.dmg` (~140 MB)
   - **Linux:** `sudo apt install rpi-imager` or download AppImage
3. Install and launch the application.

> 📸 **Screenshot Placeholder:** *Raspberry Pi Imager main window showing "Choose Device", "Choose OS", "Choose Storage" buttons*

---

## Select OS: Raspberry Pi OS (64-bit) Trixie

1. Click **Choose OS**
2. Navigate: **Raspberry Pi OS (Other)** → **Raspberry Pi OS (64-bit)**
3. Select **Raspberry Pi OS (64-bit)** — this is the Trixie (Debian 13) release
4. **Do NOT select:** "Lite" (no desktop), "Full" (includes extra apps), or "Legacy" (Bullseye/Bookworm)

> **Why 64-bit Trixie?**
> - XGBoost and scikit-learn require 64-bit for optimal performance
> - Trixie (Debian 13) has Python 3.12+ and newer system libraries
> - 64-bit allows > 4 GB RAM utilization (critical for Pi 4/5 with 8 GB)

> 📸 **Screenshot Placeholder:** *OS selection menu showing "Raspberry Pi OS (64-bit)" highlighted*

---

## Choose Storage Device

1. Click **Choose Storage**
2. Select your microSD card (e.g., "32 GB Generic Mass Storage")
3. **Double-check** you selected the correct drive — this will **ERASE ALL DATA** on the card

> ⚠️ **Warning:** Verify the drive letter/size matches your SD card. Selecting your system drive will cause data loss.

> 📸 **Screenshot Placeholder:** *Storage selection dialog with correct SD card highlighted*

---

## Configure OS Settings (Critical Step)

**Before clicking "Write", click the gear icon (⚙️) or press `Ctrl+Shift+X` to open Advanced Options.**

### General Tab

| Setting | Value | Why |
|---------|-------|-----|
| **Set hostname** | `water-meter` (or your choice) | Access via `water-meter.local` (mDNS) |
| **Set username** | `pi` (or your preferred name) | Default user for SSH/login |
| **Set password** | Strong password (12+ chars) | **Required** — no default password in Trixie |
| **Configure wireless LAN** | Your WiFi SSID + password | Optional if using Ethernet |
| **Wireless LAN country** | `PH` (Philippines) or your country | Required for WiFi regulatory compliance |
| **Set locale** | `en_US.UTF-8` / `UTC` or your timezone | Prevents locale warnings |
| **Timezone** | `Asia/Manila` (or your timezone) | Correct timestamps for logs/ML |

### Services Tab

| Setting | Value | Why |
|---------|-------|-----|
| **Enable SSH** | ✅ **Checked** | **Required** for headless access |
| **Use password authentication** | ✅ Checked | Allows `ssh pi@water-meter.local` |
| **Public key authentication** | Optional | More secure; add your `~/.ssh/id_ed25519.pub` |

> ⚠️ **Important:** If you skip SSH enablement, you MUST connect a monitor/keyboard to enable it later via `sudo raspi-config`.

> 📸 **Screenshot Placeholder:** *Advanced Options dialog showing General and Services tabs with recommended settings*

---

## Write Image to SD Card

1. Click **Write**
2. Confirm the warning: "This will erase all data on the selected device"
3. Wait for **writing** (~2-5 minutes) then **verifying** (~1-2 minutes)
4. When "Write successful" appears, click **Continue**
5. Safely eject the SD card

> 📸 **Screenshot Placeholder:** *Progress bar showing "Writing..." then "Verifying..." then success message*

---

## First Boot

1. Insert microSD card into Raspberry Pi
2. Connect Ethernet cable (recommended) or rely on preconfigured WiFi
3. Connect power supply
4. **Wait 2-3 minutes** for first boot (filesystem expansion, SSH key generation)
5. The green ACT LED will blink irregularly during boot, then settle to steady/heartbeat

### Find Your Pi's IP Address

**Option A: mDNS (hostname.local) — Recommended**
```bash
# From your computer (Windows/macOS/Linux):
ssh pi@water-meter.local
```

**Option B: Router Admin Page**
1. Log into your router (typically 192.168.1.1 or 192.168.0.1)
2. Check DHCP client list for "water-meter" or "raspberrypi"
3. Note the IP address (e.g., 192.168.1.42)

**Option C: Network Scan**
```bash
# Linux/macOS:
nmap -sn 192.168.1.0/24 | grep -i raspberry

# Windows (PowerShell):
arp -a | findstr -i "raspberry"
```

---

## Post-Install System Update

**Run immediately after first login:**

```bash
# 1. Update package lists
sudo apt update

# 2. Full system upgrade (kernel, firmware, packages)
sudo apt full-upgrade -y

# 3. Clean up
sudo apt autoremove -y
sudo apt autoclean

# 4. Reboot to load new kernel/firmware
sudo reboot
```

> **Why `full-upgrade`?** It handles kernel updates and dependency changes that `upgrade` skips. Essential for Pi 5 firmware and WiFi/BT fixes.

> ⏱ **Time:** 5-15 minutes depending on network speed and Pi model.

---

## Verification Checklist

After reboot, SSH in and verify:

```bash
# Check OS version
cat /etc/os-release
# Should show: VERSION="13 (trixie)", VERSION_ID="13"

# Check kernel
uname -a
# Should show: aarch64 (64-bit)

# Check Python version
python3 --version
# Should be 3.12+

# Check available memory
free -h

# Check disk space
df -h /

# Verify SSH works from another terminal
ssh pi@water-meter.local "echo 'SSH OK'"

# Verify hostname
hostname
# Should output: water-meter

# Check WiFi (if configured)
iwconfig
ip addr show wlan0
```

> ✅ **All green?** Your Raspberry Pi is ready for the water meter project!

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **Rainbow square / colored screen** | Power supply insufficient | Use official 5V 3A/5A PSU; check cable quality |
| **Green LED flashes 4 times** | `start.elf` not found / corrupt SD | Re-flash SD card; try different card |
| **Green LED flashes 7 times** | Kernel image not found | Re-flash with Raspberry Pi OS (not NOOBS) |
| **No SSH access** | SSH not enabled in Imager | Re-flash with SSH enabled, or connect monitor/keyboard and run `sudo raspi-config` → Interface Options → SSH → Enable |
| **`ssh: Could not resolve hostname`** | mDNS not working (Windows) | Install **Bonjour Print Services** or use IP address instead |
| **WiFi not connecting** | Wrong country code / password | Re-flash with correct `PH` country code; verify SSID/password (case-sensitive) |
| **`locale: Cannot set LC_CTYPE` warnings** | Locale not generated | Run `sudo locale-gen en_US.UTF-8 && sudo update-locale LANG=en_US.UTF-8` |
| **SD card corruption on power loss** | No UPS / improper shutdown | Use UPS; enable overlay filesystem: `sudo raspi-config` → Performance → Overlay File System |

---

## Official References

- [Raspberry Pi OS Documentation](https://www.raspberrypi.com/documentation/computers/os.html)
- [Raspberry Pi Imager GitHub](https://github.com/raspberrypi/rpi-imager)
- [Raspberry Pi Forums - OS Installation](https://forums.raspberrypi.com/viewforum.php?f=117)
- [Debian Trixie Release Notes](https://www.debian.org/releases/trixie/)

---

## Next Steps

Proceed to:
1. [Raspberry Pi Networking Guide](./raspberry-pi-networking.md) — SSH, mDNS, static IP
2. [Remote Desktop Guide](./remote-desktop-guide.md) — RealVNC setup
3. [Python Environment Guide](./python-environment-guide.md) — venv, pip, ML libraries
4. [Project Setup Guide](./setup.md) — Full project deployment

---

*Last updated: July 2026 | Tested on Raspberry Pi OS Trixie (64-bit) | Compatible with Pi 3B+/4/5*