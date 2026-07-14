# Flowchart — Water Meter with Leak Detection (ESP32 → Firebase → RPi Backend)

## 1. Main System Flow (High-Level)

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart TD
    A[Power On] --> B[ESP32 Initialization]
    B --> C[Initialize All 4 Flow Sensors<br/>+ Attach ISRs]
    C --> D[Connect to WiFi]
    D --> E{Connected?}
    E -->|Yes| F[Initialize Firebase-ESP-Client]
    E -->|No| G[Offline Mode<br/>→ SPIFFS Logging]
    F --> H[Start Firebase Stream Listener<br/>(commands)]
    G --> I[Enter Main Loop]
    H --> I
    
    I --> J[Read All Pulse Counters<br/>Sensors 1–4]
    J --> K[Calculate Flow Metrics<br/>per Fixture]
    K --> L[Update Status LEDs]
    L --> M[Apply Local Leak Rules<br/>(non-ML fallback)]
    
    M --> N{Upload Interval?<br/>(5–60s)}
    N -->|Yes| O[Push to Firebase<br/>→ /readings/{device_id}/{ts}]
    N -->|No| P{Command Received?}
    
    O --> Q{Success?}
    Q -->|Yes| R[Clear Local Buffer]
    Q -->|No| S[Save to SPIFFS Queue]
    
    R --> P
    S --> P
    
    P -->|Yes| T[Execute Command<br/>→ Calibration / Reboot]
    P -->|No| I
    
    T --> I
```

</details>

---

## 2. Firebase Data Flow (ESP32 → Firebase → RPi)

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart LR
    subgraph "ESP32 (Firebase-ESP-Client)"
        A[Read Sensors] --> B[Build JSON<br/>Payload]
        B --> C[Firebase.pushJSON<br/>→ /readings/{id}/{ts}]
        D[Firebase.stream<br/>← /commands/{id}]
        D --> E{New Command?}
        E -->|calibrate| H[Enter Calibration Mode]
        E -->|reboot| I[Reboot ESP32]
    end
    
    subgraph "Firebase Realtime DB"
        C --> J[(/readings)]
        K[(/commands)] --> D
        L[(/alerts)] --> M
        N[(/models)] --> O
    end
    
    subgraph "RPi (Pyrebase4)"
        P[Pyrebase4<br/>Poll Listener] --> J
        P --> Q[Extract Features]
        Q --> R[XGBoost Inference]
        Q --> S[Isolation Forest<br/>Anomaly Score]
        R --> T{Leak?}
        S --> T
        T -->|Yes| U[Write Alert<br/>→ /alerts/{id}]
        U --> L
        T -->|No| V[Log Normal Reading]
        U --> W[In-App Notification<br/>(Web Dashboard)]
    end
    
    subgraph "User"
        X[Web Dashboard] --> N
        X --> J
        Y[In-App Alert] --> W
        Z[User Command] --> K
    end
```

</details>

---

## 8. Data Flow Diagram (Full System)

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart LR
    A[ Water Flow]:::physical --> B[ YF-S201<br/>Flow Sensor]:::physical
    B --> C[ Pulse<br/>Interrupt]:::firmware
    C --> D[ Feature<br/>Extraction]:::firmware
    D --> E[ Firebase<br/>ESP-Client]:::firmware
    E --> F[ Firebase<br/>Realtime DB]:::cloud
    F --> G[ Pyrebase4<br/>Poll]:::backend
    G --> H[ XGBoost<br/>Inference]:::ml
    G --> I[ Isolation<br/>Forest]:::ml
    H --> J[ Alert<br/>Engine]:::backend
    I --> J
    J --> K[ In-App<br/>Notification]:::user
    F --> L[ Web<br/>Dashboard]:::user
    F --> M[ ESP32<br/>Command Stream]:::firmware
    M --> N[ Command<br/>Handler]:::firmware
    
    classDef physical fill:#e1f5fe,stroke:#0288d1
    classDef firmware fill:#fff3e0,stroke:#f57c00
    classDef cloud fill:#e8f5e9,stroke:#388e3c
    classDef backend fill:#f3e5f5,stroke:#7b1fa2
    classDef ml fill:#fce4ec,stroke:#c62828
    classDef user fill:#fffde7,stroke:#f9a825
```

</details>