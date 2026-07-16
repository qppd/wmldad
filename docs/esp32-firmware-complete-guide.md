# ESP32 Firmware Complete Guide — USB Serial to RPi

> **Target:** ESP32 Dev Module (38-pin) with Expansion Board  
> **Sensors:** 4× YF-S201 Flow Sensors (1 inlet + 3 fixtures)  
> **Communication:** USB Serial (CDC/ACM) JSON Lines @ 921600 baud  
> **IDE:** Arduino IDE 2.x on Raspberry Pi OS Trixie 64-bit (or Windows/macOS)  
> **Library:** ArduinoJson (≥ 7.x)  
> **Audience:** Complete setup from hardware to deployed firmware

---

## Table of Contents

1. [Hardware Overview](#hardware-overview)
2. [Arduino IDE Installation on Raspberry Pi OS Trixie](#arduino-ide-installation-on-raspberry-pi-os-trixie)
3. [ESP32 Board Support Configuration](#esp32-board-support-configuration)
4. [ArduinoJson Library Setup](#arduinojson-library-setup)
5. [Firmware Architecture & File Structure](#firmware-architecture--file-structure)
6. [Main Loop & Sensor Management](#main-loop--sensor-management)
7. [USB Serial Communication](#usb-serial-communication)
8. [Local Leak Detection Rules (Offline Fallback)](#local-leak-detection-rules-offline-fallback)
9. [Configuration (`config.h`)](#configuration-configh)
10. [Build, Upload & Verify](#build-upload--verify)
11. [Sensor Calibration (Bucket Test)](#sensor-calibration-bucket-test)
12. [OTA Firmware Updates](#ota-firmware-updates)
13. [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Hardware Overview

| Component | Qty | Key Specs |
|-----------|-----|-----------|
| **ESP32 Dev Module** | 1 | 38-pin, CP2102/CH340 USB-UART, 4 MB Flash |
| **ESP32 Expansion Board** | 1 | Screw terminals for all GPIOs |
| **YF-S201 Flow Sensor** | 4 | 1/2" NPT, Hall effect, 5V, ~450 pulses/L |
| **Check Valve 1/2"** | 3 | Brass/PVC, prevents backflow between fixtures |
| **12V 5A PSU + LM2596S Buck** | 1 | 220V → 12V → 5V for ESP32 + sensors |
| **IP67 ABS Enclosure** | 1 | 175×125×75mm, cable glands + USB gland |

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
**Tools → Board → ESP32 Arduino → ESP32 Dev Module**

| Setting | Value |
|---------|-------|
| **Board** | ESP32 Dev Module |
| **Upload Speed** | 921600 |
| **CPU Frequency** | 240 MHz (WiFi/BT) |
| **Flash Mode** | QIO |
| **Flash Size** | 4 MB (32 Mb) |
| **Partition Scheme** | Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS) |
| **Core Debug Level** | None |
| **PSRAM** | Disabled |

> ⚠️ **Critical:** Selecting **ESP32 Dev Module** ensures correct pin mapping for 38-pin board. The GPIO pins in `config.h` (26, 25, 33, 32) match this board definition.

---

## ArduinoJson Library Setup

### Install via Library Manager

1. **Tools → Manage Libraries...** (`Ctrl+Shift+I`)
2. Search: **ArduinoJson**
3. Click **Install** on **"ArduinoJson by Benoit Blanchon"** (v7.x+)
4. Wait for installation

> 📸 **Screenshot Placeholder:** *Library Manager showing "ArduinoJson" by Benoit Blanchon installing*

### Version Note
- **ArduinoJson v7+** uses `JsonDocument` (replaces `StaticJsonDocument`/`DynamicJsonDocument`)
- Memory efficient, zero-copy parsing
- No separate `Firebase-ESP-Client` needed — we use plain USB Serial

---

## Firmware Architecture & File Structure

```
src/
├── water-meter.ino          # Main sketch (setup + loop)
├── config.h                 # ALL parameters (WiFi, sensors, timing)
├── config.example.h         # Template for git (copy to config.h)
├── sensor_manager.h         # 4× ISR pulse counters + flow calc
├── flow_sensor.h            # Single sensor class
├── serial_comm.h            # USB Serial JSON sender/receiver
├── local_rules.h            # Offline leak detection
├── wifi_manager.h           # WiFi connect + auto-reconnect (for OTA)
├── data_logger.h            # SPIFFS fallback logging
├── ntp_sync.h               # NTP time sync for timestamps
├── ota_updater.h            # OTA firmware updates via WiFi
└── led_indicator.h          # Built-in LED (GPIO 2) status patterns
```

### Key Design Principles

- **Non-blocking loop** — `delay(100)` max, all operations poll-based
- **ISR-safe** — Pulse counters use `volatile` + `IRAM_ATTR` + 5ms debounce
- **Modular** — Each subsystem in own header, single responsibility
- **Fail-safe** — SPIFFS logging when USB disconnected
- **Observable** — LED patterns indicate state at a glance

---

## Main Loop & Sensor Management

### Main Loop (`water-meter.ino`)

```cpp
#include <Arduino.h>
#include "config.h"
#include "sensor_manager.h"
#include "serial_comm.h"
#include "local_rules.h"
#include "wifi_manager.h"
#include "data_logger.h"
#include "led_indicator.h"
#include "ota_updater.h"
#include "ntp_sync.h"

SensorManager sensorManager;
SerialComm serialComm;
LocalRules localRules;
WiFiManager wifiManager;
DataLogger dataLogger;
LEDIndicator ledIndicator;
OTAUpdater otaUpdater;
NTPSync ntpSync;

unsigned long lastSend = 0;
unsigned long lastStatus = 0;

void setup() {
    Serial.begin(921600);
    while (!Serial) delay(10);  // Wait for USB CDC
    
    // 1. Initialize sensors
    sensorManager.begin();
    
    // 2. Initialize WiFi (for OTA + NTP only)
    wifiManager.begin();
    
    // 3. Sync time via NTP
    ntpSync.begin();
    
    // 4. Initialize SPIFFS logger
    dataLogger.begin();
    
    // 5. Initialize OTA
    otaUpdater.begin();
    
    // 6. LED ready pattern
    ledIndicator.setPattern(LED_READY);
    
    Serial.println("{\"status\":\"ready\",\"device_id\":\"" DEVICE_ID "\",\"firmware\":\"" FIRMWARE_VERSION "\"}");
}

void loop() {
    // 1. Check WiFi + OTA (non-blocking)
    wifiManager.loop();
    otaUpdater.loop();
    
    // 2. Check for incoming commands from RPi
    if (Serial.available()) {
        serialComm.handleCommand();
    }
    
    // 3. Read all pulse counters (non-blocking)
    sensorManager.readAll();
    
    // 4. Periodic sensor data send (every 5 sec)
    if (millis() - lastSend >= SEND_INTERVAL_MS) {
        sendSensorData();
        lastSend = millis();
    }
    
    // 5. Local leak rules (runs every cycle)
    localRules.checkAll();
    
    // 6. Status LED update
    ledIndicator.update();
    
    // 7. Periodic status heartbeat (every 30 sec)
    if (millis() - lastStatus >= 30000) {
        serialComm.sendStatus();
        lastStatus = millis();
    }
    
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
        float intervalSec = SEND_INTERVAL_MS / 1000.0;
        for (int i = 0; i < 4; i++) {
            flowRate[i] = (pulseCountLocal[i] * 60.0) / (ppl[i] * intervalSec);
            totalVolume[i] += pulseCountLocal[i] / ppl[i];
        }
    }

    float getFlowRate(int index) { return flowRate[index]; }
    float getVolume(int index) { return totalVolume[index]; }
    uint32_t getPulses(int index) { return pulseCountLocal[index]; }

private:
    static void IRAM_ATTR pulseISR(void* arg) {
        int idx = (int)arg;
        uint32_t now = millis();
        if (now - lastPulseTime[idx] > 5) {  // 5ms debounce
            pulseCount[idx]++;
            lastPulseTime[idx] = now;
        }
    }

    const uint8_t sensorPins[4] = {PIN_INLET, PIN_FIXTURE1, PIN_FIXTURE2, PIN_FIXTURE3};
    float ppl[4] = {PPL_INLET, PPL_FIXTURE1, PPL_FIXTURE2, PPL_FIXTURE3};  // From config.h
    
    volatile uint32_t pulseCount[4] = {0};
    volatile uint32_t lastPulseTime[4] = {0};
    uint32_t pulseCountLocal[4] = {0};
    float flowRate[4] = {0};
    float totalVolume[4] = {0};
};
```

---

## USB Serial Communication

### Serial Protocol

**Baud Rate:** 921600  
**Format:** JSON Lines (newline-delimited JSON)  
**Encoding:** UTF-8

### Data Frame (ESP32 → RPi, every 5 sec)

```json
{"device_id":"wmldad-001","ts":1703123456789,"sensor":1,"gpio":26,"pulses":127,"flow_rate_lpm":2.34,"volume_ml":456}
{"device_id":"wmldad-001","ts":1703123456789,"sensor":2,"gpio":25,"pulses":89,"flow_rate_lpm":1.65,"volume_ml":321}
{"device_id":"wmldad-001","ts":1703123456789,"sensor":3,"gpio":33,"pulses":0,"flow_rate_lpm":0.00,"volume_ml":0}
{"device_id":"wmldad-001","ts":1703123456789,"sensor":4,"gpio":32,"pulses":203,"flow_rate_lpm":3.80,"volume_ml":720}
```

### Alert Frame (ESP32 Local Detection → RPi)

```json
{"device_id":"wmldad-001","ts":1703123456789,"type":"alert","level":"major_leak","sensor":3,"flow_rate_lpm":15.2,"duration_sec":45,"message":"Major leak detected on Fixture 2"}
```

### Status Frame (Periodic, every 30 sec)

```json
{"device_id":"wmldad-001","ts":1703123456789,"type":"status","uptime_sec":3600,"free_heap":245760,"wifi_rssi":-45,"sensors_ok":true}
```

### Command Frame (RPi → ESP32)

```json
{"cmd":"calibrate","sensor":1,"k_factor":7.5}
{"cmd":"reset_counters"}
{"cmd":"sleep","duration_sec":300}
{"cmd":"reboot"}
```

### Serial Communication Handler (`serial_comm.h`)

```cpp
#include <ArduinoJson.h>

class SerialComm {
public:
    void sendSensorData(const SensorManager& sensors, const char* deviceId) {
        StaticJsonDocument<256> doc;
        doc["device_id"] = deviceId;
        doc["ts"] = millis();  // Use NTP time if available
        
        const char* sensorNames[4] = {"inlet", "bidet", "kitchen", "bathroom_shower"};
        const uint8_t sensorPins[4] = {PIN_INLET, PIN_FIXTURE1, PIN_FIXTURE2, PIN_FIXTURE3};
        
        for (int i = 0; i < 4; i++) {
            JsonObject s = doc[sensorNames[i]].to<JsonObject>();
            s["gpio"] = sensorPins[i];
            s["pulses"] = sensors.getPulses(i);
            s["flow_rate_lpm"] = round(sensors.getFlowRate(i) * 100) / 100.0;
            s["volume_ml"] = round(sensors.getVolume(i) * 1000);
        }
        
        serializeJson(doc, Serial);
        Serial.println();  // Newline delimiter
    }
    
    void sendAlert(int sensorIdx, const char* level, float flowRate, int duration, const char* msg) {
        StaticJsonDocument<256> doc;
        doc["device_id"] = DEVICE_ID;
        doc["ts"] = millis();
        doc["type"] = "alert";
        doc["level"] = level;
        doc["sensor"] = sensorIdx;
        doc["flow_rate_lpm"] = flowRate;
        doc["duration_sec"] = duration;
        doc["message"] = msg;
        
        serializeJson(doc, Serial);
        Serial.println();
    }
    
    void sendStatus() {
        StaticJsonDocument<256> doc;
        doc["device_id"] = DEVICE_ID;
        doc["ts"] = millis();
        doc["type"] = "status";
        doc["uptime_sec"] = millis() / 1000;
        doc["free_heap"] = ESP.getFreeHeap();
        doc["wifi_rssi"] = WiFi.RSSI();
        doc["sensors_ok"] = true;
        
        serializeJson(doc, Serial);
        Serial.println();
    }
    
    void handleCommand() {
        String line = Serial.readStringUntil('\n');
        line.trim();
        if (line.length() == 0) return;
        
        StaticJsonDocument<256> cmdDoc;
        DeserializationError err = deserializeJson(cmdDoc, line);
        if (err) return;
        
        const char* cmd = cmdDoc["cmd"];
        if (!cmd) return;
        
        StaticJsonDocument<128> resp;
        resp["cmd"] = cmd;
        resp["status"] = "ok";
        
        if (strcmp(cmd, "calibrate") == 0) {
            sensorManager.startCalibration();
            resp["msg"] = "Calibration mode: run known volume";
        } else if (strcmp(cmd, "reboot") == 0) {
            resp["msg"] = "Rebooting...";
            serializeJson(resp, Serial);
            Serial.println();
            ESP.restart();
        } else if (strcmp(cmd, "reset_counters") == 0) {
            for (int i = 0; i < 4; i++) sensorManager.resetVolume(i);
            resp["msg"] = "Counters reset";
        } else if (strcmp(cmd, "set_ppl") == 0) {
            int sensor = cmdDoc["sensor"] | 0;
            float ppl = cmdDoc["ppl"] | 450.0;
            sensorManager.setPPL(sensor, ppl);
            resp["msg"] = "PPL updated (not persistent)";
        }
        
        serializeJson(resp, Serial);
        Serial.println();
    }
};
```

---

## Local Leak Detection Rules (Offline Fallback)

Runs on ESP32 without RPi connection — critical for immediate alerting.

```cpp
// local_rules.h — Runs on ESP32 without RPi
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
        // Send via Serial to RPi
        serialComm.sendAlert(/* sensor */ detail, type, sensorManager.getFlowRate(detail), sensorManager.getContinuousTime(detail), type);
    }
};
```

---

## Configuration (`config.h`)

```cpp
// config.h — ALL parameters in one place
// Copy config.example.h to config.h and fill in your values

#pragma once

// ===== Device Identity =====
#define DEVICE_ID        "wmldad-001"
#define FIRMWARE_VERSION "v3.0.0-usb"

// ===== WiFi (for OTA + NTP only — not required for serial operation) =====
#define WIFI_SSID        "YourWiFiSSID"
#define WIFI_PASSWORD    "YourWiFiPassword"

// ===== Sensor Calibration (PPL = Pulses Per Liter) =====
// UPDATE AFTER BUCKET TEST!
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
#define SEND_INTERVAL_MS 5000      // Serial output every 5 sec
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
2. Press and release **EN** (Reset) while holding BOOT
3. Release **BOOT**
4. Retry Upload (`Ctrl+U`)

### 4. Verify via Serial Monitor
**Tools → Serial Monitor** (`Ctrl+Shift+M`) → **921600 baud**

**Expected Output:**
```
{"status":"ready","device_id":"wmldad-001","firmware":"v3.0.0-usb"}
{"device_id":"wmldad-001","ts":123456,"sensor":1,"gpio":26,"pulses":127,"flow_rate_lpm":2.34,"volume_ml":456}
{"device_id":"wmldad-001","ts":123456,"sensor":2,"gpio":25,"pulses":89,"flow_rate_lpm":1.65,"volume_ml":321}
{"device_id":"wmldad-001","ts":123456,"sensor":3,"gpio":33,"pulses":0,"flow_rate_lpm":0.00,"volume_ml":0}
{"device_id":"wmldad-001","ts":123456,"sensor":4,"gpio":32,"pulses":203,"flow_rate_lpm":3.80,"volume_ml":720}
```

---

## Sensor Calibration (Bucket Test)

> **Importance:** Accurate calibration is critical for leak detection. An uncalibrated sensor with ±10% error will trigger false positives or miss real leaks.

### Quick Calibration (Bucket Test)

1. **Prepare:** Get a 5L graduated container
2. **Connect:** Run water from faucet through the inlet sensor into the container
3. **Open:** Turn on faucet at medium flow
4. **Collect:** Exactly 5 liters
5. **Read:** Get pulse count from Serial Monitor (command: `status` or watch pulses field)
6. **Calculate:**
   ```
   Actual PPL = Total Pulse Count ÷ 5
   ```
7. **Update:** Change `PPL_INLET` in `config.h`
8. **Repeat** for each sensor (move sensor to each fixture line)

### Target
< 3% error per sensor. Typical YF-S201: 400–480 PPL.

---

## OTA Firmware Updates

Even though primary communication is USB Serial, WiFi + OTA allows remote firmware updates without physical access.

### OTA Updater (`ota_updater.h`)

```cpp
#include <ArduinoOTA.h>

class OTAUpdater {
public:
    void begin() {
        ArduinoOTA.setHostname(DEVICE_ID);
        ArduinoOTA.setPassword(OTA_PASSWORD);  // Define in config.h
        
        ArduinoOTA.onStart([]() {
            String type = (ArduinoOTA.getCommand() == U_FLASH) ? "sketch" : "filesystem";
            Serial.println("{\"ota\":\"start\",\"type\":\"" + type + "\"}");
        });
        ArduinoOTA.onEnd([]() {
            Serial.println("{\"ota\":\"end\"}");
        });
        ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
            Serial.printf("{\"ota\":\"progress\",\"pct\":%u}\n", (progress / (total / 100)));
        });
        ArduinoOTA.onError([](ota_error_t error) {
            Serial.printf("{\"ota\":\"error\",\"code\":%u}\n", error);
        });
        
        ArduinoOTA.begin();
    }
    
    void loop() {
        ArduinoOTA.handle();
    }
};
```

### Trigger OTA Update
```bash
# From any computer on same network
arduino-cli upload -p wmldad-001.local -b esp32:esp32:esp32 --port network
# Or use Arduino IDE: Tools → Port → Network ports → wmldad-001
```

---

## Troubleshooting Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| **No Serial output** | Baud rate mismatch | Set Serial Monitor to **921600** |
| **Upload fails** | Not in bootloader | Hold BOOT → Press EN → Release BOOT → Upload |
| **JSON parse errors** | Buffer overflow | Increase `StaticJsonDocument` size |
| **Flow rate reads 0** | Wrong GPIO pin | Verify pin in `config.h` matches wiring |
| **WiFi won't connect** | Wrong credentials | Check `WIFI_SSID`/`WIFI_PASSWORD` in `config.h` |
| **OTA not showing** | mDNS not working | Use IP address; install Bonjour on Windows |
| **SPIFFS not mounting** | Partition scheme | Use "Default 4MB with spiffs" partition |
| **Pulses too high/low** | Uncalibrated | Run bucket test, update PPL in `config.h` |

---

## LED Indicator Reference

| LED Pattern | Meaning |
|-------------|---------|
| Solid green | Normal operation, all OK |
| Blink green (1s) | WiFi connecting |
| Blink blue (fast) | Transmitting serial data |
| Solid yellow | Minor leak detected (alert) |
| Solid red | Major leak detected (critical) |
| Red flash | Emergency — urgent action needed |
| Blink white (3x + pause) | Successful data send |
| Blink red (5x + pause) | Send failed / error |
| Off | Deep sleep or no power |

---

## Checklist Before Panicking

- [ ] Is ESP32 getting power? (LED on?)
- [ ] Is USB cable a **data cable**? (not charge-only)
- [ ] Is Serial Monitor baud set to **921600**?
- [ ] Is the flow sensor arrow pointing **WITH** the water flow?
- [ ] Are WiFi SSID and password correct? (for OTA only)
- [ ] Is `PPL` calibrated for each sensor?
- [ ] Is ArduinoJson v7+ installed?
- [ ] Is board set to **ESP32 Dev Module**?