# Technology Stack — Water Meter with Leak Detection

> **Architecture:** Sensors → ESP32 → Firebase Realtime DB → RPi → XGBoost → Dashboard (7" touchscreen LCD on RPi + remote via port forwarding)

---

## ESP32 Firmware Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Framework** | Arduino framework (esp32 core) | ≥ 2.0.x | Mature, well-documented, large ecosystem |
| **IDE** | Arduino IDE 2.x | Latest | ESP32 board support, Library Manager, Serial Monitor |
| **Language** | C++11/Arduino | — | Standard for ESP32 |
| **Firebase** | [Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client) | ≥ 4.4.x | Full Firebase Realtime DB support — push, set, update, stream, auth |
| **JSON** | ArduinoJson | ≥ 7.x | Payload serialization for Firebase |
| **WiFi** | WiFi.h (Arduino) | Built-in | Station mode, auto-reconnect |
| **NTP** | NTPClient / configTime() | Built-in | Time sync for timestamped data |
| **OTA** | ArduinoOTA | Built-in | Over-the-air firmware updates |

### Firebase-ESP-Client Usage

```cpp
#include <Firebase_ESP_Client.h>

FirebaseData fbData;
FirebaseData fbStream;
FirebaseAuth fbAuth;
FirebaseConfig fbConfig;

unsigned long dataMillis = 0;
bool streamCommand = false;

void setupFirebase() {
    fbConfig.api_key = FIREBASE_API_KEY;
    fbConfig.database_url = FIREBASE_DATABASE_URL;
    
    // Sign-in method: Email/Password
    fbAuth.user.email = FIREBASE_USER_EMAIL;
    fbAuth.user.password = FIREBASE_USER_PASSWORD;
    
    // Token callback
    fbConfig.token_status_callback = tokenStatusCallback;
    
    Firebase.begin(&fbConfig, &fbAuth);
    Firebase.reconnectWiFi(true);
    
    // Set buffer size for large payloads
    fbData.setResponseSize(1024);
    fbStream.setResponseSize(1024);
    
    // Start command stream
    String streamPath = "/commands/" + String(DEVICE_ID);
    if (Firebase.RTDB.beginStream(&fbStream, streamPath)) {
        Serial.println("Firebase stream started on: " + streamPath);
    }
}
```

---

## Firebase Realtime DB

| Feature | Usage |
|---------|-------|
| **Data structure** | JSON tree: `/readings/{device_id}/{timestamp}`, `/alerts/{alert_id}`, `/commands/{device_id}` |
| **Authentication** | Email/Password for ESP32 and RPi (Pyrebase4); Anonymous for ESP32 optional |
| **Security Rules** | Validate schema, restrict write paths per device |
| **Streaming** | ESP32 listens on `/commands`, RPi polls `/readings` via Pyrebase4 |
| **Storage** | Free tier: 1 GB, 100 simultaneous connections, 10 GB/month bandwidth |
| **Pricing** | Spark (free) is sufficient for 1–5 devices. Blaze (pay-as-you-go) for production. |

> Full schema: [Firebase Realtime DB Schema](./firebase-realtime-db.md)

---

## Raspberry Pi Backend Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Hardware** | Raspberry Pi 3B+/4/5 | — | Local always-on Flask server, ML inference |
| **OS** | Raspberry Pi OS (64-bit) | Bookworm | Stable Linux distribution for ARM |
| **Language** | Python | ≥ 3.11 | ML ecosystem, Firebase SDK |
| **Web Framework** | Flask | ≥ 2.x | Web dashboard + REST API endpoints |
| **Firebase Client** | [Pyrebase4](https://github.com/nhorvath/Pyrebase4) | ≥ 4.5 | Firebase Realtime DB read/write via Email/Password auth |
| **ML (primary)** | [XGBoost](https://xgboost.readthedocs.io/) | ≥ 2.0 | Gradient-boosted decision tree — leak classification |
| **ML (anomaly)** | [scikit-learn](https://scikit-learn.org/) (IsolationForest) | ≥ 1.3 | Unsupervised anomaly detection |
| **Data** | pandas, numpy | Latest | Feature engineering |
| **Scheduling** | systemd + cron | Built-in | Daily model retraining via cron |
| **Templates** | Jinja2 + Chart.js | — | Dashboard HTML/JS |

---

## ML Model Stack

| Model | Type | Framework | Task | Where it runs |
|-------|------|-----------|------|--------------|
| **XGBoost** | Gradient-boosted decision tree | xgboost Python | 3-class classification (normal, minor_leak, major_leak) | RPi (Flask) |
| **Isolation Forest** | Unsupervised ensemble | scikit-learn | Binary anomaly/not-anomaly | RPi (Flask) |

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
| **Deployment** | RPi Flask — systemd service |
| **Remote Access** | **Port forwarding** (router) + Dynamic DNS (optional) |

---

## Communication Summary

| Path | Protocol | Data Format | Frequency |
|------|----------|-------------|-----------|
| Sensor → ESP32 | Pulse (GPIO interrupt) | Rising edge | Continuous |
| ESP32 → Firebase | HTTPS | JSON | Every 5–60s |
| Firebase → ESP32 | SSE (stream) | JSON | Real-time |
| Firebase → RPi | Poll (HTTP) | REST (Pyrebase4) | On load / every 5s |
| RPi → Firebase | HTTPS (REST) | JSON | On ML result |
| RPi → Dashboard | HTTP (Flask) | HTML/JSON | On page load |
| RPi → Firebase | HTTPS (Alert write) | JSON | On leak detection |
| RPi → Telegram | HTTPS (Bot API) | Form | On leak alert |
| **Remote → RPi** | **HTTPS (port forward)** | **HTML/JSON** | **On demand** |

---

## Development Tools

| Tool | Purpose |
|------|---------|
| **Arduino IDE** | Build, upload, and debug ESP32 firmware (C++) |
| **Python 3.11+** | ML training, backend development |
| **Jupyter / Google Colab** | ML model prototyping and experimentation |
| **Firebase Console** | Database management, rules, authentication |
| **RPi console (ssh)** | Backend debugging, log viewing |
| **Serial Monitor** | ESP32 debug output |
| **Git + GitHub** | Version control |

---

## Stack Decision Matrix

| Requirement | Chosen | Alternatives Considered | Why This Won |
|-------------|--------|------------------------|--------------|
| Firebase | Custom Node.js server, Supabase, AWS IoT | Managed, free tier, SSE streaming, ESP32 library |
| Firebase-ESP-Client | HTTP client, MQTT, Blynk | Full Firebase API (stream + write), well-maintained |
| **Pyrebase4** | firebase-admin | Email/Password auth, client-style API, works on RPi |
| XGBoost | Random Forest, LightGBM, CNN | Best for tabular time-series |
| Isolation Forest | Autoencoder, One-Class SVM | Unsupervised, low memory |
| RPi (Raspberry Pi) | Heroku, Railway, cloud VPS | One-time cost, no monthly fees, full local control |
| ESP32 38-pin NodeMCU-32S | 30-pin, ESP32-C3, ESP8266 | More GPIOs for 5 sensors + peripherals |
| **Port Forwarding + DDNS** | Tailscale, ngrok, Cloudflare Tunnel | No third-party dependency, standard router feature |