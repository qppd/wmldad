# Firebase Realtime DB Schema

> **Architecture:** ESP32 (Firebase-ESP-Client) ↔ Firebase Realtime DB ↔ PythonAnywhere (Pyrebase4)
> **Data flow:** Sensors → ESP32 → Firebase → PythonAnywhere → XGBoost → Dashboard

---

## Database Root Structure

```
/ (root)
├── /readings/{device_id}/{ISO_timestamp}
├── /commands/{device_id}/{command_id}
├── /alerts/{device_id}/{alert_id}
├── /devices/{device_id}
├── /models/metadata
└── /config/
```

---

## 1. Readings Path

**Path:** `/readings/{device_id}/{ISO_timestamp}`

This is the primary data path. The ESP32 pushes a new node every upload interval (5–60 seconds).

```json
{
  "readings": {
    "wm_001": {
      "2026-07-10T08:00:00Z": {
        "inlet": {
          "flow_rate": 12.5,
          "volume": 2.5,
          "total": 10000.0,
          "pulse_count": 1125,
          "k_factor": 450
        },
        "fixture_1": {
          "flow_rate": 5.2,
          "volume": 0.9,
          "total": 3500.0,
          "pulse_count": 405,
          "k_factor": 450,
          "fixture_name": "kitchen_sink"
        },
        "fixture_2": {
          "flow_rate": 0.0,
          "volume": 0.0,
          "total": 1200.0,
          "pulse_count": 0,
          "fixture_name": "toilet"
        },
        "fixture_3": {
          "flow_rate": 0.2,
          "volume": 0.02,
          "total": 500.0,
          "pulse_count": 10,
          "fixture_name": "wash_basin"
        },
        "fixture_4": {
          "flow_rate": 0.0,
          "volume": 0.0,
          "total": 800.0,
          "pulse_count": 0,
          "fixture_name": "shower"
        },
        "device": {
          "rssi": -65,
          "uptime": 86400,
          "free_heap": 180000,
          "firmware": "v2.1.0"
        }
      }
    }
  }
}
```

### Field Descriptions

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `inlet.flow_rate` | float | ESP32 | Instantaneous flow rate (L/min) |
| `inlet.volume` | float | ESP32 | Volume since last reading (L) |
| `inlet.total` | float | ESP32 | Cumulative total volume (L) |
| `inlet.pulse_count` | int | ESP32 | Raw pulses since last upload |
| `fixture_N.flow_rate` | float | ESP32 | Fixture N flow rate |
| `fixture_N.fixture_name` | string | Config | Human-readable fixture name |
| `device.rssi` | int | ESP32 | WiFi signal strength (dBm) |
| `device.firmware` | string | ESP32 | Current firmware version |

### Indexing

```json
{
  "rules": {
    "readings": {
      ".indexOn": ["device_id"],
      "$device_id": {
        ".indexOn": [".value"]
      }
    }
  }
}
```

---

## 2. Commands Path

**Path:** `/commands/{device_id}/{command_id}`

Written by **PythonAnywhere** or **Web Dashboard**, streamed to **ESP32** via Firebase-ESP-Client stream listener.

```json
{
  "commands": {
    "wm_001": {
      "cmd_001": {
        "command": "close_fix1",
        "timestamp": "2026-07-10T08:05:00Z",
        "source": "dashboard",
        "reason": "leak_detected",
        "executed": false
      }
    }
  }
}
```

### Available Commands

| Command | Target | Description |
|---------|--------|-------------|
| `close_all` | All | Close all solenoid valves |
| `open_all` | All | Open all solenoid valves |
| `close_inlet` | Inlet (relay 1) | Close main inlet valve |
| `close_fix1` | Fixture 1 (relay 2) | Close fixture 1 valve |
| `close_fix2` | Fixture 2 (relay 3) | Close fixture 2 valve |
| `close_fix3` | Fixture 3 (relay 4) | Close fixture 3 valve |
| `close_fix4` | Fixture 4 (relay 5) | Close fixture 4 valve |
| `open_inlet` | Inlet | Open inlet valve |
| `open_fix1` | Fixture 1 | Open fixture 1 valve |
| `calibrate` | All | Start calibration mode |
| `calibrate_inlet` | Inlet | Calibrate inlet sensor only |
| `reboot` | All | Reboot ESP32 |

