# Firmware Architecture — ESP32 with Firebase-ESP-Client

> **Framework:** Arduino (ESP32 Core) via Arduino IDE
> **Firebase Client:** [Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client) v4.4+
> **Communication:** HTTPS + SSE Stream
> **Sensor Count:** 5 flow sensors (1 inlet + 4 fixtures)

---

## File Structure

```
src/
├── water-meter.ino             # Main Arduino sketch (setup() + loop())
├── config.h                    # All configurable parameters
├── config.example.h            # Template (safe for git)
├── sensor_manager.h            # Manages 5 sensor ISRs
├── flow_sensor.h               # Single pulse counter class
├── firebase_client.h           # Firebase-ESP-Client wrapper
├── local_rules.h               # Local leak detection (non-ML fallback)
├── valve_controller.h          # Relay control for 5 valves
├── wifi_manager.h              # WiFi connect + reconnect
├── data_logger.h               # SD card + SPIFFS logging
├── display_manager.h           # OLED 128×64
├── alert_manager.h             # Buzzer + RGB LED alerts
├── ntp_sync.h                  # NTP time sync
├── ota_updater.h               # OTA firmware updates
└── led_indicator.h             # Status LED patterns

```

---

## Main Loop

```cpp
void loop() {
    // 1. Read all 5 sensors (non-blocking)
    sensorManager.readAll();
    
    // 2. Calculate flow metrics per fixture
    for (int i = 0; i < NUM_SENSORS; i++) {
        float rate = sensorManager.getFlowRate(i);
        float volume = sensorManager.getVolume(i);
        metrics[i] = {rate, volume};
    }
    
    // 3. Update OLED display
    displayManager.showMetrics(metrics);
    
    // 4. Check local leak rules
    LeakStatus ls = localRules.check(metrics);
    if (ls != LEAK_NONE) {
        alertManager.activate(ls);
        valveController.close(ls.fixture_index);
    }
    
    // 5. Check Firebase stream for commands
    firebaseClient.processStream();
    
    // 6. Upload to Firebase (if interval reached)
    if (millis() - lastUpload > UPLOAD_INTERVAL_MS) {
        firebaseClient.uploadReading(metrics);
        lastUpload = millis();
    }
    
    // 7. Restart WiFi if disconnected
    wifiManager.ensureConnected();
    
    // 8. Small delay to prevent watchdog reset
    delay(100);
}
```

---

## Firebase-ESP-Client Configuration

### Initialization

```cpp
#include <Firebase_ESP_Client.h>
#include "addons/TokenHelper.h"    // For token generation
#include "addons/RTDBHelper.h"     // For RTDB helpers

FirebaseData fbData;        // Main data object
FirebaseData fbStream;      // Stream data object
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

### Uploading Reading Data

```cpp
void uploadReading(SensorMetric metrics[5]) {
    if (!Firebase.ready()) {
        Serial.println("Firebase not ready, skipping upload");
        return;
    }
    
    FirebaseJson json;
    String timestamp = getTimestamp();
    String path = "/readings/" + String(DEVICE_ID) + "/" + timestamp;
    
    // Add inlet sensor data
    json.set("inlet/flow_rate", metrics[0].flowRate);
    json.set("inlet/volume", metrics[0].volume);
    json.set("inlet/total", metrics[0].total);
    json.set("inlet/pulse_count", metrics[0].pulseCount);
    
    // Add fixture sensors (1–4)
    for (int i = 1; i < 5; i++) {
        String prefix = "fixture_" + String(i);
        json.set(prefix + "/flow_rate", metrics[i].flowRate);
        json.set(prefix + "/volume", metrics[i].volume);
        json.set(prefix + "/total", metrics[i].total);
        json.set(prefix + "/pulse_count", metrics[i].pulseCount);
    }
    
    // Add device status
    json.set("rssi", WiFi.RSSI());
    json.set("local_rules_status", (int)localRules.getStatus());
    
    // Push to Firebase Realtime DB
    if (Firebase.RTDB.pushJSON(&fbData, path, &json)) {
        Serial.println("Data uploaded to Firebase");
    } else {
        Serial.println("Firebase upload failed: " + fbData.errorReason());
        // Save to SD card as fallback
        dataLogger.save(metrics);
    }
}
```

### Streaming Commands (Real-time)

```cpp
void processStream() {
    if (!Firebase.ready()) return;
    
    // Check for stream data
    if (Firebase.RTDB.streamAvailable(&fbStream)) {
        String path = fbStream.dataPath();
        String value = fbStream.stringData();
        int type = fbStream.dataTypeEnum();
        
        Serial.printf("Stream: path=%s, value=%s\n", path.c_str(), value.c_str());
        
        // Parse command from path
        if (path.startsWith("/" + String(DEVICE_ID))) {
            // Extract command
            if (value == "close_all") {
                valveController.closeAll();
            } else if (value == "close_inlet") {
                valveController.close(0);
            } else if (value == "close_fix1") {
                valveController.close(1);
            } else if (value == "close_fix2") {
                valveController.close(2);
            } else if (value == "close_fix3") {
                valveController.close(3);
            } else if (value == "close_fix4") {
                valveController.close(4);
            } else if (value == "open_all") {
                valveController.openAll();
            } else if (value.startsWith("open_")) {
                // open_0, open_1, etc.
                int idx = value.substring(5).toInt();
                valveController.open(idx);
            } else if (value == "calibrate_inlet") {
                sensorManager.startCalibration(0);
            }
        }
    }
}
```

---

## Sensor Manager (5 × Pulse Counter)

```cpp
#define NUM_SENSORS 5
#define DEBOUNCE_MS 5

