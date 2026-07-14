# Raspberry Pi Networking Guide

> **Target:** Raspberry Pi OS Trixie (64-bit)  
> **Audience:** Beginners to intermediate — no networking expertise assumed

---

## Table of Contents

1. [Find Your Pi's IP Address](#find-your-pis-ip-address)
2. [Find Your Pi's Hostname](#find-your-pis-hostname)
3. [SSH Connection Methods](#ssh-connection-methods)
4. [Understanding mDNS (hostname.local)](#understanding-mdns-hostnamelocal)
5. [Static IP / DHCP Reservation](#static-ip--dhcp-reservation)
6. [Common SSH Issues & Fixes](#common-ssh-issues--fixes)
7. [Network Diagnostics](#network-diagnostics)

---

## Find Your Pi's IP Address

### Method 1: From the Pi Itself (with monitor/keyboard)

```bash
# Show all interfaces and IPs
hostname -I
# Output example: 192.168.1.42 10.0.0.5

# Show specific interface
ip addr show eth0   # Ethernet
ip addr show wlan0  # WiFi
```

### Method 2: From Another Computer on Same Network

**Linux/macOS:**
```bash
# Ping the hostname (if mDNS works)
ping water-meter.local

# Network scan (requires nmap)
nmap -sn 192.168.1.0/24 | grep -i raspberry

# Or using arp
arp -a | grep -i "raspberry\|water-meter"
```

**Windows (PowerShell):**
```powershell
# Ping hostname
ping water-meter.local

# ARP table
arp -a | findstr /i "raspberry"

# Network scan (if nmap installed)
nmap -sn 192.168.1.0/24
```

### Method 3: Router Admin Interface

1. Open browser → `http://192.168.1.1` (or `192.168.0.1`, `10.0.0.1`)
2. Login (admin/admin, check router label)
3. Navigate to **Attached Devices** / **DHCP Client List** / **Device List**
4. Look for `water-meter` or `raspberrypi`

---

## Find Your Pi's Hostname

```bash
# Current hostname
hostname

# Full qualified domain name (if configured)
hostname -f

# Check /etc/hostname
cat /etc/hostname
```

**Default:** `raspberrypi`  
**If configured in Imager:** `water-meter` (or your custom name)

> 📸 **Screenshot Placeholder:** *Router DHCP client list showing "water-meter" with IP 192.168.1.42*

---

## SSH Connection Methods

### Method 1: Using Hostname (mDNS) — Easiest

```bash
# Linux/macOS (works out of the box)
ssh pi@water-meter.local

# Windows 10/11 (OpenSSH built-in)
ssh pi@water-meter.local

# First connection: type "yes" to accept host key
# Then enter your password
```

> **Why this works:** mDNS (Multicast DNS) resolves `.local` names without a DNS server. Enabled by default on Raspberry Pi OS.

### Method 2: Using IP Address

```bash
ssh pi@192.168.1.42
```

> Use this if `.local` doesn't resolve (see troubleshooting below).

### Method 3: SSH Config (Convenience)

Create/edit `~/.ssh/config` on your computer:

```ssh
Host water-meter
    HostName water-meter.local
    User pi
    # IdentityFile ~/.ssh/id_ed25519  # Uncomment if using SSH keys
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Then simply:
```bash
ssh water-meter
```

> 📸 **Screenshot Placeholder:** *Terminal showing successful SSH connection with welcome message*

---

## Understanding mDNS (hostname.local)

### What is mDNS?

**Multicast DNS** allows devices on the same LAN to resolve `hostname.local` without a central DNS server. It uses multicast to `224.0.0.251:5353`.

### Why Use It?

| Benefit | Explanation |
|---------|-------------|
| **No IP tracking** | Works even if DHCP assigns new IP |
| **Human-readable** | `water-meter.local` vs `192.168.1.42` |
| **Zero config** | Works automatically on modern networks |
| **Cross-platform** | Linux, macOS, Windows 10+, Android, iOS |

### Requirements

| Platform | mDNS Support | Notes |
|----------|--------------|-------|
| **Linux** | ✅ Built-in (Avahi) | Works out of the box |
| **macOS** | ✅ Built-in (Bonjour) | Works out of the box |
| **Windows 10/11** | ✅ Built-in | Requires "Bonjour Print Services" or modern OpenSSH |
| **Windows 7/8** | ❌ | Install [Bonjour Print Services](https://support.apple.com/kb/DL999) |
| **Android** | ✅ | Works in Termux, some apps |
| **iOS** | ✅ | Works in apps like Termius, Prompt |

### Verify mDNS is Running on Pi

```bash
# Check Avahi daemon (mDNS responder)
systemctl status avahi-daemon

# Should show: active (running)

# Test local resolution
avahi-resolve -n water-meter.local
# Output: water-meter.local    192.168.1.42
```

---

## Static IP / DHCP Reservation

### Option A: Router-Side DHCP Reservation (Recommended)

**Why:** Keeps IP consistent without touching Pi config. Survives OS reinstalls.

1. Log into router admin
2. Find **DHCP Reservation** / **Address Reservation** / **Static Lease**
3. Add entry:
   - **MAC Address:** (find with `ip link show eth0` on Pi)
   - **IP Address:** `192.168.1.100` (choose outside DHCP pool)
   - **Hostname:** `water-meter`
4. Save and reboot Pi

> 📸 **Screenshot Placeholder:** *Router DHCP reservation page with MAC/IP filled in*

### Option B: Pi-Side Static IP (nmcli)

```bash
# Show current connection
nmcli con show

# Set static IP for Ethernet (adjust for your network)
sudo nmcli con mod "Wired connection 1" \
    ipv4.addresses 192.168.1.100/24 \
    ipv4.gateway 192.168.1.1 \
    ipv4.dns "192.168.1.1, 8.8.8.8" \
    ipv4.method manual

# For WiFi (replace "Wired connection 1" with your WiFi connection name)
sudo nmcli con mod "YourWiFiSSID" \
    ipv4.addresses 192.168.1.101/24 \
    ipv4.gateway 192.168.1.1 \
    ipv4.dns "192.168.1.1, 8.8.8.8" \
    ipv4.method manual

# Apply changes
sudo nmcli con up "Wired connection 1"
# or
sudo nmcli con up "YourWiFiSSID"

# Verify
ip addr show eth0
```

> ⚠️ **Warning:** Static IP on Pi can cause conflicts if router assigns same IP to another device. DHCP reservation is safer.

---

## Common SSH Issues & Fixes

### Issue 1: `ssh: Could not resolve hostname water-meter.local`

| Cause | Fix |
|-------|-----|
| mDNS not working on Windows | Install [Bonjour Print Services](https://support.apple.com/kb/DL999) or use IP address |
| Pi not on same subnet | Ensure both devices on same LAN (not guest network) |
| Avahi not running on Pi | `sudo systemctl start avahi-daemon && sudo systemctl enable avahi-daemon` |
| Hostname mismatch | Check `hostname` on Pi matches what you're typing |

### Issue 2: `Permission denied (publickey,password)`

| Cause | Fix |
|-------|-----|
| Wrong password | Re-flash with correct password, or reset via `sudo passwd pi` on Pi |
| SSH password auth disabled | Edit `/etc/ssh/sshd_config`: `PasswordAuthentication yes`, then `sudo systemctl restart ssh` |
| User doesn't exist | Check `cat /etc/passwd | grep pi` |

### Issue 3: `Connection refused`

| Cause | Fix |
|-------|-----|
| SSH not enabled | Re-flash with SSH enabled in Imager, or connect monitor and run `sudo raspi-config` → Interface Options → SSH → Enable |
| Wrong IP/port | Verify IP with `hostname -I`; default port is 22 |
| Firewall blocking | `sudo ufw status` — allow port 22: `sudo ufw allow 22/tcp` |

### Issue 4: `Host key verification failed` / `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!`

```bash
# Remove old key (safe if you re-flashed the Pi)
ssh-keygen -R water-meter.local
ssh-keygen -R 192.168.1.42

# Then reconnect
ssh pi@water-meter.local
```

### Issue 5: Slow SSH Connection

```bash
# On Pi: Edit SSH config
sudo nano /etc/ssh/sshd_config
# Add/change:
UseDNS no
GSSAPIAuthentication no

# Restart
sudo systemctl restart ssh
```

### Issue 6: SSH Times Out / Freezes

```bash
# On your computer: ~/.ssh/config
Host water-meter
    HostName water-meter.local
    User pi
    ServerAliveInterval 30
    ServerAliveCountMax 3
    TCPKeepAlive yes
```

---

## Network Diagnostics

### On the Pi

```bash
# Show all interfaces
ip addr show

# Show routing table
ip route show

# Test internet connectivity
ping -c 3 8.8.8.8
ping -c 3 google.com

# Test DNS resolution
nslookup google.com
dig @8.8.8.8 google.com

# Check WiFi signal (if applicable)
iwconfig wlan0
# Or
nmcli device wifi list

# Show listening ports
ss -tlnp

# Check firewall
sudo ufw status verbose
```

### From Your Computer

```bash
# Test SSH port connectivity
nc -zv water-meter.local 22
# Or: telnet water-meter.local 22

# Trace route
traceroute water-meter.local

# Check if port 22 is open
nmap -p 22 water-meter.local
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Find Pi IP | `hostname -I` |
| Find Pi hostname | `hostname` |
| SSH via hostname | `ssh pi@water-meter.local` |
| SSH via IP | `ssh pi@192.168.1.42` |
| Test mDNS resolution | `avahi-resolve -n water-meter.local` |
| Restart SSH | `sudo systemctl restart ssh` |
| Enable SSH on boot | `sudo systemctl enable ssh` |
| Check SSH status | `sudo systemctl status ssh` |
| View SSH logs | `sudo journalctl -u ssh -f` |

---

## Official References

- [Raspberry Pi SSH Documentation](https://www.raspberrypi.com/documentation/computers/remote-access.html#ssh)
- [Raspberry Pi Network Configuration](https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-networking)
- [Avahi (mDNS) Documentation](https://github.com/lathiat/avahi)
- [systemd-networkd / NetworkManager on Pi](https://www.raspberrypi.com/documentation/computers/configuration.html#networkmanager)
- [Raspberry Pi Forums - Networking](https://forums.raspberrypi.com/viewforum.php?f=36)

---

## Next Steps

Proceed to:
1. [Remote Desktop Guide](./remote-desktop-guide.md) — RealVNC setup for GUI access
2. [Python Environment Guide](./python-environment-guide.md) — venv, pip, ML libraries
3. [Project Setup Guide](./setup.md) — Full project deployment

---

*Last updated: July 2026 | Tested on Raspberry Pi OS Trixie (64-bit) | Compatible with Pi 3B+/4/5*