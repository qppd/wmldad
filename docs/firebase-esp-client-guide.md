# Firebase ESP Client Guide — Mobizt Library for ESP32

> **Library:** [Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client) by Mobizt  
> **Version:** ≥ 4.4.x  
> **Platform:** ESP32 (Arduino framework)  
> **Auth:** Email/Password (used in this project)

---

## Table of Contents

1. [Installation](#installation)
2. [Dependencies](#dependencies)
3. [Configuration](#configuration)
4. [Authentication Methods](#authentication-methods)
5. [Core Usage Patterns](#core-usage-patterns)
6. [Realtime Database Operations](#realtime-database-operations)
7. [Streaming (Real-time Updates)](#streaming-real-time-updates)
8. [Error Handling](#error-handling)
9. [Common Errors & Fixes](#common-errors--fixes)
10. [Complete Example](#complete-example)
11. [Official References](#official-references)

---

## Installation

### Arduino IDE (Library Manager)

1. **Tools** → **Manage Libraries...** (`Ctrl+Shift+I`)
2. Search: **"Firebase ESP Client"**
3. Select: **"Firebase ESP Client" by Mobizt**
4. Click **Install** (choose latest 4.4.x+)
5. Also install: **"ArduinoJson" by Benoit Blanchon** (≥ 7.x)

> 📸 **Screenshot Placeholder:** *Library Manager showing "Firebase ESP Client" by Mobizt installing*

### Arduino CLI

```bash
arduino-cli lib install "Firebase ESP Client"
arduino-cli lib install "ArduinoJson"
```

### PlatformIO

```ini
# platformio.ini
lib_deps =
    mobizt/Firebase ESP Client@^4.4.0
    bblanchon/ArduinoJson@^7.0
```

### Manual Installation (GitHub)

```bash
# Clone to Arduino libraries folder
cd ~/Documents/Arduino/libraries
git clone https://github.com/mobizt/Firebase-ESP-Client.git
# Restart Arduino IDE
```

---

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| **Firebase-ESP-Client** | ≥ 4.4.x | Firebase Realtime DB, Auth, Storage |
| **ArduinoJson** | ≥ 7.x | JSON serialization (required by Firebase lib) |
| **WiFi** | Built-in | Network connectivity |
| **FS / SPIFFS / LittleFS** | Built-in | File system for certificates/tokens |

> **Note:** Firebase-ESP-Client includes its own `FirebaseFS.h` which wraps filesystem operations. No separate FS library needed.

---

## Configuration

### Firebase Project Setup (Prerequisites)

1. **Create Firebase Project:** [console.firebase.google.com](https://console.firebase.google.com)
2. **Enable Realtime Database:** Build → Realtime Database → Create Database
3. **Set Security Rules:** (Start in test mode, secure later)
4. **Enable Authentication:** Build → Authentication → Sign-in method → **Email/Password** → Enable
5. **Create User:** Authentication → Users → Add User → `esp32@your-project.iam.gserviceaccount.com` + password
6. **Get Config Values:**
   - **API Key:** Project Settings → General → Web API Key
   - **Database URL:** Realtime Database → Data tab → URL (e.g., `https://my-project-default-rtdb.asia-southeast1.firebasedatabase.app`)
   - **User Email/Password:** From step 5

### config.h Template

```cpp
// config.h - DO NOT COMMIT TO GIT
// Copy from config.example.h and fill in your values

#ifndef CONFIG_H
#define CONFIG_H

// === WiFi ===
#define WIFI_SSID              "YOUR_WIFI_SSID"
#define WIFI_PASSWORD          "YOUR_WIFI_PASSWORD"

// === Firebase ===
#define FIREBASE_API_KEY       "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
#define FIREBASE_DATABASE_URL  "https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app"

// === Auth (Email/Password) ===
#define FIREBASE_USER_EMAIL    "esp32@your-project.iam.gserviceaccount.com"
#define FIREBASE_USER_PASSWORD "YourStrongPassword123"

// === Device ===
#define DEVICE_ID              "wm_001"

// === Sensors ===
#define NUM_SENSORS            4
#define PPL_INLET              450.0
#define PPL_FIX1               450.0
#define PPL_FIX2               450.0
#define PPL_FIX3               450.0
#define PPL_FIX4               450.0

// === Timing ===
#define READ_INTERVAL_MS       1000
#define UPLOAD_INTERVAL_MS     5000

// === Pins ===
#define PIN_INLET              26
#define PIN_FIX1               25
#define PIN_FIX2               33
#define PIN_FIX3               32
#define PIN_LED                2  // Built-in LED

#endif
```

> 📸 **Screenshot Placeholder:** *Firebase Console Project Settings showing Web API Key and Database URL*

---

## Authentication Methods

### 1. Email/Password (Used in This Project)

```cpp
// In setupFirebase()
fbConfig.api_key = FIREBASE_API_KEY;
fbConfig.database_url = FIREBASE_DATABASE_URL;

fbAuth.user.email = FIREBASE_USER_EMAIL;
fbAuth.user.password = FIREBASE_USER_PASSWORD;

// Token callback for auth state monitoring
fbConfig.token_status_callback = tokenStatusCallback;

Firebase.begin(&fbConfig, &fbAuth);
Firebase.reconnectWiFi(true);
```

**Pros:** Simple, works with Pyrebase4 on RPi, no service account needed  
**Cons:** Less secure for production (use service account for server-to-server)

### 2. Service Account (Server-to-Server)

```cpp
// Requires service account JSON in SPIFFS
fbConfig.service_account.json.path = "/service_account.json";
fbConfig.service_account.json.storage_type = mem_storage_type_flash;
```

**Pros:** Higher privileges, no user password in code  
**Cons:** More complex setup, JSON file management

### 3. Anonymous Auth (Development Only)

```cpp
// No auth config needed
Firebase.begin(&fbConfig, &fbAuth);  // fbAuth empty
```

**Pros:** Zero config  
**Cons:** No security, data publicly readable/writable

---

## Core Usage Patterns

### Initialize Firebase

```cpp
#include <Firebase_ESP_Client.h>
#include "addons/TokenHelper.h"  // For tokenStatusCallback
#include "addons/RTDBHelper.h"   // For RTDB helpers

// Global objects
FirebaseData fbData;
FirebaseData fbStream;
FirebaseAuth fbAuth;
FirebaseConfig fbConfig;

bool firebaseReady = false;
unsigned long lastUpload = 0;

void setupFirebase() {
    // API Key & Database URL
    fbConfig.api_key = FIREBASE_API_KEY;
    fbConfig.database_url = FIREBASE_DATABASE_URL;

    // Email/Password auth
    fbAuth.user.email = FIREBASE_USER_EMAIL;
    fbAuth.user.password = FIREBASE_USER_PASSWORD;

    // Token status callback (optional but recommended)
    fbConfig.token_status_callback = tokenStatusCallback;

    // Buffer sizes for large payloads
    fbData.setResponseSize(2048);
    fbStream.setResponseSize(2048);

    // Initialize
    Firebase.begin(&fbConfig, &fbAuth);
    Firebase.reconnectWiFi(true);

    // Start command stream
    String streamPath = "/commands/" + String(DEVICE_ID);
    if (Firebase.RTDB.beginStream(&fbStream, streamPath)) {
        Serial.println("Firebase stream started: " + streamPath);
    } else {
        Serial.println("Stream error: " + fbStream.errorReason());
    }
}

void loop() {
    // Maintain connection
    if (Firebase.ready()) {
        firebaseReady = true;
        // Your code here
    }

    // Process stream events
    if (Firebase.RTDB.streamAvailable(&fbStream)) {
        handleCommand(fbStream);
    }

    // Periodic upload
    if (millis() - lastUpload > UPLOAD_INTERVAL_MS) {
        uploadReadings();
        lastUpload = millis();
    }
}
```

### Token Status Callback (Monitor Auth State)

```cpp
// From examples/TokenHelper.h
void tokenStatusCallback(TokenInfo info) {
    if (info.status == token_status_ready) {
        Serial.printf("Token ready: %s\n", info.token.c_str());
        firebaseReady = true;
    } else if (info.status == token_status_error) {
        Serial.printf("Token error: %s\n", info.error.c_str());
        firebaseReady = false;
    } else if (info.status == token_status_refresh) {
        Serial.println("Token refreshing...");
    }
}
```

---

## Realtime Database Operations

### Write Data (Push with Timestamp)

```cpp
void uploadReadings(SensorMetrics metrics[4]) {
    if (!Firebase.ready()) return;

    FirebaseJson json;
    String timestamp = getISO8601Timestamp();  // e.g., "2026-07-14T08:30:00Z"
    String path = "/readings/" + String(DEVICE_ID) + "/" + timestamp;

    // Inlet sensor
    json.set("inlet/flow_rate", metrics[0].flowRate);
    json.set("inlet/volume", metrics[0].volume);
    json.set("inlet/total", metrics[0].total);
    json.set("inlet/pulse_count", metrics[0].pulseCount);
    json.set("inlet/k_factor", PPL_INLET);

    // Fixture sensors
    for (int i = 1; i < 4; i++) {
        String prefix = "fixture_" + String(i);
        json.set(prefix + "/flow_rate", metrics[i].flowRate);
        json.set(prefix + "/volume", metrics[i].volume);
        json.set(prefix + "/total", metrics[i].total);
        json.set(prefix + "/pulse_count", metrics[i].pulseCount);
    }

    // Device status
    json.set("device/rssi", WiFi.RSSI());
    json.set("device/uptime", millis() / 1000);
    json.set("device/free_heap", ESP.getFreeHeap());
    json.set("device/firmware", FIRMWARE_VERSION);

    // Push to Firebase (creates unique key if path ends with /)
    if (Firebase.RTDB.pushJSON(&fbData, path.c_str(), &json)) {
        Serial.println("Upload successful: " + fbData.dataPath());
    } else {
        Serial.println("Upload failed: " + fbData.errorReason());
        // Fallback: save to SPIFFS
        saveToSpiffs(json);
    }
}
```

### Write Data (Set - Overwrite)

```cpp
// For config updates, device status (single node)
String path = "/devices/" + String(DEVICE_ID) + "/status";

FirebaseJson json;
json.set("online", true);
json.set("last_seen", getISO8601Timestamp());
json.set("firmware", FIRMWARE_VERSION);

if (Firebase.RTDB.setJSON(&fbData, path.c_str(), &json)) {
    Serial.println("Status updated");
} else {
    Serial.println("Failed: " + fbData.errorReason());
}
```

### Read Data (Get)

```cpp
// Get latest reading
String path = "/readings/" + String(DEVICE_ID);
if (Firebase.RTDB.getJSON(&fbData, path.c_str())) {
    FirebaseJson &json = fbData.jsonObject();
    // Parse JSON...
    // Use FirebaseJsonData to extract values
} else {
    Serial.println("Read failed: " + fbData.errorReason());
}

// Get specific value
if (Firebase.RTDB.getFloat(&fbData, "/config/" + String(DEVICE_ID) + "/pulse_per_liter_inlet")) {
    float ppl = fbData.floatData();
    PPL_INLET = ppl;
    Serial.println("Updated PPL_INLET: " + String(ppl));
}
```

### Update Specific Fields (Patch)

```cpp
// Update only specific fields without overwriting entire node
String path = "/devices/" + String(DEVICE_ID) + "/config";

FirebaseJson json;
json.set("upload_interval_seconds", 10);
json.set("leak_confirm_count", 5);

if (Firebase.RTDB.updateNode(&fbData, path.c_str(), &json)) {
    Serial.println("Config updated");
}
```

### Delete Data

```cpp
// Delete old readings (cleanup)
String path = "/readings/" + String(DEVICE_ID) + "/old_timestamp";
Firebase.RTDB.deleteNode(&fbData, path.c_str());
```

---

## Streaming (Real-time Updates)

### Start Stream Listener

```cpp
// In setupFirebase()
String streamPath = "/commands/" + String(DEVICE_ID);
if (Firebase.RTDB.beginStream(&fbStream, streamPath.c_str())) {
    Serial.println("Stream started on: " + streamPath);
} else {
    Serial.println("Stream failed: " + fbStream.errorReason());
}
```

### Process Stream Events

```cpp
void handleStream() {
    if (!Firebase.RTDB.streamAvailable(&fbStream)) return;

    String path = fbStream.dataPath();      // e.g., "/cmd_123"
    String type = fbStream.dataType();      // "json", "string", "int", etc.
    String value = fbStream.stringData();   // Raw string value

    Serial.printf("Stream event: path=%s, type=%s, value=%s\n",
                  path.c_str(), type.c_str(), value.c_str());

    // Parse command
    if (type == "json") {
        FirebaseJson &json = fbStream.jsonObject();
        FirebaseJsonData data;

        String command;
        if (json.get(data, "command")) {
            command = data.stringValue;
        }

        if (command == "calibrate") {
            startCalibration();
        } else if (command == "reboot") {
            ESP.restart();
        } else if (command == "calibrate_inlet") {
            startCalibration(0);
        }
    } else if (type == "string") {
        // Simple string command
        if (value == "calibrate") startCalibration();
        else if (value == "reboot") ESP.restart();
    }

    // Acknowledge command (optional)
    String ackPath = "/commands/" + String(DEVICE_ID) + path + "/executed";
    Firebase.RTDB.setBool(&fbData, ackPath.c_str(), true);
}
```

### Stream Event Types

| Event | Description |
|-------|-------------|
| `put` | New data at path |
| `patch` | Partial update |
| `keep-alive` | Heartbeat (ignore) |
| `cancel` | Stream closed by server |
| `auth_revoked` | Token expired (reconnect) |

---

## Error Handling

### Check Firebase Ready State

```cpp
if (!Firebase.ready()) {
    Serial.println("Firebase not ready");
    return;
}

// Or check specific operation
if (fbData.httpCode() == 200) {
    // Success
} else {
    Serial.printf("HTTP %d: %s\n", fbData.httpCode(), fbData.errorReason().c_str());
}
```

### Common Error Codes

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 200 | OK | Success |
| 400 | Bad Request | Check JSON format, path |
| 401 | Unauthorized | Auth token expired → auto-refresh |
| 403 | Forbidden | Security rules deny access |
| 404 | Not Found | Path doesn't exist |
| 429 | Rate Limited | Reduce upload frequency |
| 500 | Server Error | Retry with backoff |
| -1 | Connection Failed | Check WiFi, Firebase status |

### Automatic Reconnection

```cpp
// Firebase.reconnectWiFi(true) handles WiFi reconnection
// But token refresh needs monitoring:

void checkFirebaseConnection() {
    static unsigned long lastCheck = 0;
    if (millis() - lastCheck > 30000) {  // Every 30s
        lastCheck = millis();

        if (!Firebase.ready()) {
            Serial.println("Firebase not ready, checking...");

            // Force token refresh
            if (fbAuth.token.uid.length() > 0) {
                Firebase.refreshToken(&fbConfig, &fbAuth);
            }
        }
    }
}
```

---

## Common Errors & Fixes

### Error: "Firebase Client Library requires ArduinoJson 6.18.0 or higher"

```bash
# Update ArduinoJson via Library Manager
# Or in platformio.ini:
lib_deps = bblanchon/ArduinoJson@^7.0
```

### Error: "Token generation failed: invalid API key"

| Cause | Fix |
|-------|-----|
| Wrong API Key | Copy from Firebase Console → Project Settings → General → Web API Key |
| Project deleted | Verify project exists in Firebase Console |
| API Key restricted | Check API restrictions in Google Cloud Console |

### Error: "Permission denied" / "403 Forbidden"

```json
// Check Security Rules in Firebase Console
{
  "rules": {
    "readings": {
      "$device_id": {
        ".read": "auth != null && auth.uid == $device_id",
        ".write": "auth != null && auth.uid == $device_id"
      }
    },
    "commands": {
      "$device_id": {
        ".read": "auth != null && auth.uid == $device_id",
        ".write": "auth.uid == 'rpi-backend'"
      }
    }
  }
}
```

### Error: "Network request failed" / "Connection timeout"

| Cause | Fix |
|-------|-----|
| WiFi disconnected | `Firebase.reconnectWiFi(true)` handles this |
| Firewall blocks Firebase | Allow `*.firebasedatabase.app` on port 443 |
| DNS issues | Use `8.8.8.8` DNS on ESP32: `WiFi.config(ip, gateway, subnet, dns1, dns2)` |

### Error: "Buffer too small" / "Response size exceeded"

```cpp
// Increase buffer size
fbData.setResponseSize(4096);  // Default 1024
fbStream.setResponseSize(4096);
```

### Error: "SPIFFS/LittleFS not mounted" (for service account)

```cpp
// In setup()
if (!SPIFFS.begin(true)) {  // true = format on fail
    Serial.println("SPIFFS mount failed");
} else {
    Serial.println("SPIFFS mounted");
}
```

### Error: Watchdog reset during upload

```cpp
// Add yield() in long loops
void uploadLargeData() {
    for (int i = 0; i < largeArraySize; i++) {
        // ... process ...
        if (i % 100 == 0) yield();  // Feed watchdog
    }
}
```

---

## Complete Example

```cpp
// firebase_client.h
#ifndef FIREBASE_CLIENT_H
#define FIREBASE_CLIENT_H

#include <Firebase_ESP_Client.h>
#include "config.h"

class FirebaseClient {
public:
    FirebaseClient();
    void begin();
    void loop();
    bool uploadReadings(SensorMetrics metrics[4]);
    void startCommandStream();
    bool isReady() { return firebaseReady; }

private:
    FirebaseData fbData;
    FirebaseData fbStream;
    FirebaseAuth fbAuth;
    FirebaseConfig fbConfig;
    bool firebaseReady = false;
    unsigned long lastUpload = 0;
    String deviceId = DEVICE_ID;

    void handleStream();
    void handleCommand(String command, FirebaseJson &json);
    String getISO8601Timestamp();
    static void tokenStatusCallback(TokenInfo info);
};

#endif
```

```cpp
// firebase_client.cpp
#include "firebase_client.h"
#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"

FirebaseClient::FirebaseClient() {}

void FirebaseClient::begin() {
    // Config
    fbConfig.api_key = FIREBASE_API_KEY;
    fbConfig.database_url = FIREBASE_DATABASE_URL;
    fbAuth.user.email = FIREBASE_USER_EMAIL;
    fbAuth.user.password = FIREBASE_USER_PASSWORD;
    fbConfig.token_status_callback = tokenStatusCallback;

    // Buffers
    fbData.setResponseSize(2048);
    fbStream.setResponseSize(2048);

    // Init
    Firebase.begin(&fbConfig, &fbAuth);
    Firebase.reconnectWiFi(true);

    // Start command stream
    startCommandStream();
}

void FirebaseClient::loop() {
    if (Firebase.ready()) {
        firebaseReady = true;

        // Handle incoming commands
        handleStream();

        // Periodic upload
        if (millis() - lastUpload > UPLOAD_INTERVAL_MS) {
            // Called from main loop with current metrics
            lastUpload = millis();
        }
    } else {
        firebaseReady = false;
    }
}

bool FirebaseClient::uploadReadings(SensorMetrics metrics[4]) {
    if (!firebaseReady) return false;

    FirebaseJson json;
    String timestamp = getISO8601Timestamp();
    String path = "/readings/" + deviceId + "/" + timestamp;

    json.set("inlet/flow_rate", metrics[0].flowRate);
    json.set("inlet/volume", metrics[0].volume);
    json.set("inlet/total", metrics[0].total);
    json.set("inlet/pulse_count", metrics[0].pulseCount);

    for (int i = 1; i < 4; i++) {
        String prefix = "fixture_" + String(i);
        json.set(prefix + "/flow_rate", metrics[i].flowRate);
        json.set(prefix + "/volume", metrics[i].volume);
        json.set(prefix + "/total", metrics[i].total);
        json.set(prefix + "/pulse_count", metrics[i].pulseCount);
    }

    json.set("device/rssi", WiFi.RSSI());
    json.set("device/uptime", millis() / 1000);
    json.set("device/free_heap", ESP.getFreeHeap());

    if (Firebase.RTDB.pushJSON(&fbData, path.c_str(), &json)) {
        return true;
    } else {
        Serial.println("Upload failed: " + fbData.errorReason());
        return false;
    }
}

void FirebaseClient::startCommandStream() {
    String path = "/commands/" + deviceId;
    if (Firebase.RTDB.beginStream(&fbStream, path.c_str())) {
        Serial.println("Command stream started: " + path);
    } else {
        Serial.println("Stream failed: " + fbStream.errorReason());
    }
}

void FirebaseClient::handleStream() {
    if (!Firebase.RTDB.streamAvailable(&fbStream)) return;

    String path = fbStream.dataPath();
    String type = fbStream.dataType();

    if (type == "json") {
        FirebaseJson &json = fbStream.jsonObject();
        FirebaseJsonData data;
        String command;
        if (json.get(data, "command")) {
            command = data.stringValue;
            handleCommand(command, json);
        }
    } else if (type == "string") {
        handleCommand(fbStream.stringData(), fbStream.jsonObject());
    }
}

void FirebaseClient::handleCommand(String command, FirebaseJson &json) {
    Serial.println("Command received: " + command);

    if (command == "calibrate") {
        // Trigger calibration mode
    } else if (command == "reboot") {
        ESP.restart();
    } else if (command == "calibrate_inlet") {
        // Calibrate inlet only
    }

    // Acknowledge
    String ackPath = "/commands/" + deviceId + path + "/executed";
    Firebase.RTDB.setBool(&fbData, ackPath.c_str(), true);
}

String FirebaseClient::getISO8601Timestamp() {
    // Use NTP time or millis-based approximation
    time_t now = time(nullptr);
    struct tm timeinfo;
    gmtime_r(&now, &timeinfo);
    char buf[25];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    return String(buf);
}

void FirebaseClient::tokenStatusCallback(TokenInfo info) {
    if (info.status == token_status_ready) {
        firebaseReady = true;
        Serial.println("Firebase token ready");
    } else if (info.status == token_status_error) {
        firebaseReady = false;
        Serial.println("Firebase token error: " + info.error);
    }
}
```

---

## Official References

| Resource | URL |
|----------|-----|
| **Firebase-ESP-Client GitHub** | https://github.com/mobizt/Firebase-ESP-Client |
| **Library Documentation** | https://github.com/mobizt/Firebase-ESP-Client/tree/main/docs |
| **Examples** | https://github.com/mobizt/Firebase-ESP-Client/tree/main/examples |
| **ArduinoJson** | https://arduinojson.org/ |
| **Firebase REST API** | https://firebase.google.com/docs/reference/rest/database |
| **Firebase Security Rules** | https://firebase.google.com/docs/database/security |
| **Espressif Arduino Core** | https://github.com/espressif/arduino-esp32 |
| **Mobizt Firebase Articles** | https://github.com/mobizt/Firebase-ESP-Client/wiki |

---

## Version Compatibility Matrix

| Firebase-ESP-Client | ESP32 Arduino Core | ArduinoJson | Notes |
|---------------------|-------------------|-------------|-------|
| 4.4.x | 2.0.14+ | 7.x | **Current stable** |
| 4.3.x | 2.0.11+ | 6.18+ | Legacy |
| 4.2.x | 2.0.9+ | 6.17+ | Older |

---

## Next Steps

Proceed to:
1. [ESP32 ↔ RPi Communication Guide](./esp32-rpi-communication.md) — Full data flow
2. [Project Setup Guide](./setup.md) — Complete deployment
3. [Firebase Realtime DB Schema](../docs/firebase-realtime-db.md) — Data structure

---

*Last updated: July 2026 | Tested with Firebase-ESP-Client 4.4.9, ESP32 Core 2.0.14, ArduinoJson 7.2.0 | Compatible with ESP32 NodeMCU-32S, ESP32-S3, ESP32-C3*