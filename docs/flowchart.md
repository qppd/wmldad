# Flowchart — Water Meter with Leak Detection

## 1. Main System Flow

```mermaid
flowchart TD
    A[Power On] --> B[Initialize ESP32]
    B --> C[Initialize All 5 Flow Sensors]
    C --> D[Load Random Forest Model<br/>from Flash/SD]
    D --> E[Connect to WiFi]
    E --> F{Connected?}
    F -->|Yes| G[Sync NTP Time]
    F -->|No| H[Offline Mode]
    G --> I[Enter Main Loop]
    H --> I
    
    I --> J[Read All Pulse Counters<br/>Sensor 1–5]
    J --> K{Any Activity?}
    K -->|No| L[Idle / Sleep]
    L --> J
    
    K -->|Yes| M[Extract Features<br/>per Fixture]
    M --> N[Run Random Forest<br/>Inference]
    N --> O{Classification}
    
    O -->|Normal| P[Log Usage]
    O -->|Minor Leak| Q[Sound Alert<br/>Close Valve]
    O -->|Major Leak| R[Sound Alarm<br/>Close Valve<br/>Send Emergency Alert]
    O -->|Anomaly| S[Flag for Review]
    
    P --> T[Update Display]
    Q --> T
    R --> T
    S --> T
    
    T --> U{Upload Interval?}
    U -->|Yes| V[Send to Server]
    U -->|No| W[Continue]
    
    V --> X{Server OK?}
    X -->|Yes| Y[Clear Local Buffer]
    X -->|No| Z[Queue for Retry]
    
    Y --> J
    Z --> J
    W --> J
```

## 2. Pulse Interrupt Flow

```mermaid
flowchart LR
    A[Pulse from<br/>Flow Sensor N] --> B[ISR Triggered]
    B --> C[Increment<br/>Pulse Counter N]
    C --> D[Debounce Guard<br/>> 5ms]
    D --> E[Timestamp Pulse<br/>for Duration Calc]
    E --> F[Return to Main Loop]
```

## 3. Leak Detection Flow (ML Inference)

```mermaid
flowchart TD
    A[Features Collected] --> B[Normalize Features]
    B --> C[Feed to Random Forest<br/>TensorFlow Lite Model]
    C --> D[Get Probabilities<br/>Normal / Minor Leak / Major Leak / Anomaly]
    D --> E{Confidence > 80%?}
    
    E -->|No| F[Wait for More Data<br/>Buffer Next N Readings]
    F --> C
    
    E -->|Yes| G{Prediction?}
    
    G -->|Normal| H[Reset Leak Counters<br/>Green LED]
    G -->|Minor Leak| I[Increment Minor Count]
    I --> J{Count > 3}<br/>consecutive?
    J -->|Yes| K[CONFIRMED MINOR LEAK]
    J -->|No| H
    
    G -->|Major Leak| L[CONFIRMED MAJOR LEAK]
    G -->|Anomaly| M[Log Anomaly Features]
```

## 4. Valve Control Flow

```mermaid
flowchart TD
    A[Leak Confirmed<br/>Fixture N] --> B[Sound Buzzer]
    B --> C[Set RGB Red<br/>Flash Pattern]
    C --> D{Fixture N<br/>Valve Exists?}
    
    D -->|Yes| E[Activate Relay N<br/>→ Close Solenoid Valve]
    D -->|No| F[Alert Only Mode]
    
    E --> G[Send Notification<br/>Telegram / SMS]
    F --> G
    
    G --> H{User Action?}
    H -->|Manual Reset| I[User Opens Valve]
    H -->|Auto Reset| J[Wait 5 min<br/>Re-evaluate]
    J --> K{Leak Stopped?}
    K -->|Yes| L[Reopen Valve]
    K -->|No| M[Keep Closed<br/>Escalate Alert]
    
    I --> N[Resume Normal Ops]
    L --> N
```

## 5. Data Upload Flow

```mermaid
flowchart TD
    A[Build JSON Payload<br/>5 sensor readings + ML result] --> B[Open HTTP/MQTT Connection]
    B --> C{Send Successful?}
    C -->|200 OK| D[Mark as Synced]
    C -->|Error| E{Retries < 5?}
    E -->|Yes| F[Exponential Backoff]
    F --> C
    E -->|No| G[Save to SD Card + Flash]
    D --> H[Clear In-Memory Buffer]
    G --> I[Next Interval]
    H --> I
```

## 6. ML Model Update Flow

```mermaid
flowchart LR
    A[Server Receives<br/>New Labeled Data] --> B[Retrain Random Forest]
    B --> C[Export to TFLite]
    C --> D[OTA Push to ESP32]
    D --> E[Validate New Model<br/>Dry Run First]
    E --> F{Accuracy Improved?}
    F -->|Yes| G[Swap Model]
    F -->|No| H[Keep Old Model]
```
