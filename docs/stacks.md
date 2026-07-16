# Technology Stack — Water Meter with Leak Detection

> **Architecture:** Sensors → ESP32 → USB Serial (CDC/ACM) → RPi → XGBoost → Dashboard (7" touchscreen LCD on RPi + remote via port forwarding)

---

## ESP32 Firmware Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Framework** | Arduino framework (esp32 core) | ≥ 2.0.x | Mature, well-documented, large ecosystem |
| **IDE** | Arduino IDE 2.x | Latest | ESP32 board support, Library Manager, Serial Monitor |
| **Language** | C++11/Arduino | — | Standard for ESP32 |
| **JSON** | [ArduinoJson](https://arduinojson.org/) | ≥ 7.x | Payload serialization for USB Serial |
| **WiFi** | WiFi.h (Arduino) | Built-in | Station mode, auto-reconnect (for OTA + NTP only) |
| **NTP** | NTPClient / configTime() | Built-in | Time sync for timestamped data |
| **OTA** | ArduinoOTA | Built-in | Over-the-air firmware updates |
| **SPIFFS** | SPIFFS (via LittleFS) | Built-in | Offline data logging |

### ArduinoJson Usage (v7+)

```cpp
#include <ArduinoJson.h>

JsonDocument doc;  // v7+ uses JsonDocument (replaces StaticJsonDocument)

doc["device_id"] = "wmldad-001";
doc["ts"] = millis();
doc["sensor"] = 1;
doc["gpio"] = 26;
doc["pulses"] = 127;
doc["flow_rate_lpm"] = 2.34;
doc["volume_ml"] = 456;

serializeJson(doc, Serial);
Serial.println();  // Newline delimiter for JSON Lines
```

---

## USB Serial Communication Stack

| Layer | Technology | Protocol | Details |
|-------|------------|----------|---------|
| **Physical** | USB Micro-B / USB-C cable | USB 2.0 | Data + power (5V backup) |
| **CDC/ACM** | CP2102 / CH340 USB-UART bridge | UART | Appears as `/dev/ttyUSB0` or `/dev/ttyUSB1` on RPi |
| **Baud Rate** | 921600 | — | High throughput for 4 sensors @ 5s interval |
| **Format** | JSON Lines (NDJSON) | UTF-8 | One JSON object per line |
| **RPi Driver** | pyserial + asyncio | Python | Auto-detects ESP32 via VID:PID |

---

## Raspberry Pi Backend Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Hardware** | Raspberry Pi 3B+/4/5 | — | Local always-on Flask server, ML inference |
| **OS** | Raspberry Pi OS (64-bit) | Trixie (Debian 13) | Stable Linux distribution for ARM |
| **Language** | Python | ≥ 3.11 | ML ecosystem, serial comms |
| **Web Framework** | Flask | ≥ 3.0 | Web dashboard + REST API endpoints |
| **Serial** | pyserial + asyncio | ≥ 3.5 | USB Serial reader with auto-reconnect |
| **ML (primary)** | [XGBoost](https://xgboost.readthedocs.io/) | ≥ 2.0 | Gradient-boosted decision tree — leak classification |
| **ML (anomaly)** | [scikit-learn](https://scikit-learn.org/) (IsolationForest) | ≥ 1.3 | Unsupervised anomaly detection |
| **Data** | pandas, numpy | Latest | Feature engineering |
| **Scheduling** | systemd + cron | Built-in | Daily model retraining via cron |
| **Templates** | Jinja2 + Chart.js | — | Dashboard HTML/JS |
| **Storage** | SQLite / InfluxDB | — | Time-series data storage |

---

## ML Model Stack

| Model | Type | Framework | Task | Where it runs |
|-------|------|-----------|------|---------------|
| **XGBoost** | Gradient-boosted decision tree | xgboost Python | 3-class classification (normal, minor_leak, major_leak) | RPi (Flask) |
| **Isolation Forest** | Unsupervised ensemble | scikit-learn | Binary anomaly/not-anomaly | RPi (Flask) |

### Feature Set (9 features)

| Feature | Description | Type | Range |
|---------|-------------|------|-------|
| `flow_rate` | Instantaneous flow rate (L/min) | float | 0–40 |
| `duration_seconds` | Seconds since water started flowing | int | 0–3600+ |
| `hour_of_day` | Hour (0–23) | int | 0–23 |
| `day_of_week` | Day (0=Mon) | int | 0–6 |
| `fixture_id` | One-hot encoded fixture | int | 0–3 |
| `inlet_ratio` | Inlet rate ÷ fixture rate | float | 0.5–2.0 |
| `rate_variance` | Flow rate variance (last 10s) | float | 0–10 |
| `is_night_time` | Between 10PM–5AM | bool | 0/1 |
| `pulse_trend` | Slope of pulses (last 5 readings) | float | -∞ to +∞ |

### Target Classes

| Class | Description | Training Labels |
|-------|-------------|-----------------|
| `normal` | Regular water usage (faucet, flush, shower) | Label 0 |
| `minor_leak` | Drip / slow leak (0.1–0.5 L/min sustained >30s) | Label 1 |
| `major_leak` | Burst / stuck valve (>5 L/min for >30s) | Label 2 |

> See [ML Model](./ml-complete-guide.md) for complete model training guide and performance benchmarks.

---

## Web Dashboard Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Flask (Python) — serves HTML + JSON API |
| **Frontend** | HTML5 + CSS3 + Vanilla JS (no framework needed) |
| **Charts** | Chart.js (real-time line/bar charts) |
| **Real-time** | Server-Sent Events (SSE) from Flask, or periodic fetch |
| **Styling** | Bootstrap 5 / Tailwind CSS |
| **Deployment** | RPi Flask — systemd service |
| **Remote Access** | **Port forwarding** (router) + Dynamic DNS (optional) |

---

## Communication Summary

| Path | Protocol | Data Format | Frequency |
|------|----------|-------------|-----------|
| Sensor → ESP32 | Pulse (GPIO interrupt) | Rising edge | Continuous |
| ESP32 → RPi | USB CDC/ACM (UART) | JSON Lines | Every 5 sec |
| RPi → ESP32 | USB CDC/ACM (UART) | JSON Commands | On demand |
| User → Dashboard | HTTP/WebSocket | HTTPS | On demand |
| Dashboard → Commands | Write to Serial | JSON | On demand |
| **Remote → RPi** | **HTTPS (port forward)** | **HTML/JSON** | **On demand** |

---

## Development Tools

| Tool | Purpose |
|------|---------|
| **Arduino IDE** | Build, upload, and debug ESP32 firmware (C++) |
| **Python 3.11+** | ML training, backend development |
| **Jupyter / Google Colab** | ML model prototyping and experimentation |
| **Firebase Console** | *(Removed - no longer used)* |
| **RPi console (ssh)** | Backend debugging, log viewing |
| **Serial Monitor** | ESP32 debug output |
| **Git + GitHub** | Version control |

---

## Stack Decision Matrix

| Requirement | Chosen | Alternatives Considered | Why This Won |
|-------------|--------|------------------------|--------------|
| Firebase | **Removed - USB Serial** | Custom Node.js server, Supabase, AWS IoT | Zero monthly cost, no internet dependency, lower latency |
| Firebase-ESP-Client | **ArduinoJson** | HTTP client, MQTT, Blynk | Simple, no dependencies, zero cloud cost |
| **Pyrebase4** | **pyserial + asyncio** | firebase-admin | No auth tokens, no polling, instant local comms |
| XGBoost | Random Forest, LightGBM, CNN | Best for tabular time-series |
| Isolation Forest | Autoencoder, One-Class SVM | Unsupervised, low memory |
| RPi (Raspberry Pi) | Heroku, Railway, cloud VPS | One-time cost, no monthly fees, full local control |
| ESP32 38-pin ESP32 Dev Module | 30-pin, ESP32-C3, ESP8266 | More GPIOs for 4 sensors + peripherals |
| **Port Forwarding + DDNS** | Tailscale, ngrok, Cloudflare Tunnel | No third-party dependency, standard router feature |

---

## Stack Summary

- **ESP32**: Arduino + ArduinoJson → 4 flow sensors → USB Serial (921600 baud, JSON Lines)
- **RPi**: Flask + pyserial (asyncio) + XGBoost + Isolation Forest → Dashboard + Alerts
- **Dashboard**: 7" touchscreen (local) + remote via port forwarding
- **Alerts**: In-app (dashboard polls `/api/alerts`) + optional webhook
- **No Firebase, no cloud dependency for core loop** — fully local, zero monthly cost