struct SensorConfig {
    uint8_t gpio;
    const char* name;
    const char* fixture_name;
};

// Pin configuration
SensorConfig sensors[NUM_SENSORS] = {
    {34, "inlet", "Main Inlet"},
    {35, "fix1", "Kitchen Sink"},
    {32, "fix2", "Toilet"},
    {33, "fix3", "Wash Basin"},
    {25, "fix4", "Shower"}
};

// ISR-safe variables (volatile + IRAM)
static volatile unsigned long pulseCount[NUM_SENSORS] = {0};
static volatile unsigned long lastPulseTime[NUM_SENSORS] = {0};

// One ISR function for all sensors (parameterized)
void IRAM_ATTR pulseCounterISR(void* arg) {
    int index = (int)(size_t)arg;
    unsigned long now = millis();
    if (now - lastPulseTime[index] > DEBOUNCE_MS) {
        pulseCount[index]++;
        lastPulseTime[index] = now;
    }
}

void SensorManager::begin() {
    for (int i = 0; i < NUM_SENSORS; i++) {
        pinMode(sensors[i].gpio, INPUT_PULLUP);
        // Attach ISR — works because different GPIOs have different interrupt entries
        attachInterruptArg(
            digitalPinToInterrupt(sensors[i].gpio),
            pulseCounterISR,
            (void*)(size_t)i,
            RISING
        );
    }
}
```

---

## Firebase Data Structure

```
/readings/{device_id}/
  /{ISO_timestamp}/
    /inlet/
      flow_rate: 12.5
      volume: 2.5
      total: 10000.0
      pulse_count: 1125
    /fixture_1/
      flow_rate: 5.2
      volume: 0.9
      total: 3500.0
      pulse_count: 405
    /fixture_2/   (same structure)
    /fixture_3/   (same structure)
    /fixture_4/   (same structure)
    /rssi: -65
    /local_rules_status: 0

/commands/{device_id}/
  /{command_id}/
    command: "close_fix1"
    timestamp: "2026-07-10T12:00:00Z"
    source: "dashboard"
    executed: false

/alerts/{device_id}/
  /{alert_id}/
    fixture_id: 1
    fixture_name: "Kitchen Sink"
    alert_type: "minor_leak"
    confidence: 0.87
    flow_rate: 0.3
    duration: 300
    valve_action: "closed"
    timestamp: "2026-07-10T12:05:00Z"
    resolved: false
