# API Documentation

## Base URL

```
http://<server-address>:<port>/api/v1
```

---

## Endpoints

### 1. Submit Multi-Sensor Reading

`POST /readings`

Submit a batch water consumption reading from all 5 sensors.

**Request Body:**

```json
{
  "device_id": "wm-001",
  "timestamp": "2026-07-10T01:00:00Z",
  "sensors": [
    {
      "sensor_id": "inlet",
      "pulse_count": 1234,
      "flow_rate_lpm": 12.5,
      "volume_liters": 2.5,
      "total_liters": 10000.0,
      "fixture": "inlet"
    },
    {
      "sensor_id": "fix1",
      "pulse_count": 450,
      "flow_rate_lpm": 5.2,
      "volume_liters": 0.9,
      "total_liters": 3500.0,
      "fixture": "kitchen_sink"
    },
    {
      "sensor_id": "fix2",
      "pulse_count": 0,
      "flow_rate_lpm": 0.0,
      "volume_liters": 0.0,
      "total_liters": 1200.0,
      "fixture": "toilet"
    },
    {
      "sensor_id": "fix3",
      "pulse_count": 10,
      "flow_rate_lpm": 0.2,
      "volume_liters": 0.02,
      "total_liters": 500.0,
      "fixture": "wash_basin"
    },
    {
      "sensor_id": "fix4",
      "pulse_count": 0,
      "flow_rate_lpm": 0.0,
      "volume_liters": 0.0,
      "total_liters": 800.0,
      "fixture": "shower"
    }
  ],
  "ml_result": {
    "inference": "normal",
    "confidence": 0.96,
    "anomaly_score": 0.02,
    "model_version": "rf_v2.1"
  },
  "leak_alerts": [],
  "valve_states": {
    "inlet": "open",
    "fix1": "open",
    "fix2": "open",
    "fix3": "open",
    "fix4": "open"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| device_id | string | Unique meter identifier |
| timestamp | string | ISO 8601 datetime |
| sensors[] | array | Array of 5 sensor readings |
| sensors[].sensor_id | string | `inlet`, `fix1`–`fix4` |
| sensors[].pulse_count | int | Raw pulses since last report |
| sensors[].flow_rate_lpm | float | Instantaneous flow (L/min) |
| sensors[].volume_liters | float | Volume since last reading |
| sensors[].total_liters | float | Cumulative total |
| sensors[].fixture | string | Human-readable fixture name |
| ml_result | object | ML inference output |
| leak_alerts[] | array | Active leak alerts |
| valve_states | object | Current valve positions |

**Response:**

```json
{
  "status": "ok",
  "reading_id": "abc123",
  "message": "Reading recorded"
}
```

---

### 2. Submit Leak Event

`POST /alerts`

Report a leak detection event from the edge.

**Request Body:**

```json
{
  "device_id": "wm-001",
  "timestamp": "2026-07-10T01:05:00Z",
  "fixture": "kitchen_sink",
  "sensor_id": "fix1",
  "leak_type": "minor",
  "confidence": 0.87,
  "duration_seconds": 300,
  "flow_rate_lpm": 0.3,
  "action_taken": "valve_closed",
  "current_valve_state": "closed"
}
```

**Response:**

```json
{
  "status": "ok",
  "alert_id": "alert-456",
  "severity": "warning"
}
```

---

### 3. Get Latest Readings

`GET /readings/latest?device_id={device_id}`

**Response:**

```json
{
  "device_id": "wm-001",
  "timestamp": "2026-07-10T01:00:00Z",
  "sensors": [
    {"sensor_id": "inlet", "flow_rate_lpm": 12.5, "total_liters": 10000.0},
    {"sensor_id": "fix1", "flow_rate_lpm": 5.2, "total_liters": 3500.0},
    {"sensor_id": "fix2", "flow_rate_lpm": 0.0, "total_liters": 1200.0},
    {"sensor_id": "fix3", "flow_rate_lpm": 0.2, "total_liters": 500.0},
    {"sensor_id": "fix4", "flow_rate_lpm": 0.0, "total_liters": 800.0}
  ],
  "total_flow_lpm": 17.9,
  "total_volume_l": 16000.0,
  "inlet_balance": 0.0,
  "leak_active": false,
  "battery_pct": 85
}
```

---

### 4. Get Reading History

`GET /readings?device_id={device_id}&from={iso_date}&to={iso_date}&limit=100`

**Response:**

```json
{
  "device_id": "wm-001",
  "readings": [
    {
      "timestamp": "2026-07-10T00:00:00Z",
      "sensors": [
        {"sensor_id": "inlet", "volume_liters": 1.5, "total_liters": 14998.5},
        {"sensor_id": "fix1", "volume_liters": 1.2, "total_liters": 3499.1},
        {"sensor_id": "fix2", "volume_liters": 0.0, "total_liters": 1200.0},
        {"sensor_id": "fix3", "volume_liters": 0.3, "total_liters": 499.7},
        {"sensor_id": "fix4", "volume_liters": 0.0, "total_liters": 800.0}
      ],
      "inlet_minus_fixtures": 0.0,
      "ml_inference": "normal",
      "leak_detected": false
    }
  ],
  "total": 1,
  "page": 1
}
```

---

### 5. Get Active Alerts

`GET /alerts?device_id={device_id}&active=true`

**Response:**

```json
{
  "alerts": [
    {
      "alert_id": "alert-456",
      "timestamp": "2026-07-10T01:05:00Z",
      "fixture": "kitchen_sink",
      "leak_type": "minor",
      "confidence": 0.87,
      "action": "valve_closed",
      "resolved": false,
      "resolved_at": null
    }
  ],
  "total_active": 1
}
```

---

### 6. Register Device

`POST /devices`

**Request:**

```json
{
  "device_id": "wm-001",
  "name": "Ground Floor Water Meter",
  "location": "Quezon Province",
  "sensors": [
    {"id": "inlet", "fixture": "main_inlet", "type": "yf-s201"},
    {"id": "fix1", "fixture": "kitchen_sink", "type": "yf-s201"},
    {"id": "fix2", "fixture": "toilet", "type": "yf-s201"},
    {"id": "fix3", "fixture": "wash_basin", "type": "yf-s201"},
    {"id": "fix4", "fixture": "shower", "type": "yf-s201"}
  ],
  "valves": {
    "inlet": true,
    "fix1": true,
    "fix2": true,
    "fix3": true,
    "fix4": true
  },
  "ml_model": "random_forest_v2"
}
```

**Response:**

```json
{
  "status": "ok",
  "api_key": "sk-...",
  "device_secret": "***"
}
```

---

### 7. Device Status / Health

`GET /devices/{device_id}/status`

**Response:**

```json
{
  "device_id": "wm-001",
  "online": true,
  "last_seen": "2026-07-10T01:00:00Z",
  "signal_rssi": -65,
  "uptime_seconds": 86400,
  "sensor_count": 5,
  "valve_count": 5,
  "open_valves": 4,
  "closed_valves": 1,
  "firmware": "v2.1.0",
  "ml_model": "rf_v2.1",
  "ml_accuracy": 96.2,
  "storage_usage_pct": 23,
  "leak_alerts_24h": 3
}
```

---

### 8. Remote Valve Control

`POST /devices/{device_id}/valve`

**Request:**

```json
{
  "sensor_id": "fix1",
  "action": "close",
  "reason": "user_command"
}
```

**Response:**

```json
{
  "status": "ok",
  "sensor_id": "fix1",
  "previous_state": "open",
  "current_state": "closed"
}
```

---

### 9. Trigger Calibration

`POST /devices/{device_id}/calibrate`

**Request:**

```json
{
  "sensor_id": "inlet",
  "known_volume_liters": 10.0
}
```

**Response:**

```json
{
  "status": "ok",
  "previous_k_factor": 450,
  "new_k_factor": 462
}
```

---

## WebSocket (Real-time)

`ws://<server>/ws/{device_id}`

**Server push events:**

```json
{
  "type": "reading",
  "data": {
    "sensor_id": "inlet",
    "flow_rate_lpm": 8.2,
    "total_liters": 10050.0
  }
}
```

```json
{
  "type": "leak_alert",
  "data": {
    "fixture": "kitchen_sink",
    "leak_type": "major",
    "confidence": 0.94
  }
}
```

```json
{
  "type": "command",
  "data": {
    "command": "close_valve",
    "sensor_id": "fix1"
  }
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 400 | Bad Request / Invalid JSON |
| 401 | Unauthorized / Bad API Key |
| 404 | Device Not Found |
| 409 | Valve already in requested state |
| 422 | Unprocessable Entity (sensor ID not found) |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

## Authentication

```http
Authorization: Bearer <api_key>
```