---

## 3. Alerts Path

**Path:** `/alerts/{device_id}/{alert_id}`

Written by **PythonAnywhere** (ML-based) or **ESP32** (local rules).

```json
{
  "alerts": {
    "wm_001": {
      "alert_001": {
        "fixture_index": 1,
        "fixture_name": "kitchen_sink",
        "alert_type": "minor_leak",
        "confidence": 0.87,
        "source": "xgboost",
        "details": {
          "flow_rate": 0.3,
          "duration_seconds": 300,
          "inlet_ratio": 1.3,
          "anomaly_score": null
        },
        "valve_action": "closed",
        "valve_state": "closed",
        "timestamp": "2026-07-10T08:05:00Z",
        "resolved": false,
        "resolved_at": null,
        "resolved_by": null
      }
    }
  }
}
```

### Alert Types

| Type | Severity | Description | Action |
|------|----------|-------------|--------|
| `minor_leak` | Warning | Drip / slow leak | Close valve + notify |
| `major_leak` | Critical | Burst / stuck valve | Close valve + alarm + emergency notify |
| `anomaly` | Info | Unrecognized pattern | Log + review |
| `hidden_leak` | Warning | Inlet >> sum(fixtures) | Alert (unknown leak) |
| `sensor_fault` | Warning | Sensor reading inconsistency | Flag for maintenance |

---

## 4. Devices Path

**Path:** `/devices/{device_id}`

Written on device registration, updated by ESP32.

```json
{
  "devices": {
    "wm_001": {
      "name": "Ground Floor Water Meter",
      "location": "Quezon Province",
      "sensors": [
        {"id": 0, "name": "inlet", "fixture": "main_inlet", "pin": 34},
        {"id": 1, "name": "fix1", "fixture": "kitchen_sink", "pin": 35},
        {"id": 2, "name": "fix2", "fixture": "toilet", "pin": 32},
        {"id": 3, "name": "fix3", "fixture": "wash_basin", "pin": 33},
        {"id": 4, "name": "fix4", "fixture": "shower", "pin": 25}
      ],
      "valves": [true, true, true, true, true],
      "status": {
        "online": true,
        "last_seen": "2026-07-10T08:00:00Z",
        "firmware": "v2.1.0",
        "total_readings": 50000,
        "active_alerts": 1
      },
      "config": {
        "upload_interval_seconds": 5,
        "pulse_per_liter": 450,
        "leak_confirm_count": 3,
        "continuous_flow_minutes": 30,
        "confidence_threshold": 0.80
      },
      "created_at": "2026-06-01T00:00:00Z"
    }
  }
}
```

---

## 5. Models Metadata Path

**Path:** `/models/metadata`

Used by PythonAnywhere to publish model info.

```json
{
  "models": {
    "metadata": {
      "active_xgboost": "xgboost_v3",
      "active_isolation_forest": "iforest_v2",
      "last_trained": "2026-07-09T00:00:00Z",
      "accuracy": 96.2,
      "precision": 94.5,
      "recall": 95.8,
      "training_samples": 15000
    },
    "versions": {
      "xgboost_v3": {
        "trained_at": "2026-07-09T00:00:00Z",
        "accuracy": 96.2,
        "features": ["flow_rate", "duration", "hour", "day", "fixture_id", "inlet_ratio", "variance", "night", "trend"],
        "classes": ["normal", "minor_leak", "major_leak"],
        "file": "/home/username/water_meter/models/xgboost_v3.json"
      }
    }
  }
}
```

---

## 6. Config Path

