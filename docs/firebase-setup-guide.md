# ⚠️ DEPRECATED — Firebase Setup Guide (Legacy)

> **This guide documents the OLD architecture (ESP32 → Firebase → RPi).**  
> **Current architecture uses USB Serial (ESP32 → RPi) — no Firebase required.**

---

## Archived for Reference Only

This guide is kept for historical reference. The current system uses **direct USB Serial communication** between ESP32 and Raspberry Pi, eliminating the need for Firebase entirely.

### Why Firebase Was Removed

| Factor | Firebase (Old) | USB Serial (New) |
|--------|---------------|------------------|
| **Monthly Cost** | Free tier limits, Blaze for production | $0 — fully local |
| **Internet Dependency** | Required for core loop | Not required for core loop |
| **Latency** | ~100-500ms (RTT to cloud) | < 1ms (local USB) |
| **Reliability** | Depends on Firebase uptime | Local only — no cloud dependency |
| **Complexity** | Auth, tokens, rules, config | Plug and play |
| **Data Privacy** | Data leaves premises | Data stays local |

---

## What Changed

### Old Flow (Deprecated)
```
ESP32 → WiFi → Firebase Realtime DB → RPi (Pyrebase4 polling) → ML → Dashboard
```

### New Flow (Current)
```
ESP32 → USB Cable → RPi (pyserial) → ML → Dashboard
```

---

## If You Still Need Cloud Sync (Optional Add-on)

You can add cloud sync **on top of** the local USB Serial architecture:

1. **RPi → Cloud**: RPi pushes alerts/summaries to Firebase/MQTT/AWS IoT via WiFi/Ethernet
2. **ESP32 stays local**: ESP32 only talks to RPi via USB Serial
3. **No Firebase on ESP32**: Removes WiFi dependency from edge device

This is an **optional enhancement** — the core leak detection works 100% offline.

---

## Migration Notes

If you were following the old Firebase setup:

| Old Component | New Replacement |
|---------------|-----------------|
| Firebase-ESP-Client (ESP32) | ArduinoJson + Serial |
| Pyrebase4 (RPi) | pyserial + asyncio |
| Firebase Auth (Email/Password) | Not needed |
| Firebase Security Rules | Not needed |
| `/readings` path in Firebase | Local SQLite/InfluxDB on RPi |
| `/alerts` path in Firebase | Local alerts.db (AlertEngine) |
| `/commands` path in Firebase | Serial JSON commands |
| Web App Config (`firebase_config.json`) | Not needed |

---

## See Current Documentation

- [System Architecture](./system-architecture.md) — Current USB Serial architecture
- [ESP32 Firmware Guide](./esp32-firmware-complete-guide.md) — Updated for USB Serial
- [RPi Setup Guide](./pi-complete-setup.md) — Updated for local ML + Serial
- [ESP32 ↔ RPi Communication](./esp32-rpi-communication.md) — USB Serial protocol details
- [Troubleshooting](./troubleshooting.md) — Updated for USB Serial issues