# Firebase Realtime DB Schema

> **Architecture:** ESP32 (Firebase-ESP-Client) ↔ Firebase Realtime DB ↔ RPi (Pyrebase4)
> **Data flow:** Sensors → ESP32 → Firebase → RPi → XGBoost → Dashboard

---

## Database Root Structure

```
/
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
          "fixture_name": "bidet"
        },
        "fixture_2": {
          "flow_rate": 0.0,
          "volume": 0.0,
          "total": 1200.0,
          "pulse_count": 0,
          "fixture_name": "kitchen"
        },
        "fixture_3": {
          "flow_rate": 0.2,
          "volume": 0.02,
          "total": 500.0,
          "pulse_count": 10,
          "fixture_name": "bathroom_shower"
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

Written by **RPi backend** or **Web Dashboard**, streamed to **ESP32** via Firebase-ESP-Client stream listener.

```json
{
  "commands": {
    "wm_001": {
      "cmd_001": {
        "command": "calibrate",
        "timestamp": "2026-07-10T08:05:00Z",
        "source": "dashboard",
        "reason": "calibration_requested",
        "executed": false
      }
    }
  }
}
```

### Available Commands

| Command | Target | Description |
|---------|--------|-------------|
| `calibrate` | All | Start calibration mode |
| `calibrate_inlet` | Inlet | Calibrate inlet sensor only |
| `reboot` | All | Reboot ESP32 |

---

## 3. Alerts Path

**Path:** `/alerts/{device_id}/{alert_id}`

Written by **RPi backend (ML-based)** or **ESP32** (local rules).

```json
{
  "alerts": {
    "wm_001": {
      "alert_001": {
        "fixture_index": 1,
        "fixture_name": "bidet",
        "alert_type": "minor_leak",
        "confidence": 0.87,
        "source": "xgboost",
        "details": {
          "flow_rate": 0.3,
          "duration_seconds": 300,
          "inlet_ratio": 1.3,
          "anomaly_score": null
        },
        "valve_action": "monitoring",
        "valve_state": "open",
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
| `minor_leak` | Warning | Drip / slow leak | Log + notify |
| `major_leak` | Critical | Burst / stuck valve | Log + alarm + emergency notify |
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
        {"id": 1, "name": "fix1", "fixture": "bidet", "pin": 35},
        {"id": 2, "name": "fix2", "fixture": "kitchen", "pin": 32},
        {"id": 3, "name": "fix3", "fixture": "bathroom_shower", "pin": 33}
      ],
      "valves": [false, false, false, false],
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

Used by RPi backend to publish model info.

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
      "leak_confirm_count": 3,
      "continuous_flow_minutes": 30,
      "confidence_threshold": 0.80,
      "alert_telegram": true,
      "alert_email": false,
      "auto_shutoff": false,
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
        ".write": "auth.uid == 'rpi-backend' || auth.uid == 'dashboard-admin'"
      }
    },
    "alerts": {
      "$device_id": {
        ".read": "auth != null",
        ".write": "auth.uid == 'rpi-backend' || auth.uid == $device_id"
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
      ".write": "auth.uid == 'rpi-backend'"
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

## Pyrebase4 Code (RPi Backend)

```python
import pyrebase
import json
import threading
import time
from datetime import datetime

# Load Firebase config
with open("firebase_config.json", "r") as f:
    firebase_config = json.load(f)

# Initialize Pyrebase4
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

# Email/Password authentication
EMAIL = "esp32@your-project.iam.gserviceaccount.com"
PASSWORD = "your-strong-password"

# Sign in
user = auth.sign_in_with_email_and_password(EMAIL, PASSWORD)
id_token = user['idToken']
refresh_token = user['refreshToken']

DEVICE_ID = "wm_001"

# References
readings_ref = db.child(f"readings/{DEVICE_ID}")
alerts_ref = db.child(f"alerts/{DEVICE_ID}")
commands_ref = db.child(f"commands/{DEVICE_ID}")

def refresh_token():
    """Refresh auth token if expired"""
    global user, id_token
    try:
        user = auth.refresh(refresh_token)
        id_token = user['idToken']
    except Exception as e:
        print(f"Token refresh failed: {e}")
        # Re-authenticate
        user = auth.sign_in_with_email_and_password(EMAIL, PASSWORD)
        id_token = user['idToken']

def poll_readings():
    """Poll Firebase for new readings every 5 seconds"""
    last_timestamp = None
    
    while True:
        try:
            # Get latest reading
            readings = readings_ref.order_by_key().limit_to_last(1).get(id_token)
            if readings and readings.val():
                for ts, data in readings.val().items():
                    if ts != last_timestamp:
                        last_timestamp = ts
                        process_reading(data)
        except Exception as e:
            print(f"Poll error: {e}")
            if "permission" in str(e).lower() or "unauthorized" in str(e).lower():
                refresh_token()
        time.sleep(5)

def process_reading(data):
    """Extract features and run ML inference"""
    features = extract_features(data)
    result = detector.predict(features)
    
    if result['final'] != 'normal':
        # Write alert to Firebase
        alert_data = {
            "alert_type": result['final'],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "confidence": result.get('confidence', 0),
            "fixture_index": data.get('fixture_index', -1),
            "valve_action": "monitoring"
        }
        alerts_ref.push(alert_data, id_token)
        
        # Send notification
        alert_engine.send_telegram(alert_data)

def send_command(command):
    """Send command to ESP32 via Firebase"""
    commands_ref.push({
        "command": command,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "dashboard"
    }, id_token)

# Example: Get latest reading
def get_latest_reading():
    readings = readings_ref.order_by_key().limit_to_last(1).get(id_token)
    return readings.val() if readings else None

# Example: Get recent alerts
def get_recent_alerts(limit=20):
    alerts = alerts_ref.order_by_key().limit_to_last(limit).get(id_token)
    return alerts.val() if alerts else None
```

---

## Token Refresh Pattern (Pyrebase4)

```python
def _refresh_token(self):
    """Refresh auth token if expired"""
    try:
        self.user = self.auth.refresh(self.user['refreshToken'])
        self.id_token = self.user['idToken']
    except Exception as e:
        print(f"Token refresh failed: {e}")
        # Re-authenticate
        self.user = self.auth.sign_in_with_email_and_password(
            self.email, self.password
        )
        self.id_token = self.user['idToken']
```

Call `_refresh_token()` before each DB operation or when catching "permission_denied" / "unauthorized" errors.

---

## Security Rules (for Pyrebase4 Email/Password Auth)

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
        ".write": "auth.uid == $device_id"
      }
    },
    "alerts": {
      "$device_id": {
        ".read": "auth != null",
        ".write": "auth.uid == $device_id"
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
      ".write": "auth.uid == 'rpi-backend'"
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