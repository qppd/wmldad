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
12. [Sensor Calibration (Bucket Test)](#sensor-calibration-bucket-test)
13. [Firebase Security Rules](#firebase-security-rules)
14. [Troubleshooting Common Issues](#troubleshooting-common-issues)

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
    // 1. Check WiFi + Firebase connectivity
    wifiManager.loop();
    firebaseClient.loop();

    // 2. Check for incoming commands from RPi
    if (Serial.available()) {
        handleCommand();
    }

    // 3. Read all pulse counters (non-blocking)
    sensorManager.readAll();

    // 4. Periodic sensor data send
    if (millis() - lastSend >= SEND_INTERVAL_MS) {
        sendSensorData();
        lastSend = millis();
    }

    // 5. Local leak rules (runs every cycle)
    localRules.checkAll();

    // 6. Status LED update
    ledIndicator.update();

    delay(100);  // Non-blocking cycle
}
```

### Sensor Manager (`sensor_manager.h`)

```cpp
// Manages 4 flow sensors with ISR pulse counting
class SensorManager {
public:
    void begin() {
        for (int i = 0; i < 4; i++) {
            pinMode(sensorPins[i], INPUT);
            attachInterruptArg(digitalPinToInterrupt(sensorPins[i]),
                               pulseISR, (void*)i, RISING);
        }
    }

    void readAll() {
        // Atomic read of pulse counters
        noInterrupts();
        for (int i = 0; i < 4; i++) {
            pulseCountLocal[i] = pulseCount[i];
            pulseCount[i] = 0;  // Reset for next interval
        }
        interrupts();
        
        // Calculate flow rate per sensor
        for (int i = 0; i < 4; i++) {
            flowRate[i] = (pulseCountLocal[i] * 60.0) / (ppl[i] * (SEND_INTERVAL_MS / 1000.0));
            totalVolume[i] += pulseCountLocal[i] / ppl[i];
        }
    }

private:
    static void IRAM_ATTR pulseISR(void* arg) {
        int idx = (int)arg;
        uint32_t now = millis();
        if (now - lastPulseTime[idx] > 5) {  // 5ms debounce
            pulseCount[idx]++;
            lastPulseTime[idx] = now;
        }
    }

    const uint8_t sensorPins[4] = {26, 25, 33, 32};
    float ppl[4] = {450, 450, 450, 450};  // Overridden by config.h
    volatile uint32_t pulseCount[4] = {0};
    volatile uint32_t lastPulseTime[4] = {0};
    uint32_t pulseCountLocal[4] = {0};
    float flowRate[4] = {0};
    float totalVolume[4] = {0};
};
```

---

## Firebase Integration: Upload, Stream, Commands

### Firebase Client Wrapper (`firebase_client.h`)

```cpp
class FirebaseClient {
public:
    bool begin() {
        // Configure Firebase
        config.api_key = API_KEY;
        config.database_url = DATABASE_URL;
        config.signer.test_mode = false;

        // Auth: Email/Password
        auth.user.email = USER_EMAIL;
        auth.user.password = USER_PASSWORD;

        // Token callback
        config.token_status_callback = tokenStatusCallback;

        // Initialize
        Firebase.begin(&config, &auth);
        Firebase.reconnectWiFi(true);

        // Start stream listener for commands
        Firebase.RTDB.beginStream(&stream, "/commands/" + String(DEVICE_ID));
        return true;
    }

    void loop() {
        // Handle stream events (commands from RPi)
        if (Firebase.RTDB.readStream(&stream)) {
            if (stream.dataType() == "json") {
                handleCommand(stream.jsonObject());
            }
        }
    }

    void pushReadings(const JsonObject& data) {
        String path = "/readings/" + String(DEVICE_ID) + "/" + String(millis());
        Firebase.RTDB.pushJSON(&fbdo, path.c_str(), data);
    }

private:
    void handleCommand(const FirebaseJson& json) {
        String cmd;
        json.get(cmd, "cmd");
        if (cmd == "calibrate") {
            sensorManager.startCalibration();
        } else if (cmd == "reboot") {
            ESP.restart();
        }
    }

    FirebaseConfig config;
    FirebaseAuth auth;
    FirebaseData fbdo;
    FirebaseData stream;
};
```

---

## Local Leak Detection Rules (Offline Fallback)

```cpp
// local_rules.h — Runs on ESP32 without Firebase
class LocalRules {
public:
    void checkAll() {
        // Rule 1: Hidden leak (inlet > sum of fixtures + 10%)
        float inletVolume = sensorManager.getVolume(0);
        float sumFixtures = sensorManager.getVolume(1) + sensorManager.getVolume(2) + sensorManager.getVolume(3);
        if (inletVolume > sumFixtures * 1.10) {
            triggerAlert("hidden_leak", inletVolume - sumFixtures);
        }

        // Rule 2: Continuous flow > 30 min (stuck valve / running toilet)
        for (int i = 1; i <= 3; i++) {
            if (sensorManager.getFlowRate(i) > 0.01 && sensorManager.getContinuousTime(i) > 30 * 60) {
                triggerAlert("continuous_flow", i);
            }
        }

        // Rule 3: Drip detection (0.1–0.5 L/min for > 5 min)
        for (int i = 1; i <= 3; i++) {
            float rate = sensorManager.getFlowRate(i);
            if (rate > 0.1 && rate < 0.5 && sensorManager.getContinuousTime(i) > 5 * 60) {
                triggerAlert("drip_leak", i);
            }
        }

        // Rule 4: Sensor fault (inlet flows but fixture reads 0)
        if (sensorManager.getFlowRate(0) > 1.0) {
            for (int i = 1; i <= 3; i++) {
                if (sensorManager.getFlowRate(i) == 0) {
                    triggerAlert("sensor_fault", i);
                }
            }
        }
    }

    void triggerAlert(const char* type, int detail) {
        // Log to SPIFFS
        dataLogger.logAlert(type, detail);
        // LED pattern: fast blink = local alert
        ledIndicator.setPattern(LED_FAST_BLINK);
    }
};
```

---

## Configuration (`config.h`)

```cpp
// config.h — ALL parameters in one place
// Copy config.example.h to config.h and fill in your values

#pragma once

// ===== WiFi =====
#define WIFI_SSID        "YourWiFiSSID"
#define WIFI_PASSWORD    "YourWiFiPassword"

// ===== Firebase =====
#define API_KEY          "YOUR_WEB_API_KEY"
#define DATABASE_URL     "https://your-project-default-rtdb.region.firebasedatabase.app"
#define USER_EMAIL       "esp32@your-project.iam.gserviceaccount.com"
#define USER_PASSWORD    "StrongPassword123!"
#define DEVICE_ID        "wm_001"

// ===== Sensor Calibration (PPL = Pulses Per Liter) =====
#define PPL_INLET        450   // Update after bucket test
#define PPL_FIXTURE1     450
#define PPL_FIXTURE2     450
#define PPL_FIXTURE3     450

// ===== Sensor Pins =====
#define PIN_INLET        26
#define PIN_FIXTURE1     25
#define PIN_FIXTURE2     33
#define PIN_FIXTURE3     32

// ===== Timing =====
#define SEND_INTERVAL_MS 5000      // Firebase upload every 5 sec
#define CALIBRATION_TIMEOUT_MS 300000  // 5 min calibration window

// ===== Local Leak Thresholds =====
#define HIDDEN_LEAK_THRESHOLD 1.10   // 10% imbalance
#define CONTINUOUS_FLOW_MIN 30       // Minutes
#define DRIP_MIN_RATE 0.1            // L/min
#define DRIP_MAX_RATE 0.5            // L/min
#define DRIP_MIN_TIME 5              // Minutes

// ===== SPIFFS Logging =====
#define MAX_OFFLINE_LOGS 500
```

---

## Build, Upload & Verify

### 1. Verify (Compile)
**Sketch → Verify/Compile** (`Ctrl+R`)
- Should compile with 0 errors, ~250 KB flash usage

### 2. Select Port
**Tools → Port** → `/dev/ttyUSB0` (Linux) or `COMx` (Windows)

### 3. Upload
**Sketch → Upload** (`Ctrl+U`)

#### If Upload Fails (Bootloader Mode):
1. Hold **BOOT** button
2. Press and release **EN** (Reset)
3. Release **BOOT**
4. Retry Upload (`Ctrl+U`)

### 4. Verify via Serial Monitor
**Tools → Serial Monitor** (`Ctrl+Shift+M`) → **115200 baud**

**Expected Output:**
```
ESP32 Water Meter Ready
WiFi connected: 192.168.1.100
Firebase: Auth successful
Firebase: Stream started
Sensors: All 4 ISRs attached
Loop: Running...
```

---

## Sensor Calibration (Bucket Test)

> **Importance:** Accurate calibration is critical for leak detection. An uncalibrated sensor with ±10% error will trigger false positives or miss real leaks.

### The K-Factor (PPL)

```
K-Factor (PPL) = Number of electrical pulses generated per liter of water
Volume (L)     = Total Pulse Count ÷ K-Factor
Flow Rate (L/min) = (Pulse Count × 60) ÷ (K-Factor × Interval Seconds)
```

Most YF-S201 sensors are rated at **450 PPL**, but actual values vary by ±10% due to:
- Manufacturing tolerances (±5%)
- Pipe diameter and water pressure
- Flow rate (low vs high behave differently)
- Temperature
- Wear over time

### Calibration Method: Bucket Test (Per Sensor)

#### What You Need
- **Graduated container** (1L, 5L, or 10L — bigger = more accurate)
- **Smartphone stopwatch** (optional for flow rate)
- **ESP32** flashed with firmware, Serial Monitor open (115200 baud)
- **Water source** (faucet / hose)
- **One YF-S201 sensor** at a time

#### Procedure (Per Sensor)

**Step 1:** Connect only the sensor being calibrated.

**Step 2:** Set initial K-factor in `config.h`:
```cpp
#define PPL_INLET 450
```
Upload to ESP32.

**Step 3:** Open Serial Monitor (115200 baud). Type `status` to see pulse count.

**Step 4:** Run the test:
1. Place container under faucet
2. Connect flow sensor between faucet and container
3. Open faucet at a **steady medium flow**
4. Collect exactly **5 liters** (or more for accuracy)
5. Close faucet
6. Note the pulse count from Serial Monitor

**Step 5:** Calculate:
```
Actual PPL = Total Pulse Count ÷ Volume Collected

Example: 2,320 pulses for 5 liters
Actual PPL = 2,320 ÷ 5 = 464 PPL
```

**Step 6:** Repeat 3 times and average:
```
Test 1: 2,320 pulses ÷ 5L = 464 PPL
Test 2: 2,310 pulses ÷ 5L = 462 PPL 
Test 3: 2,340 pulses ÷ 5L = 468 PPL

Average PPL = (464 + 462 + 468) ÷ 3 = 464.7 → round to 465
```

**Step 7:** Update firmware:
```cpp
// Per-sensor calibration (config.h)
#define PPL_INLET    465
#define PPL_FIXTURE1 450
#define PPL_FIXTURE2 458
#define PPL_FIXTURE3 452
#define PPL_FIXTURE4 460
```

---

### Two-Point Calibration (Best Accuracy)

For different flow rates, the K-factor changes slightly:

| Test | Flow Rate | Volume | Start Pulse | End Pulse | Calculated PPL |
|------|-----------|--------|-------------|-----------|----------------|
| Low | Drip (~0.3 L/min) | 2L | 0 | 920 | 460 |
| Medium | Faucet (~6 L/min) | 5L | 0 | 2,310 | 462 |
| High | Full open (~15 L/min) | 5L | 0 | 2,355 | 471 |

**Recommended:** Use the **medium flow** PPL and apply a correction factor in code:
```python
if flow_rate < 1.0:
    ppl = medium_ppl * 0.98
elif flow_rate > 10.0:
    ppl = medium_ppl * 1.02
else:
    ppl = medium_ppl
```

---

### Calibration Verification

After calibration, verify accuracy:

| Accuracy | Error Range | Impact on Leak Detection |
|----------|-------------|-------------------------|
| Excellent | < ±2% | Reliable leak detection |
| Good | ±2% – ±5% | Minor false positive risk |
| Acceptable | ±5% – ±10% | May miss small leaks |
| Needs work | > ±10% | Unreliable for leak detection |

**Formula:**
```
Error % = |(Measured Volume - Actual Volume) ÷ Actual Volume| × 100
```

---

### Calibration via Firebase (Optional)

If you've implemented the calibration endpoint:

```json
// POST to Flask API or write to Firebase:
{
  "command": "calibrate",
  "sensor_id": "inlet",
  "known_volume": 5.0
}
```

1. Run exactly 5L through the inlet sensor
2. The system calculates the K-factor and updates `/config/device_id/pulse_per_liter_inlet`

---

### Calibration Log Template

```
Sensor Calibration Log
──────────────────────
Date: 2026-07-10
Device: wm_001

INLET SENSOR (GPIO 26):
  Test 1: 2320 pulses / 5L = 464 PPL
  Test 2: 2310 pulses / 5L = 462 PPL
  Test 3: 2340 pulses / 5L = 468 PPL
  Average: 465 PPL ← USE THIS

FIXTURE 1 (GPIO 25):
  Test 1: 2250 pulses / 5L = 450 PPL
  Average: 450 PPL

FIXTURE 2 (GPIO 33):
  Test 1: 2290 pulses / 5L = 458 PPL
  Average: 458 PPL

FIXTURE 3 (GPIO 32):
  Test 1: 2260 pulses / 5L = 452 PPL
  Average: 452 PPL

FIXTURE 4 (GPIO 32):
  Test 1: 2300 pulses / 5L = 460 PPL
  Average: 460 PPL
```

---

### Common Pitfalls

| Problem | Why | Fix |
|---------|-----|-----|
| Air bubbles in sensor | Gives wrong pulse count | Tap sensor, purge air first |
| Sensor installed backwards | Zero reading | Arrow must point WITH flow |
| Low flow gives different PPL | Non-linear sensor response | Use 2-point calibration |
| Temperature change | K-factor shifts slightly | Re-calibrate seasonally |
| Using different pipe diameter | Changes flow profile | Calibrate with actual plumbing |
| Multiple sensors sharing same calibration | Each sensor is different | Calibrate EACH sensor individually |

---

### Quick Reference

| Sensor Model | Nominal PPL (start here) | Typical Range |
|-------------|-------------------------|---------------|
| YF-S201 | 450 | 440–480 |
| YF-S401 | 450 | 440–470 |
| YF-B1 | 2760 | 2600–2900 |
| Generic clone | 450 | 420–500 (test carefully) |

> **Tip:** After calibration, write the PPL value on each sensor with a permanent marker so you don't forget which sensor has which value!

---

## Firebase Security Rules

```json
{
  "rules": {
    "readings": {
      "$device_id": {
        "$timestamp": {
          ".read": "auth != null",
          ".write": "auth.uid == $device_id || auth.uid == 'rpi-backend'"
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
1. **Calibrate sensors** — 5L bucket test (this guide, above)
2. **Deploy RPi backend** — [Pi Complete Setup](./pi-complete-setup.md)
3. **Train ML models** — [Complete ML Guide](./ml-complete-guide.md)
4. **Monitor dashboard** — `http://water-meter.local:5000/`

---

*Last updated: July 2026 | Tested with ESP32 Core 3.x, Firebase-ESP-Client 4.4.x, Arduino IDE 2.3.x | Compatible with NodeMCU-32S, ESP32-S3, ESP32-C3*