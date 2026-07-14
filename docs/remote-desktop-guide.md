# Raspberry Pi Remote Desktop Guide (RealVNC)

> **Target:** Raspberry Pi OS Trixie (64-bit)  
> **Method:** RealVNC (pre-installed on Raspberry Pi OS with desktop)  
> **Audience:** Beginners — step-by-step with screenshots placeholders

---

## Table of Contents

1. [Why RealVNC?](#why-realvnc)
2. [Enable VNC on Raspberry Pi](#enable-vnc-on-raspberry-pi)
3. [Install VNC Viewer on Your Computer](#install-vnc-viewer-on-your-computer)
4. [Connect via IP Address](#connect-via-ip-address)
5. [Connect via hostname.local (mDNS)](#connect-via-hostnamelocal-mdns)
6. [Configure VNC Settings](#configure-vnc-settings)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)
9. [Alternative: WayVNC (Wayland)](#alternative-wayvnc-wayland)

---

## Why RealVNC?

| Feature | RealVNC | Alternatives |
|---------|---------|--------------|
| **Pre-installed** | ✅ On Raspberry Pi OS Desktop | ❌ Requires install |
| **Headless support** | ✅ Virtual desktop mode | ⚠️ Limited |
| **Encryption** | ✅ Built-in (RealVNC protocol) | ⚠️ Varies |
| **Cross-platform viewer** | ✅ Win/macOS/Linux/iOS/Android | ✅ Most |
| **Cloud connectivity** | ✅ Optional (RealVNC Cloud) | ❌ Rare |
| **Performance** | Good (H.264 encoding on Pi 4/5) | Varies |

> **Note:** RealVNC Server is **free for personal/educational use** on Raspberry Pi. No license key needed.

---

## Enable VNC on Raspberry Pi

### Method 1: Via raspi-config (Terminal/SSH)

```bash
# 1. Open configuration tool
sudo raspi-config

# 2. Navigate:
#    3 Interface Options → I3 VNC → Yes → Ok → Finish

# 3. Reboot (optional but recommended)
sudo reboot
```

> 📸 **Screenshot Placeholder:** *raspi-config menu showing "Interface Options" → "VNC" selected*

### Method 2: Via Desktop GUI (if monitor attached)

1. Click **Menu** (Raspberry icon) → **Preferences** → **Raspberry Pi Configuration**
2. Click **Interfaces** tab
3. Set **VNC** to **Enabled**
4. Click **OK** → Reboot if prompted

> 📸 **Screenshot Placeholder:** *Raspberry Pi Configuration window with Interfaces tab, VNC enabled*

### Method 3: Headless (no monitor) — Via SSH

```bash
# Enable VNC service
sudo systemctl enable vncserver-x11-serviced.service
sudo systemctl start vncserver-x11-serviced.service

# For virtual desktop (headless, no monitor connected):
sudo systemctl enable vncserver-virtuald.service
sudo systemctl start vncserver-virtuald.service

# Verify status
systemctl status vncserver-x11-serviced.service
systemctl status vncserver-virtuald.service
```

> **Important:** 
> - `vncserver-x11-serviced` = mirrors the physical display (requires monitor or HDMI dummy plug)
> - `vncserver-virtuald` = creates virtual desktop (headless, no monitor needed)

---

## Install VNC Viewer on Your Computer

### Windows
1. Go to: **https://www.realvnc.com/en/connect/download/viewer/**
2. Download **VNC Viewer for Windows** (64-bit MSI or EXE)
3. Run installer → Accept defaults → Finish

### macOS
1. Go to: **https://www.realvnc.com/en/connect/download/viewer/**
2. Download **VNC Viewer for macOS** (DMG)
3. Open DMG → Drag VNC Viewer to Applications

### Linux
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y realvnc-vnc-viewer

# Arch/Manjaro
yay -S realvnc-vnc-viewer

# Fedora
sudo dnf install realvnc-vnc-viewer

# Or download generic tarball from RealVNC website
```

### Mobile (iOS/Android)
- **iOS:** App Store → Search "VNC Viewer" → RealVNC (free)
- **Android:** Play Store → Search "VNC Viewer" → RealVNC (free)

> 📸 **Screenshot Placeholder:** *RealVNC download page with platform options highlighted*

---

## Connect via IP Address

### Step 1: Find Pi's IP

```bash
# On Pi (via SSH)
hostname -I
# Example output: 192.168.1.42
```

### Step 2: Open VNC Viewer

1. Launch **VNC Viewer** on your computer
2. In the address bar, type: `192.168.1.42`
3. Press **Enter**

> 📸 **Screenshot Placeholder:** *VNC Viewer main window with IP address entered*

### Step 3: Authenticate

| Prompt | Enter |
|--------|-------|
| **Username** | `pi` (or your custom username) |
| **Password** | Your Raspberry Pi login password |

> **Tip:** Check "Remember password" for convenience (stored in OS keychain).

### Step 4: Accept Encryption Warning (First Time Only)

> 📸 **Screenshot Placeholder:** *VNC encryption warning dialog - click "Continue"*

> RealVNC uses encryption by default. The first connection shows a fingerprint verification — click **Continue**.

---

## Connect via hostname.local (mDNS)

If you set a hostname in Raspberry Pi Imager (e.g., `water-meter`):

```bash
# In VNC Viewer address bar, type:
water-meter.local
```

Or with display number (if multiple):
```
water-meter.local:1
```

> **Why use hostname?**
> - Works even if IP changes (DHCP)
> - Easier to remember
> - Works across reboots without checking router

> 📸 **Screenshot Placeholder:** *VNC Viewer connecting to "water-meter.local"*

---

## Configure VNC Settings

### Access VNC Server Options

**On Pi (via SSH):**
```bash
# For physical display
sudo vncserver-x11-serviced --config

# For virtual display
vncserver-virtual --config
```

**Or via GUI:** Right-click VNC icon in Pi's top panel → **Options**

> 📸 **Screenshot Placeholder:** *VNC Server Options dialog showing Security, Connections, Display tabs*

### Recommended Settings

#### Security Tab
| Setting | Value | Reason |
|---------|-------|--------|
| **Encryption** | Prefer On / Require | Force encryption |
| **Authentication** | System Authentication | Uses Pi user accounts |
| **Permissions** | Add your user → Full Access | Control who can connect |

#### Connections Tab
| Setting | Value | Reason |
|---------|-------|--------|
| **Port** | 5900 (default) | Standard VNC port |
| **Idle Timeout** | 0 (disabled) | Prevents auto-disconnect |
| **Allow Cloud Connections** | Off (unless using RealVNC Cloud) | Security |

#### Display Tab (Virtual Desktop Only)
| Setting | Value | Reason |
|---------|-------|--------|
| **Geometry** | 1920x1080 or 1366x768 | Match your screen |
| **Depth** | 24-bit | Color quality |
| **DPI** | 96 | Standard |

---

## Headless Setup (No Monitor Attached)

### Option A: Virtual Desktop (Recommended)

```bash
# 1. Enable virtual VNC service
sudo systemctl enable vncserver-virtuald.service
sudo systemctl start vncserver-virtuald.service

# 2. Create a virtual desktop for your user
vncserver-virtual -geometry 1920x1080 -depth 24 :1

# 3. Connect to: water-meter.local:1  (or IP:1)
```

> **Note:** Display `:1` means port 5901. `:0` is physical display (5900).

### Option B: HDMI Dummy Plug (Physical Display Emulation)

1. Buy **HDMI Dummy Plug / Headless Ghost** (₱150-300 on Shopee)
2. Plug into Pi's HDMI port
3. Pi thinks monitor is connected → uses `vncserver-x11-serviced` on `:0`
4. Connect to `water-meter.local` (port 5900)

> 📸 **Screenshot Placeholder:** *HDMI dummy plug photo with caption "₱150 on Shopee - enables headless physical display"*

### Option C: Force HDMI in config.txt

```bash
# Edit boot config
sudo nano /boot/firmware/config.txt

# Add/Uncomment:
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=82  # 1920x1080 @ 60Hz

# Reboot
sudo reboot
```

> Works without dummy plug on Pi 4/5. Pi 3 may need dummy plug.

---

## Troubleshooting

### Issue: "Cannot connect to VNC Server" / Connection Refused

| Check | Command / Action |
|-------|------------------|
| VNC service running? | `systemctl status vncserver-x11-serviced` |
| Port 5900 listening? | `ss -tlnp | grep 5900` |
| Firewall blocking? | `sudo ufw allow 5900/tcp` |
| Correct IP/hostname? | `hostname -I` and `hostname` |
| Virtual vs Physical? | Try `:1` (5901) for virtual |

### Issue: Black Screen / Gray Screen / Only Wallpaper

| Cause | Fix |
|-------|-----|
| No monitor + physical VNC | Use virtual desktop (`vncserver-virtuald`) or HDMI dummy plug |
| Wayland session (Pi 5/Bookworm+) | RealVNC requires X11. Force X11: `sudo raspi-config` → Advanced → Wayland → Disable |
| Display power management | `xset -dpms; xset s off` in autostart |

### Issue: Slow / Laggy Performance

| Optimization | Command |
|--------------|---------|
| Enable H.264 encoding (Pi 4/5) | VNC Options → Display → "Use H.264 encoding" ✅ |
| Reduce resolution | Connect to `water-meter.local:1` with `-geometry 1366x768` |
| Lower color depth | `-depth 16` (less bandwidth) |
| Wired Ethernet | Use Ethernet instead of WiFi |

### Issue: "Authentication Rejected"

```bash
# Check if user exists
id pi

# Reset password (if forgotten)
sudo passwd pi

# Check VNC authentication method
# In VNC Options → Security → Authentication: "System Authentication"
```

### Issue: Keyboard/Mouse Not Working

```bash
# Install/input issues
sudo apt install -y xserver-xorg-input-all

# For virtual desktop, ensure input devices exist
ls /dev/input/
```

---

## Security Considerations

### 1. Change Default Password (Mandatory)

```bash
passwd pi
# Enter strong password (12+ chars, mixed case, numbers, symbols)
```

### 2. Use SSH Tunnel for VNC (Recommended for Remote Access)

**Instead of port forwarding 5900, tunnel over SSH:**

```bash
# On YOUR computer:
ssh -L 5901:localhost:5900 pi@water-meter.local

# Then connect VNC Viewer to:
localhost:5901
```

> **Benefits:** Encrypted, no open VNC port on router, uses SSH keys.

### 3. Enable SSH Key Authentication (Disable Password)

```bash
# On your computer:
ssh-copy-id pi@water-meter.local

# On Pi: Edit SSH config
sudo nano /etc/ssh/sshd_config
# Set:
PasswordAuthentication no
PubkeyAuthentication yes

# Restart
sudo systemctl restart ssh
```

### 4. Firewall Rules

```bash
# Allow VNC only from local network
sudo ufw allow from 192.168.1.0/24 to any port 5900 proto tcp

# Or allow only via SSH tunnel (deny direct VNC)
sudo ufw deny 5900/tcp
```

### 5. Fail2Ban for VNC

```bash
sudo apt install -y fail2ban

sudo tee /etc/fail2ban/jail.d/vnc.conf > /dev/null <<'EOF'
[vnc]
enabled = true
port = 5900
filter = vnc
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

sudo systemctl restart fail2ban
```

---

## Alternative: WayVNC (For Wayland on Pi 5 / Bookworm+)

> **Note:** Raspberry Pi OS Trixie uses **Wayland** by default on Pi 4/5. RealVNC's `vncserver-x11-serviced` requires X11.

### If RealVNC Doesn't Work on Wayland:

```bash
# Option 1: Force X11 (easiest)
sudo raspi-config
# Advanced Options → Wayland → Disable → Reboot

# Option 2: Use WayVNC (native Wayland VNC)
sudo apt install -y wayvnc

# Configure
mkdir -p ~/.config/wayvnc
cat > ~/.config/wayvnc/config <<'EOF'
address=0.0.0.0
port=5900
enable_auth=true
username=pi
password=your_secure_password
EOF

# Run
wayvnc
```

> 📸 **Screenshot Placeholder:** *WayVNC running in terminal showing "Listening on 0.0.0.0:5900"*

---

## Quick Reference

| Task | Command |
|------|---------|
| Enable VNC (physical) | `sudo systemctl enable --now vncserver-x11-serviced` |
| Enable VNC (virtual) | `sudo systemctl enable --now vncserver-virtuald` |
| Create virtual desktop | `vncserver-virtual -geometry 1920x1080 :1` |
| List VNC displays | `vncserver-virtual -list` |
| Kill virtual desktop | `vncserver-virtual -kill :1` |
| Check VNC port | `ss -tlnp | grep 590` |
| VNC logs (physical) | `journalctl -u vncserver-x11-serviced -f` |
| VNC logs (virtual) | `journalctl -u vncserver-virtuald -f` |

---

## Official References

- [RealVNC Raspberry Pi Documentation](https://www.realvnc.com/en/connect/docs/raspberry-pi.html)
- [Raspberry Pi VNC Documentation](https://www.raspberrypi.com/documentation/computers/remote-access.html#vnc)
- [RealVNC Viewer Downloads](https://www.realvnc.com/en/connect/download/viewer/)
- [Raspberry Pi Forums - VNC](https://forums.raspberrypi.com/viewforum.php?f=66)
- [wayvnc GitHub](https://github.com/any1/wayvnc)

---

## Next Steps

Proceed to:
1. [Python Environment Guide](./python-environment-guide.md) — venv, pip, ML libraries
2. [Project Setup Guide](./setup.md) — Full project deployment

---

*Last updated: July 2026 | Tested on Raspberry Pi OS Trixie (64-bit) with RealVNC Server 7.x | Compatible with Pi 3B+/4/5*