# ESP32 ↔ Raspberry Pi Communication Guide

> **Architecture:** ESP32 (Firebase-ESP-Client) ↔ Firebase Realtime DB ↔ RPi (Pyrebase4)  
> **Protocols:** HTTPS/SSE (ESP32→Firebase), REST Polling (RPi→Firebase)  
> **Audience:** Developers implementing the complete data pipeline

---

## Table of Contents

1. [Communication Overview](#communication-overview)
2. [ESP32 → Firebase (Upstream)](#esp32--firebase-upstream)
3. [Firebase → ESP32 (Downstream/Commands)](#firebase--esp32-downstreamcommands)
4. [RPi → Firebase (Polling)](#rpi--firebase-polling)
5. [RPi → Firebase (Alerts/Commands)](#rpi--firebase-alertscommands)
6. [Synchronization & Timing](#synchronization--timing)
7. [Retry Logic & Error Handling](#retry-logic--error-handling)
8. [Timeouts & Watchdogs](#timeouts--watchdogs)
9. [Offline Handling](#offline-handling)
10. [Security Considerations](#security-considerations)
11. [Monitoring & Debugging](#monitoring--debugging)

---

## Communication Overview

```
┌─────────────┐     HTTPS/SSE      ┌──────────────────┐     REST Poll      ┌─────────────┐
│   ESP32     │ ─────────────────▶ │ Firebase Realtime │ ◀───────────────── │    RPi      │
│  (Edge)     │ ◀───────────────── │    Database      │ ─────────────────▶ │  (Backend)  │
└─────────────┘   Commands/Stream  └──────────────────┘   Alerts/Config    └─────────────┘
      │                                                              │
      │                    ┌──────────────────┐                     │
      └──────────────────▶ │   SPIFFS Log     │ ◀──────────────────┘
                           │  (Offline Queue) │
                           └──────────────────┘
```

### Data Flow Summary

| Direction | Method | Frequency | Payload | Library |
|-----------|--------|-----------|---------|---------|
| ESP32 → Firebase | `pushJSON` (HTTPS) | 5-60 sec | Sensor readings | Firebase-ESP-Client |
| Firebase → ESP32 | SSE Stream | Real-time | Commands | Firebase-ESP-Client |
| RPi → Firebase | REST Poll | 5 sec | Read readings | Pyrebase4 |
| RPi → Firebase | REST Write | On event | Alerts, commands | Pyrebase4 |

---

## ESP32 → Firebase (Upstream)

### Initialization

```cpp
// firebase_client.h
#include <Firebase_ESP_Client.h>
#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"

FirebaseData fbData;
FirebaseData fbStream;
FirebaseAuth fbAuth;
FirebaseConfig fbConfig;

bool firebaseReady = false;
unsigned long lastUpload = 0;

void setupFirebase() {
    fbConfig.api_key = FIREBASE_API_KEY;
    fbConfig.database_url = FIREBASE_DATABASE_URL;
    
    fbAuth.user.email = FIREBASE_USER_EMAIL;
    fbAuth.user.password = FIREBASE_USER_PASSWORD;
    
    fbConfig.token_status_callback = tokenStatusCallback;
    
    Firebase.begin(&fbConfig, &fbAuth);
    Firebase.reconnectWiFi(true);
    
    // Buffer sizes for payloads
    fbData.setResponseSize(2048);
    fbStream.setResponseSize(2048);
    
    // Start command stream
    String streamPath = "/commands/" + String(DEVICE_ID);
    if (Firebase.RTDB.beginStream(&fbStream, streamPath)) {
        Serial.println("Firebase stream started on: " + streamPath);
    }
}
```

### Upload Readings (Periodic)

```cpp
void uploadReadings(SensorMetrics metrics[4]) {
    if (!Firebase.ready()) {
        Serial.println("Firebase not ready, queueing to SPIFFS");
        queueToSpiffs(metrics);
        return;
    }
    
    FirebaseJson json;
    String timestamp = getISO8601Timestamp();  // "2026-07-14T08:30:00Z"
    String path = "/readings/" + String(DEVICE_ID) + "/" + timestamp;
    
    // Inlet sensor (index 0)
    json.set("inlet/flow_rate", metrics[0].flowRate);
    json.set("inlet/volume", metrics[0].volume);
    json.set("inlet/total", metrics[0].total);
    json.set("inlet/pulse_count", metrics[0].pulseCount);
    json.set("inlet/k_factor", PPL_INLET);
    
    // Fixture sensors (indices 1-3)
    for (int i = 1; i < 4; i++) {
        String prefix = "fixture_" + String(i);
        json.set(prefix + "/flow_rate", metrics[i].flowRate);
        json.set(prefix + "/volume", metrics[i].volume);
        json.set(prefix + "/total", metrics[i].total);
        json.set(prefix + "/pulse_count", metrics[i].pulseCount);
    }
    
    // Device metadata
    json.set("device/rssi", WiFi.RSSI());
    json.set("device/uptime", millis() / 1000);
    json.set("device/free_heap", ESP.getFreeHeap());
    json.set("device/firmware", FIRMWARE_VERSION);
    
    // Push to Firebase
    if (Firebase.RTDB.pushJSON(&fbData, path.c_str(), &json)) {
        Serial.println("✅ Uploaded: " + fbData.dataPath());
        
        // Process any queued offline data
        processSpiffsQueue();
    } else {
        Serial.println("❌ Upload failed: " + fbData.errorReason());
        queueToSpiffs(metrics);
    }
}
```

### Payload Size Optimization

```cpp
// Keep payloads small for faster uploads
// Target: < 1 KB per reading

// Use short field names in production
json.set("fr", flow_rate);      // instead of "flow_rate"
json.set("vol", volume);        // instead of "volume"
json.set("tot", total);         // instead of "total"
json.set("pc", pulse_count);    // instead of "pulse_count"
json.set("kf", k_factor);       // instead of "k_factor"

// Device metadata (only send periodically)
json.set("rssi", WiFi.RSSI());
json.set("heap", ESP.getFreeHeap());
```

---

## Firebase → ESP32 (Downstream/Commands)

### Stream Listener

```cpp
void processStream() {
    if (!Firebase.RTDB.streamAvailable(&fbStream)) return;
    
    String path = fbStream.dataPath();      // e.g., "/cmd_123"
    String type = fbStream.dataType();      // "json", "string", "int"
    String value = fbStream.stringData();   // Raw value
    
    Serial.printf("Stream: path=%s, type=%s, value=%s\n", 
                  path.c_str(), type.c_str(), value.c_str());
    
    if (path == "/") {
        // Full payload update
        if (type == "json") {
            FirebaseJson &json = fbStream.jsonObject();
            processCommandJson(json);
        }
    } else {
        // Individual field update
        processCommandField(path, value);
    }
}

void processCommandJson(FirebaseJson &json) {
    FirebaseJsonData data;
    
    String command;
    if (json.get(data, "command")) {
        command = data.stringValue;
    }
    
    if (command == "calibrate") {
        startCalibration(0);  // All sensors
    } else if (command == "calibrate_inlet") {
        startCalibration(0);  // Inlet only
    } else if (command == "reboot") {
        ESP.restart();
    } else if (command == "update_config") {
        FirebaseJsonData pplData;
        if (json.get(pplData, "pulse_per_liter_inlet")) {
            PPL_INLET = pplData.floatValue;
            saveConfig();
        }
    }
    
    // Acknowledge
    acknowledgeCommand(path);
}
```

### Command Structure (Firebase)

```json
// Written by RPi or Dashboard to: /commands/wm_001/cmd_abc123
{
  "command": "calibrate",
  "timestamp": "2026-07-14T08:30:00Z",
  "source": "dashboard",
  "params": {
    "sensor": "inlet",
    "known_volume": 5.0
  },
  "executed": false
}

// ESP32 acknowledges by updating:
{
  "command": "calibrate",
  "timestamp": "2026-07-14T08:30:00Z",
  "source": "dashboard",
  "params": {...},
  "executed": true,
  "executed_at": "2026-07-14T08:30:05Z",
  "result": "success"
}
```

---

## RPi → Firebase (Polling)

### Pyrebase4 Listener

```python
# rpi/firebase_listener.py
import pyrebase
import json
import threading
import time
from datetime import datetime

class FirebaseListener:
    def __init__(self, config_path, email, password, device_id, poll_interval=5):
        self.device_id = device_id
        self.poll_interval = poll_interval
        self.last_timestamp = None
        self.running = False
        self._detector = None
        self._alert_engine = None
        
        # Load config
        with open(config_path) as f:
            self.firebase_config = json.load(f)
        
        # Initialize Pyrebase4
        self.firebase = pyrebase.initialize_app(self.firebase_config)
        self.auth = self.firebase.auth()
        self.db = self.firebase.database()
        
        # Sign in
        self.user = self.auth.sign_in_with_email_and_password(email, password)
        self.id_token = self.user['idToken']
        self.refresh_token = self.user['refreshToken']
        
        # Refs
        self.readings_ref = self.db.child(f"readings/{device_id}")
        self.alerts_ref = self.db.child(f"alerts/{device_id}")
        self.commands_ref = self.db.child(f"commands/{device_id}")
        self.device_ref = self.db.child(f"devices/{device_id}")
    
    def _refresh_token(self):
        """Refresh auth token if expired"""
        try:
            self.user = self.auth.refresh(self.refresh_token)
            self.id_token = self.user['idToken']
        except Exception as e:
            print(f"Token refresh failed: {e}")
            # Re-authenticate
            self.user = self.auth.sign_in_with_email_and_password(email, password)
            self.id_token = self.user['idToken']
    
    def set_detector(self, detector):
        self._detector = detector
    
    def set_alert_engine(self, alert_engine):
        self._alert_engine = alert_engine
    
    def start(self):
        """Start polling thread"""
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
    
    def stop(self):
        self.running = False
        if self.poll_thread:
            self.poll_thread.join(timeout=5)
    
    def _poll_loop(self):
        while self.running:
            try:
                self._check_new_readings()
            except Exception as e:
                print(f"Poll error: {e}")
                if "permission" in str(e).lower() or "unauthorized" in str(e).lower():
                    self._refresh_token()
            time.sleep(self.poll_interval)
    
    def _check_new_readings(self):
        """Fetch latest reading from Firebase"""
        readings = self.readings_ref.order_by_key().limit_to_last(1).get(self.id_token)
        
        if readings and readings.val():
            for ts, data in readings.val().items():
                if ts != self.last_timestamp:
                    self.last_timestamp = ts
                    self.process_reading(data, ts)
    
    def process_reading(self, data, timestamp):
        """Extract features and run ML inference"""
        if not self._detector:
            return
        
        try:
            # Extract features for each fixture
            inlet = data.get('inlet', {})
            
            for fixture_idx in [1, 2, 3]:
                fixture_key = f'fixture_{fixture_idx}'
                fixture = data.get(fixture_key, {})
                
                if fixture.get('flow_rate', 0) > 0.01:  # Only process if flowing
                    features = self._extract_features(data, fixture_idx)
                    result = self._detector.predict(features)
                    
                    if result['final'] != 'normal':
                        self._write_alert(result, fixture_idx, data, timestamp)
                        
        except Exception as e:
            print(f"Error processing reading: {e}")
    
    def _extract_features(self, data, fixture_idx):
        """Extract 9 features from raw Firebase data"""
        import numpy as np
        from datetime import datetime
        
        inlet = data.get('inlet', {})
        fixture = data.get(f'fixture_{fixture_idx}', {})
        
        # 1. Flow rate
        flow_rate = fixture.get('flow_rate', 0)
        
        # 2. Duration (approximate from volume/rate)
        volume = fixture.get('volume', 0)
        duration = volume / max(flow_rate / 60, 0.01) if flow_rate > 0 else 0
        
        # 3-4. Time features
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
        
        # 5. Fixture ID
        fixture_id = fixture_idx
        
        # 6. Inlet ratio
        inlet_rate = inlet.get('flow_rate', 0)
        inlet_ratio = inlet_rate / max(flow_rate, 0.01)
        
        # 7. Rate variance (simplified - would need rolling buffer)
        rate_variance = 0
        
        # 8. Night flag
        is_night = 1 if (hour >= 22 or hour < 5) else 0
        
        # 9. Pulse trend (simplified)
        pulse_trend = 0
        
        return np.array([[
            flow_rate, duration, hour, day, fixture_id,
            inlet_ratio, rate_variance, is_night, pulse_trend
        ]], dtype=np.float32)
    
    def _write_alert(self, result, fixture_idx, data, timestamp):
        """Write alert to Firebase"""
        alert_data = {
            'alert_type': result['final'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'confidence': result.get('confidence', 0),
            'fixture_index': fixture_idx,
            'fixture_name': {1: 'bidet', 2: 'kitchen', 3: 'bathroom_shower'}.get(fixture_idx),
            'action': 'monitoring',
            'details': {
                'flow_rate': data.get(f'fixture_{fixture_idx}', {}).get('flow_rate', 0),
                'inlet_flow_rate': data.get('inlet', {}).get('flow_rate', 0),
                'xgboost_class': result['xgboost']['class'],
                'xgboost_confidence': result['xgboost']['confidence'],
                'isolation_forest_anomaly': result['isolation_forest']['anomaly'],
                'isolation_forest_score': result['isolation_forest']['score']
            }
        }
        
        try:
            self.alerts_ref.push(alert_data, self.id_token)
            print(f"⚠️ ALERT: {result['final']} on fixture {fixture_idx} (conf: {result.get('confidence', 0):.2f})")
            
            # Send notification
            if self._alert_engine:
                self._alert_engine.send_notification(alert_data)
        except Exception as e:
            print(f"Failed to write alert: {e}")
    
    def get_latest_reading(self):
        readings = self.readings_ref.order_by_key().limit_to_last(1).get(self.id_token)
        return readings.val() if readings else None
    
    def get_recent_alerts(self, limit=20):
        alerts = self.alerts_ref.order_by_key().limit_to_last(limit).get(self.id_token)
        return alerts.val() if alerts else None
    
    def send_command(self, command):
        """Send command to ESP32 via Firebase"""
        self.commands_ref.push({
            'command': command,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source': 'dashboard'
        }, self.id_token)
    
    def is_connected(self):
        """Check if Firebase connection is healthy"""
        try:
            self.db.child('.info/connected').get(self.id_token)
            return True
        except:
            return False
    
    def reconnect(self):
        """Force reconnection"""
        print("Reconnecting to Firebase...")
        self._sign_in()
```

---

## RPi → Firebase (Alerts/Commands)

### Writing Alerts

```python
def write_alert(self, alert_data):
    """Write alert to Firebase /alerts/{device_id}"""
    try:
        self.alerts_ref.push(alert_data, self.id_token)
        return True
    except Exception as e:
        print(f"Alert write failed: {e}")
        self._refresh_token()
        return False
```

### Writing Commands

```python
def send_calibrate_command(self, sensor='all'):
    """Send calibration command to ESP32"""
    cmd = 'calibrate' if sensor == 'all' else f'calibrate_{sensor}'
    self.send_command(cmd)

def send_reboot_command(self):
    self.send_command('reboot')

def update_device_config(self, config_dict):
    """Update device configuration in Firebase"""
    config_ref = self.db.child(f"config/{self.device_id}")
    config_ref.update(config_dict, self.id_token)
```

---

## Synchronization & Timing

### NTP Time Sync (ESP32)

```cpp
// ntp_sync.h
#include <time.h>

void setupNTP() {
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    
    // Wait for sync
    struct tm timeinfo;
    int retry = 0;
    while (!getLocalTime(&timeinfo) && retry < 10) {
        delay(1000);
        retry++;
    }
    
    if (retry < 10) {
        Serial.println("NTP synced: " + getISO8601Timestamp());
    } else {
        Serial.println("NTP sync failed, using millis()");
    }
}

String getISO8601Timestamp() {
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
        char buf[25];
        strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
        return String(buf);
    }
    // Fallback: millis-based approximation
    return "1970-01-01T00:00:" + String(millis() / 1000) + "Z";
}
```

### RPi Time Handling

```python
# All timestamps in UTC ISO 8601
from datetime import datetime, timezone

def get_utc_timestamp():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def parse_firebase_timestamp(ts_str):
    """Parse ISO 8601 timestamp from Firebase"""
    return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
```

### Timing Constraints

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| ESP32 read interval | 1000 ms | Sensor physics |
| ESP32 upload interval | 5000 ms | Firebase rate limits |
| RPi poll interval | 5000 ms | Match upload rate |
| NTP sync interval | 24 hours | Clock drift ~1s/day |
| Command timeout | 30 sec | Network latency buffer |
| Stream reconnect | Immediate | Firebase handles |

---

## Retry Logic & Error Handling

### ESP32 Retry Strategy

```cpp
void uploadWithRetry(SensorMetrics metrics[4], int maxRetries = 3) {
    for (int attempt = 1; attempt <= maxRetries; attempt++) {
        if (uploadReadings(metrics)) {
            return;  // Success
        }
        
        Serial.printf("Upload attempt %d failed, retrying...\n", attempt);
        delay(1000 * attempt);  // Exponential backoff: 1s, 2s, 3s
    }
    
    // All retries failed
    Serial.println("All upload attempts failed, queuing to SPIFFS");
    queueToSpiffs(metrics);
}

void processSpiffsQueue() {
    // Process queued readings when connection restored
    while (hasQueuedData() && Firebase.ready()) {
        SensorMetrics m = getNextQueued();
        if (uploadReadings(m)) {
            removeQueued();
        } else {
            break;  // Stop if still failing
        }
    }
}
```

### RPi Retry Strategy

```python
import time
from functools import wraps

def with_retry(max_retries=3, base_delay=1, max_delay=30):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    print(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class FirebaseListener:
    @with_retry(max_retries=3)
    def _check_new_readings(self):
        # ... existing code ...
        pass
    
    @with_retry(max_retries=3)
    def write_alert(self, alert_data):
        # ... existing code ...
        pass
```

---

## Timeouts & Watchdogs

### ESP32 Watchdogs

```cpp
// Hardware watchdog (prevents freeze)
#include <esp_task_wdt.h>

void setup() {
    // Enable task watchdog (timeout: 30 seconds)
    esp_task_wdt_init(30, true);  // 30s timeout, panic on timeout
    esp_task_wdt_add(NULL);       # Add current task
}

void loop() {
    // Feed watchdog regularly
    esp_task_wdt_reset();
    
    // Your loop code...
    sensorManager.readAll();
    firebaseClient.processStream();
    
    if (millis() - lastUpload > UPLOAD_INTERVAL_MS) {
        firebaseClient.uploadReadings(metrics);
        lastUpload = millis();
    }
    
    delay(100);  # Prevent watchdog reset
}
```

### Network Watchdogs

```cpp
void checkNetworkHealth() {
    static unsigned long lastWiFiCheck = 0;
    if (millis() - lastWiFiCheck > 60000) {  // Every minute
        lastWiFiCheck = millis();
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("WiFi disconnected, reconnecting...");
            WiFi.reconnect();
        }
        if (!Firebase.ready()) {
            Serial.println("Firebase not ready");
        }
    }
}
```

### RPi Timeouts

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# Firebase REST timeout
FIREBASE_TIMEOUT = 10  # seconds

# In firebase_listener.py
readings = self.readings_ref.order_by_key().limit_to_last(1).get(
    self.id_token, 
    timeout=FIREBASE_TIMEOUT
)
```

---

## Offline Handling

### ESP32 SPIFFS Queue

```cpp
// data_logger.h
#include <SPIFFS.h>

#define MAX_QUEUED_READINGS 1000
#define QUEUE_FILE "/queue.json"

void queueToSpiffs(SensorMetrics metrics[4]) {
    if (!SPIFFS.begin(true)) return;
    
    File file = SPIFFS.open(QUEUE_FILE, FILE_APPEND);
    if (!file) return;
    
    FirebaseJson json;
    // ... build same JSON as uploadReadings ...
    
    String output;
    json.toString(output);
    file.println(output);
    file.close();
}

bool hasQueuedData() {
    return SPIFFS.exists(QUEUE_FILE);
}

SensorMetrics getNextQueued() {
    // Read first line from queue file
    // Parse and return metrics
}

void removeQueued() {
    // Remove first line from queue file
    // (rewrite file without first line)
}
```

### RPi Offline Detection

```python
def check_firebase_connectivity():
    """Check if Firebase is reachable"""
    try:
        response = requests.get(
            "https://www.googleapis.com",
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

# In poll_loop:
if not check_firebase_connectivity():
    print("Firebase unreachable, waiting...")
    time.sleep(30)
    continue
```

---

## Security Considerations

### Firebase Security Rules

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
    },
    "models": {
      ".read": "auth != null",
      ".write": "auth.uid == 'rpi-backend'"
    },
    "config": {
      "$device_id": {
        ".read": "auth != null && auth.uid == $device_id",
        ".write": "auth.uid == 'dashboard-admin'"
      }
    }
  }
}
```

### ESP32 Security

```cpp
// Use certificate validation (Firebase-ESP-Client does this automatically)
// Ensure time is synced for TLS certificate validation
configTime(0, 0, "pool.ntp.org");

// Never hardcode secrets in firmware
// Use config.h (gitignored) or secure element
```

### RPi Security

```python
# Store credentials in .env (gitignored)
# .env file:
FIREBASE_EMAIL=esp32@your-project.iam.gserviceaccount.com
FIREBASE_PASSWORD=strong_random_password
DEVICE_ID=wm_001

# Load in Python
from dotenv import load_dotenv
import os

load_dotenv()
EMAIL = os.getenv('FIREBASE_EMAIL')
PASSWORD = os.getenv('FIREBASE_PASSWORD')
DEVICE_ID = os.getenv('DEVICE_ID')
```

---

## Monitoring & Debugging

### ESP32 Debug Commands

```cpp
// Serial commands for debugging
void handleSerialCommand(String cmd) {
    if (cmd == "status") {
        printStatus();
    } else if (cmd == "firebase") {
        printFirebaseStatus();
    } else if (cmd == "queue") {
        printQueueSize();
    } else if (cmd == "test_upload") {
        uploadReadings(testMetrics);
    } else if (cmd == "clear_queue") {
        clearSpiffsQueue();
    }
}

void printFirebaseStatus() {
    Serial.printf("Firebase ready: %s\n", Firebase.ready() ? "YES" : "NO");
    Serial.printf("WiFi RSSI: %d dBm\n", WiFi.RSSI());
    Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("Stream connected: %s\n", fbStream.httpConnected() ? "YES" : "NO");
}
```

### RPi Monitoring

```python
# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'firebase_connected': firebase_listener.is_connected() if hasattr(firebase_listener, 'is_connected') else True,
        'model_loaded': detector.model_loaded,
        'last_reading': firebase_listener.last_timestamp,
        'uptime_seconds': time.time() - start_time,
        'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
    })

# Firebase connection monitor
def monitor_firebase():
    while True:
        if not firebase_listener.is_connected():
            logger.warning("Firebase connection lost, attempting reconnect")
            firebase_listener.reconnect()
        time.sleep(60)
```

### Log Analysis

```bash
# ESP32 logs (via Serial)
# Filter for:
# ✅ Upload successful
# ❌ Upload failed
# 📥 Command received
# 🔄 Stream reconnected

# RPi logs (systemd)
journalctl -u water-meter.service -f

# Key metrics to watch:
# - Upload success rate (target: > 99%)
# - Command latency (target: < 5s)
# - Inference latency (target: < 5ms)
# - Memory usage (target: < 200MB)
# - Queue size (target: 0)
```

---

## Quick Reference

| Task | ESP32 Code | RPi Code |
|------|------------|----------|
| Upload reading | `Firebase.RTDB.pushJSON()` | N/A |
| Listen commands | `Firebase.RTDB.beginStream()` + `streamAvailable()` | N/A |
| Poll readings | N/A | `readings_ref.order_by_key().limit_to_last(1).get()` |
| Write alert | N/A | `alerts_ref.push(alert_data, id_token)` |
| Send command | N/A | `commands_ref.push(cmd_data, id_token)` |
| Check connection | `Firebase.ready()` | `check_firebase_connectivity()` |
| Sync time | `configTime()` + `getLocalTime()` | `datetime.now(timezone.utc)` |
| Handle offline | SPIFFS queue | Local log + retry |

---

## Official References

- [Firebase-ESP-Client Docs](https://github.com/mobizt/Firebase-ESP-Client)
- [Pyrebase4 Docs](https://github.com/nhorvath/Pyrebase4)
- [Firebase Realtime DB REST API](https://firebase.google.com/docs/database/rest/start)
- [Firebase Security Rules](https://firebase.google.com/docs/database/security)
- [ESP32 Arduino Time](https://github.com/espressif/arduino-esp32/tree/master/cores/esp32)
- [SPIFFS on ESP32](https://github.com/espressif/arduino-esp32/tree/master/libraries/SPIFFS)

---

## Next Steps

Proceed to:
1. [Firebase Setup Guide](./firebase-setup-guide.md) — Complete Firebase project configuration
2. [Project Setup Guide](./setup.md) — Full system deployment
3. [Troubleshooting Guide](./troubleshooting.md) — Common issues and fixes