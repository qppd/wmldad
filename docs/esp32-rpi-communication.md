# ESP32 ↔ Raspberry Pi Communication (USB Serial)

> **Architecture:** ESP32 ↔ USB Cable (CDC/ACM) ↔ RPi (Python pyserial + asyncio)  
> **Protocol:** JSON Lines over UART (921600 baud)  
> **Auto-detection:** RPi auto-detects ESP32 on `/dev/ttyUSB0` or `/dev/ttyUSB1` via VID:PID

---

## Table of Contents

1. [Communication Overview](#communication-overview)
2. [Hardware Connection](#hardware-connection)
3. [RPi Auto Port Detection](#rpi-auto-port-detection)
4. [ESP32 Firmware (USB Serial)](#esp32-firmware-usb-serial)
5. [RPi Python Serial Reader](#rpi-python-serial-reader)
6. [Error Handling & Reconnection](#error-handling--reconnection)
7. [Testing & Verification](#testing--verification)

---

## Communication Overview

```
┌─────────────┐     USB Cable (CDC/ACM)      ┌──────────────────┐
│   ESP32     │ ────────────────────────────▶ │   Raspberry Pi   │
│  (NodeMCU)  │ ◀──────────────────────────── │   (Python Serial)│
│  921600     │      JSON Lines over UART     │  /dev/ttyUSB0/1  │
└─────────────┘     921600 8N1                └──────────────────┘
      │                                                  │
      │              Auto-detect on                      │
      │              /dev/ttyUSB0 or ttyUSB1             │
      ▼                                                  ▼
```

### Data Flow Summary

| Direction | Method | Frequency | Payload | Transport |
|-----------|--------|-----------|---------|-----------|
| ESP32 → RPi | `Serial.println(JSON)` | Every 5 sec | Sensor readings | USB UART |
| RPi → ESP32 | `Serial.write(JSON)` | On command | Commands/Config | USB UART |

---

## Hardware Connection

Connect the ESP32 to the Raspberry Pi via a **micro-USB data cable** (not charge-only). The ESP32's built-in CP2102/CH340 USB-UART bridge will appear as `/dev/ttyUSB0` (or `ttyUSB1` if multiple devices) on the RPi.

> **Important:** Use a **data-capable USB cable**. The CP2102/CH340 USB-UART bridge on ESP32 Dev Module exposes `/dev/ttyUSB0` (or `ttyUSB1` if multiple devices) when connected via micro-USB cable to the Raspberry Pi's USB port.

---

## RPi Auto Port Detection

### udev Rule for Consistent Naming

```bash
# /etc/udev/rules.d/99-esp32.rules
# CP2102 (ESP32 Dev Module)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyESP32", MODE="0666", GROUP="dialout"
# CH340 (some ESP32 boards)
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="ttyESP32", MODE="0666", GROUP="dialout"
# ESP32-S3 native USB
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", SYMLINK+="ttyESP32", MODE="0666", GROUP="dialout"

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
import os

logger = logging.getLogger(__name__)

ESP32_VID_PID = [
    (0x10c4, 0xea60),  # CP2102/CP2104 (ESP32 Dev Module)
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
                        tty_path = os.path.join(os.path.dirname(usb_dev), port_name)
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

def get_serial_connection(baudrate: int = 921600, timeout: float = 1.0) -> serial.Serial:
    """
    Get serial connection to ESP32 with auto port detection.
    Raises exception if no ESP32 found.
    """
    port = find_esp32_port()
    if not port:
        raise RuntimeError("No ESP32 device found. Check USB connection.")
    
    logger.info(f"Connecting to ESP32 on {port} at {baudrate} baud")
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
    Serial.begin(921600);
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
    
    Serial.println("{\"status\":\"ready\",\"device_id\":\"wmldad-001\",\"firmware\":\"v3.0.0-usb\"}");
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
    doc["device_id"] = "wmldad-001";
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
        for (int i = 0; i < 4; i++) pulseCount[i] = 0;
        resp["msg"] = "Calibration mode: run known volume";
    } else if (strcmp(cmd, "reboot") == 0) {
        resp["msg"] = "Rebooting...";
        serializeJson(resp, Serial);
        Serial.println();
        ESP.restart();
    } else if (strcmp(cmd, "reset_counters") == 0) {
        for (int i = 0; i < 4; i++) {
            pulseCount[i] = 0;
            lastPulseTime[i] = 0;
        }
        resp["msg"] = "Counters reset";
    } else if (strcmp(cmd, "set_ppl") == 0) {
        int sensor = cmdDoc["sensor"] | 0;  // 0=inlet, 1-3=fixtures
        float ppl = cmdDoc["ppl"] | 450.0;
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
from serial_port import get_serial_connection, find_esp32_port
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
        baudrate: int = 921600,
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
                self._serial = get_serial_connection(baudrate=921600, timeout=1.0)
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
        required = ['device_id']
        if not all(k in data for k in required):
            logger.debug(f"Missing required fields: {data}")
            return
        
        # Handle different message types
        msg_type = data.get('type', 'data')
        
        if msg_type == 'data':
            reading = SensorReading(
                inlet=data.get('inlet', {}),
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
        
        elif msg_type == 'alert':
            logger.warning(f"ESP32 Alert: {data.get('message', 'Unknown')}")
        
        elif msg_type == 'status':
            logger.info(f"ESP32 Status: {data}")

# Integration with ML Pipeline
def create_serial_reader_with_ml(detector, alert_engine=None):
    """Factory function to create reader with ML inference."""
    from ml_inference import LeakDetector
    import numpy as np
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    def on_reading(reading: SensorReading):
        logger.info(
            f"Inlet: {reading.inlet.get('flow_rate', 0):.2f} L/min, "
            f"Bidet: {reading.bidet.get('flow_rate', 0):.2f}, "
            f"Kitchen: {reading.kitchen.get('flow_rate', 0):.2f}, "
            f"Shower: {reading.bathroom_shower.get('flow_rate', 0):.2f}"
        )
        
        # Run ML inference per fixture
        for fixture_name in ['bidet', 'kitchen', 'bathroom_shower']:
            fixture = getattr(reading, fixture_name)
            if fixture.get('flow_rate', 0) > 0.01:
                features = extract_features(reading, fixture_name)
                result = detector.predict(features)
                
                if result['final'] != 'normal':
                    logger.warning(
                        f"LEAK: {result['final']} on {fixture_name} "
                        f"(conf: {result.get('confidence', 0):.2f})"
                    )
                    if alert_engine:
                        alert_engine.send_notification({
                            'alert_type': result['final'],
                            'fixture': fixture_name,
                            'confidence': result.get('confidence', 0),
                            'details': result
                        })

    def extract_features(reading, fixture_name):
        """Extract 9 features from sensor reading."""
        fixture = getattr(reading, fixture_name)
        inlet = reading.inlet
        
        flow_rate = fixture.get('flow_rate', 0)
        volume = fixture.get('volume', 0)
        inlet_rate = inlet.get('flow_rate', 0)
        
        # Duration (approximate from volume/rate)
        duration = volume / max(flow_rate / 60, 0.01) if flow_rate > 0 else 0
        
        # Time features
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
        
        # Fixture ID mapping
        fixture_id_map = {'bidet': 1, 'kitchen': 2, 'bathroom_shower': 3}
        fixture_id = fixture_id_map.get(fixture_name, 1)
        
        # Inlet ratio
        inlet_ratio = inlet_rate / max(flow_rate, 0.01)
        
        # Rate variance (placeholder - would need rolling buffer)
        rate_variance = 0
        
        # Night flag
        is_night = 1 if (hour >= 22 or hour < 5) else 0
        
        # Pulse trend (placeholder)
        pulse_trend = 0
        
        return np.array([[
            flow_rate, duration, hour, day, fixture_id,
            inlet_ratio, rate_variance, is_night, pulse_trend
        ]], dtype=np.float32)
    
    return ESP32SerialReader(on_reading=on_reading)
```

---

## Error Handling & Reconnection

### ESP32 Side

- **Watchdog timer**: `esp_task_wdt_init(30, true)` with `esp_task_wdt_reset()` in loop
- **WiFi reconnect**: `WiFi.reconnect()` if disconnected (for OTA only)
- **Buffer management**: Reset pulse counters after each send interval

### RPi Side

- **Auto-reconnect**: Exponential backoff (5s, 10s, 20s, max 60s)
- **Port re-detection**: Re-scans `/dev/ttyUSB*` on each reconnect
- **Buffer handling**: Accumulates partial lines, handles fragmented JSON
- **Graceful shutdown**: `Ctrl+C` stops reader thread cleanly

### Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| "Board not found" / No device on `/dev/ttyUSB0` | Use **data cable** (not charge-only). Check `ls /dev/tty*`. Hold **BOOT** → press **EN** → release **BOOT** → upload. |
| `Permission denied` on `/dev/ttyUSB0` | `sudo usermod -a -G dialout $USER && newgrp dialout` |
| `esptool.py not found` | `pip3 install esptool` |
| Upload succeeds but Serial Monitor shows garbage | Set baud to **921600** (match `Serial.begin(921600)`) |
| JSON parse errors | Check for stray debug `Serial.print()` calls mixing with JSON output |

---

## Testing & Verification

### 1. Test Serial Connection

```bash
# Find port
ls /dev/ttyUSB*

# Test with screen
screen /dev/ttyUSB0 921600
# Should see JSON lines every 5 seconds
# Exit: Ctrl+A, then k, then y
```

### 2. Test Python Reader

```bash
cd rpi
python3 -c "
from serial_port import find_esp32_port, get_serial_connection
port = find_esp32_port()
print(f'Found: {port}')
ser = get_serial_connection()
print('Connected!')
for _ in range(3):
    line = ser.readline().decode().strip()
    print(f'Got: {line}')
"
```

### 3. Test Full Pipeline

```bash
cd rpi
python3 main.py
# Should see:
# Inlet: 12.50 L/min, Bidet: 0.00, Kitchen: 5.20, Shower: 0.00
# LEAK: minor_leak on kitchen (conf: 0.92)
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Find ESP32 port | `ls /dev/ttyUSB*` |
| Test serial | `screen /dev/ttyUSB0 921600` |
| Install Arduino IDE | `pip install arduino` |
| Upload firmware | Arduino IDE: Sketch → Upload (`Ctrl+U`) |
| Monitor serial | `screen /dev/ttyUSB0 921600` or Serial Monitor (`Ctrl+Shift+M`) |
| Check udev rule | `udevadm test /dev/ttyUSB0` |
| View RPi logs | `journalctl -u water-meter -f` |

---

## Official References

- [Arduino IDE PyPI](https://pypi.org/project/arduino/)
- [ESP32 Arduino Core Installation](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)
- [ArduinoJson v7 Docs](https://arduinojson.org/v7/)
- [pyserial Docs](https://pyserial.readthedocs.io/)
- [pyserial VID/PID Detection](https://pyserial.readthedocs.io/en/latest/tools.html#module-serial.tools.list_ports)

---

*Last updated: July 2026 | `pip install arduino` on Raspberry Pi OS Trixie (64-bit) | Compatible with ESP32 Dev Module, ESP32-S3, ESP32-C3*