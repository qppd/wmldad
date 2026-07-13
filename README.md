#  WMLDAD

> **A Capstone / Research Project** — Smart Water Monitoring System that detects leaks, anomalies, and per-fixture consumption using ESP32, Firebase, Raspberry Pi, and Machine Learning (XGBoost).

---

##  Project Overview

A complete IoT system that monitors water consumption across multiple fixtures in a building, detects leaks in real-time, and identifies anomalous usage patterns using machine learning on a **Raspberry Pi**.

### How It Works

```text
|[Inlet Flow Sensor] ─┐
|[Fixture 1 Sensor] ──┤
|[Fixture 2 Sensor] ──┤──→ ESP32 → Firebase Realtime DB → RPi (Flask + ML)
|[Fixture 3 Sensor] ──┘                                              ↓
                                    Leak Alert / Dashboard
```

### Key Features

-  **1 Inlet + 3 Fixture Flow Sensors** — total consumption + per-fixture monitoring (bidet, kitchen, bathroom shower)
-  **Fixture-Level Leak Detection** — exactly which fixture is leaking
-  **Real-time Firebase Sync** — data streamed via [Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client)
-  **XGBoost ML Model** — detects leaks, anomalies, and usage patterns (server-side)
-  **Isolation Forest** — unsupervised anomaly detection for unknown patterns
-  **RPi Backend** — Flask + **Pyrebase4** + XGBoost
-  **Check Valves** — prevent backflow between fixtures
-  **Web Dashboard** — real-time monitoring via RPi Flask dashboard (7" touchscreen)
-  **Remote Access** — port forwarding + Dynamic DNS for worldwide access
-  **Local Data Logging** — SPIFFS backup when offline

---

##  System Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                      PLUMBING LAYER                              │
│  Supply → Inlet Sensor → Check Valve → Junction → Fixture 1-3   │
│                                         ↓ (×3)                   │
│                                  [Sensor + Check Valve] → Faucet  │
└──────────────────────────────────────────────────────────────────┘
                               ↓ (pulse signals)
┌──────────────────────────────────────────────────────────────────┐
│                      ESP32 EDGE LAYER                             │
│  • Pulse Counter (4× interrupts, debounced)                       │
│  • Local Feature Extraction (flow rate, volume, duration)         │
│  • Firebase-ESP-Client → Firebase Realtime DB (stream + write)    │
│  • SPIFFS Logger (offline backup)                                 │
└──────────────────────────────────────────────────────────────────┘
                               ↓ (HTTPS/SSE stream)
┌──────────────────────────────────────────────────────────────────┐
│                      CLOUD LAYER                                  │
│   Firebase Realtime Database                                    │
│     - /readings/{device_id}/{timestamp} → raw sensor data        │
│     - /alerts/{alert_id} → leak events                           │
│     - /commands/{device_id} → device commands                    │
│     - /models/{version} → ML model metadata                      │
└──────────────────────────────────────────────────────────────────┘
                               ↓ (Pyrebase4 polling)
┌──────────────────────────────────────────────────────────────────┐
│                      RPi BACKEND                                  │
│  • Pyrebase4 — Firebase polling + writes                          │
│  • XGBoost Model — leak classification (normal/minor/major)      │
│  • Isolation Forest — unsupervised anomaly detection             │
│  • Flask Web App — dashboard + API endpoints                     │
│  • Alert Engine — Telegram notifications                         │
│  • Daily Retraining Pipeline — model improvement over time       │
└──────────────────────────────────────────────────────────────────┘
                               ↓ (Port forwarding + DDNS)
┌──────────────────────────────────────────────────────────────────┐
│                      USER LAYER                                   │
│  • Web Dashboard (local: 7" touchscreen, remote: port forward)   │
│  • Telegram / Email Alerts                                        │
│  • Remote Device Control                                          │
└──────────────────────────────────────────────────────────────────┘
```

---

##  Complete Documentation

| Document | Description |
|----------|-------------|
| [System Architecture](./docs/system-architecture.md) | Detailed architecture with Mermaid diagrams |
| [Flowchart](./docs/flowchart.md) | System flow, data flow, ML pipeline |
| [Block Diagram](./docs/block-diagram.md) | Hardware connections, pinout, enclosure layout |
| [Technology Stack](./docs/stacks.md) | Full tech stack with versions and justifications |
| [Firebase Realtime DB Schema](./docs/firebase-realtime-db.md) | Complete Firebase database structure |
| [ML Model](./docs/ml-model.md) | XGBoost + Isolation Forest — training, features, deployment |
| [Firmware Guide](./docs/firmware.md) | ESP32 code structure, Firebase-ESP-Client usage |
| [Setup Guide](./docs/setup.md) | Step-by-step from zero to working system |
| [Calibration Guide](./docs/calibration.md) | Sensor calibration procedures |
| [RPi Backend App](./docs/rpi-backend.md) | Deploying the backend on Raspberry Pi |
| [Bill of Materials](./docs/bom.md) | Complete parts list with prices & links (Makerlab) |
| [Troubleshooting](./docs/troubleshooting.md) | Common issues and solutions |
| [Project Timeline](./docs/project-timeline.md) | Student capstone timeline with milestones |

---

##  ML Model Summary

**Primary:** [XGBoost](./docs/ml-model.md) — gradient-boosted decision trees
- 9 input features (flow rate, duration, time patterns, fixture ID, etc.)
- 3 output classes: `normal`, `minor_leak`, `major_leak`
- Accuracy target: ≥ 95%
- Trained on RPi, served via Flask API

**Secondary:** Isolation Forest — catches unknown/unseen anomaly patterns
- Unsupervised — no training labels needed
- Flags data points that don't match normal usage patterns

---

##  Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/qppd/wmldad.git
cd wmldad

# 2. Set up Firebase
#    - Create a Firebase project
#    - Enable Realtime Database
#    - Download service account JSON (for ESP32)
#    - Configure Firebase credentials in ESP32 firmware
#    - Create email/password user for Pyrebase4 (RPi)

# 3. Upload ESP32 firmware (Arduino IDE)
#    - Open src/water-meter.ino in Arduino IDE
#    - Select board: Tools -> Board -> ESP32 Arduino -> NodeMCU-32S
#    - Select port: Tools -> Port -> COMx
#    - Click Sketch -> Upload (Ctrl+U)

# 4. Deploy RPi backend
#    - Set up Raspberry Pi with Python 3.11+
#    - Install dependencies: pip install -r rpi/requirements.txt
#    - Copy firebase_config.json to rpi/
#    - Run Flask app on RPi
#    (Or use systemd service for auto-start)

# 5. Train the model
#    - Upload training/water_meter_ml_training.ipynb to Google Colab
#    - Run all cells (Runtime -> Run all)
#    - Trained models are saved to model/ folder
```

See [Setup Guide](./docs/setup.md) for complete step-by-step instructions.

---

##  Hardware Requirements (Minimum)

| Item | Qty | Estimated Cost (₱) |
|------|-----|-------------------|
| ESP32 38-Pin Dev Board | 1 | ₱450 |
| ESP32 38-Pin Expansion Board | 1 | ₱180 |
| YF-S201 Flow Sensor | 4 | ₱720 |
| Check Valve 1/2" | 3 | ₱360 |
| Breadboard + Jumpers | 1 set | ₱150 |
| 5V Power Adapter + USB Cable | 1 | ₱250 |
| **TOTAL** | | **~₱2,110** |

> Full BOM with links, alternatives, and pricing tiers: [BOM.md](./docs/bom.md)

---

##  Project Structure

```text
wmldad/
├── docs/                     # Complete documentation (14 files)
│   ├── system-architecture.md
│   ├── flowchart.md
│   ├── block-diagram.md
│   ├── stacks.md
│   ├── firebase-realtime-db.md
│   ├── ml-model.md
│   ├── firmware.md
│   ├── setup.md
│   ├── calibration.md
│   ├── rpi-backend.md
│   ├── bom.md
│   ├── troubleshooting.md
│   └── project-timeline.md
├── src/                      # ESP32 firmware (Arduino C++ / .ino)
│   ├── water-meter.ino          # Main Arduino sketch
│   ├── config.h                 # WiFi, Firebase, sensor config
│   ├── sensor_manager.h         # 4 sensor ISR management
│   ├── flow_sensor.h            # Pulse counter class
│   ├── firebase_client.h        # Firebase-ESP-Client wrapper
│   ├── local_rules.h            # Offline leak detection
│   ├── wifi_manager.h           # WiFi connect + reconnect
│   ├── data_logger.h            # SPIFFS logging
│   ├── alert_manager.h          # Buzzer + LED alerts
│   ├── ntp_sync.h               # NTP time sync
│   ├── ota_updater.h            # OTA firmware updates
│   └── led_indicator.h          # Status LED patterns
├── rpi/                  # RPi backend (Flask + ML)
│   ├── app.py                # Flask web app
│   ├── firebase_listener.py  # Pyrebase4 polling
│   ├── ml_inference.py       # XGBoost + Isolation Forest
│   ├── alert_engine.py       # Notification system
│   ├── models/               # Trained models
│   │   ├── xgboost_model.json
│   │   └── isolation_forest.pkl
│   ├── templates/            # Jinja2 HTML templates
│   ├── static/               # CSS, JS, Chart.js
│   ├── requirements.txt
│   ├── firebase_config.json  # Pyrebase4 config (gitignored)
│   └── water-meter.service   # systemd service file
├── training/                  # ML training notebooks
│   ├── water_meter_ml_training.ipynb   # Main training notebook (Colab/Jupyter)
│   └── requirements.txt                # Dependencies for local runs
├── model/                    # Trained models
│   ├── xgboost_model.json
│   └── isolation_forest.pkl
├── wiring/                  # CAD, Fritzing, enclosure designs
│   └── water-meter-wiring.fzz
└── README.md
```

---

##  Remote Access (Port Forwarding + DDNS)

The RPi dashboard is accessible locally on the 7" touchscreen. For **remote access from anywhere with internet**:

### 1. Router Port Forwarding

| Setting | Value |
|---------|-------|
| **External Port** | 8443 (or any unused port) |
| **Internal IP** | Raspberry Pi's local IP (e.g., 192.168.1.100) |
| **Internal Port** | 5000 |
| **Protocol** | TCP |

**Example (TP-Link/Asus/Netgear):**
1. Access router admin (usually 192.168.1.1 or 192.168.0.1)
2. Go to **Advanced → NAT Forwarding → Port Forwarding / Virtual Server**
3. Add rule:
   - Service Name: `WaterMeter`
   - External Port: `8443`
   - Internal IP: `<rpi-local-ip>`
   - Internal Port: `5000`
   - Protocol: `TCP`
4. Save and apply

### 2. Static DHCP Reservation (Recommended)

Reserve a fixed IP for the RPi in router's DHCP settings so port forwarding doesn't break after reboot.

### 3. Dynamic DNS (Optional but Recommended)

If your ISP doesn't provide a static public IP:

**Option A: DuckDNS (Free)**
```bash
# Create account at duckdns.org
# Get token, then:
curl "https://www.duckdns.org/update?domains=yourdomain&token=yourtoken&ip="
# Add to cron for auto-update:
crontab -e
# */5 * * * * curl "https://www.duckdns.org/update?domains=yourdomain&token=yourtoken&ip="
```

**Option B: Cloudflare Tunnel (Best for HTTPS)**
```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb
# Authenticate: cloudflared tunnel login
# Create tunnel: cloudflared tunnel create water-meter
# Route: cloudflared tunnel route dns water-meter yourdomain.com
# Run as service
```

### 4. Access from Anywhere

- **Local:** `http://<rpi-local-ip>:5000/`
- **Remote:** `http://yourdomain.duckdns.org:8443/` or `https://yourdomain.com` (if Cloudflare Tunnel)

### 5. Security Considerations

| Measure | Implementation |
|---------|----------------|
| **HTTPS** | Use Cloudflare Tunnel (free SSL) or Caddy/Nginx reverse proxy with Let's Encrypt |
| **Authentication** | Add basic auth or Flask-Login to dashboard |
| **Firewall** | `sudo ufw allow 5000/tcp` (local), block unnecessary ports |
| **Fail2Ban** | `sudo apt install fail2ban` — protect against brute force |
| **Change default port** | Use non-standard external port (e.g., 8443 instead of 5000) |

---

## ‍ For Students

This project is designed as a **complete capstone / thesis project**. See:

- **[Project Timeline](./docs/project-timeline.md)** — 16-week breakdown with milestones
- **[Setup Guide](./docs/setup.md)** — step-by-step from parts to working system
- **[ML Model](./docs/ml-model.md)** — theory and implementation details
- **[Troubleshooting](./docs/troubleshooting.md)** — solutions to common problems

---

##  License

MIT

## ‍ Author

[qppd](https://github.com/qppd) — Quezon Province, Philippines