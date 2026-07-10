# Technology Stack — Water Meter with Leak Detection

> **Architecture:** Sensors → ESP32 → Firebase Realtime DB → PythonAnywhere → XGBoost → Dashboard

---

## Hardware Stack

| Component | Specification | Qty | Justification |
|-----------|--------------|-----|---------------|
| **ESP32 38-Pin Dev Board** | CP2102, Xtensa LX6 dual-core, WiFi + BLE | 1 | 5 simultaneous ISRs, WiFi stack, Firebase library support |
| **ESP32 Expansion Board** | Screw terminals, labeled pinout, breadboard-friendly | 1 | Clean wiring for 5 sensors + relays + peripherals |
| **YF-S201 Flow Sensor** | 1/2" thread, Hall-effect pulse output, 450 PPL nominal | 5 | Industry-standard for Arduino/ESP32 projects, cheap & reliable |
| **Check Valve 1/2"** | Brass or PVC, non-return | 4 | Prevents backflow between fixtures (critical for per-fixture monitoring) |
| **Solenoid Valve 1/2" NC** | 12V, Normally Closed | 4–5 | Automatic shutoff per fixture when leak detected |
| **4-Ch Relay Module** | 5V, optocoupler isolated, active LOW | 1 | Drives solenoid valves from ESP32 GPIO |
| **OLED 128×64** | SSD1306, I²C, 0.96" | 1 | Live display of per-fixture readings |
| **Micro SD Card Module** | SPI interface | 1 | Data backup during WiFi/Firebase outages |
| **Active Buzzer** | 5V | 1 | Audible alarm on leak detection |
| **Power Supply** | 5V 2A USB adapter | 1 | Powers ESP32 + sensors |
| **Power Supply** | 12V 2A adapter (valves only) | 1 | Separate supply for solenoid valves |
| **LM2596 DC-DC** | Step-down regulator | 1 | (Optional) if using single 12V rail |
| **Breadboard + Jumpers** | 830 points + 65 wires | 1 set | Prototyping |
| **ABS Project Box** | 200×120×70mm | 1 | Enclosure with cable glands |

> See [BOM.md](./bom.md) for complete parts list with prices and purchase links.

---

## ESP32 Firmware Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Framework** | Arduino framework (esp32 core) | ≥ 2.0.x | Mature, well-documented, large ecosystem |
| **IDE** | Arduino IDE 2.x | Latest | ESP32 board support, Library Manager, Serial Monitor |
| **Language** | C++11/Arduino | — | Standard for ESP32 |
| **Firebase** | [Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client) | ≥ 4.4.x | Full Firebase Realtime DB support — push, set, update, stream, auth |
| **JSON** | ArduinoJson | ≥ 7.x | Payload serialization for Firebase |
| **SD Card** | SD_MMC / SD (ESP32) | Built-in | Local data backup |
| **Display** | Adafruit SSD1306 + Adafruit GFX | Latest | OLED graphics |
| **WiFi** | WiFi.h (Arduino) | Built-in | Station mode, auto-reconnect |
| **NTP** | NTPClient / configTime() | Built-in | Time sync for timestamped data |
| **OTA** | ArduinoOTA | Built-in | Over-the-air firmware updates |

### Firebase-ESP-Client Usage

```cpp
#include <Firebase_ESP_Client.h>

FirebaseData fbData;
FirebaseAuth fbAuth;
FirebaseConfig fbConfig;

// Initialize
fbConfig.api_key = FIREBASE_API_KEY;
fbConfig.database_url = FIREBASE_DATABASE_URL;
fbAuth.user.email = FIREBASE_USER_EMAIL;
fbAuth.user.password = FIREBASE_USER_PASSWORD;

Firebase.begin(&fbConfig, &fbAuth);
Firebase.reconnectWiFi(true);

// Push reading
FirebaseJson json;
json.set("inlet/flow_rate", 12.5);
json.set("inlet/volume", 2.5);
Firebase.pushJSON(fbData, "/readings/device_001", json);

// Stream commands
Firebase.stream(fbData, "/commands/device_001");
if (fbData.streamAvailable()) {
    String cmd = fbData.stringData();
}
```

---

## Firebase Realtime DB

| Feature | Usage |
|---------|-------|
| **Data structure** | JSON tree: `/readings/{device_id}/{timestamp}`, `/alerts/{alert_id}`, `/commands/{device_id}` |
| **Authentication** | Email/Password or Anonymous for ESP32; Service Account for PythonAnywhere |
| **Security Rules** | Validate schema, restrict write paths per device |
| **Streaming** | ESP32 listens on `/commands`, PythonAnywhere listens on `/readings` via Pyrebase4 stream |
| **Storage** | Free tier: 1 GB, 100 simultaneous connections, 10 GB/month bandwidth |
| **Pricing** | Spark (free) is sufficient for 1–5 devices. Blaze (pay-as-you-go) for production. |

> Full schema: [Firebase Realtime DB Schema](./firebase-realtime-db.md)

---

