# Complete Raspberry Pi OS Setup to Water Meter Project Deployment

> **Target:** Raspberry Pi 3B+/4/5  
> **OS:** Raspberry Pi OS Trixie 64-bit (Debian 13)  
> **Goal:** Fresh Pi OS → SSH + VNC → Full Water Meter Backend (Flask + ML + USB Serial)  
> **Audience:** Beginners to intermediate — no prior Linux/RPi experience needed

---

## Table of Contents

### Phase 1: Pi OS Foundation
1. [Download & Flash Raspberry Pi OS](#1-download--flash-raspberry-pi-os)
2. [Initial Boot & SSH Verification](#2-initial-boot--ssh-verification)
3. [Enable SSH (If Not Done in Imager)](#3-enable-ssh-if-not-done-in-imager)
4. [Configure Networking (WiFi + mDNS)](#4-configure-networking-wifi--mdns)
5. [Expand Filesystem](#5-expand-filesystem)
6. [System Update & Upgrade](#6-system-update--upgrade)
7. [Enable RealVNC Server](#7-enable-realvnc-server)

### Phase 2: Project Setup
9. [Clone Water Meter Project](#9-clone-water-meter-project)
10. [Create Python Virtual Environment](#10-create-python-virtual-environment)
11. [Install All Project Dependencies](#11-install-all-project-dependencies)
12. [Configure USB Serial (udev rule)](#12-configure-usb-serial-udev-rule)
13. [Create Backend Application Files](#13-create-backend-application-files)
14. [Add ML Model Files](#14-add-ml-model-files)
15. [Verify Installation](#15-verify-installation)
16. [Systemd Service for Auto-start](#16-systemd-service-for-auto-start)

---

## Phase 1: Pi OS Foundation

## 1. Download & Flash Raspberry Pi OS

### 1.1 Download Raspberry Pi Imager
1. Go to: https://www.raspberrypi.com/software/
2. Download **Raspberry Pi Imager** for your OS (Windows/macOS/Linux)
3. Install and launch

### 1.2 Select OS Image
1. **Choose Device:** Your Pi model (Pi 4/5 → Raspberry Pi 4/5; Pi 3B+ → Raspberry Pi 3)
2. **Choose OS:** 
   - Click **Operating System** → **Raspberry Pi OS (Other)** → **Raspberry Pi OS (64-bit)**
   - ⚠️ **Important:** Select the **64-bit** version (required for XGBoost/ML)
   - Version: **Trixie (Debian 13)** — latest as of 2026
3. **Choose Storage:** Your microSD card (minimum 16 GB, recommended 32 GB+)

### 1.3 Pre-configure OS Settings (Before Flashing)
Click the **gear icon (⚙️ Advanced Options)** or press `Ctrl+Shift+X`:

| Setting | Value | Why |
|---------|-------|-----|
| **Hostname** | `water-meter` | Access via `water-meter.local` |
| **Enable SSH** | ✅ **Checked** | Remote terminal access |
| **SSH Password Auth** | ✅ **Checked** | Use password (not keys) |
| **Username** | `pi` | Default user |
| **Password** | `your-strong-password` | **Change from default!** |
| **Configure Wireless LAN** | ✅ **Checked** | Pre-configure WiFi |
| **SSID** | `YourWiFiName` | Your router's WiFi name |
| **Password** | `YourWiFiPassword` | Your WiFi password |
| **Wireless Country** | `PH` (or your country) | Regulatory domain |
| **Locale** | `en_US.UTF-8` | Language/encoding |
| **Timezone** | `Asia/Manila` (or your timezone) | Correct timestamps |
| **Keyboard Layout** | `us` | Standard US layout |

> 📸 **Screenshot Placeholder:** *Raspberry Pi Imager Advanced Options showing all settings configured*

### 1.4 Flash the SD Card
1. Click **Write**
2. Confirm overwrite warning
3. Wait for "Write Successful" (2-5 minutes)
4. Eject SD card safely

---

## 2. Initial Boot & SSH Verification

### 2.1 First Boot
1. Insert SD card into Pi
2. Connect power (5V 3A+ USB-C for Pi 4/5; micro-USB for Pi 3B+)
3. Wait 60-90 seconds for first boot (auto-resize, SSH key gen)

### 2.2 Verify SSH Access
From your computer (Linux/macOS/Windows 10+):

```bash
# Test mDNS hostname (preferred)
ssh pi@water-meter.local

# If mDNS fails, find IP via router or:
ssh pi@192.168.1.xxx
```

**First connection:** Type `yes` to accept host key, then enter your password.

> ⚠️ **Windows Users:** If `water-meter.local` doesn't resolve, install [Bonjour Print Services](https://support.apple.com/kb/DL999) or use IP address.

---

## 3. Enable SSH (If Not Done in Imager)

> **Skip if you configured SSH in Raspberry Pi Imager**

```bash
# On Pi (with monitor/keyboard) or via temporary connection:
sudo raspi-config
# Navigate: Interface Options → SSH → Yes → OK → Finish
sudo systemctl enable ssh
sudo systemctl start ssh
```

**Verify:**
```bash
systemctl status ssh
# Should show: Active: active (running)
```

---

## 4. Configure Networking (WiFi + mDNS)

### 4.1 Verify WiFi Connection
```bash
# Check IP address
hostname -I
# Should show: 192.168.1.xxx (your Pi's IP)

# Test internet
ping -c 3 8.8.8.8
ping -c 3 google.com
```

### 4.2 Set Static IP (Optional but Recommended)

**Option A: Router DHCP Reservation (Best)**
1. Log into router admin (192.168.1.1)
2. Find **DHCP Reservation** / **Address Reservation**
3. Add: MAC address of Pi → IP `192.168.1.100` (outside DHCP pool)
4. Reboot Pi

**Option B: nmcli on Pi**
```bash
# Show connections
nmcli con show

# Set static IP for WiFi (replace "YourWiFiSSID" with actual name)
sudo nmcli con mod "YourWiFiSSID" \
    ipv4.addresses 192.168.1.100/24 \
    ipv4.gateway 192.168.1.1 \
    ipv4.dns "192.168.1.1, 8.8.8.8" \
    ipv4.method manual

sudo nmcli con up "YourWiFiSSID"
```

### 4.3 Verify mDNS (hostname.local)
```bash
# From your computer:
ping water-meter.local
# Should resolve to Pi's IP

# On Pi - check Avahi:
systemctl status avahi-daemon
# Should show: active (running)
```

---

## 5. Expand Filesystem

> **Usually automatic on first boot**, but verify:

```bash
# Check disk usage
df -h /
# Should show full SD card size (e.g., 29G on 32GB card)

# If not expanded:
sudo raspi-config
# Advanced Options → Expand Filesystem → OK → Reboot
```

---

## 6. System Update & Upgrade

```bash
# Update package lists
sudo apt update

# Full upgrade (includes kernel, firmware)
sudo apt full-upgrade -y

# Install essential tools
sudo apt install -y \
    git \
    curl \
    wget \
    vim \
    htop \
    tree \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libopenblas-dev \
    libatlas-base-dev \
    pkg-config \
    cmake

# Clean up
sudo apt autoremove -y
sudo apt clean

# Reboot if kernel updated
sudo reboot
```

**Wait for reboot, then reconnect:**
```bash
ssh pi@water-meter.local
```

---

## 7. Enable RealVNC Server

RealVNC is **pre-installed** on Raspberry Pi OS Desktop. You only need to enable it.

### 7.1 Verify Installation
```bash
# Check if RealVNC is installed
dpkg -l | grep realvnc
# Should show: realvnc-vnc-server, realvnc-vnc-viewer
```

### 7.2 Enable VNC Server
```bash
# Via raspi-config (recommended)
sudo raspi-config
# Interface Options → VNC → Yes → OK → Finish
```

Or via systemctl:
```bash
sudo systemctl enable vncserver-x11-serviced
sudo systemctl start vncserver-x11-serviced

# Check status
systemctl status vncserver-x11-serviced
```

### 7.3 Set VNC Password (Required for Touchscreen/Remote)
```bash
# Set VNC password (different from user password)
sudo -u pi vncpasswd -service
# Enter password twice (8 chars max)

# Restart VNC service
sudo systemctl restart vncserver-x11-serviced
```

### 7.4 Configure Display Resolution (for 800×480 Touchscreen)
```bash
# Set resolution for 7" touchscreen
sudo raspi-config
# Advanced Options → Resolution → 800x480
# OR via config.txt:
echo "hdmi_force_hotplug=1" | sudo tee -a /boot/firmware/config.txt
echo "hdmi_group=2" | sudo tee -a /boot/firmware/config.txt
echo "hdmi_mode=87" | sudo tee -a /boot/firmware/config.txt
echo "hdmi_cvt=800 480 60 6 0 0 0" | sudo tee -a /boot/firmware/config.txt

sudo reboot
```

### 7.5 Connect via VNC Viewer
1. Download **VNC Viewer** on your computer: https://www.realvnc.com/en/connect/download/viewer/
2. Open VNC Viewer
3. Enter: `water-meter.local` or `192.168.1.100`
4. Enter VNC password (set in 7.3)

> 📸 **Screenshot Placeholder:** *VNC Viewer connecting to water-meter.local*

---

## Phase 2: Project Setup

## 9. Clone Water Meter Project

```bash
# Via SSH or VNC terminal
cd /home/pi

# Clone repository
git clone https://github.com/qppd/wmldad.git
cd wmldad

# Verify structure
ls -la
# Should see: docs/, rpi/, esp32/, training/, model/, wiring/
```

---

## 10. Create Python Virtual Environment

```bash
cd /home/pi/wmldad/rpi

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Verify
which python
# /home/pi/wmldad/rpi/venv/bin/python

python --version
# Python 3.12.x

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 10.1 Make Activation Persistent (Optional)
```bash
# Add to .bashrc for auto-activation on SSH login
echo 'source /home/pi/wmldad/rpi/venv/bin/activate' >> ~/.bashrc
source ~/.bashrc
```

---

## 11. Install All Project Dependencies

### 11.1 Create requirements.txt
```bash
cd /home/pi/wmldad/rpi

cat > requirements.txt << 'EOF'
# ML Dependencies
xgboost==2.0.3
scikit-learn==1.3.2
pandas==2.1.4
numpy==1.24.3
joblib==1.3.2

# Web Dependencies
flask==3.0.0
gunicorn==21.2.0
python-dotenv==1.0.0
requests==2.31.0

# Serial Communication
pyserial==3.5
pyserial-asyncio==0.6
EOF
```

### 11.2 Install Dependencies
```bash
# Activate venv if not already
source /home/pi/wmldad/rpi/venv/bin/activate

# Install (takes 5-10 minutes on Pi - compiling xgboost/numpy)
pip install --no-cache-dir -r requirements.txt

# Verify
python -c "
import xgboost, sklearn, pandas, numpy, flask, serial
print('✅ All packages installed successfully')
print(f'XGBoost: {xgboost.__version__}')
print(f'sklearn: {sklearn.__version__}')
print(f'Flask: {flask.__version__}')
"
```

---

## 12. Configure USB Serial (udev rule)

Create a persistent symlink `/dev/ttyESP32` for the ESP32 USB device:

```bash
# Create udev rule
cat > /tmp/99-esp32.rules << 'EOF'
# CP2102 (ESP32 Dev Module)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyESP32", MODE="0666", GROUP="dialout"
# CH340 (some ESP32 boards)
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="ttyESP32", MODE="0666", GROUP="dialout"
# ESP32-S3 native USB
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", SYMLINK+="ttyESP32", MODE="0666", GROUP="dialout"
EOF

sudo mv /tmp/99-esp32.rules /etc/udev/rules.d/99-esp32.rules

# Apply rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add pi user to dialout group (for serial access)
sudo usermod -a -G dialout pi

# Verify (after reconnecting ESP32 via USB)
ls -la /dev/ttyESP32
# Should show symlink to ttyUSB0 or ttyUSB1
```

> **Note:** Log out and back in (or reboot) for group changes to take effect.

---

## 13. Create Backend Application Files

Create all backend files in `/home/pi/wmldad/rpi/`. Each file is created with `cat > filename << 'EOF'`.

### 13.1 Create ml_inference.py (XGBoost + Isolation Forest)

```bash
cat > ml_inference.py << 'PYEOF'
"""
ML Inference — XGBoost + Isolation Forest
Production leak detector for Raspberry Pi.
"""

import xgboost as xgb
import joblib
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Union, List

logger = logging.getLogger(__name__)


class LeakDetector:
    """Production leak detector combining XGBoost + Isolation Forest."""

    def __init__(
        self,
        xgb_path: str = 'models/xgboost_model.json',
        iforest_path: str = 'models/isolation_forest.pkl',
        scaler_path: str = 'models/scaler.pkl',
        threshold_path: str = 'models/iso_threshold.pkl',
        feature_cols_path: str = 'models/feature_cols.pkl',
        confidence_threshold: float = 0.80
    ):
        self.xgb_path = Path(xgb_path)
        self.iforest_path = Path(iforest_path)
        self.scaler_path = Path(scaler_path)
        self.threshold_path = Path(threshold_path)
        self.feature_cols_path = Path(feature_cols_path)
        self.confidence_threshold = confidence_threshold
        
        self.model_loaded = False
        self.n_features = 9
        self.target_names = ['normal', 'minor_leak', 'major_leak']
        self.inference_count = 0
        
        self._load_models()

    def _load_models(self):
        """Load all model artifacts"""
        try:
            # XGBoost
            self.xgb = xgb.XGBClassifier()
            self.xgb.load_model(str(self.xgb_path))
            
            # Isolation Forest
            self.iso_forest = joblib.load(self.iforest_path)
            
            # Scaler
            self.scaler = joblib.load(self.scaler_path)
            
            # Threshold
            self.iso_threshold = joblib.load(self.threshold_path)
            
            # Feature columns
            self.feature_cols = joblib.load(self.feature_cols_path)
            self.n_features = len(self.feature_cols)
            
            self.model_loaded = True
            logger.info("✅ All models loaded successfully")
            logger.info(f"   XGBoost: {self.xgb.n_estimators} trees, {self.n_features} features")
            logger.info(f"   Isolation Forest: {self.iso_forest.n_estimators} estimators")
            logger.info(f"   Threshold: {self.iso_threshold:.4f}")
            
        except Exception as e:
            logger.error(f"❌ Model loading failed: {e}")
            self.model_loaded = False
            raise
    
    def predict(self, features_raw: Union[np.ndarray, List]) -> Dict[str, Any]:
        """Run inference on raw features."""
        if not self.model_loaded:
            raise RuntimeError("Models not loaded")
        
        # Ensure 2D array
        features = np.asarray(features_raw, dtype=np.float32)
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Validate feature count
        if features.shape[1] != self.n_features:
            raise ValueError(f"Expected {self.n_features} features, got {features.shape[1]}")
        
        # Scale
        features_scaled = self.scaler.transform(features)
        
        results = []
        
        for i in range(features_scaled.shape[0]):
            sample = features_scaled[i:i+1]
            
            # 1. XGBoost inference
            xgb_proba = self.xgb.predict_proba(sample)[0]
            xgb_pred = int(np.argmax(xgb_proba))
            xgb_conf = float(xgb_proba[xgb_pred])
            
            # 2. Isolation Forest
            iso_score = float(self.iso_forest.score_samples(sample)[0])
            iso_anomaly = bool(iso_score < self.iso_threshold)
            
            # Build result
            result = {
                'xgboost': {
                    'class': self.target_names[xgb_pred],
                    'confidence': xgb_conf,
                    'probabilities': {
                        name: float(xgb_proba[j]) 
                        for j, name in enumerate(self.target_names)
                    }
                },
                'isolation_forest': {
                    'anomaly': iso_anomaly,
                    'score': iso_score
                }
            }
            
            # Decision logic
            if xgb_conf >= self.confidence_threshold:
                result['final'] = result['xgboost']['class']
                result['confidence'] = xgb_conf
            elif iso_anomaly:
                result['final'] = 'anomaly'
                result['confidence'] = float(1.0 - abs(iso_score))
            else:
                result['final'] = 'uncertain'
                result['confidence'] = xgb_conf
            
            results.append(result)
        
        self.inference_count += 1
        
        # Periodic garbage collection
        if self.inference_count % 1000 == 0:
            import gc
            gc.collect()
        
        return results[0] if len(results) == 1 else results
    
    def warm_up(self, n_warmup: int = 10):
        """Run dummy inferences to warm up."""
        dummy = np.zeros((1, self.n_features), dtype=np.float32)
        for _ in range(n_warmup):
            _ = self.predict(dummy)
        logger.info(f"🔥 Warm-up complete ({n_warmup} iterations)")
    
    def benchmark(self, n_iterations: int = 100) -> Dict[str, float]:
        """Benchmark inference speed."""
        import time
        
        dummy = np.zeros((1, self.n_features), dtype=np.float32)
        
        # Warm up
        self.warm_up(10)
        
        # Benchmark
        start = time.perf_counter()
        for _ in range(n_iterations):
            _ = self.predict(dummy)
        elapsed = time.perf_counter() - start
        
        return {
            'total_time_ms': elapsed * 1000,
            'avg_time_ms': (elapsed / n_iterations) * 1000,
            'iterations': n_iterations,
            'throughput_fps': n_iterations / elapsed
        }


def load_deployment_package(model_dir: str = 'models') -> Dict[str, Any]:
    """Load complete deployment package from directory."""
    model_dir = Path(model_dir)
    
    detector = LeakDetector(
        xgb_path=model_dir / 'xgboost_model.json',
        iforest_path=model_dir / 'isolation_forest.pkl',
        scaler_path=model_dir / 'scaler.pkl',
        threshold_path=model_dir / 'iso_threshold.pkl',
        feature_cols_path=model_dir / 'feature_cols.pkl'
    )
    
    import json
    with open(model_dir / 'metadata.json') as f:
        metadata = json.load(f)
    
    return {
        'detector': detector,
        'metadata': metadata
    }
PYEOF
```

### 13.2 Create serial_reader.py (pyserial + asyncio)

```bash
cat > serial_reader.py << 'PYEOF'
"""
ESP32 Serial Reader — Reads JSON Lines from ESP32 via USB Serial
with auto-reconnect and auto port detection.
"""

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
    import logging
    
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
                    # Write alert to DB if needed
                    if alert_engine:
                        alert_engine.send_notification({
                            'alert_type': result['final'],
                            'fixture': fixture_name,
                            'confidence': result.get('confidence', 0),
                            'details': result
                        })

    def extract_features(reading, fixture_name):
        """Extract 9 features from sensor reading."""
        import numpy as np
        from datetime import datetime
        
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
PYEOF
```

### 13.3 Create serial_port.py (auto-detection)

```bash
cat > serial_port.py << 'PYEOF'
"""
Serial Port Auto-Detection for ESP32
Finds ESP32 on /dev/ttyUSB* or /dev/ttyACM* by VID:PID
"""

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
    Raises RuntimeError if no ESP32 found.
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
PYEOF
```

### 13.4 Create alert_engine.py

```bash
cat > alert_engine.py << 'PYEOF'
"""
Alert Engine — In-app notifications via dashboard polling /api/alerts
"""

import logging
from typing import Dict, Any
import sqlite3
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class AlertEngine:
    """Handles in-app alert notifications via database + API polling."""
    
    def __init__(self, db_path: str = 'data/alerts.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for alerts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    fixture TEXT,
                    confidence REAL,
                    details TEXT,
                    timestamp REAL NOT NULL,
                    acknowledged INTEGER DEFAULT 0
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON alerts(timestamp)')
            conn.commit()
    
    def send_notification(self, alert_data: Dict[str, Any]):
        """
        Send notification for alert.
        
        The alert is written to SQLite database.
        The Flask dashboard polls /api/alerts and displays them in real-time.
        """
        alert_type = alert_data.get('alert_type', 'unknown')
        fixture = alert_data.get('fixture', 'unknown')
        confidence = alert_data.get('confidence', 0)
        details = alert_data.get('details', {})
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO alerts (alert_type, fixture, confidence, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (alert_type, fixture, confidence, str(details), time.time()))
            conn.commit()
        
        logger.info(f"Notification stored: {alert_type} on {fixture} (conf: {confidence:.2f})")
        
        # Future: add email, webhook, Telegram, etc.
        # if alert_type == 'major_leak':
        #     self._send_webhook(alert_data)
    
    def get_recent_alerts(self, limit: int = 20) -> list:
        """Get recent alerts for API."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?',
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def acknowledge_alert(self, alert_id: int):
        """Mark alert as acknowledged."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('UPDATE alerts SET acknowledged = 1 WHERE id = ?', (alert_id,))
            conn.commit()
    
    def get_unacknowledged_count(self) -> int:
        """Get count of unacknowledged alerts."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM alerts WHERE acknowledged = 0')
            return cursor.fetchone()[0]
    
    def _send_webhook(self, alert_data: Dict):
        """Optional: send to external webhook."""
        pass
PYEOF
```

### 13.5 Create api_endpoints.py (Flask Blueprint)

```bash
cat > api_endpoints.py << 'PYEOF'
"""
Flask API Endpoints — Dashboard data, alerts, commands
"""

from flask import Blueprint, jsonify, request, current_app
import logging

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/status')
def status():
    """System status endpoint."""
    return jsonify({
        'status': 'ok',
        'serial_connected': current_app.serial_reader._serial is not None and current_app.serial_reader._serial.is_open if current_app.serial_reader else False,
        'ml_loaded': current_app.detector.model_loaded if current_app.detector else False,
        'uptime': 0  # Could add actual uptime
    })


@api.route('/readings/latest')
def latest_readings():
    """Get latest sensor readings."""
    # This would come from the serial reader's last reading
    # For now, return empty - dashboard polls serial reader directly
    return jsonify({'message': 'Readings streamed via SSE'})


@api.route('/readings/stream')
def readings_stream():
    """Server-Sent Events stream for real-time readings."""
    from flask import Response
    import json
    import time
    
    def event_stream():
        last_reading = None
        while True:
            # Get latest reading from app context
            if hasattr(current_app, 'latest_reading') and current_app.latest_reading:
                reading = current_app.latest_reading
                if reading != last_reading:
                    data = {
                        'inlet': reading.inlet,
                        'bidet': reading.bidet,
                        'kitchen': reading.kitchen,
                        'bathroom_shower': reading.bathroom_shower,
                        'device_id': reading.device_id,
                        'timestamp': reading.timestamp
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    last_reading = reading
            time.sleep(1)
    
    return Response(event_stream(), mimetype='text/event-stream')


@api.route('/alerts')
def get_alerts():
    """Get recent alerts."""
    limit = request.args.get('limit', 20, type=int)
    alerts = current_app.alert_engine.get_recent_alerts(limit)
    return jsonify({'alerts': alerts})


@api.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert."""
    current_app.alert_engine.acknowledge_alert(alert_id)
    return jsonify({'success': True})


@api.route('/alerts/unacknowledged_count')
def unacknowledged_count():
    """Get count of unacknowledged alerts."""
    count = current_app.alert_engine.get_unacknowledged_count()
    return jsonify({'count': count})


@api.route('/command', methods=['POST'])
def send_command():
    """Send command to ESP32 via serial."""
    data = request.get_json()
    if not data or 'cmd' not in data:
        return jsonify({'error': 'Missing cmd field'}), 400
    
    cmd = data['cmd']
    
    if current_app.serial_reader and current_app.serial_reader._serial and current_app.serial_reader._serial.is_open:
        try:
            import json
            cmd_json = json.dumps(data) + '\n'
            current_app.serial_reader._serial.write(cmd_json.encode('utf-8'))
            return jsonify({'success': True, 'message': 'Command sent'})
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Serial not connected'}), 503


@api.route('/models/info')
def model_info():
    """Get ML model metadata."""
    if hasattr(current_app, 'ml_metadata'):
        return jsonify(current_app.ml_metadata)
    return jsonify({'error': 'No metadata available'})


@api.route('/models/benchmark')
def benchmark_model():
    """Run ML inference benchmark."""
    if current_app.detector:
        result = current_app.detector.benchmark(100)
        return jsonify(result)
    return jsonify({'error': 'Detector not loaded'}), 503
PYEOF
```

### 13.6 Create app.py (Flask Entry Point)

```bash
cat > app.py << 'PYEOF'
"""
Water Meter Leak Detection — Flask Backend
Runs on Raspberry Pi, reads from ESP32 via USB Serial, runs ML inference, serves dashboard.
"""

import os
import logging
from flask import Flask, render_template, send_from_directory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Local imports
from ml_inference import load_deployment_package
from serial_reader import ESP32SerialReader, create_serial_reader_with_ml
from alert_engine import AlertEngine
from api_endpoints import api
from serial_port import find_esp32_port

# Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.register_blueprint(api)

# Configuration
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
DEVICE_ID = os.getenv('DEVICE_ID', 'wmldad-001')

# Global components (initialized in initialize_components)
serial_reader = None
detector = None
alert_engine = None
ml_metadata = {}

# Store latest reading for SSE
app.latest_reading = None


def initialize_components():
    """Initialize all backend components."""
    global serial_reader, detector, alert_engine, ml_metadata
    
    logger.info("Initializing ML detector...")
    package = load_deployment_package('models')
    detector = package['detector']
    ml_metadata = package['metadata']
    detector.warm_up()
    
    logger.info(f"✅ ML models loaded: XGBoost {ml_metadata.get('xgboost_version', 'unknown')}, IF {ml_metadata.get('isolation_forest_version', 'unknown')}")
    logger.info(f"   Accuracy: {ml_metadata.get('accuracy', 'N/A')}%")
    logger.info(f"   Training samples: {ml_metadata.get('training_samples', 'N/A')}")
    
    # Attach to app for API access
    app.detector = detector
    app.ml_metadata = ml_metadata
    
    logger.info("Initializing Alert Engine...")
    alert_engine = AlertEngine('data/alerts.db')
    app.alert_engine = alert_engine
    
    logger.info("Initializing Serial Reader...")
    
    def on_reading(reading):
        # Store for SSE stream
        app.latest_reading = reading
        
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
                    alert_engine.send_notification({
                        'alert_type': result['final'],
                        'fixture': fixture_name,
                        'confidence': result.get('confidence', 0),
                        'details': result
                    })
    
    serial_reader = ESP32SerialReader(on_reading=on_reading)
    app.serial_reader = serial_reader
    serial_reader.start()
    
    logger.info("✅ All components initialized")


def extract_features(reading, fixture_name):
    """Extract 9 features from sensor reading."""
    import numpy as np
    from datetime import datetime
    
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
    
    # Rate variance (placeholder)
    rate_variance = 0
    
    # Night flag
    is_night = 1 if (hour >= 22 or hour < 5) else 0
    
    # Pulse trend (placeholder)
    pulse_trend = 0
    
    return np.array([[
        flow_rate, duration, hour, day, fixture_id,
        inlet_ratio, rate_variance, is_night, pulse_trend
    ]], dtype=np.float32)


# Routes
@app.route('/')
def index():
    """Serve main dashboard."""
    return render_template('index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'serial': serial_reader._serial.is_open if serial_reader and serial_reader._serial else False,
        'ml': detector.model_loaded if detector else False
    })


if __name__ == '__main__':
    initialize_components()
    
    logger.info(f"Starting Flask on {FLASK_HOST}:{FLASK_PORT}")
    logger.info(f"Dashboard: http://water-meter.local:{FLASK_PORT}/")
    logger.info(f"Touchscreen: Auto-launch Chromium kiosk mode")
    
    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if serial_reader:
            serial_reader.stop()
PYEOF
```

---

## 14. Add ML Model Files

```bash
# Create models directory
mkdir -p /home/pi/wmldad/rpi/models

# After training in Google Colab/Jupyter, copy model files:
# (these files are generated by ml-complete-guide.md training notebook)

# From Google Colab: download from Files tab
# From local Jupyter:
cp /home/pi/wmldad/training/xgboost_model.json /home/pi/wmldad/rpi/models/
cp /home/pi/wmldad/training/isolation_forest.pkl /home/pi/wmldad/rpi/models/
cp /home/pi/wmldad/training/scaler.pkl /home/pi/wmldad/rpi/models/
cp /home/pi/wmldad/training/iso_threshold.pkl /home/pi/wmldad/rpi/models/
cp /home/pi/wmldad/training/feature_cols.pkl /home/pi/wmldad/rpi/models/
cp /home/pi/wmldad/training/metadata.json /home/pi/wmldad/rpi/models/

# Verify
ls -la /home/pi/wmldad/rpi/models/
# Should see: xgboost_model.json, isolation_forest.pkl, scaler.pkl, iso_threshold.pkl, feature_cols.pkl, metadata.json
```

---

## 15. Verify Installation

```bash
cd /home/pi/wmldad/rpi
source venv/bin/activate

# Quick test
python -c "
from ml_inference import load_deployment_package
pkg = load_deployment_package('models')
detector = pkg['detector']
detector.warm_up()
result = detector.predict([[2.5, 10, 14, 2, 1, 1.1, 0.5, 0, 0.1]])
print('Test inference:', result)
print('Benchmark:', detector.benchmark(50))
"

# Start Flask
python app.py
# Should start on port 5000
# Visit http://water-meter.local:5000/ in browser
```

---

## 16. Systemd Service for Auto-start

### 16.1 Create Service File

```bash
cat > /home/pi/wmldad/rpi/water-meter.service << 'EOF'
[Unit]
Description=Water Meter Leak Detection Backend
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wmldad/rpi
Environment=PATH=/home/pi/wmldad/rpi/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/pi/wmldad/rpi/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### 16.2 Install & Enable Service

```bash
sudo cp /home/pi/wmldad/rpi/water-meter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable water-meter.service
sudo systemctl start water-meter.service

# Check status
sudo systemctl status water-meter.service
# Should show: Active: active (running)

# View logs
journalctl -u water-meter.service -f
```

---

## 17. Configure 800×480 Touchscreen Auto-Launch (Kiosk Mode)

```bash
# Create autostart for Chromium kiosk
mkdir -p /home/pi/.config/lxsession/LXDE-pi/
cat > /home/pi/.config/lxsession/LXDE-pi/autostart << 'EOF'
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
@chromium-browser --noerrdialogs --disable-infobars --kiosk --incognito http://localhost:5000/
EOF

# Disable screen blanking
echo -e "\n# Disable screen blanking\nxserver-command=X -s 0 -dpms" | sudo tee -a /etc/lightdm/lightdm.conf

# Or via raspi-config
sudo raspi-config
# Display Options → Screen Blanking → No → Finish
```

---

## 18. Remote Access Setup (Optional)

### Port Forwarding (Router)
1. Log into router admin (192.168.1.1)
2. **Port Forwarding:** External 8443 → Internal `water-meter.local:5000` (TCP)
3. Access remotely: `http://your-external-ip:8443`

### DDNS (DuckDNS - Free)
```bash
# Install duckdns updater
sudo apt install -y curl
# Create /home/pi/duckdns.sh with your token
# Add to crontab: */5 * * * * /home/pi/duckdns.sh
```

### Cloudflare Tunnel (HTTPS, no port forward)
```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb
cloudflared tunnel login
cloudflared tunnel create water-meter
cloudflared tunnel route dns water-meter yourdomain.com
# Run as service
```

---

## Quick Reference

```bash
# Clone repo
git clone https://github.com/qppd/wmldad.git

# Setup venv
cd wmldad/rpi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# USB Serial udev rule
sudo cp /home/pi/wmldad/rpi/99-esp32.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -a -G dialout pi

# Add models to models/

# Run
python app.py

# Or as service
sudo systemctl start water-meter.service
journalctl -u water-meter.service -f
```

---

## Dashboard Access

- **Local:** `http://water-meter.local:5000/`
- **Touchscreen:** Auto-launches Chromium kiosk on boot
- **Remote:** `http://your-external-ip:8443/` (after port forward)