# ESP32 ↔ Raspberry Pi Communication (USB Serial)

> **Architecture:** ESP32 ↔ USB Cable (ttyUSB0/ttyUSB1) ↔ RPi (Python Serial)
> **Protocol:** JSON over UART (115200 baud)
> **Auto-detection:** RPi auto-detects ESP32 on ttyUSB0 or ttyUSB1

---

## Table of Contents

1. [Communication Overview](#communication-overview)
2. [Hardware Connection](#hardware-connection)
3. [RPi Auto Port Detection](#rpi-auto-port-detection)
4. [ESP32 Firmware (USB Serial)](#esp32-firmware-usb-serial)
5. [RPi Python Serial Reader](#rpi-python-serial-reader)
6. [Message Protocol (JSON)](#message-protocol-json)
7. [Auto Port Detection Logic](#auto-port-detection-logic)
8. [Error Handling & Reconnection](#error-handling--reconnection)
9. [Testing & Verification](#testing--verification)

---

## Communication Overview

```
┌─────────────┐     USB Cable (UART)      ┌──────────────────┐
│   ESP32     │ ─────────────────────────▶ │   Raspberry Pi   │
│  (NodeMCU)  │ ◀───────────────────────── │   (Python Serial)│
│  115200     │      JSON over UART        │  /dev/ttyUSB0/1  │
└─────────────┘     115200 8N1            └──────────────────┘
      │                                                  │
      │              Auto-detect on                      │
      │              /dev/ttyUSB0 or ttyUSB1             │
      ▼                                                  ▼
```

### Data Flow Summary

| Direction | Method | Frequency | Payload | Transport |
|-----------|--------|-----------|---------|-----------|
| ESP32 → RPi | `Serial.println(JSON)` | Every 1-5 sec | Sensor readings | USB UART |
| RPi → ESP32 | `Serial.write(JSON)` | On command | Commands/Config | USB UART |

---

## Hardware Connection

| ESP32 Pin | USB Cable | RPi Port | Notes |
|-----------|-----------|----------|-------|
| USB D+ | USB D+ | USB D+ | Data+ |
| USB D- | USB D- | USB D- | Data- |
| 5V (VIN) | USB 5V | USB 5V | Power from RPi |
| GND | USB GND | USB GND | Common ground |

> **Important:** Use a **data-capable USB cable** (not charge-only). The CP2102/CH340 USB-UART bridge on NodeMCU-32S exposes `/dev/ttyUSB0` (or `ttyUSB1` if multiple devices).

---

## RPi Auto Port Detection

### udev Rule for Consistent Naming

```bash
# /etc/udev/rules.d/99-esp32.rules
# CP2102 (NodeMCU-32S)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyESP32", MODE="0666", GROUP="dialout"
# CH340 (some ESP32 boards)
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="ttyESP32", MODE="0666", GROUP="dialout"

# Apply:
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Now ESP32 always appears as `/dev/ttyESP32` (symlink to ttyUSB0/1).

### Python Auto-Detection (No udev Required)

```python
# rpi/serial_port.py
import glob
import serial
import logging

logger = logging.getLogger(__name__)

ESP32_VID_PID = [
    (0x10c4, 0xea60),  # CP2102/CP2104 (NodeMCU-32S)
    (0x1a86, 0x7523),  # CH340
    (0x303a, 0x1001),  # ESP32-S3 native USB
]

def find_esp32_port() -> str | None:
    """
    Auto-detect ESP32 serial port.
    Checks /dev/ttyUSB* and /dev/ttyACM* for known ESP32 VID:PID.
    Returns first matching port or None.
    """
    candidates = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    
    for port in candidates:
        try:
            # Try to open and check VID:PID via sysfs
            if _is_esp32_device(port):
                logger.info(f"Found ESP32 on {port}")
                return port
        except (OSError, PermissionError) as e:
            logger.debug(f"Cannot access {port}: {e}")
            continue
    
    logger.warning("No ESP32 device found on any ttyUSB/ttyACM port")
    return None

def _is_esp32_device(port: str) -> bool:
    """Check if port matches known ESP32 VID:PID via sysfs."""
    import os
    try:
        # Get device path: /dev/ttyUSB0 -> /sys/bus/usb-serial/devices/ttyUSB0
        port_name = os.path.basename(port)
        sysfs_path = f"/sys/bus/usb-serial/devices/{port_name}"
        
        if not os.path.exists(sysfs_path):
            # Try alternative: /sys/bus/usb/devices/
            for usb_dev in glob.glob('/sys/bus/usb/devices/*/idVendor'):
                try:
                    with open(usb_dev) as f:
                        vid = int(f.read().strip(), 16)
                    pid_path = usb_dev.replace('idVendor', 'idProduct')
                    with open(pid_path) as f:
                        pid = int(f.read().strip(), 16)
                    if (vid, pid) in ESP32_VID_PID:
                        # Check if this USB device has our tty
                        tty_path = os.path.join(os.path.dirname(usb_dev), f'{port_name}')
                        if os.path.exists(tty_path):
                            return True
                except:
                    continue
            return False
        
        # Read VID/PID from sysfs
        vid_path = os.path.join(sysfs_path, '../idVendor')
        pid_path = os.path.join(sysfs_path, '../idProduct')
        
        if os.path.exists(vid_path) and os.path.exists(pid_path):
            with open(vid_path) as f:
                vid = int(f.read().strip(), 16)
            with open(pid_path) as f:
                pid = int(f.read().strip(), 16)
            return (vid, pid) in ESP32_VID_PID
    except Exception:
        pass
    return False

def get_serial_connection(baudrate: int = 115200, timeout: float = 1.0) -> serial.Serial | None:
    """
    Get serial connection to ESP32 with auto port detection.
    Raises exception if no ESP32 found.
    """
    port = find_esp32_port()
    if not port:
        raise RuntimeError("No ESP32 device found. Check USB connection.")
    
    logger.info(f"Connecting to ESP32 on {port} at 115200 baud")
    return serial.Serial(
        port=port,
        baudrate=baudrate,
        timeout=1.0,
        write_timeout=1.0,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        rtscts=False,
        dsrdtr=False
    )
```

---

## ESP32 Firmware (USB Serial)

### Minimal Serial JSON Sender

```cpp
// esp32/src/main.cpp
#include <Arduino.h>
#include <ArduinoJson.h>

// Sensor pins
const uint8_t PIN_INLET = 26;
const uint8_t PIN_FIX1 = 25;
const uint8_t PIN_FIX2 = 33;
const uint8_t PIN_FIX3 = 32;

// Calibration (pulses per liter)
const float PPL_INLET = 450.0;
const float PPL_FIX1 = 450.0;
const float PPL_FIX2 = 450.0;
const float PPL_FIX3 = 450.0;

// Pulse counters (volatile for ISR)
volatile uint32_t pulseCount[4] = {0, 0, 0, 0};
volatile uint32_t lastPulseTime[4] = {0, 0, 0, 0};

// Timing
unsigned long lastSend = 0;
const unsigned long SEND_INTERVAL_MS = 5000;  // 5 seconds

// JSON document
StaticJsonDocument<512> doc;

void IRAM_ATTR pulseISR0() { if (millis() - lastPulseTime[0] > 5) { pulseCount[0]++; lastPulseTime[0] = millis(); } }
void IRAM_ATTR pulseISR1() { if (millis() - lastPulseTime[1] > 5) { pulseCount[1]++; lastPulseTime[1] = millis(); } }
void IRAM_ATTR pulseISR2() { if (millis() - lastPulseTime[2] > 5) { pulseCount[2]++; lastPulseTime[2] = millis(); } }
void IRAM_ATTR pulseISR3() { if (millis() - lastPulseTime[3] > 5) { pulseCount[3]++; lastPulseTime[3] = millis(); } }

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    // Setup pins
    pinMode(PIN_INLET, INPUT);
    pinMode(PIN_FIX1, INPUT);
    pinMode(PIN_FIX2, INPUT);
    pinMode(PIN_FIX3, INPUT);
    
    // Attach interrupts
    attachInterrupt(digitalPinToInterrupt(PIN_INLET), pulseISR0, RISING);
    attachInterrupt(digitalPinToInterrupt(PIN_FIX1), pulseISR1, RISING);
    attachInterrupt(digitalPinToInterrupt(PIN_FIX2), pulseISR2, RISING);
    attachInterrupt(digitalPinToInterrupt(PIN_FIX3), pulseISR3, RISING);
    
    Serial.println("ESP32 Water Meter Ready");
}

void loop() {
    // Check for incoming commands from RPi
    if (Serial.available()) {
        handleCommand();
    }
    
    // Periodic sensor data send
    if (millis() - lastSend >= SEND_INTERVAL_MS) {
        sendSensorData();
        lastSend = millis();
    }
}

void sendSensorData() {
    doc.clear();
    
    // Inlet (index 0)
    float inletRate = (pulseCount[0] * 60.0) / (PPL_INLET * (SEND_INTERVAL_MS / 1000.0));
    float inletVolume = pulseCount[0] / PPL_INLET;
    
    doc["inlet"]["flow_rate"] = round(inletRate * 100) / 100.0;
    doc["inlet"]["volume"] = round(inletVolume * 100) / 100.0;
    doc["inlet"]["pulses"] = pulseCount[0];
    doc["inlet"]["ppl"] = PPL_INLET;
    
    // Fixtures (1-3)
    const char* fixNames[3] = {"bidet", "kitchen", "bathroom_shower"};
    const float PPL_FIX[3] = {PPL_FIX1, PPL_FIX2, PPL_FIX3};
    
    for (int i = 0; i < 3; i++) {
        float rate = (pulseCount[i+1] * 60.0) / (PPL_FIX[i] * (SEND_INTERVAL_MS / 1000.0));
        float vol = pulseCount[i+1] / PPL_FIX[i];
        
        JsonObject fix = doc[fixNames[i]].to<JsonObject>();
        fix["flow_rate"] = round(rate * 100) / 100.0;
        fix["volume"] = round(vol * 100) / 100.0;
        fix["pulses"] = pulseCount[i+1];
        fix["ppl"] = PPL_FIX[i];
    }
    
    // Device info
    doc["device_id"] = "wm_001";
    doc["uptime_ms"] = millis();
    doc["free_heap"] = ESP.getFreeHeap();
    doc["rssi"] = WiFi.RSSI();
    
    // Serialize and send
    serializeJson(doc, Serial);
    Serial.println();  // Newline delimiter
    
    // Reset pulse counters for next interval
    for (int i = 0; i < 4; i++) pulseCount[i] = 0;
}

void handleCommand() {
    StaticJsonDocument<256> cmdDoc;
    DeserializationError err = deserializeJson(cmdDoc, Serial);
    if (err) return;
    
    const char* cmd = cmdDoc["cmd"];
    if (!cmd) return;
    
    StaticJsonDocument<256> resp;
    resp["cmd"] = cmd;
    resp["status"] = "ok";
    
    if (strcmp(cmd, "calibrate") == 0) {
        // Reset all counters, wait for known volume
        for (int i = 0; i < 4; i++) pulseCount[i] = 0;
        resp["msg"] = "Calibration mode: run known volume";
    } else if (strcmp(cmd, "reboot") == 0) {
        resp["msg"] = "Rebooting...";
        serializeJson(resp, Serial);
        Serial.println();
        ESP.restart();
    } else if (strcmp(cmd, "set_ppl") == 0) {
        int sensor = cmdDoc["sensor"] | 0;  // 0=inlet, 1-3=fixtures
        float ppl = cmdDoc["ppl"] | 450.0;
        // Update PPL (would need persistent storage)
        resp["msg"] = "PPL updated (not persistent)";
    }
    
    serializeJson(resp, Serial);
    Serial.println();
}
```

---

## RPi Python Serial Reader

### Complete Reader with Auto-Reconnect

```python
# rpi/serial_reader.py
import json
import time
import threading
import logging
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass
from serial_reader import get_serial_connection, find_esp32_port
import serial

logger = logging.getLogger(__name__)

@dataclass
class SensorReading:
    inlet: Dict[str, Any]
    bidet: Dict[str, Any]
    kitchen: Dict[str, Any]
    bathroom_shower: Dict[str, Any]
    device_id: str
    uptime_ms: int
    free_heap: int
    rssi: int
    timestamp: float

class ESP32SerialReader:
    """Reads JSON sensor data from ESP32 via USB serial with auto-reconnect."""
    
    def __init__(
        self,
        on_reading: Callable[[SensorReading], None],
        on_error: Optional[Callable[[Exception], None]] = None,
        baudrate: int = 115200,
        reconnect_delay: float = 5.0
    ):
        self.on_reading = on_reading
        self.on_error = on_error
        self.baudrate = baudrate
        self.reconnect_delay = reconnect_delay
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._serial: Optional[serial.Serial] = None
        self._buffer = ""
    
    def start(self):
        """Start reading thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        logger.info("ESP32 serial reader started")
    
    def stop(self):
        """Stop reading thread."""
        self._running = False
        if self._serial:
            self._serial.close()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("ESP32 serial reader stopped")
    
    def _read_loop(self):
        while self._running:
            try:
                # Get connection (auto-detects port)
                if not self._serial or not self._serial.is_open:
                    self._connect()
                
                # Read line
                line = self._serial.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                # Parse JSON
                self._process_line(line)
                
            except serial.SerialException as e:
                logger.warning(f"Serial error: {e}. Reconnecting in {self.reconnect_delay}s...")
                self._close_serial()
                time.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if self.on_error:
                    self.on_error(e)
                time.sleep(1)
    
    def _connect(self):
        """Establish serial connection with auto port detection."""
        while self._running:
            try:
                self._serial = get_serial_connection(baudrate=115200, timeout=1.0)
                logger.info("Serial connection established")
                self._buffer = ""
                return
            except RuntimeError as e:
                logger.warning(f"Connection failed: {e}. Retrying in {self.reconnect_delay}s...")
                time.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"Unexpected connection error: {e}")
                time.sleep(self.reconnect_delay)
    
    def _close_serial(self):
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except:
                pass
            self._serial = None
    
    def _process_line(self, line: str):
        """Parse JSON line and emit reading."""
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            logger.debug(f"Invalid JSON: {line[:100]}")
            return
        
        # Validate required fields
        required = ['inlet', 'bidet', 'kitchen', 'bathroom_shower', 'device_id']
        if not all(k in data for k in required):
            logger.debug(f"Missing required fields: {data}")
            return
        
        reading = SensorReading(
            inlet=data['inlet'],
            bidet=data.get('bidet', {}),
            kitchen=data.get('kitchen', {}),
            bathroom_shower=data.get('bathroom_shower', {}),
            device_id=data.get('device_id', 'unknown'),
            uptime_ms=data.get('uptime_ms', 0),
            free_heap=data.get('free_heap', 0),
            rssi=data.get('rssi', 0),
            timestamp=time.time()
        )
        
        # Call callback
        try:
            self.on_reading(reading)
        except Exception as e:
            logger.error(f"Callback error: {e}")
```

### Integration with ML Pipeline

```python
# rpi/main.py
from rpi.serial_reader import ESP32SerialReader, SensorReading
from rpi.ml_inference import LeakDetector
from rpi.firebase_listener import FirebaseListener
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ML detector
detector = LeakDetector(
    xgb_path='models/xgboost_model.json',
    iforest_path='models/isolation_forest.pkl',
    scaler_path='models/scaler.pkl',
    threshold_path='models/iso_threshold.pkl'
)
detector.warm_up()

# Initialize Firebase (for alerts/commands)
firebase = FirebaseListener(
    config_path='firebase_config.json',
    email='esp32@project.iam.gserviceaccount.com',
    password='password',
    device_id='wm_001'
)
firebase.set_detector(detector)
firebase.start()

# Callback for serial readings
def on_reading(reading: SensorReading):
    logger.info(f"Inlet: {reading.inlet['flow_rate']:.2f} L/min, "
                f"Bidet: {reading.bidet.get('flow_rate', 0):.2f}, "
                f"Kitchen: {reading.kitchen.get('flow_rate', 0):.2f}, "
                f"Shower: {reading.bathroom_shower.get('flow_rate', 0):.2f}")
    
    # Run ML inference per fixture
    for fixture_name in ['bidet', 'kitchen', 'bathroom_shower']:
        fixture = getattr(reading, fixture_name)
        if fixture.get('flow_rate', 0) > 0.01:
            features = extract_features(reading, fixture_name)  # 9 features
            result = detector.predict(features)
            
            if result['final'] != 'normal':
                logger.warning(f"LEAK: {result['final']} on {fixture_name} (conf: {result['confidence']:.2f})")
                firebase.write_alert({
                    'alert_type': result['final'],
                    'fixture': fixture_name,
                    'confidence': result['confidence'],
                    'details': result
                })

# Start serial reader
reader = ESP32SerialReader(on_reading=on_reading)
reader.start()

# Keep main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    reader.stop()
    firebase.stop()
```

---

## Message Protocol (JSON)

### ESP32 → RPi (Sensor Data)

```json
{
  "inlet": {
    "flow_rate": 12.5,
    "volume": 2.5,
    "pulses": 1125,
    "ppl": 450
  },
  "bidet": {
    "flow_rate": 5.2,
    "volume": 0.9,
    "pulses": 405,
    "ppl": 450
  },
  "kitchen": {
    "flow_rate": 0.0,
    "volume": 0.0,
    "pulses": 0,
    "ppl": 450
  },
  "bathroom_shower": {
    "flow_rate": 0.2,
    "volume": 0.02,
    "pulses": 10,
    "ppl": 450
  },
  "device_id": "wm_001",
  "uptime_ms": 86400000,
  "free_heap": 180000,
  "rssi": -65
}
```

### RPi → ESP32 (Commands)

```json
{"cmd": "calibrate"}
{"cmd": "reboot"}
{"cmd": "set_ppl", "sensor": 0, "ppl": 462.5}
```

### ESP32 → RPi (Command Response)

```json
{"cmd": "calibrate", "status": "ok", "msg": "Calibration mode: run known volume"}
{"cmd": "reboot", "status": "ok", "msg": "Rebooting..."}
```

---

## Auto Port Detection Logic

### Detection Priority

1. **`/dev/ttyESP32`** (udev symlink) — highest priority
2. **`/dev/ttyUSB*`** with matching VID:PID (CP2102/CH340)
3. **`/dev/ttyACM*`** with matching VID:PID (native USB)

### Detection Flow

```
find_esp32_port()
    │
    ├─ Check /dev/ttyESP32 (udev symlink) → return if exists
    │
    ├─ Scan /dev/ttyUSB* and /dev/ttyACM*
    │     │
    │     ├─ For each port: read VID:PID from sysfs
    │     │
    │     ├─ Match against known ESP32 VID:PID pairs
    │     │
    │     └─ Return first match
    │
    └─ No match → return None
```

### Known ESP32 VID:PID Pairs

| Chip | VID (hex) | PID (hex) | Description |
|------|-----------|-----------|-------------|
| CP2102/CP2104 | 0x10c4 | 0xea60 | NodeMCU-32S, most ESP32 dev boards |
| CH340/CH341 | 0x1a86 | 0x7523 | Cheap ESP32 boards |
| ESP32-S3 native | 0x303a | 0x1001 | Native USB (no bridge) |

---

## Error Handling & Reconnection

### Reconnection Strategy

| Failure Type | Action | Delay |
|--------------|--------|-------|
| Port not found | Scan all ttyUSB/ttyACM, retry | 5 sec |
| Permission denied | Check dialout group, retry | 5 sec |
| SerialException (disconnect) | Close port, re-scan, reopen | 5 sec |
| JSON decode error | Log warning, continue | 1 sec |
| Buffer overflow | Reset buffer, continue | 1 sec |

### Buffer Management

```python
def _process_line(self, line: str):
    """Handle incomplete/truncated lines."""
    self._buffer += line
    
    while '\n' in self._buffer:
        line, self._buffer = self._buffer.split('\n', 1)
        self._process_line(line.strip())
```

---

## Testing & Verification

### 1. Verify Hardware Connection

```bash
# Check USB device
lsusb | grep -E "(10c4:ea60|1a86:7523|303a:1001)"
# Should show: Bus 001 Device 004: ID 10c4:ea60 Cygnal Integrated Products, Inc. CP210x

# Check serial port
ls -l /dev/ttyUSB* /dev/ttyACM* /dev/ttyESP32
# Should show: /dev/ttyUSB0 or /dev/ttyESP32 -> ttyUSB0
```

### 2. Test Serial Communication

```bash
# Using screen (exit: Ctrl+A, K, Y)
screen /dev/ttyUSB0 115200

# Or using Python one-liner
python3 -c "
import serial, time
s = serial.Serial('/dev/ttyUSB0', 115200, timeout=2)
time.sleep(2)
for _ in range(5):
    line = s.readline().decode().strip()
    print(line)
"
```

### 3. Verify JSON Output

```json
// Expected output every 5 seconds:
{
  "inlet": {"flow_rate": 12.5, "volume": 2.5, "pulses": 1125, "ppl": 450},
  "bidet": {"flow_rate": 5.2, "volume": 0.9, "pulses": 405, "ppl": 450},
  "kitchen": {"flow_rate": 0.0, "volume": 0.0, "pulses": 0, "ppl": 450},
  "bathroom_shower": {"flow_rate": 0.2, "volume": 0.02, "pulses": 10, "ppl": 450},
  "device_id": "wm_001",
  "uptime_ms": 123456,
  "free_heap": 180000,
  "rssi": -65
}
```

### 4. End-to-End Test Script

```bash
# test_serial.py
python3 -c "
from rpi.serial_reader import ESP32SerialReader, SensorReading
import time

def on_reading(r):
    print(f'Inlet: {r.inlet[\"flow_rate\"]:.2f} L/min | '
          f'Bidet: {r.bidet.get(\"flow_rate\",0):.2f} | '
          f'Kitchen: {r.kitchen.get(\"flow_rate\",0):.2f} | '
          f'Shower: {r.bathroom_shower.get(\"flow_rate\",0):.2f}')

reader = ESP32SerialReader(on_reading=lambda r: print(f'OK: {r.device_id}'))
reader.start()
time.sleep(15)
reader.stop()
print('Test passed!')
"
```

---

## Quick Reference

| Task | Command/Code |
|------|--------------|
| Find ESP32 port | `python3 -c "from serial_port import find_esp32_port; print(find_esp32_port())"` |
| Monitor serial | `screen /dev/ttyUSB0 115200` |
| Check permissions | `groups \$USER` (must include `dialout`) |
| Add udev rule | `sudo tee /etc/udev/rules.d/99-esp32.rules < rules.txt && sudo udevadm control --reload && sudo udevadm trigger` |
| Install deps | `pip install pyserial` |

---

## Official References

- [pyserial Documentation](https://pyserial.readthedocs.io/)
- [ESP32 Arduino Serial](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/serial.html)
- [ArduinoJson v7](https://arduinojson.org/v7/doc/)
- [udev Rules](https://www.freedesktop.org/software/systemd/man/udev.html)
- [USB VID/PID Database](https://www.linux-usb.org/usb.ids)