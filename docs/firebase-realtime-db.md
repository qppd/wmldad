# ⚠️ DEPRECATED — Firebase Realtime DB Schema (Legacy)

> **This document describes the OLD Firebase schema.**  
> **Current architecture uses USB Serial + Local SQLite/InfluxDB on RPi — no Firebase.**

---

## Archived for Reference Only

The current system stores all data locally on the Raspberry Pi. Firebase is **not used** in the core data path.

### Local Storage Replaces Firebase

| Firebase Path (Old) | Local Replacement (New) |
|---------------------|-------------------------|
| `/readings/{device_id}/{timestamp}` | SQLite `readings` table / InfluxDB |
| `/alerts/{device_id}/{alert_id}` | SQLite `alerts` table (AlertEngine) |
| `/commands/{device_id}/{command_id}` | USB Serial JSON commands |
| `/devices/{device_id}` | Local device config (config.h / JSON) |
| `/models/metadata` | `models/metadata.json` on RPi filesystem |
| `/config/{device_id}` | `config.h` on ESP32 + local JSON on RPi |

---

## If You Need Cloud Sync (Optional)

Add cloud sync as a **separate layer on the RPi**:

```python
# rpi/cloud_sync.py (optional)
import requests
import json

def sync_to_cloud():
    """Push alerts + daily summaries to cloud (Firebase/MQTT/AWS)."""
    # Read from local SQLite
    # POST to cloud endpoint
    pass
```

The ESP32 remains **completely local** — only talks to RPi via USB Serial.

---

## See Current Documentation

- [System Architecture](./system-architecture.md) — Current local-first architecture
- [RPi Setup Guide](./pi-complete-setup.md) — Local ML + Serial setup
- [ESP32 Firmware Guide](./esp32-firmware-complete-guide.md) — USB Serial firmware
- [Troubleshooting](./troubleshooting.md) — Serial/USB issues