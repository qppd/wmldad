# System Architecture

## Overview

Smart water monitoring system with **fixture-level leak detection**. Uses 1 inlet flow sensor + 4 fixture flow sensors to detect leaks and anomalies via a Random Forest machine learning model.

## Architecture Diagram

```mermaid
graph TB
    subgraph "Water Supply"
        A[Main Water Line] --> B[Inlet Flow Sensor]
        B --> C[Check Valve]
        C --> D{Junction}
    end
    
    subgraph "Fixture Sensors"
        D --> E[Fixture 1 Sensor]
        D --> F[Fixture 2 Sensor]
        D --> G[Fixture 3 Sensor]
        D --> H[Fixture 4 Sensor]
        E --> E1[Check Valve]
        F --> F1[Check Valve]
        G --> G1[Check Valve]
        H --> H1[Check Valve]
        E1 --> I1[Faucet / Toilet / Fixture 1]
        F1 --> I2[Faucet / Toilet / Fixture 2]
        G1 --> I3[Faucet / Toilet / Fixture 3]
        H1 --> I4[Faucet / Toilet / Fixture 4]
    end
    
    subgraph "ESP32 Edge Node"
        J[Inlet Pulse Counter]
        K[Fixture 1 Pulse Counter]
        L[Fixture 2 Pulse Counter]
        M[Fixture 3 Pulse Counter]
        N[Fixture 4 Pulse Counter]
        O[Feature Extractor]
        P[Random Forest Classifier]
        Q[Relay Controller]
        R[Solenoid Valves]
        
        B --> J
        E --> K
        F --> L
        G --> M
        H --> N
        
        J --> O
        K --> O
        L --> O
        M --> O
        N --> O
        
        O --> P
        P -->|Leak Detected| Q
        Q --> R
    end
    
    subgraph "Communication"
        O --> S[WiFi Module]
        S --> T{Protocol}
        T -->|HTTP REST| U[Backend API]
        T -->|MQTT| V[MQTT Broker]
    end
    
    subgraph "Cloud / Backend"
        U --> W[API Server]
        V --> W
        W --> X[Database]
        W --> Y[Notification Service]
        X --> Z[Retrain Pipeline]
        Z --> Z2[Improved Model → ESP32 OTA]
    end
    
    subgraph "Dashboard"
        X --> AA[Web Dashboard]
        Y --> AB[Alerts / Telegram / SMS]
        AA --> AC[User]
    end
```

## System Flow

1. **Inlet sensor** measures total water entering the system
2. **4 fixture sensors** measure individual consumption per fixture
3. **ESP32** reads all 5 sensors via hardware interrupts
4. **Feature extraction** computes per-fixture metrics: flow rate, duration, start/end times, daily patterns
5. **Random Forest model** (TFLite Micro) classifies each event as:
   - ✅ Normal usage
   - ⚠️ Minor leak (drip)
   - 🚨 Major leak (burst / stuck valve)
   - ❓ Anomaly (unrecognized pattern)
6. **If leak detected** → ESP32 triggers relay → closes solenoid valve on that fixture
7. **Data logged** locally (SD card) and uploaded to server
8. **Backend** stores readings, retrains model periodically, sends alerts

## ML Pipeline

```mermaid
flowchart LR
    A[Raw Pulse Data<br/>×5 sensors] --> B[Feature Extraction]
    B --> C[Feature Vector<br/>flow_rate, duration, hour,<br/>day_of_week, fixture_id,<br/>inlet-to-fixture ratio]
    C --> D[Random Forest Model<br/>TFLite Micro]
    D --> E{Classification}
    E -->|Normal| F[Log + Continue]
    E -->|Minor Leak| G[Alert + Valve Shutoff]
    E -->|Major Leak| H[Alert + Valve Shutoff + Alarm]
    E -->|Anomaly| I[Flag for Review]
```

## Key Features

- **Real-time monitoring** — 5 flow sensors read simultaneously via interrupts
- **Fixture-level leak detection** — identify exactly which fixture is leaking
- **Check valves** prevent backflow between fixtures
- **Solenoid shutoff** — automatic valve closure on leak detection
- **ML-powered** — Random Forest model tuned for water usage patterns
- **Local + Cloud** — runs on ESP32 edge; backend for dashboard and retraining
- **OTA updates** — model and firmware updates over the air
