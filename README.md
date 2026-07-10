#  Water Meter with Leak Detection & Anomaly Detection System

> **A Capstone / Research Project** — Smart Water Monitoring System that detects leaks, anomalies, and per-fixture consumption using ESP32, Firebase, PythonAnywhere, and Machine Learning (XGBoost).

---

##  Project Overview

A complete IoT system that monitors water consumption across multiple fixtures in a building, detects leaks in real-time, and identifies anomalous usage patterns using machine learning.

### How It Works

```
[Inlet Flow Sensor] ─┐
[Fixture 1 Sensor] ──┤
[Fixture 2 Sensor] ──┤──→ ESP32 → Firebase Realtime DB → PythonAnywhere → XGBoost ML
[Fixture 3 Sensor] ──┤                                              ↓
[Fixture 4 Sensor] ──┘                                    Leak Alert / Dashboard
```

### Key Features

-  **1 Inlet + 4 Fixture Flow Sensors** — total consumption + per-fixture monitoring
-  **Fixture-Level Leak Detection** — exactly which fixture is leaking
-  **Real-time Firebase Sync** — data streamed via [Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client)
-  **XGBoost ML Model** — detects leaks, anomalies, and usage patterns (server-side)
-  **Isolation Forest** — unsupervised anomaly detection for unknown patterns
-  **PythonAnywhere Backend** — connects to Firebase via Pyrebase4
-  **Check Valves** — prevent backflow between fixtures
-  **Web Dashboard** — real-time monitoring via PythonAnywhere web app
-  **Solenoid Valve Control** — automatic shutoff on leak detection
-  **Local Data Logging** — SD card backup when offline

---

##  System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      PLUMBING LAYER                              │
│  Supply → Inlet Sensor → Check Valve → Junction → Fixture 1-4   │
│                                         ↓ (×4)                   │
│                                  [Sensor + Check Valve] → Faucet  │
└──────────────────────────────────────────────────────────────────┘
                               ↓ (pulse signals)
┌──────────────────────────────────────────────────────────────────┐
│                      ESP32 EDGE LAYER                             │
│  • Pulse Counter (5× interrupts, debounced)                       │
│  • Local Feature Extraction (flow rate, volume, duration)         │
│  • Firebase-ESP-Client → Firebase Realtime DB (stream + write)    │
│  • OLED Display (live readings per fixture)                       │
│  • Relay Control (5× solenoid valves for shutoff)                 │
│  • SD Card Logger (offline backup)                                │
└──────────────────────────────────────────────────────────────────┘
                               ↓ (HTTPS/SSE stream)
┌──────────────────────────────────────────────────────────────────┐
│                      CLOUD LAYER                                  │
│   Firebase Realtime Database                                    │
│     - /readings/{device_id}/{timestamp} → raw sensor data        │
│     - /alerts/{alert_id} → leak events                           │
│     - /commands/{device_id} → valve control from dashboard       │
│     - /models/{version} → ML model metadata                      │
└──────────────────────────────────────────────────────────────────┘
                               ↓ (Pyrebase4 stream + REST)
┌──────────────────────────────────────────────────────────────────┐
│                      PYTHONANYWHERE ( Backend)                   │
│  • Pyrebase4 — Firebase listener (real-time stream)               │
│  • XGBoost Model — leak classification (normal/minor/major)      │
│  • Isolation Forest — unsupervised anomaly detection             │
│  • Flask Web App — dashboard + API endpoints                     │
│  • Alert Engine — email/SMS/Telegram notifications               │
│  • Daily Retraining Pipeline — model improvement over time       │
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
| [PythonAnywhere App](./docs/pythonanywhere-app.md) | Deploying the backend on PythonAnywhere |
| [Bill of Materials](./docs/bom.md) | Complete parts list with prices & links (Makerlab) |
| [Troubleshooting](./docs/troubleshooting.md) | Common issues and solutions |
| [Project Timeline](./docs/project-timeline.md) | Student capstone timeline with milestones |

---

##  ML Model Summary

**Primary:** [XGBoost](./docs/ml-model.md) — gradient-boosted decision trees
- 9 input features (flow rate, duration, time patterns, fixture ID, etc.)
- 4 output classes: `normal`, `minor_leak`, `major_leak`, `anomaly`
- Accuracy target: ≥ 95%
- Trained on PythonAnywhere, served via Flask API

**Secondary:** Isolation Forest — catches unknown/unseen anomaly patterns
- Unsupervised — no training labels needed
- Flags data points that don't match normal usage patterns

---

##  Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/qppd/water-meter.git
cd water-meter

# 2. Set up Firebase
#    - Create a Firebase project
#    - Enable Realtime Database
#    - Download service account JSON
#    - Configure Firebase credentials in ESP32 firmware

# 3. Upload ESP32 firmware (Arduino IDE)
#    - Open src/water-meter.ino in Arduino IDE
#    - Select board: Tools -> Board -> ESP32 Arduino -> NodeMCU-32S
#    - Select port: Tools -> Port -> COMx
#    - Click Sketch -> Upload (Ctrl+U)

# 4. Deploy PythonAnywhere backend
#    - Upload the pythonanywhere/ folder to PythonAnywhere
#    - Configure Pyrebase4 with your Firebase credentials
#    - Set up Flask web app

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
| YF-S201 Flow Sensor | 5 | ₱900 |
| Check Valve 1/2" | 4 | ₱480 |
| Breadboard + Jumpers | 1 set | ₱150 |
| 5V Power Adapter + USB Cable | 1 | ₱250 |
| **TOTAL** | | **~₱2,410** |

> Full BOM with links, alternatives, and pricing tiers: [BOM.md](./docs/bom.md)

---

##  Project Structure

```
water-meter/
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
│   ├── pythonanywhere-app.md
│   ├── bom.md
│   ├── troubleshooting.md
│   └── project-timeline.md
├── src/                      # ESP32 firmware (Arduino C++ / .ino)
│   ├── water-meter.ino          # Main Arduino sketch
│   ├── config.h                 # WiFi, Firebase, sensor config
│   ├── sensor_manager.h         # 5 sensor ISR management
│   ├── flow_sensor.h            # Pulse counter class
│   ├── firebase_client.h        # Firebase-ESP-Client wrapper
│   ├── local_rules.h            # Offline leak detection
│   ├── valve_controller.h       # Relay/solenoid control
│   ├── wifi_manager.h           # WiFi connect + reconnect
│   ├── data_logger.h            # SD card + SPIFFS logging
│   ├── display_manager.h        # OLED 128x64
│   ├── alert_manager.h          # Buzzer + LED alerts
│   ├── ntp_sync.h               # NTP time sync
│   └── led_indicator.h          # Status LED patterns
├── pythonanywhere/           # PythonAnywhere backend
│   ├── app.py                # Flask web app
│   ├── firebase_listener.py  # Pyrebase4 stream listener
│   ├── ml_inference.py       # XGBoost + Isolation Forest
│   ├── alert_engine.py       # Notification system
│   └── requirements.txt
├── training/                  # ML training notebooks
│   ├── water_meter_ml_training.ipynb   # Main training notebook (Colab/Jupyter)
│   └── requirements.txt                # Dependencies for local runs
├── model/                    # Trained models
│   ├── xgboost_model.json
│   └── isolation_forest.pkl
├── hardware/                  # CAD, Fritzing, enclosure designs
│   └── water-meter-wiring.fzz
└── README.md
```

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
