# System Architecture

## Overview

Smart water monitoring system with **fixture-level leak detection** using **ESP32 → Firebase → RPi → XGBoost ML**.

The system uses 1 inlet flow sensor to measure total consumption and 3 fixture flow sensors to monitor individual water outlets (bidet, kitchen, bathroom shower). Data flows from the ESP32 to Firebase Realtime DB via the [Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client) library (stream + regular calls). A **Raspberry Pi** backend consumes the Firebase data using **Pyrebase4**, runs **XGBoost** and **Isolation Forest** ML models, and serves a web dashboard on the 7" touchscreen LCD.

---

## Architecture Diagram

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
graph TB
    subgraph "Plumbing Layer"
        A[Main Water Supply] --> B[Inlet Flow Sensor<br/>YF-S201]
        B --> C[Check Valve]
        C --> D[Junction]
        D --> E1[Fixture 1 Sensor]
        D --> E2[Fixture 2 Sensor]
        D --> E3[Fixture 3 Sensor]
        E1 --> CV1[Check Valve] --> F1[Fixture 1]
        E2 --> CV2[Check Valve] --> F2[Fixture 2]
        E3 --> CV3[Check Valve] --> F3[Fixture 3]
    end

    subgraph "ESP32 Edge Layer"
        direction TB
        Sensors["4× Flow Sensor<br/>Pulse Counters<br/>(ISR + Debounce)"]
        Features["Feature Extractor<br/>flow_rate, volume,<br/>duration, time, ratio"]
        FirebaseClient["Firebase-ESP-Client<br/>Stream + Write"]
        LocalCtrl["Local Leak Rules"]
        SPIFFS["SPIFFS Logger<br/>(Offline Backup)"]
        
        Sensors --> Features
        Features --> FirebaseClient
        Features --> LocalCtrl
        Sensors --> SPIFFS
    end

    subgraph "Firebase Realtime DB"
        direction TB
        Readings["/readings/{device_id}/{ts}<br/>Raw sensor data"]
        Alerts["/alerts/{alert_id}<br/>Leak events"]
        Commands["/commands/{device_id}<br/>Device commands"]
        Models["/models/{version}<br/>ML metadata"]
    end

    subgraph "RPi Backend"
        direction TB
        FBAdmin["Pyrebase4<br/>(Poll + Write)"]
        XGB["XGBoost Classifier<br/>normal / minor_leak / major_leak"]
        ISO["Isolation Forest<br/>Unsupervised Anomaly Detection"]
        Flask["Flask Web App<br/>Dashboard + API"]
        AlertEngine["Alert Engine<br/>Email / Telegram"]
        Retrain["Daily Retrain Pipeline"]
        
        FBAdmin --> XGB
        FBAdmin --> ISO
        XGB --> Flask
        ISO --> Flask
        Flask --> AlertEngine
        Flask --> Retrain
    end

    subgraph "User Layer"
        Dashboard["Web Dashboard<br/>Real-time Charts"]
        Notif["Telegram / Email<br/>Alerts"]
        Cmd["Remote Device<br/>Control"]
    end

    B --> Sensors
    E1 --> Sensors
    E2 --> Sensors
    E3 --> Sensors
    
    FirebaseClient --> Readings
    FirebaseClient --> Alerts
    Commands --> FirebaseClient
    
    Readings --> FBAdmin
    Alerts --> FBAdmin
    Commands --> FBAdmin
    
    Flask --> Dashboard
    AlertEngine --> Notif
    Dashboard --> Cmd
    Cmd --> Commands
```

</details>

---

## Data Flow (End-to-End)

```
Step 1: SENSING
        Inlet Sensor (GPIO 34)  ─┐
        Fixture 1 Sensor (35)   ─┤  Every 1 second:
        Fixture 2 Sensor (32)   ─┤  → Read pulse count via ISR
        Fixture 3 Sensor (33)   ─┘  → Debounce (5ms)
                                    → Calculate flow rate & volume

Step 2: LOCAL PROCESSING
        For each fixture:
        → flow_rate = (pulse_count * 60) / (PPL * interval_s)
        → volume = pulse_count / PPL
        → total_liters += volume
        → Inlet balance = inlet_volume - sum(fixtures_volume)

Step 3: FIREBASE UPLOAD (every 5–60 seconds via Firebase-ESP-Client)
        → Write to /readings/{device_id}/{timestamp}
        → Stream listener for /commands/{device_id}

Step 4: RPi PROCESSING (polling via Pyrebase4)
        → Poll /readings/{device_id} for new data
        → Extract features for ML
        → Run XGBoost inference
        → Run Isolation Forest anomaly score
        → If leak detected → write to /alerts/ + trigger notification

Step 5: USER ACTION
        → Dashboard displays real-time readings
        → Telegram / Email alert sent
        → User sends command → /commands/{device_id}
        → ESP32 Firebase listener receives command → executes action
```

---

## Communication Paths

| Path | Method | Protocol | Library |
|------|--------|----------|---------|
| ESP32 → Firebase | Write + Stream | HTTPS/SSE | Firebase-ESP-Client |
| Firebase → ESP32 | Stream Listener | Server-Sent Events | Firebase-ESP-Client |
| RPi → Firebase | Read + Write | REST (Pyrebase4) | Pyrebase4 |
| Firebase → RPi | Poll (HTTP) | REST | Pyrebase4 |
| User → Dashboard | HTTP/WebSocket | HTTPS | Flask + JavaScript |
| Dashboard → Commands | Write to /commands | HTTPS | Fetch API |
| RPi → Firebase | HTTPS (Alert write) | JSON | On leak detection |
| RPi → Telegram | HTTPS (Bot API) | Form | On leak alert |
| **Remote → RPi** | **HTTPS (port forward)** | **HTML/JSON** | **On demand** |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Firebase over custom server** | Managed real-time DB, built-in auth, no server maintenance |
| **Firebase-ESP-Client** | Most mature Firebase library for ESP32, supports streaming (SSE) |
| **Pyrebase4** | Email/Password auth, client-style API, works on RPi |
| **RPi over cloud hosting** | Local processing — no monthly fees, full control, no internet dependency for LAN dashboard |
| **Isolation Forest + XGBoost** | XGBoost for known leak patterns, Isolation Forest for unknown anomalies |
| **Check Valves per Fixture** | Prevents backflow contamination between fixtures |
| **SPIFFS Backup** | Survives WiFi/Firebase outages — data never lost |
| **Port Forwarding + DDNS** | Remote access anywhere with internet; standard router feature |