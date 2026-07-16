# System Architecture

## Overview

Smart water monitoring system with **fixture-level leak detection** using **ESP32 → USB Serial → RPi → XGBoost ML**.

The system uses 1 inlet flow sensor to measure total consumption and 3 fixture flow sensors to monitor individual water outlets (bidet, kitchen, bathroom shower). Data flows from the ESP32 to Raspberry Pi via **USB Serial (CDC/ACM)** at 921600 baud. A **Raspberry Pi** backend consumes the serial data using **pyserial**, runs **XGBoost** and **Isolation Forest** ML models, and serves a web dashboard on the 7" touchscreen LCD.

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
        SerialOut["USB Serial Output<br/>JSON Lines<br/>(921600 baud)"]
        LocalCtrl["Local Leak Rules<br/>(Threshold-based)"]
        SPIFFS["SPIFFS Logger<br/>(Offline Buffer)"]
        
        Sensors --> SerialOut
        Sensors --> LocalCtrl
        Sensors --> SPIFFS
        LocalCtrl --> SerialOut
    end

    subgraph "USB Connection"
        USB[USB Cable<br/>CDC/ACM Device<br/>(/dev/ttyUSB0)]
    end

    subgraph "RPi Backend"
        direction TB
        SerialReader["Serial Reader<br/>(pyserial / asyncio)"]
        Parser["JSON Parser<br/>Validate + Normalize"]
        XGB["XGBoost Classifier<br/>normal / minor_leak / major_leak"]
        ISO["Isolation Forest<br/>Unsupervised Anomaly Detection"]
        Flask["Flask Web App<br/>Dashboard + API"]
        AlertEngine["Alert Engine<br/>In-App + Webhook"]
        Retrain["Daily Retrain Pipeline"]
        DB["SQLite / InfluxDB<br/>Time-series Storage"]
        
        SerialReader --> Parser
        Parser --> XGB
        Parser --> ISO
        Parser --> DB
        XGB --> Flask
        ISO --> Flask
        Flask --> AlertEngine
        Flask --> Retrain
        DB --> Flask
    end

    subgraph "User Layer"
        Dashboard["Web Dashboard<br/>Real-time Charts"]
        Notif["In-App + Webhook<br/>Alerts"]
        Cmd["Remote Device<br/>Control (via Serial)"]
    end

    B --> Sensors
    E1 --> Sensors
    E2 --> Sensors
    E3 --> Sensors
    
    SerialOut --> USB
    USB --> SerialReader
    
    Flask --> Dashboard
    AlertEngine --> Notif
    Dashboard --> Cmd
    Cmd --> SerialReader
```

</details>

---

## Data Flow (End-to-End)

```
Step 1: SENSING
        Inlet Sensor (GPIO 26)  
        Fixture 1 Sensor (25)   
        Fixture 2 Sensor (33)   
        Fixture 3 Sensor (32)   
        Every 1 second:
        → Read pulse count via ISR
        → Debounce (5ms)
        → Calculate flow rate & volume

Step 2: LOCAL PROCESSING
        For each fixture:
        → flow_rate = (pulse_count * 60) / (PPL * interval_s)
        → volume = pulse_count / PPL
        → total_liters += volume
        → Inlet balance = inlet_volume - sum(fixtures_volume)
        → Local leak rules (hidden leak, continuous flow, drip)

Step 3: USB SERIAL OUTPUT (every 5 sec)
        → Build JSON payload with all 4 sensors
        → Write JSON line to Serial (921600 baud)
        → Format: {"device_id":"wmldad-001","ts":1703123456789,"sensor":1,"gpio":26,"pulses":127,"flow_rate_lpm":2.34,"volume_ml":456}

Step 4: RPi PROCESSING (pyserial + asyncio)
        → Auto-detect ESP32 on /dev/ttyUSB0 or /dev/ttyUSB1
        → Read JSON lines continuously
        → Parse and validate JSON
        → Extract features for ML (9 features per fixture)
        → Run XGBoost inference
        → Run Isolation Forest anomaly score
        → Store in SQLite/InfluxDB
        → If leak detected → write alert + trigger notification

Step 5: USER ACTION
        → Dashboard displays real-time readings on 7" touchscreen
        → In-app alert displayed on touchscreen + webhook
        → User sends command via dashboard → Serial to ESP32
```

---

## Communication Paths

| Path | Method | Protocol | Library |
|------|--------|----------|---------|
| Sensor → ESP32 | Pulse (GPIO interrupt) | Rising edge | Arduino ISR |
| ESP32 → RPi | USB UART | JSON Lines (921600 baud) | Arduino Serial / pyserial |
| RPi → ESP32 | USB UART | JSON Commands | pyserial / Arduino Serial |
| User → Dashboard | HTTP/WebSocket | HTTPS | Flask + JavaScript |
| Dashboard → Commands | Write to Serial | JSON | pyserial |
| **Remote → RPi** | **HTTPS (port forward)** | **HTML/JSON** | **On demand** |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **USB Serial over Firebase** | No internet dependency for core loop; zero monthly cost; lower latency; works offline |
| **pyserial + asyncio** | Non-blocking reads, handles reconnection, standard Python |
| **RPi over cloud hosting** | Local processing — no monthly fees, full control, no internet dependency for LAN dashboard |
| **Isolation Forest + XGBoost** | XGBoost for known leak patterns, Isolation Forest for unknown anomalies |
| **Check Valves per Fixture** | Prevents backflow contamination between fixtures |
| **SPIFFS Backup** | Survives USB disconnects / RPi reboots — data never lost |
| **Port Forwarding + DDNS** | Remote access anywhere with internet; standard router feature |
| **921600 baud** | High throughput for 4 sensors × 5 sec interval; reliable on CP2102/CH340 |

---

## Hardware Summary

| Component | Qty | Purpose |
|-----------|-----|---------|
| ESP32 38-Pin Dev Board (ESP32 Dev Module) | 1 | Main MCU |
| ESP32 38-Pin Expansion Board | 1 | Screw terminals for wiring |
| YF-S201 Flow Sensor | 4 | 1 inlet + 3 fixtures |
| Check Valve 1/2" | 3 | One per fixture (backflow prevention) |
| 12V 5A Switching PSU (S-60-12 / LRS-60-12) | 1 | Mains power → 12V |
| LM2596S Buck Converter | 1 | 12V → 5V for ESP32 + sensors |
| Waterproof ABS Enclosure IP67 (175×125×75mm) | 1 | Outdoor protection |
| Raspberry Pi 4/5 + 7" Touchscreen LCD | 1 | Local dashboard + ML backend (800×480) |

---

## Power Architecture

```
220V AC Outlet
    │
    ▼
12V 5A Switching PSU (S-60-12 / LRS-60-12)
    │
    ├──► 12V Rail (future 12V components)
    │
    ▼
LM2596S Buck Converter (12V → 5V)
    │
    ├──► ESP32 VIN (5V)
    │
    ▼
Flow Sensors VCC (5V)

USB from RPi → ESP32 USB (Data + 5V Backup)
```

> All sensors connect directly to GPIO (26, 25, 33, 32) — no pull-up resistors or capacitors needed (YF-S201 outputs digital pulses).

---

## References

- [Raspberry Pi OS Documentation](https://www.raspberrypi.com/documentation/computers/os.html)
- [Raspberry Pi Imager GitHub](https://github.com/raspberrypi/rpi-imager)
- [Raspberry Pi Forums - OS Installation](https://forums.raspberrypi.com/viewforum.php?f=117)
- [Debian Trixie Release Notes](https://www.debian.org/releases/trixie/)