```

> Full Firebase schema: [Firebase Realtime DB Schema](./firebase-realtime-db.md)

---

## Local Leak Rules (ESP32 Fallback)

These run on the ESP32 when Firebase/ML is unreachable — they're less accurate but work offline:

| Rule | Condition | Action |
|------|-----------|--------|
| **Inlet imbalance** | `inlet_volume > sum(fixtures) * 1.10` | Alert: hidden leak detected |
| **Continuous flow** | Flow > 0 for > 30 minutes | Alert: possible stuck valve or running toilet |
| **Drip detection** | Flow 0.1–0.5 L/min for > 5 min | Alert: drip leak suspected |
| **No flow** | All sensors read 0 for > 60 min | Info: no water usage (normal) |
| **Sensor fault** | A fixture reads 0 while inlet reads > 5 L/min | Alert: possible sensor fault |

---

## Configuration (`config.h`)

```cpp
// === WiFi ===
#define WIFI_SSID        "YourWiFiName"
#define WIFI_PASSWORD    "YourWiFiPassword"

// === Firebase ===
#define FIREBASE_API_KEY       "AIzaSy..."
#define FIREBASE_DATABASE_URL  "https://your-project.firebaseio.com"
#define FIREBASE_USER_EMAIL    "esp32@your-project.iam.gserviceaccount.com"
#define FIREBASE_USER_PASSWORD "your-password"
#define DEVICE_ID              "wm_001"

// === Sensors ===
#define NUM_SENSORS      5
#define PULSE_PER_LITER  450.0   // Calibration value (adjust per sensor)
#define DEBOUNCE_MS      5       // Debounce in milliseconds

// === Timing (milliseconds) ===
#define READ_INTERVAL_MS     1000    // Read sensors every 1 second
#define UPLOAD_INTERVAL_MS   5000    // Upload to Firebase every 5 seconds

// === Valve Control ===
#define RELAY_PINS   {26, 27, 14, 12, 13}
#define VALVE_CLOSE_STATE  LOW    // Relay active LOW = valve closed

// === Local Rules ===
#define LEAK_CONFIRM_COUNT  3      // Consecutive readings to confirm minor leak
#define CONTINUOUS_FLOW_MIN  30    // Minutes before alerting
```

---

## Build and Upload

### Arduino IDE Setup

1. Install **Arduino IDE 2.x** from [arduino.cc](https://www.arduino.cc/en/software)
2. Add ESP32 board support:
   - File -> Preferences -> Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools -> Board -> Boards Manager -> search "ESP32" -> install "ESP32 Arduino"
3. Select your board: **Tools -> Board -> ESP32 Arduino -> NodeMCU-32S**
4. Select port: **Tools -> Port -> COMx** (check Windows Device Manager)
5. Install libraries via Library Manager (Tools -> Manage Libraries):
   - `Firebase ESP Client` by mobizt
   - `ArduinoJson` by bblanchon
   - `Adafruit SSD1306` by Adafruit
   - `Adafruit GFX Library` by Adafruit

### Required Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| Firebase-ESP-Client | 4.4+ | Firebase Realtime DB (push, set, stream) |
| ArduinoJson | 7+ | JSON payload serialization |
| Adafruit SSD1306 | 2.5+ | OLED display driver |
| Adafruit GFX Library | 1.11+ | OLED graphics primitives |

### Compile and Upload

1. Open `src/water-meter.ino` in Arduino IDE
2. Click **Sketch -> Verify/Compile** (Ctrl+R) to check for errors
3. Click **Sketch -> Upload** (Ctrl+U) to flash to ESP32
4. If upload fails:
   - Hold **BOOT** button on ESP32
   - Press **EN** (reset) while holding BOOT
   - Release EN, then release BOOT
   - Click Upload again

### Serial Monitor

1. Open **Tools -> Serial Monitor** (Ctrl+Shift+M)
2. Set baud rate to **115200** (bottom-right of Serial Monitor window)
3. You should see startup logs from the ESP32

---

## Firebase Security Rules

```json
{
  "rules": {
    "readings": {
      ".indexOn": ["device_id"],
      "$device_id": {
        "$timestamp": {
          ".read": "auth.uid === $device_id",
          ".write": "auth.uid === $device_id"
        }
      }
    },
    "commands": {
      "$device_id": {
        ".read": "auth.uid === $device_id",
        ".write": "auth.uid === 'pythonanywhere' || auth.uid === 'dashboard'"
      }
    },
    "alerts": {
      "$device_id": {
        ".read": "auth.uid === $device_id || auth.uid === 'pythonanywhere'",
        ".write": "auth.uid === 'pythonanywhere'"
      }
    }
  }
}
```