**Path:** `/config/{device_id}`

Dashboard-adjustable device parameters.

```json
{
  "config": {
    "wm_001": {
      "upload_interval_seconds": 5,
      "pulse_per_liter_inlet": 462,
      "pulse_per_liter_fix1": 450,
      "pulse_per_liter_fix2": 450,
      "pulse_per_liter_fix3": 448,
      "pulse_per_liter_fix4": 455,
      "leak_confirm_count": 3,
      "continuous_flow_minutes": 30,
      "confidence_threshold": 0.80,
      "alert_telegram": true,
      "alert_email": false,
      "auto_shutoff": true,
      "night_mode_quiet": false
    }
  }
}
```

---

## Firebase Security Rules (Production)

```json
{
  "rules": {
    "readings": {
      ".indexOn": ["device_id"],
      "$device_id": {
        "$timestamp": {
          ".read": "auth != null && auth.uid == $device_id",
          ".write": "auth != null && auth.uid == $device_id",
          ".validate": "newData.hasChildren(['inlet'])"
        }
      }
    },
    "commands": {
      "$device_id": {
        ".read": "auth != null && auth.uid == $device_id",
        ".write": "auth.uid == 'pythonanywhere-bot' || auth.uid == 'dashboard-admin'"
      }
    },
    "alerts": {
      "$device_id": {
        ".read": "auth != null",
        ".write": "auth.uid == 'pythonanywhere-bot' || auth.uid == $device_id"
      }
    },
    "devices": {
      ".read": "auth != null",
      "$device_id": {
        ".write": "auth.uid == $device_id || auth.uid == 'dashboard-admin'"
      }
    },
    "models": {
      ".read": "auth != null",
      ".write": "auth.uid == 'pythonanywhere-bot'"
    },
    "config": {
      "$device_id": {
        ".read": "auth != null && auth.uid == $device_id",
        ".write": "auth.uid == 'dashboard-admin'"
      }
    }
  }
}
```

---

## Firebase Pricing Estimate

| Path | Write Ops/day | Read Ops/day | Storage (90 days) |
|------|--------------|-------------|-------------------|
| `/readings` | 17,280 (1 device, 5s interval) | 1,000 (dashboard queries) | ~200 MB |
| `/commands` | 10 | 500 | < 1 MB |
| `/alerts` | 10 | 100 | < 1 MB |
| **Total (free tier)** | 17,300 | 1,600 | ~200 MB |

> **Firebase Spark (Free) Plan:** 50K reads/day, 20K writes/day, 1 GB storage — sufficient for 1–3 devices.

---

## Pyrebase4 Code (PythonAnywhere)

```python
import pyrebase

config = {
    "apiKey": "AIzaSy...",
    "authDomain": "your-project.firebaseapp.com",
    "databaseURL": "https://your-project.firebaseio.com",
    "storageBucket": "your-project.appspot.com",
    "serviceAccount": "serviceAccountKey.json"  # Download from Firebase Console
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

# Stream readings (real-time)
def stream_handler(message):
    print(f"Stream event: {message['event']} at {message['path']}")
    data = message['data']
    if data:
        # Process with ML model
        features = extract_features(data)
        prediction = xgboost_model.predict(features)
        if prediction != "normal":
            # Write alert
            alert_data = {
                "alert_type": prediction,
                "timestamp": get_timestamp(),
                "fixture_index": data.get("fixture_index", -1)
            }
            db.child("alerts").child(DEVICE_ID).push(alert_data)

my_stream = db.child("readings").child(DEVICE_ID).stream(stream_handler, stream_id="readings_stream")

# Read data on demand
readings = db.child("readings").child(DEVICE_ID).order_by_key().limit_to_last(100).get()

# Write data
db.child("commands").child(DEVICE_ID).push({
    "command": "close_fix1",
    "timestamp": get_timestamp(),
    "source": "ml_model"
})

# Full code: ./docs/pythonanywhere-app.md
```