## PythonAnywhere Backend Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Hosting** | PythonAnywhere (paid tier) | — | Always-on Flask app on cloud |
| **Language** | Python | ≥ 3.9 | ML ecosystem, Firebase SDK |
| **Web Framework** | Flask | ≥ 2.x | Web dashboard + REST API endpoints |
| **Firebase Client** | [pyrebase4](https://github.com/nhorvath/Pyrebase4) | ≥ 4.6 | Firebase Real-time DB read/write + stream |
| **ML (primary)** | [XGBoost](https://xgboost.readthedocs.io/) | ≥ 2.0 | Gradient-boosted decision tree — leak classification |
| **ML (anomaly)** | [scikit-learn](https://scikit-learn.org/) (IsolationForest) | ≥ 1.3 | Unsupervised anomaly detection |
| **Data** | pandas, numpy | Latest | Feature engineering |
| **Scheduling** | PythonAnywhere task scheduler | — | Daily model retraining |
| **Templates** | Jinja2 + Chart.js | — | Dashboard HTML/JS |
| **Notifications** | Telegram Bot API / smtplib | — | Alert delivery |

---

## ML Model Stack

| Model | Type | Framework | Task | Where it runs |
|-------|------|-----------|------|--------------|
| **XGBoost** | Gradient-boosted decision tree | xgboost Python | 4-class classification (normal, minor_leak, major_leak, anomaly) | PythonAnywhere |
| **Isolation Forest** | Unsupervised ensemble | scikit-learn | Binary anomaly/not-anomaly | PythonAnywhere |

### Feature Set (9 features)

| Feature | Description | Type | Range |
|---------|-------------|------|-------|
| `flow_rate` | Instantaneous flow rate (L/min) | float | 0–40 |
| `duration_seconds` | Seconds since water started flowing | int | 0–3600 |
| `hour_of_day` | Hour (0–23) | int | 0–23 |
| `day_of_week` | Day (0=Mon) | int | 0–6 |
| `fixture_id` | One-hot encoded fixture | int | 0–4 |
| `inlet_to_fixture_ratio` | Inlet rate ÷ fixture rate | float | 0.5–2.0 |
| `rate_variance` | Flow rate variance (last 10s) | float | 0–10 |
| `is_night_time` | Between 10PM–5AM | bool | 0/1 |
| `pulse_trend` | Slope of pulses (last 5 readings) | float | -∞ to +∞ |

### Target Classes

| Class | Description | Training Labels |
|-------|-------------|-----------------|
| `normal` | Regular water usage (faucet, flush, shower) | Label 0 |
| `minor_leak` | Drip / slow leak (0.1–0.5 L/min sustained >30s) | Label 1 |
| `major_leak` | Burst / stuck valve (>5 L/min for >30s) | Label 2 |
| `anomaly` | Unrecognized pattern / sensor fault | Label 3 (partial labels) |

> See [ML Model](./ml-model.md) for complete model training guide and performance benchmarks.

---

## Web Dashboard Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Flask (Python) — serves HTML + JSON API |
| **Frontend** | HTML5 + CSS3 + Vanilla JS (no framework needed) |
| **Charts** | Chart.js (real-time line/bar charts) |
| **Real-time** | Server-Sent Events (SSE) from Flask, or periodic fetch |
| **Styling** | Bootstrap 5 / Tailwind CSS |
| **Deployment** | PythonAnywhere Web tab — WSGI config |

---

## Communication Summary

| Path | Protocol | Data Format | Frequency |
|------|----------|-------------|-----------|
| Sensor → ESP32 | Pulse (GPIO interrupt) | Rising edge | Continuous |
| ESP32 → Firebase | HTTPS | JSON | Every 5–60s |
| Firebase → ESP32 | SSE (stream) | JSON | Real-time |
| Firebase → PythonAnywhere | SSE (Pyrebase4 stream) | JSON | Real-time |
| PythonAnywhere → Firebase | HTTPS (REST) | JSON | On ML result |
| PythonAnywhere → Dashboard | HTTP (Flask) | HTML/JSON | On page load |
| PythonAnywhere → Firebase | HTTPS (Alert write) | JSON | On leak detection |
| PythonAnywhere → Telegram | HTTPS (Bot API) | Form | On leak alert |

---

## Development Tools

| Tool | Purpose |
|------|---------|
| **Arduino IDE** | Build, upload, and debug ESP32 firmware (C++) |
| **Python 3.9+** | ML training, backend development |
| **Jupyter / Google Colab** | ML model prototyping and experimentation |
| **Firebase Console** | Database management, rules, authentication |
| **PythonAnywhere Console** | Backend debugging, log viewing |
| **Postman** | API testing |
| **Serial Monitor** | ESP32 debug output |
| **Git + GitHub** | Version control |

---

## Stack Decision Matrix

| Requirement | Chosen | Alternatives Considered | Why This Won |
|-------------|--------|------------------------|--------------|
| Real-time DB | Firebase | Custom Node.js server, Supabase, AWS IoT | Managed, free tier, SSE streaming, ESP32 library |
| ESP32 → Cloud | Firebase-ESP-Client | HTTP client, MQTT, Blynk | Full Firebase API (stream + write), well-maintained |
| Python → Firebase | Pyrebase4 | firebase-admin, rest-client | Stream support, PythonAnywhere compatible |
| ML Model | XGBoost | Random Forest, LightGBM, CNN | Best accuracy for tabular time-series, faster than RF, better calibrated probabilities |
| Anomaly Detection | Isolation Forest | Autoencoder, One-Class SVM | Unsupervised, low memory, interpretable |
| Cloud Hosting | PythonAnywhere | Heroku, Railway, AWS Free Tier | Philippine-friendly (no credit card needed for basic), pre-installed pip |
| ESP32 Board | 38-pin NodeMCU-32S | 30-pin, ESP32-C3, ESP8266 | More GPIOs for 5 sensors + relays + peripherals |
