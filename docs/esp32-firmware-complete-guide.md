# ESP32 Firmware Complete Guide — Hardware to Deployment

> **Target:** ESP32 NodeMCU-32S (38-pin) with Expansion Board  
> **Sensors:** 4× YF-S201 Flow Sensors (1 inlet + 3 fixtures)  
> **Communication:** HTTPS + SSE Stream to Firebase Realtime Database  
> **IDE:** Arduino IDE 2.x on Raspberry Pi OS Trixie 64-bit (or Windows/macOS)  
> **Library:** Firebase-ESP-Client by Mobizt (≥ 4.4.x)  
> **Audience:** Complete setup from hardware to deployed firmware

---

## Table of Contents

1. [Hardware Overview](#hardware-overview)
2. [Arduino IDE Installation on Raspberry Pi OS Trixie](#arduino-ide-installation-on-raspberry-pi-os-trixie)
3. [ESP32 Board Support Configuration](#esp32-board-support-configuration)
4. [Firebase Project Prerequisites](#firebase-project-prerequisites)
5. [Firebase-ESP-Client Library Setup](#firebase-esp-client-library-setup)
6. [Firmware Architecture & File Structure](#firmware-architecture--file-structure)
7. [Main Loop & Sensor Management](#main-loop--sensor-management)
8. [Firebase Integration: Upload, Stream, Commands](#firebase-integration-upload-stream-commands)
9. [Local Leak Detection Rules (Offline Fallback)](#local-leak-detection-rules-offline-fallback)
10. [Configuration (`config.h`)](#configuration-configh)
11. [Build, Upload & Verify](#build-upload--verify)
12. [Firebase Security Rules](#firebase-security-rules)
13. [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Hardware Overview

| Component | Qty | Key Specs |
|-----------|-----|-----------|
| **ESP32 NodeMCU-32S** | 1 | 38-pin, CP2102 USB-UART, 4 MB Flash |
| **ESP32 Expansion Board** | 1 | Screw terminals for all GPIOs |
| **YF-S201 Flow Sensor** | 4 | 1/2" NPT, Hall effect, 5V, ~450 pulses/L |
| **Check Valve 1/2"** | 3 | Brass/PVC, prevents backflow between fixtures |
| **12V 5A PSU + LM2596S Buck** | 1 | 220V → 12V → 5V for ESP32 + sensors |
| **IP67 ABS Enclosure** | 1 | 175×125×75mm, cable glands |

### Pin Connections

| Sensor | GPIO | Expansion Board Terminal | Notes |
|--------|------|-------------------------|-------|
| **Inlet (Main)** | 26 | D26 | Primary flow measurement |
| **Fixture 1: Bidet** | 25 | D25 | Bathroom bidet |
| **Fixture 2: Kitchen** | 33 | D33 | Kitchen faucet |
| **Fixture 3: Shower** | 32 | D32 | Bathroom shower |
| **Built-in LED** | 2 | Onboard | Status indication |

> 📸 **Screenshot Placeholder:** *Expansion board wiring diagram showing 4 sensor connections to GPIOs 26, 25, 33, 32 with shared 5V/GND rails*

---

## Arduino IDE Installation on Raspberry Pi OS Trixie

### Method: `pip install arduino` (Recommended)

```bash
# 1. Update system
sudo apt update && sudo apt full-upgrade -y

# 2. Install pip if needed
sudo apt install -y python3-pip

# 3. Install Arduino IDE (includes Arduino CLI + IDE 2.x)
pip install arduino

# 4. Verify
arduino --version
# Arduino IDE 2.3.x
```

### Launch
```bash
# From terminal
arduino

# Or Applications Menu → Programming → Arduino IDE 2
```

### Why pip?
- Official Arduino distribution for Linux ARM64
- Automatic updates via `pip install --upgrade arduino`
- No Flatpak sandbox issues with serial ports
- Works natively on Raspberry Pi OS Trixie 64-bit

### Alternative: Flatpak (if pip fails)
```bash
flatpak install flathub cc.arduino.IDE2
flatpak run cc.arduino.IDE2
# Grant serial permission:
flatpak permission-set device serial cc.arduino.IDE2 yes
```

---

## ESP32 Board Support Configuration

### 1. Open Preferences
**File → Preferences** (`Ctrl+,`)

### 2. Add Board Manager URL
In **Additional Boards Manager URLs**, paste:
```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```
Click **OK**.

> 📸 **Screenshot Placeholder:** *Arduino IDE Preferences dialog with ESP32 URL in Additional Boards Manager URLs field*

### 3. Install ESP32 Core
**Tools → Board → Boards Manager...** (`Ctrl+Shift+B`)
1. Search: **esp32**
2. Click **Install** on **"esp32 by Espressif Systems"** (latest version)
3. Wait for ~200 MB download (toolchain, libraries, examples)

> 📸 **Screenshot Placeholder:** *Boards Manager showing "esp32 by Espressif Systems" installing with progress bar*

### 4. Select Your Board
**Tools → Board → ESP32 Arduino → NodeMCU-32S**

| Setting | Value |
|---------|-------|
| **Board** | NodeMCU-32S |
| **Upload Speed** | 921600 |
| **CPU Frequency** | 240 MHz (WiFi/BT) |
| **Flash Mode** | QIO |
| **Flash Size** | 4 MB (32 Mb) |
| **Partition Scheme** | Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS) |
| **Core Debug Level** | None |
| **PSRAM** | Disabled |

> ⚠️ **Critical:** Selecting **NodeMCU-32S** ensures correct pin mapping for 38-pin board. Do NOT use "ESP32 Dev Module" — pin definitions differ.

---

## Firebase Project Prerequisites

> Complete **before** firmware configuration.

### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com)
2. **Create a project** → Name: `water-meter-leak-detection`
3. Disable Google Analytics (optional)
4. Click **Create project**

### 2. Enable Realtime Database
1. **Build → Realtime Database** → **Create Database**
2. Location: `asia-southeast1` (or closest)
3. Start in **test mode** (secure later)

### 3. Enable Authentication
1. **Build → Authentication → Sign-in method**
2. **Email/Password** → **Enable** → **Save**
3. **Users → Add user**:
   - Email: `esp32@your-project.iam.gserviceaccount.com`
   - Password: `StrongPassword123!`
   - **Save credentials** for `config.h`

### 4. Get Config Values
| Value | Location |
|-------|----------|
| **API Key** | Project Settings → General → Web API Key |
| **Database URL** | Realtime Database → Data tab → URL (e.g., `https://my-project-default-rtdb.asia-southeast1.firebasedatabase.app`) |
| **User Email/Password** | From step 3 |

### 5. Create Web App Config (for RPi backend)
1. **Project Settings → General → Your apps → Web (</>)**
2. Register app: `water-meter-rpi`
3. Copy `firebaseConfig` object → save as `rpi/firebase_config.json`

---

## Firebase-ESP-Client Library Setup

### Install via Library Manager
1. **Tools → Manage Libraries...** (`Ctrl+Shift+I`)
2. Search: **Firebase ESP Client**
3. Click **Install** on **"Firebase ESP Client" by Mobizt** (v4.4.x+)
4. Wait for installation

> 📸 **Screenshot Placeholder:** *Library Manager showing "Firebase ESP Client" by mobizt installing*

### No ArduinoJson Needed
> **Important:** Firebase-ESP-Client v4.4+ bundles JSON handling internally. Do NOT install ArduinoJson separately — it causes conflicts.

### PlatformIO (Alternative)
```ini
# platformio.ini
lib_deps =
    mobizt/Firebase ESP Client@^4.4.0
```

---

## Firmware Architecture & File Structure

```
src/
├── water-meter.ino          # Main sketch (setup + loop)
├── config.h                 # ALL parameters (WiFi, Firebase, sensors, timing)
├── config.example.h         # Template for git (copy to config.h)
├── sensor_manager.h         # 4× ISR pulse counters + flow calc
├── flow_sensor.h            # Single sensor class
├── firebase_client.h        # Firebase-ESP-Client wrapper
├── local_rules.h            # Offline leak detection
├── wifi_manager.h           # WiFi connect + auto-reconnect
├── data_logger.h            # SPIFFS fallback logging
├── ntp_sync.h               # NTP time sync for timestamps
├── ota_updater.h            # OTA firmware updates
└── led_indicator.h          # Built-in LED (GPIO 2) status patterns
```

### Key Design Principles
- **Non-blocking loop** — `delay(100)` max, all operations poll-based
- **ISR-safe** — Pulse counters use `volatile` + `IRAM_ATTR` + debounce
- **Modular** — Each subsystem in own header, single responsibility
- **Fail-safe** — SPIFFS logging when Firebase unavailable
- **Observable** — LED patterns indicate state at a glance

---

## Main Loop & Sensor Management

### Main Loop (`water-meter.ino`)

```cpp
void loop() {
    // 1. Read all 4 sensors (non-blocking, updates internal counters)
    sensorManager.readAll();
    
    // 2. Calculate flow metrics per fixture
    for (int i = 0; i < NUM_SENSORS; i++) {
        metrics[i].flowRate = sensorManager.getFlowRate(i);
        metrics[i].volume   = sensorManager.getVolume(i);
        metrics[i].total    = sensorManager.getTotal(i);
    }
    
    // 3. Local leak rules (runs even without Firebase)
    LeakStatus ls = localRules.check(metrics);
    ledIndicator.setStatus(ls);  // LED pattern reflects state
    
    // 4. Process incoming Firebase commands
    firebaseClient.processStream();
    
    // 5. Periodic upload to Firebase
    if (millis() - lastUpload > UPLOAD_INTERVAL_MS) {
        firebaseClient.uploadReading(metrics);
        lastUpload = millis();
    }
    
    // 6. Ensure WiFi connected
    wifiManager.ensureConnected();
    
    // 7. Feed watchdog, prevent reset
    delay(100);
}
```

### Sensor Manager — 4× Pulse Counter with Debounce

```cpp
// flow_sensor.h — Single sensor
class FlowSensor {
    uint8_t gpio;
    float ppl;           // Pulses per liter (calibrated)
    volatile uint32_t pulseCount = 0;
    volatile uint32_t lastPulseTime = 0;
    
    static void IRAM_ATTR isr(void* arg) {
        FlowSensor* self = (FlowSensor*)arg;
        uint32_t now = millis();
        if (now - self->lastPulseTime > DEBOUNCE_MS) {
            self->pulseCount++;
            self->lastPulseTime = now;
        }
    }
    
    void begin() {
        pinMode(gpio, INPUT);
        attachInterruptArg(digitalPinToInterrupt(gpio), isr, this, RISING);
    }
    
    float getFlowRate(uint32_t intervalMs) {
        uint32_t pulses = pulseCount;
        pulseCount = 0;  // Reset for next interval
        return (pulses * 60000.0) / (ppl * intervalMs);  // L/min
    }
};

// sensor_manager.h — Manages 4 sensors
struct SensorConfig {
    uint8_t gpio;
    const char* name;
    const char* fixtureName;
};

SensorConfig sensors[4] = {
    {26, "inlet", "Main Inlet"},
    {25, "fix1", "Bidet"},
    {33, "fix2", "Kitchen"},
    {32, "fix3", "Bathroom Shower"}
};

void SensorManager::begin() {
    for (int i = 0; i < 4; i++) {
        sensors[i] = FlowSensor(sensors[i].gpio, getPPL(i));
        sensors[i].begin();
    }
}

void SensorManager::readAll() {
    // Non-blocking — just updates internal pulse counts
    // Actual flow rate calculated on demand via getFlowRate()
}
```

### Calibration Constants (in `config.h`)
```cpp
#define PPL_INLET      450.0  // Calibrate per sensor — see calibration guide
#define PPL_FIXTURE1   450.0
#define PPL_FIXTURE2   450.0
#define PPL_FIXTURE3   450.0
#define DEBOUNCE_MS    5      // Ignore pulses < 5ms apart
```

> 📸 **Screenshot Placeholder:** *Serial Monitor showing sensor ISR attachment confirmation at startup*

---

## Firebase Integration: Upload, Stream, Commands

### Firebase Client Wrapper (`firebase_client.h`)

```cpp
#include <Firebase_ESP_Client.h>
#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"

class FirebaseClient {
    FirebaseData fbData;
    FirebaseData fbStream;
    FirebaseAuth fbAuth;
    FirebaseConfig fbConfig;
    
    bool firebaseReady = false;
    String deviceId = DEVICE_ID;
    
    void begin() {
        fbConfig.api_key = FIREBASE_API_KEY;
        fbConfig.database_url = FIREBASE_DATABASE_URL;
        fbAuth.user.email = FIREBASE_USER_EMAIL;
        fbAuth.user.password = FIREBASE_USER_PASSWORD;
        fbConfig.token_status_callback = tokenStatusCallback;
        
        fbData.setResponseSize(2048);
        fbStream.setResponseSize(2048);
        
        Firebase.begin(&fbConfig, &fbAuth);
        Firebase.reconnectWiFi(true);
        
        // Start command stream
        String path = "/commands/" + deviceId;
        if (Firebase.RTDB.beginStream(&fbStream, path.c_str())) {
            Serial.println("Stream started: " + path);
        }
    }
    
    void loop() {
        if (Firebase.ready()) firebaseReady = true;
        else firebaseReady = false;
    }
    
    // ========== UPLOAD ==========
    bool uploadReading(SensorMetric metrics[4]) {
        if (!firebaseReady) return false;
        
        FirebaseJson json;
        String timestamp = getISO8601Timestamp();  // "2026-07-14T08:30:00Z"
        String path = "/readings/" + deviceId + "/" + timestamp;
        
        // Inlet (index 0)
        json.set("inlet/flow_rate", metrics[0].flowRate);
        json.set("inlet/volume", metrics[0].volume);
        json.set("inlet/total", metrics[0].total);
        json.set("inlet/pulse_count", metrics[0].pulseCount);
        
        // Fixtures (1-3)
        for (int i = 1; i < 4; i++) {
            String p = "fixture_" + String(i);
            json.set(p + "/flow_rate", metrics[i].flowRate);
            json.set(p + "/volume", metrics[i].volume);
            json.set(p + "/total", metrics[i].total);
            json.set(p + "/pulse_count", metrics[i].pulseCount);
        }
        
        // Device status
        json.set("device/rssi", WiFi.RSSI());
        json.set("device/uptime", millis() / 1000);
        json.set("device/free_heap", ESP.getFreeHeap());
        
        if (Firebase.RTDB.pushJSON(&fbData, path.c_str(), &json)) {
            // Upload SPIFFS queue if any
            dataLogger.processQueue();
            return true;
        }
        return false;
    }
    
    // ========== STREAM (COMMANDS) ==========
    void processStream() {
        if (!Firebase.RTDB.streamAvailable(&fbStream)) return;
        
        String path = fbStream.dataPath();      // e.g., "/cmd_123"
        String type = fbStream.dataType();      // "json", "string"
        String value = fbStream.stringData();
        
        Serial.printf("Stream: path=%s, type=%s, value=%s\n", 
                      path.c_str(), type.c_str(), value.c_str());
        
        if (type == "json") {
            FirebaseJson& json = fbStream.jsonObject();
            FirebaseJsonData data;
            String cmd;
            if (json.get(data, "command")) cmd = data.stringValue;
            
            if (cmd == "calibrate") sensorManager.startCalibration(0);
            else if (cmd == "calibrate_inlet") sensorManager.startCalibration(0);
            else if (cmd == "reboot") ESP.restart();
            
            // Acknowledge
            String ackPath = "/commands/" + deviceId + path + "/executed";
            Firebase.RTDB.setBool(&fbData, ackPath.c_str(), true);
        }
    }
    
    // ========== HELPERS ==========
    String getISO8601Timestamp() {
        time_t now = time(nullptr);
        struct tm t; gmtime_r(&now, &t);
        char buf[25]; strftime(buf, 25, "%Y-%m-%dT%H:%M:%SZ", &t);
        return String(buf);
    }
    
    static void tokenStatusCallback(TokenInfo info) {
        if (info.status == token_status_ready) {
            Serial.println("Firebase token ready");
        } else if (info.status == token_status_error) {
            Serial.println("Firebase token error: " + info.error);
        }
    }
};
```

### Firebase Data Structure

```
readings/{device_id}/
  /{ISO_timestamp}/
    /inlet/
      flow_rate: 12.5
      volume: 2.5
      total: 10000.0
      pulse_count: 1125
    /fixture_1/ (bidet)
      flow_rate: 5.2
      volume: 0.9
      total: 3500.0
      pulse_count: 405
    /fixture_2/ (kitchen) — same structure
    /fixture_3/ (shower) — same structure
    /device/
      rssi: -65
      uptime: 86400
      free_heap: 180000

commands/{device_id}/
  /{command_id}/
    command: "calibrate"
    timestamp: "2026-07-14T08:30:00Z"
    source: "dashboard"
    executed: false

alerts/{device_id}/
  /{alert_id}/
    fixture_id: 1
    fixture_name: "Bidet"
    alert_type: "minor_leak"
    confidence: 0.87
    flow_rate: 0.3
    duration: 300
    action: "monitoring"
    timestamp: "2026-07-14T08:35:00Z"
    resolved: false
```

---

## Local Leak Detection Rules (Offline Fallback)

Runs on ESP32 when Firebase/ML unavailable — no internet required.

| Rule | Condition | Action |
|------|-----------|--------|
| **Inlet Imbalance** | `inlet_volume > sum(fixtures) * 1.10` | LED: Yellow blink (hidden leak) |
| **Continuous Flow** | Any fixture flow > 0 for > 30 min | LED: Red solid (stuck valve/running toilet) |
| **Drip Detection** | Flow 0.1–0.5 L/min for > 5 min | LED: Yellow pulse (drip leak) |
| **No Flow** | All sensors 0 for > 60 min | LED: Green slow pulse (normal idle) |
| **Sensor Fault** | Fixture reads 0 while inlet > 5 L/min | LED: Red fast blink (sensor fault) |

```cpp
// local_rules.h
enum LeakStatus { LEAK_NONE, LEAK_MINOR, LEAK_MAJOR, LEAK_DRIP, SENSOR_FAULT };

LeakStatus LocalRules::check(SensorMetric m[4]) {
    // Inlet imbalance
    float sumFixtures = m[1].volume + m[2].volume + m[3].volume;
    if (m[0].volume > sumFixtures * 1.10) return LEAK_MAJOR;
    
    // Continuous flow per fixture
    for (int i = 1; i < 4; i++) {
        if (m[i].flowRate > 0 && m[i].durationSec > 1800) return LEAK_MAJOR;
        if (m[i].flowRate >= 0.1 && m[i].flowRate <= 0.5 && m[i].durationSec > 300) return LEAK_DRIP;
    }
    
    // Sensor fault
    if (m[0].flowRate > 5.0) {
        for (int i = 1; i < 4; i++) {
            if (m[i].flowRate == 0 && m[0].total > sumFixtures) return SENSOR_FAULT;
        }
    }
    return LEAK_NONE;
}
```

> 📸 **Screenshot Placeholder:** *Built-in LED patterns for each leak status*

---

## Configuration (`config.h`)

```cpp
#ifndef CONFIG_H
#define CONFIG_H

// === WiFi ===
#define WIFI_SSID              "YourWiFiName"
#define WIFI_PASSWORD          "YourWiFiPassword"

// === Firebase ===
#define FIREBASE_API_KEY       "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
#define FIREBASE_DATABASE_URL  "https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app"
#define FIREBASE_USER_EMAIL    "esp32@your-project.iam.gserviceaccount.com"
#define FIREBASE_USER_PASSWORD "YourStrongPassword123!"
#define DEVICE_ID              "wm_001"

// === Sensors ===
#define NUM_SENSORS            4
#define PPL_INLET              450.0    // Calibrate! See calibration guide
#define PPL_FIXTURE1           450.0
#define PPL_FIXTURE2           450.0
#define PPL_FIXTURE3           450.0
#define DEBOUNCE_MS            5

// === Timing (milliseconds) ===
#define READ_INTERVAL_MS       1000     // Sensor read frequency
#define UPLOAD_INTERVAL_MS     5000     // Firebase upload interval
#define NTP_SYNC_INTERVAL_MS   3600000  // 1 hour

// === Local Rules ===
#define LEAK_CONFIRM_COUNT     3        // Consecutive readings to confirm
#define CONTINUOUS_FLOW_MIN    30       // Minutes before alert

// === Pins ===
#define PIN_INLET              26
#define PIN_FIXTURE1           25
#define PIN_FIXTURE2           33
#define PIN_FIXTURE3           32
#define PIN_LED                2        // Built-in LED

// === Firmware ===
#define FIRMWARE_VERSION       "2.1.0"

#endif
```

> **Never commit `config.h` to git.** Use `config.example.h` as template:
```bash
cp src/config.example.h src/config.h
# Edit with your credentials
```

---

## Build, Upload & Verify

### 1. Open Sketch
- **File → Open** → Select `src/water-meter.ino`

### 2. Verify (Compile)
- **Sketch → Verify/Compile** (`Ctrl+R`)
- Should show: `Sketch uses XXX bytes (XX%) of program storage space`

### 3. Connect ESP32
- Micro-USB **data cable** (not charge-only!) to RPi/PC
- Check port: **Tools → Port** → `/dev/ttyUSB0` (Linux) or `COM3` (Windows)

### 4. Upload
- **Sketch → Upload** (`Ctrl+U`)
- **If fails:** Hold **BOOT** → Press **EN** → Release **EN** → Release **BOOT** → Retry Upload

> 📸 **Screenshot Placeholder:** *Arduino IDE showing successful upload with "Hard resetting via RTS pin..."*

### 5. Serial Monitor
- **Tools → Serial Monitor** (`Ctrl+Shift+M`)
- **Baud: 115200** (bottom-right dropdown)

**Expected startup output:**
```
ets Jun  8 2016 00:22:57
rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)
configsip: 0, SPIWP:0xee
mode:DIO, clock div:2
load:0x3fff0030,len:1184
entry 0x400805e0
Connecting to WiFi...
WiFi connected! IP: 192.168.1.105
Firebase initialized successfully
Firebase stream started on: /commands/wm_001
Sensor 0 (inlet): ISR attached on GPIO 26
Sensor 1 (fix1): ISR attached on GPIO 25
Sensor 2 (fix2): ISR attached on GPIO 33
Sensor 3 (fix3): ISR attached on GPIO 32
Reading: inlet=0.00 L/min fix1=0.00 L/min fix2=0.00 L/min fix3=0.00 L/min
Data uploaded to Firebase
```

### 6. Verify in Firebase Console
- **Realtime Database → Data → `/readings/wm_001/`**
- New timestamped entry every 5 seconds

---

## Firebase Security Rules

```json
{
  "rules": {
    "readings": {
      "$device_id": {
        "$timestamp": {
          ".read": "auth != null && auth.uid == $device_id",
          ".write": "auth != null && auth.uid == $device_id",
          ".validate": "newData.hasChildren(['inlet', 'fixture_1', 'fixture_2', 'fixture_3'])"
        }
      }
    },
    "commands": {
      "$device_id": {
        ".read": "auth != null && auth.uid == $device_id",
        ".write": "auth.uid == 'rpi-backend' || auth.uid == 'dashboard-admin'"
      }
    },
    "alerts": {
      "$device_id": {
        ".read": "auth != null",
        ".write": "auth.uid == 'rpi-backend' || auth.uid == $device_id"
      }
    },
    "devices": {
      ".read": "auth != null",
      "$device_id": {
        ".write": "auth.uid == $device_id || auth.uid == 'dashboard-admin'"
      }
    }
  }
}
```

**Apply:** Firebase Console → Realtime Database → Rules → Paste → **Publish**

---

## Troubleshooting Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| **Upload fails: "Timed out waiting for packet header"** | Not in bootloader mode | Hold BOOT → Press EN → Release EN → Release BOOT → Upload |
| **Upload fails: "Permission denied /dev/ttyUSB0"** | User not in dialout group | `sudo usermod -a -G dialout $USER && newgrp dialout` |
| **Serial Monitor shows garbage** | Wrong baud rate | Set **115200** in Serial Monitor (bottom-right) |
| **Firebase: "Permission denied" / 403** | Security rules or auth | Check rules; verify email/password in `config.h` |
| **Firebase: "Token generation failed"** | Wrong API Key | Copy Web API Key from Project Settings → General |
| **WiFi connects but Firebase fails** | DNS/time issues | Check NTP sync; try `WiFi.config(ip, gateway, subnet, dns1, dns2)` |
| **Sensor reads 0 always** | Wiring or GPIO wrong | Check `config.h` pins match wiring; verify 5V/GND to sensors |
| **LED shows sensor fault** | Fixture reads 0 while inlet flows | Check sensor wiring; verify check valve direction (arrow = flow) |
| **"ArduinoJson not found" error** | Old code expects separate lib | Firebase-ESP-Client 4.4+ includes JSON — remove ArduinoJson from lib_deps |

---

## Quick Reference Card

| Task | Command / Menu |
|------|----------------|
| Open Preferences | File → Preferences (`Ctrl+,`) |
| Board Manager | Tools → Board → Boards Manager (`Ctrl+Shift+B`) |
| Library Manager | Tools → Manage Libraries (`Ctrl+Shift+I`) |
| Select Board | Tools → Board → ESP32 Arduino → **NodeMCU-32S** |
| Select Port | Tools → Port → `/dev/ttyUSB0` or `COMx` |
| Verify | Sketch → Verify/Compile (`Ctrl+R`) |
| Upload | Sketch → Upload (`Ctrl+U`) |
| Serial Monitor | Tools → Serial Monitor (`Ctrl+Shift+M`) |
| Baud Rate | **115200** (must match `Serial.begin(115200)`) |
| Bootloader Mode | Hold BOOT → Press EN → Release EN → Release BOOT |
| Erase Flash (clean) | `esptool.py --port /dev/ttyUSB0 erase_flash` |

---

## Next Steps

After firmware deployed:
1. **Calibrate sensors** — [Calibration Guide](./calibration.md) (5L bucket test)
2. **Deploy RPi backend** — [RPi Backend Guide](./rpi-backend.md)
3. **Train ML models** — [Complete ML Guide](./ml-complete-guide.md)
4. **Monitor dashboard** — `http://water-meter.local:5000/`

---

*Last updated: July 2026 | Tested with ESP32 Core 3.x, Firebase-ESP-Client 4.4.x, Arduino IDE 2.3.x | Compatible with NodeMCU-32S, ESP32-S3, ESP32-C3*