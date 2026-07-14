# Complete Raspberry Pi OS Setup to Water Meter Project Deployment

> **Target:** Raspberry Pi 3B+/4/5  
> **OS:** Raspberry Pi OS Trixie 64-bit (Debian 13)  
> **Goal:** Fresh Pi OS → SSH + VNC → Full Water Meter Backend (Flask + ML + Firebase)  
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
12. [Configure Firebase Credentials](#12-configure-firebase-credentials)
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
# Should see: docs/, rpi/, esp32/, etc.
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
pyrebase4==4.5.0
gunicorn==21.2.0
python-dotenv==1.0.0
requests==2.31.0
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
import xgboost, sklearn, pandas, numpy, flask, pyrebase
print('✅ All packages installed successfully')
print(f'XGBoost: {xgboost.__version__}')
print(f'sklearn: {sklearn.__version__}')
print(f'Flask: {flask.__version__}')
"
```

---

## 12. Configure Firebase Credentials

### 12.1 Get Firebase Web Config
1. Open [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. **Project Settings** → **General** → **Your apps** → **Web app (</>)**
4. Copy the `firebaseConfig` object

### 12.2 Create firebase_config.json
```bash
cd /home/pi/wmldad/rpi

cat > firebase_config.json << 'EOF'
{
  "apiKey": "YOUR_API_KEY_HERE",
  "authDomain": "your-project.firebaseapp.com",
  "databaseURL": "https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app",
  "projectId": "your-project",
  "storageBucket": "your-project.appspot.com",
  "messagingSenderId": "123456789",
  "appId": "1:123456789:web:abcdef123456"
}
EOF
```

> **Replace ALL values** with your actual Firebase config.

### 12.3 Create .env File
```bash
cat > .env << 'EOF'
FIREBASE_EMAIL=esp32@your-project.iam.gserviceaccount.com
FIREBASE_PASSWORD=your-strong-password-here
DEVICE_ID=wm_001
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
EOF
```

> **Important:** The email/password must match a user created in Firebase Console → **Authentication** → **Sign-in method** → **Email/Password** → **Add user**.

### 12.4 Verify Config
```bash
python3 -c "
import json, os
from dotenv import load_dotenv
load_dotenv()

with open('firebase_config.json') as f:
    config = json.load(f)
print('Firebase config loaded:')
for k, v in config.items():
    print(f'  {k}: {v[:20]}...' if len(v) > 20 else f'  {k}: {v}')

print()
print('Environment variables:')
print(f'  FIREBASE_EMAIL: {os.getenv(\"FIREBASE_EMAIL\")}')
print(f'  DEVICE_ID: {os.getenv(\"DEVICE_ID\")}')
"
```

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

---

### 13.2 Create firebase_listener.py (Pyrebase4 Polling)
```bash
cat > firebase_listener.py << 'PYEOF'
"""
Firebase Listener — Polls Firebase Realtime DB for new sensor readings
using Pyrebase4 (Email/Password auth).
"""

import pyrebase
import json
import threading
import time
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)


class FirebaseListener:
    """Polls Firebase for new readings, runs ML inference, writes alerts."""
    
    def __init__(
        self,
        config_path: str,
        email: str,
        password: str,
        device_id: str,
        poll_interval: int = 5
    ):
        self.device_id = device_id
        self.poll_interval = poll_interval
        self.email = email
        self.password = password
        self.last_timestamp = None
        self.running = False
        self._detector = None
        self._alert_engine = None
        self._poll_thread: Optional[threading.Thread] = None
        
        # Load Firebase config
        with open(config_path, 'r') as f:
            self.firebase_config = json.load(f)
        
        # Initialize Pyrebase4
        self.firebase = pyrebase.initialize_app(self.firebase_config)
        self.auth = self.firebase.auth()
        self.db = self.firebase.database()
        
        # Sign in
        self._sign_in()
        
        # Database references
        self.readings_ref = self.db.child(f"readings/{device_id}")
        self.alerts_ref = self.db.child(f"alerts/{device_id}")
        self.commands_ref = self.db.child(f"commands/{device_id}")
        self.device_ref = self.db.child(f"devices/{device_id}")
    
    def _sign_in(self):
        """Authenticate with Firebase."""
        try:
            self.user = self.auth.sign_in_with_email_and_password(
                self.email, self.password
            )
            self.id_token = self.user['idToken']
            self.refresh_token = self.user['refreshToken']
            logger.info("Firebase authentication successful")
        except Exception as e:
            logger.error(f"Firebase auth failed: {e}")
            raise
    
    def _refresh_token(self):
        """Refresh expired auth token."""
        try:
            self.user = self.auth.refresh(self.refresh_token)
            self.id_token = self.user['idToken']
            logger.info("Token refreshed")
        except Exception as e:
            logger.warning(f"Token refresh failed, re-authenticating: {e}")
            self._sign_in()
    
    def set_detector(self, detector):
        """Set ML detector for inference."""
        self._detector = detector
    
    def set_alert_engine(self, alert_engine):
        """Set alert engine for notifications."""
        self._alert_engine = alert_engine
    
    def start(self):
        """Start polling thread."""
        if self.running:
            return
        self.running = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        logger.info("Firebase listener started")
    
    def stop(self):
        """Stop polling thread."""
        self.running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=5)
        logger.info("Firebase listener stopped")
    
    def _poll_loop(self):
        """Main polling loop."""
        while self.running:
            try:
                self._check_new_readings()
            except Exception as e:
                logger.error(f"Poll error: {e}")
                if "permission" in str(e).lower() or "unauthorized" in str(e).lower():
                    self._refresh_token()
            time.sleep(self.poll_interval)
    
    def _check_new_readings(self):
        """Fetch latest reading from Firebase."""
        readings = self.readings_ref.order_by_key().limit_to_last(1).get(self.id_token)
        
        if readings and readings.val():
            for ts, data in readings.val().items():
                if ts != self.last_timestamp:
                    self.last_timestamp = ts
                    self.process_reading(data, ts)
    
    def process_reading(self, data: Dict, timestamp: str):
        """Extract features, run ML inference, write alerts."""
        if not self._detector:
            return
        
        try:
            inlet = data.get('inlet', {})
            
            # Process each fixture (1-3)
            for fixture_idx in [1, 2, 3]:
                fixture_key = f'fixture_{fixture_idx}'
                fixture = data.get(fixture_key, {})
                
                # Only process if water is flowing
                if fixture.get('flow_rate', 0) > 0.01:
                    features = self._extract_features(data, fixture_idx, fixture, inlet)
                    result = self._detector.predict(features)
                    
                    if result['final'] != 'normal':
                        self._write_alert(result, fixture_idx, fixture, inlet, timestamp)
                        
        except Exception as e:
            logger.error(f"Error processing reading: {e}")
    
    def _extract_features(self, data: Dict, fixture_idx: int, fixture: Dict, inlet: Dict):
        """Extract 9 features from raw Firebase data."""
        import numpy as np
        from datetime import datetime
        
        flow_rate = fixture.get('flow_rate', 0)
        volume = fixture.get('volume', 0)
        inlet_rate = inlet.get('flow_rate', 0)
        
        # 1. Flow rate
        # 2. Duration (approximate from volume/rate)
        duration = volume / max(flow_rate / 60, 0.01) if flow_rate > 0 else 0
        
        # 3-4. Time features
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
        
        # 5. Fixture ID
        fixture_id = fixture_idx
        
        # 6. Inlet ratio
        inlet_ratio = inlet_rate / max(flow_rate, 0.01)
        
        # 7. Rate variance (simplified)
        rate_variance = 0
        
        # 8. Night flag
        is_night = 1 if (hour >= 22 or hour < 5) else 0
        
        # 9. Pulse trend (simplified)
        pulse_trend = 0
        
        return np.array([[
            flow_rate, duration, hour, day, fixture_id,
            inlet_ratio, rate_variance, is_night, pulse_trend
        ]], dtype=np.float32)
    
    def _write_alert(self, result: Dict, fixture_idx: int, fixture: Dict, inlet: Dict, timestamp: str):
        """Write alert to Firebase /alerts."""
        fixture_names = {1: 'bidet', 2: 'kitchen', 3: 'bathroom_shower'}
        
        alert_data = {
            'alert_type': result['final'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'confidence': result.get('confidence', 0),
            'fixture_index': fixture_idx,
            'fixture_name': fixture_names.get(fixture_idx),
            'action': 'monitoring',
            'details': {
                'flow_rate': fixture.get('flow_rate', 0),
                'inlet_flow_rate': inlet.get('flow_rate', 0),
                'xgboost_class': result['xgboost']['class'],
                'xgboost_confidence': result['xgboost']['confidence'],
                'isolation_forest_anomaly': result['isolation_forest']['anomaly'],
                'isolation_forest_score': result['isolation_forest']['score']
            }
        }
        
        try:
            self.alerts_ref.push(alert_data, self.id_token)
            logger.warning(f"⚠️ ALERT: {result['final']} on fixture {fixture_idx} (conf: {result.get('confidence', 0):.2f})")
            
            # Send notification
            if self._alert_engine:
                self._alert_engine.send_notification(alert_data)
        except Exception as e:
            logger.error(f"Failed to write alert: {e}")
    
    def get_latest_reading(self):
        """Get latest reading for API."""
        readings = self.readings_ref.order_by_key().limit_to_last(1).get(self.id_token)
        return readings.val() if readings else None
    
    def get_recent_alerts(self, limit=20):
        """Get recent alerts for API."""
        alerts = self.alerts_ref.order_by_key().limit_to_last(limit).get(self.id_token)
        return alerts.val() if alerts else None
    
    def send_command(self, command: str):
        """Send command to ESP32 via Firebase."""
        self.commands_ref.push({
            'command': command,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source': 'dashboard'
        }, self.id_token)
    
    def is_connected(self):
        """Check Firebase connectivity."""
        try:
            self.db.child('.info/connected').get(self.id_token)
            return True
        except:
            return False
    
    def reconnect(self):
        """Force reconnection."""
        logger.info("Reconnecting to Firebase...")
        self._sign_in()
PYEOF
```

---

### 13.3 Create alert_engine.py (In-App Notifications)
```bash
cat > alert_engine.py << 'PYEOF'
"""
Alert Engine — In-app notifications via Firebase /alerts
The web dashboard polls /api/alerts and displays alerts in real-time.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AlertEngine:
    """Handles in-app alert notifications."""
    
    def __init__(self):
        # In-app notifications are handled by writing to Firebase /alerts
        # The Flask dashboard (JavaScript) polls /api/alerts and displays them
        # No external dependencies (email, SMS, push) required
        pass
    
    def send_notification(self, alert_data: Dict[str, Any]):
        """
        Send notification for alert.
        
        The alert is already written to Firebase /alerts by firebase_listener.
        This method is a hook for future extensions (email, webhook, etc.).
        """
        logger.info(f"Notification sent for: {alert_data['alert_type']} on {alert_data.get('fixture_name')}")
        
        # Future: add email, webhook, Telegram, etc.
        # Example:
        # if alert_data['alert_type'] in ['major_leak']:
        #     self._send_webhook(alert_data)
    
    def _send_webhook(self, alert_data: Dict):
        """Optional: send to external webhook."""
        pass
PYEOF
```

---

### 13.4 Create app.py (Flask Entry Point)
```bash
cat > app.py << 'PYEOF'
"""
Water Meter Leak Detection — Flask Backend
Runs on Raspberry Pi, polls Firebase, runs ML inference, serves dashboard.
"""

import os
import logging
from flask import Flask, render_template, jsonify, request
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
from firebase_listener import FirebaseListener
from ml_inference import load_deployment_package
from alert_engine import AlertEngine
from api_endpoints import api

# Flask app
app = Flask(__name__)
app.register_blueprint(api)

# Configuration from environment
FIREBASE_CONFIG_PATH = os.getenv('FIREBASE_CONFIG_PATH', 'firebase_config.json')
FIREBASE_EMAIL = os.getenv('FIREBASE_EMAIL')
FIREBASE_PASSWORD = os.getenv('FIREBASE_PASSWORD')
DEVICE_ID = os.getenv('DEVICE_ID', 'wm_001')

# Global components
firebase_listener = None
detector = None
alert_engine = None


def initialize_components():
    """Initialize all backend components."""
    global firebase_listener, detector, alert_engine
    
    logger.info("Initializing ML detector...")
    package = load_deployment_package('models')
    detector = package['detector']
    detector.warm_up()
    
    # Log metadata
    metadata = package['metadata']
    logger.info(f"Model version: {metadata.get('version', 'unknown')}")
    logger.info(f"Created: {metadata.get('created', 'unknown')}")
    logger.info(f"Performance: {metadata.get('performance', {})}")
    
    logger.info("Initializing alert engine...")
    alert_engine = AlertEngine()
    
    logger.info("Initializing Firebase listener...")
    firebase_listener = FirebaseListener(
        config_path=FIREBASE_CONFIG_PATH,
        email=FIREBASE_EMAIL,
        password=FIREBASE_PASSWORD,
        device_id=DEVICE_ID,
        poll_interval=5
    )
    firebase_listener.set_detector(detector)
    firebase_listener.set_alert_engine(alert_engine)
    firebase_listener.start()
    
    logger.info("✅ All components initialized")


# Initialize on startup
initialize_components()


# ==================== ROUTES ====================

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'firebase_connected': firebase_listener.is_connected() if firebase_listener else False,
        'model_loaded': detector.model_loaded if detector else False,
        'device_id': DEVICE_ID
    })


@app.route('/api/latest')
def api_latest():
    """Get latest sensor reading."""
    if not firebase_listener:
        return jsonify({'error': 'Firebase listener not initialized'}), 503
    
    latest = firebase_listener.get_latest_reading()
    return jsonify(latest) if latest else jsonify({})


@app.route('/api/alerts')
def api_alerts():
    """Get recent alerts."""
    if not firebase_listener:
        return jsonify({'error': 'Firebase listener not initialized'}), 503
    
    alerts = firebase_listener.get_recent_alerts(limit=50)
    return jsonify(alerts) if alerts else jsonify({})


@app.route('/api/command', methods=['POST'])
def api_command():
    """Send command to ESP32 via Firebase."""
    if not firebase_listener:
        return jsonify({'error': 'Firebase listener not initialized'}), 503
    
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'Missing command'}), 400
    
    try:
        firebase_listener.send_command(data['command'])
        return jsonify({'status': 'sent', 'command': data['command']})
    except Exception as e:
        logger.error(f"Command send error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/benchmark')
def benchmark():
    """Run inference benchmark."""
    if not detector:
        return jsonify({'error': 'Detector not initialized'}), 503
    
    return jsonify(detector.benchmark(100))


# ==================== MAIN ====================

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    
    logger.info(f"Starting Flask on {host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
PYEOF
```

---

### 13.5 Create api_endpoints.py (API Blueprint)
```bash
cat > api_endpoints.py << 'PYEOF'
"""
API Endpoints Blueprint — Separated for modularity.
"""

from flask import Blueprint, request, jsonify
import numpy as np
import logging

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)


def get_detector():
    """Get detector instance from app context."""
    from app import detector
    return detector


@api.route('/api/predict', methods=['POST'])
def predict():
    """Single prediction endpoint."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data'}), 400
        
        features = extract_features_from_request(data)
        
        detector = get_detector()
        result = detector.predict(features)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500


def extract_features_from_request(data: dict) -> np.ndarray:
    """Extract 9 features from request data."""
    # If features already provided
    if 'features' in data:
        return np.array(data['features'], dtype=np.float32)
    
    # Otherwise build from raw Firebase reading
    inlet = data.get('inlet', {})
    fixture = data.get('fixture', {})
    
    return np.array([[
        fixture.get('flow_rate', 0),
        fixture.get('duration', 0),
        data.get('hour', 12),
        data.get('day', 0),
        data.get('fixture_id', 1),
        inlet.get('flow_rate', 0) / max(fixture.get('flow_rate', 0.01), 0.01),
        0,  # rate_variance
        1 if data.get('hour', 12) >= 22 or data.get('hour', 12) < 5 else 0,
        0   # pulse_trend
    ]], dtype=np.float32)
PYEOF
```

---

### 13.6 Create templates/dashboard.html
```bash
cat > templates/dashboard.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Water Meter Monitor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4"></script>
</head>
<body>
    <div class="container-fluid p-3">
        <!-- Header -->
        <div class="row mb-3">
            <div class="col-12">
                <h2 class="mb-0">💧 Water Meter Monitor</h2>
                <small class="text-muted" id="last-update">Loading...</small>
            </div>
        </div>
        
        <!-- Status Cards -->
        <div class="row mb-3" id="status-cards">
            <!-- Inlet -->
            <div class="col-6 col-md-3">
                <div class="card sensor-card inlet-card">
                    <div class="card-body text-center">
                        <h6 class="card-title">Inlet</h6>
                        <div class="sensor-value" id="inlet-flow">-- L/min</div>
                        <div class="sensor-sub">Total: <span id="inlet-total">-- L</span></div>
                    </div>
                </div>
            </div>
            
            <!-- Fixture 1: Bidet -->
            <div class="col-6 col-md-3">
                <div class="card sensor-card" id="fixture1-card">
                    <div class="card-body text-center">
                        <h6 class="card-title">Bidet</h6>
                        <div class="sensor-value" id="fix1-flow">-- L/min</div>
                        <div class="sensor-sub">Total: <span id="fix1-total">-- L</span></div>
                    </div>
                </div>
            </div>
            
            <!-- Fixture 2: Kitchen -->
            <div class="col-6 col-md-3">
                <div class="card sensor-card" id="fixture2-card">
                    <div class="card-body text-center">
                        <h6 class="card-title">Kitchen</h6>
                        <div class="sensor-value" id="fix2-flow">-- L/min</div>
                        <div class="sensor-sub">Total: <span id="fix2-total">-- L</span></div>
                    </div>
                </div>
            </div>
            
            <!-- Fixture 3: Shower -->
            <div class="col-6 col-md-3">
                <div class="card sensor-card" id="fixture3-card">
                    <div class="card-body text-center">
                        <h6 class="card-title">Shower</h6>
                        <div class="sensor-value" id="fix3-flow">-- L/min</div>
                        <div class="sensor-sub">Total: <span id="fix3-total">-- L</span></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Charts & Status -->
        <div class="row mb-3">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">Flow Rate History (Last 50 readings)</div>
                    <div class="card-body">
                        <canvas id="flowChart" height="100"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">System Status</div>
                    <div class="card-body">
                        <div class="mb-2">
                            <strong>Firebase:</strong> 
                            <span class="badge bg-success" id="firebase-status">Connected</span>
                        </div>
                        <div class="mb-2">
                            <strong>ML Model:</strong> 
                            <span class="badge bg-success" id="ml-status">Loaded</span>
                        </div>
                        <div class="mb-2">
                            <strong>Device:</strong> 
                            <span id="device-id">wm_001</span>
                        </div>
                        <div class="mt-3">
                            <button class="btn btn-sm btn-outline-primary" onclick="sendCommand('calibrate')">
                                Calibrate
                            </button>
                            <button class="btn btn-sm btn-outline-danger ms-2" onclick="sendCommand('reboot')">
                                Reboot ESP32
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Alerts Table -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between">
                        <h5 class="mb-0">Recent Alerts</h5>
                        <button class="btn btn-sm btn-outline-secondary" onclick="loadAlerts()">Refresh</button>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0" id="alerts-table">
                                <thead class="table-light">
                                    <tr>
                                        <th>Time</th>
                                        <th>Type</th>
                                        <th>Fixture</th>
                                        <th>Confidence</th>
                                        <th>Details</th>
                                    </tr>
                                </thead>
                                <tbody id="alerts-body">
                                    <tr><td colspan="5" class="text-center text-muted">Loading...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
</body>
</html>
HTMLEOF
```

---

### 13.7 Create static/css/dashboard.css
```bash
cat > static/css/dashboard.css << 'CSSEOF'
/* Water Meter Dashboard Styles */

.sensor-card {
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}
.sensor-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.inlet-card { border-top: 4px solid #0d6efd; }
#fixture1-card { border-top: 4px solid #198754; }
#fixture2-card { border-top: 4px solid #fd7e14; }
#fixture3-card { border-top: 4px solid #6f42c1; }

.sensor-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #212529;
}
.sensor-sub {
    font-size: 0.85rem;
    color: #6c757d;
}

.card-header {
    background: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    font-weight: 600;
}

#flowChart {
    max-height: 300px;
}

.alert-minor_leak { border-left: 4px solid #fd7e14; }
.alert-major_leak { border-left: 4px solid #dc3545; }
.alert-anomaly { border-left: 4px solid #6f42c1; }

@media (max-width: 576px) {
    .sensor-value { font-size: 1.2rem; }
    .card-header { font-size: 0.9rem; }
}
CSSEOF
```

---

### 13.8 Create static/js/dashboard.js
```bash
cat > static/js/dashboard.js << 'JSEOF'
// Water Meter Dashboard JavaScript

let flowChart = null;
let updateInterval = null;

const FIXTURE_NAMES = {
    1: 'Bidet',
    2: 'Kitchen',
    3: 'Bathroom Shower'
};

const ALERT_COLORS = {
    'minor_leak': 'warning',
    'major_leak': 'danger',
    'anomaly': 'purple',
    'normal': 'success'
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initFlowChart();
    loadLatest();
    loadAlerts();
    startAutoRefresh();
});

function initFlowChart() {
    const ctx = document.getElementById('flowChart').getContext('2d');
    flowChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Inlet', data: [], borderColor: '#0d6efd', backgroundColor: 'rgba(13,110,253,0.1)', fill: true, tension: 0.3 },
                { label: 'Bidet', data: [], borderColor: '#198754', backgroundColor: 'rgba(25,135,84,0.1)', fill: true, tension: 0.3 },
                { label: 'Kitchen', data: [], borderColor: '#fd7e14', backgroundColor: 'rgba(253,126,20,0.1)', fill: true, tension: 0.3 },
                { label: 'Shower', data: [], borderColor: '#6f42c1', backgroundColor: 'rgba(111,66,193,0.1)', fill: true, tension: 0.3 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'L/min' } },
                x: { display: false }
            }
        }
    });
}

async function loadLatest() {
    try {
        const res = await fetch('/api/latest');
        const data = await res.json();
        
        if (data && Object.keys(data).length > 0) {
            updateDashboard(data);
        }
    } catch (e) {
        console.error('Load latest failed:', e);
        document.getElementById('firebase-status').className = 'badge bg-danger';
        document.getElementById('firebase-status').textContent = 'Disconnected';
    }
}

function updateDashboard(data) {
    document.getElementById('last-update').textContent = `Last update: ${new Date().toLocaleTimeString()}`;
    
    // Inlet
    const inlet = data.inlet || {};
    document.getElementById('inlet-flow').textContent = `${inlet.flow_rate || 0} L/min`;
    document.getElementById('inlet-total').textContent = `${inlet.total || 0} L`;
    
    // Fixtures
    for (let i = 1; i <= 3; i++) {
        const fix = data[`fixture_${i}`] || {};
        document.getElementById(`fix${i}-flow`).textContent = `${fix.flow_rate || 0} L/min`;
        document.getElementById(`fix${i}-total`).textContent = `${fix.total || 0} L`;
    }
    
    // Update chart
    updateChart(inlet, data);
}

function updateChart(inlet, data) {
    const now = new Date().toLocaleTimeString();
    const maxPoints = 50;
    
    flowChart.data.labels.push(now);
    flowChart.data.datasets[0].data.push(inlet.flow_rate || 0);
    
    for (let i = 1; i <= 3; i++) {
        const fix = data[`fixture_${i}`] || {};
        flowChart.data.datasets[i].data.push(fix.flow_rate || 0);
    }
    
    // Trim old points
    if (flowChart.data.labels.length > maxPoints) {
        flowChart.data.labels.shift();
        flowChart.data.datasets.forEach(ds => ds.data.shift());
    }
    
    flowChart.update('none');
}

async function loadAlerts() {
    try {
        const res = await fetch('/api/alerts');
        const alerts = await res.json();
        renderAlerts(alerts);
    } catch (e) {
        console.error('Load alerts failed:', e);
    }
}

function renderAlerts(alerts) {
    const tbody = document.getElementById('alerts-body');
    if (!alerts || Object.keys(alerts).length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No alerts</td></tr>';
        return;
    }
    
    // Sort by timestamp descending
    const sorted = Object.entries(alerts)
        .sort((a, b) => b[1].timestamp.localeCompare(a[1].timestamp))
        .slice(0, 20);
    
    tbody.innerHTML = sorted.map(([key, alert]) => {
        const time = new Date(alert.timestamp).toLocaleTimeString();
        const type = alert.alert_type || 'unknown';
        const fixture = alert.fixture_name || `Fixture ${alert.fixture_index}`;
        const conf = alert.confidence ? `${(alert.confidence * 100).toFixed(1)}%` : '--';
        const color = ALERT_COLORS[type] || 'secondary';
        
        return `
            <tr class="alert-${type}">
                <td>${time}</td>
                <td><span class="badge bg-${color}">${type.replace('_', ' ')}</span></td>
                <td>${fixture}</td>
                <td>${conf}</td>
                <td>
                    <small class="text-muted">
                        Flow: ${alert.details?.flow_rate || 0} L/min | 
                        Inlet: ${alert.details?.inlet_flow_rate || 0} L/min
                    </small>
                </td>
            </tr>
        `;
    }).join('');
}

async function sendCommand(command) {
    if (!confirm(`Send "${command}" command to ESP32?`)) return;
    
    try {
        const res = await fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });
        const result = await res.json();
        alert(`Command sent: ${result.command}`);
    } catch (e) {
        alert('Failed to send command');
    }
}

function startAutoRefresh() {
    updateInterval = setInterval(() => {
        loadLatest();
        loadAlerts();
    }, 5000);
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) clearInterval(updateInterval);
});
JSEOF
```

---

## 14. Add ML Model Files

### If you have trained models (from ml-complete-guide.md):
```bash
# Copy from training machine to RPi:
scp -r models/ pi@water-meter.local:~/wmldad/rpi/models/
```

### If you DON'T have trained models yet (create placeholders for testing):
```bash
cd /home/pi/wmldad/rpi

python3 << 'PYEOF'
import xgboost as xgb
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
import joblib
import json
import os

os.makedirs('models', exist_ok=True)

# Dummy XGBoost
xgb_model = xgb.XGBClassifier()
xgb_model.fit(np.random.rand(100, 9), np.random.randint(0, 3, 100))
xgb_model.save_model('models/xgboost_model.json')

# Dummy Isolation Forest
iforest = IsolationForest(contamination=0.05, random_state=42)
iforest.fit(np.random.rand(100, 9))
joblib.dump(iforest, 'models/isolation_forest.pkl')

# Dummy Scaler
scaler = RobustScaler()
scaler.fit(np.random.rand(100, 9))
joblib.dump(scaler, 'models/scaler.pkl')

# Dummy Threshold
joblib.dump(-0.5, 'models/iso_threshold.pkl')

# Feature columns
feature_cols = ['flow_rate', 'duration', 'hour', 'day', 'fixture_id',
                'inlet_ratio', 'rate_variance', 'is_night', 'pulse_trend']
joblib.dump(feature_cols, 'models/feature_cols.pkl')

# Metadata
with open('models/metadata.json', 'w') as f:
    json.dump({
        'version': '1.0-placeholder',
        'created': '2026-07-14T00:00:00Z',
        'feature_cols': feature_cols,
        'target_names': ['normal', 'minor_leak', 'major_leak'],
        'note': 'PLACEHOLDER - Replace with real trained models'
    }, f, indent=2)

print('Placeholder models created')
PYEOF
```

> ⚠️ **Important:** Replace with real trained models from [ml-complete-guide.md](./ml-complete-guide.md) for production use.

---

## 15. Verify Installation

### 15.1 Test ML Inference
```bash
source /home/pi/wmldad/rpi/venv/bin/activate
cd /home/pi/wmldad/rpi

python3 -c "
from ml_inference import load_deployment_package
package = load_deployment_package('models')
detector = package['detector']
print('Model loaded:', detector.model_loaded)
print('Features:', detector.n_features)
print('Benchmark:', detector.benchmark(10))
"
```

### 15.2 Test Flask App Manually
```bash
# Terminal 1: Run Flask
source /home/pi/wmldad/rpi/venv/bin/activate
cd /home/pi/wmldad/rpi
python app.py
# Should show: * Running on all addresses (0.0.0.0:5000)

# Terminal 2: Test endpoints
curl http://localhost:5000/api/health
# {"status":"healthy","firebase_connected":true,"model_loaded":true,"device_id":"wm_001"}

curl http://localhost:5000/api/latest
# Should show latest sensor reading

curl http://localhost:5000/api/alerts
# Should show alerts (or empty)

# Dashboard
# Open browser: http://water-meter.local:5000/
```

### 15.3 Verify Firebase Data Flow
1. Open Firebase Console → Realtime Database
2. Check `/readings/wm_001/` — new data every 5 seconds
3. Check `/alerts/wm_001/` — alerts appear when leaks detected
4. Check `/commands/wm_001/` — commands sent from dashboard

---

## 16. Systemd Service for Auto-start

### 16.1 Create Service File
```bash
sudo tee /etc/systemd/system/water-meter.service > /dev/null << 'EOF'
[Unit]
Description=Water Meter Leak Detection Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wmldad/rpi
Environment=PATH=/home/pi/wmldad/rpi/venv/bin
ExecStart=/home/pi/wmldad/rpi/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### 16.2 Enable & Start
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable water-meter.service

# Start now
sudo systemctl start water-meter.service

# Check status
sudo systemctl status water-meter.service

# View logs
journalctl -u water-meter.service -f
```

### 16.3 Test Auto-start on Reboot
```bash
sudo reboot
# Wait 60 seconds, then:
curl http://water-meter.local:5000/api/health
# Should return healthy status
```

---

## Quick Reference: Complete Command Summary

```bash
# ===== ONE-LINE SETUP (after SSH access) =====
# Run each section separately, not as one script

# 1. Update & tools
sudo apt update && sudo apt full-upgrade -y && sudo apt install -y git python3-venv python3-dev build-essential libopenblas-dev libatlas-base-dev

# 2. Clone project
cd /home/pi && git clone https://github.com/qppd/wmldad.git && cd wmldad/rpi

# 3. Virtual environment
python3 -m venv venv && source venv/bin/activate

# 4. Dependencies
cat > requirements.txt << 'EOF'
xgboost==2.0.3
scikit-learn==1.3.2
pandas==2.1.4
numpy==1.24.3
joblib==1.3.2
flask==3.0.0
pyrebase4==4.5.0
gunicorn==21.2.0
python-dotenv==1.0.0
requests==2.31.0
EOF
pip install --no-cache-dir -r requirements.txt

# 5. Firebase config
cat > firebase_config.json << 'EOF'
{ "apiKey": "YOUR_KEY", "authDomain": "proj.firebaseapp.com", "databaseURL": "https://proj-default-rtdb.region.firebasedatabase.app", "projectId": "proj", "storageBucket": "proj.appspot.com", "messagingSenderId": "123", "appId": "1:123:web:abc" }
EOF

cat > .env << 'EOF'
FIREBASE_EMAIL=esp32@proj.iam.gserviceaccount.com
FIREBASE_PASSWORD=your-password
DEVICE_ID=wm_001
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
EOF

# 6. Models (placeholder or real)
mkdir -p models
python3 -c "
import xgboost as xgb, numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
import joblib, json, os
os.makedirs('models', exist_ok=True)
xgb.XGBClassifier().fit(np.random.rand(100,9), np.random.randint(0,3,100)).save_model('models/xgboost_model.json')
joblib.dump(IsolationForest(contamination=0.05,random_state=42).fit(np.random.rand(100,9)), 'models/isolation_forest.pkl')
joblib.dump(RobustScaler().fit(np.random.rand(100,9)), 'models/scaler.pkl')
joblib.dump(-0.5, 'models/iso_threshold.pkl')
joblib.dump(['flow_rate','duration','hour','day','fixture_id','inlet_ratio','rate_variance','is_night','pulse_trend'], 'models/feature_cols.pkl')
json.dump({'version':'placeholder','note':'Replace with real models'}, open('models/metadata.json','w'))
"

# 7. Test
python -c "from ml_inference import load_deployment_package; d=load_deployment_package('models'); print('OK:', d['detector'].benchmark(5))"

# 8. Run manually
python app.py
# Visit http://water-meter.local:5000/

# 9. Auto-start (optional)
sudo tee /etc/systemd/system/water-meter.service > /dev/null << 'EOF'
[Unit]
Description=Water Meter Backend
After=network.target
[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wmldad/rpi
Environment=PATH=/home/pi/wmldad/rpi/venv/bin
ExecStart=/home/pi/wmldad/rpi/venv/bin/python app.py
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable water-meter && sudo systemctl start water-meter
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Can't SSH** | Check IP: `hostname -I` on Pi. Use IP not hostname. Check `systemctl status ssh`. |
| **VNC "Cannot connect"** | Ensure VNC enabled: `sudo raspi-config` → Interface Options → VNC. Set password: `sudo -u pi vncpasswd -service`. |
| **pip install fails (xgboost)** | `sudo apt install -y libopenblas-dev libatlas-base-dev gfortran` then retry. |
| **Firebase permission denied** | Check Security Rules in Firebase Console. Verify email/password user exists in Auth. |
| **Module not found** | Ensure venv activated: `source /home/pi/wmldad/rpi/venv/bin/activate`. |
| **Port 5000 in use** | `sudo lsof -i :5000` → kill process, or change `FLASK_PORT` in `.env`. |
| **SD card full** | `df -h` → clean with `sudo apt clean`, `sudo journalctl --vacuum-time=7d`. |
| **VNC no display / touchscreen not detected** | Add to `/boot/firmware/config.txt`: `hdmi_force_hotplug=1`, `hdmi_group=2`, `hdmi_mode=87`, `hdmi_cvt=800 480 60 6 0 0 0`. Reboot. |

---

## 17. Touchscreen Setup (800×480 LCD)

The Water Meter project includes a **7" Touchscreen LCD (800×480)** connected via HDMI + USB for touch input. This provides a local dashboard display without needing a remote computer.

### 17.1 Hardware Connection
| Connection | Pi Port | LCD Port |
|------------|---------|----------|
| HDMI | HDMI 0 (Pi 4/5) / HDMI (Pi 3B+) | HDMI input |
| USB Touch | Any USB 2.0/3.0 | USB Micro-B (touch controller) |
| Power | 5V GPIO pins (2/4) or USB | 5V input |

> **Note:** Most 7" 800×480 touchscreens (Waveshare, Elecrow, generic) use HDMI for video and USB for touch. Some use DSI ribbon cable — check your specific model.

### 17.2 Configure Display Resolution
```bash
# Edit config.txt
sudo nano /boot/firmware/config.txt

# Add/modify these lines for 800x480:
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=800 480 60 6 0 0 0
hdmi_drive=2

# For DSI displays (ribbon cable), use instead:
# dtoverlay=vc4-kms-v3d
# dtoverlay=waveshare-7inch-dsi  # or your specific overlay

sudo reboot
```

### 17.3 Auto-launch Chromium in Kiosk Mode (Dashboard on Boot)
Create a systemd user service to auto-start the dashboard on the touchscreen:

```bash
# Create autostart directory
mkdir -p ~/.config/autostart

# Create desktop entry for Chromium kiosk
cat > ~/.config/autostart/chromium-kiosk.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Water Meter Dashboard
Exec=chromium-browser --noerrdialogs --disable-infobars --kiosk --start-fullscreen http://localhost:5000/
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
```

### 17.4 Hide Mouse Cursor (Touch-Only)
```bash
# Install unclutter to hide mouse after inactivity
sudo apt install -y unclutter

# Create systemd user service for unclutter
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/unclutter.service << 'EOF'
[Unit]
Description=Hide mouse cursor for touchscreen
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/unclutter -idle 1 -root
Restart=always

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable unclutter.service
systemctl --user start unclutter.service
```

### 17.5 Disable Screen Blanking
```bash
# Edit lightdm config (for desktop autologin)
sudo nano /etc/lightdm/lightdm.conf

# Under [Seat:*], add:
[Seat:*]
xserver-command=X -s 0 -dpms

# Or via raspi-config:
sudo raspi-config
# Display Options → Screen Blanking → Disable
```

### 17.6 Touchscreen Calibration (If Needed)
```bash
# Install calibration tool
sudo apt install -y xinput-calibrator

# Run calibration
DISPLAY=:0 xinput_calibrator

# Copy output to X11 config
sudo mkdir -p /etc/X11/xorg.conf.d
sudo nano /etc/X11/xorg.conf.d/99-calibration.conf

# Paste the calibration matrix from xinput_calibrator output
# Example:
# Section "InputClass"
#     Identifier "calibration"
#     MatchProduct "Your Touchscreen Name"
#     Option "Calibration" "min_x max_x min_y max_y"
#     Option "SwapAxes" "0"
# EndSection
```

### 17.7 Verify Touchscreen Works
```bash
# Check touch device detected
ls /dev/input/ | grep -i touch

# List input devices
xinput list

# Test: touch screen should move cursor / click
```

---

## Next Steps After Setup

1. **Hardware:** Wire ESP32 + 4× YF-S201 per [block-diagram.md](./block-diagram.md)
2. **Firmware:** Flash ESP32 per [esp32-firmware-complete-guide.md](./esp32-firmware-complete-guide.md)
3. **Calibrate:** Bucket test per [esp32-firmware-complete-guide.md](./esp32-firmware-complete-guide.md#sensor-calibration-bucket-test)
4. **ML Training:** Follow [ml-complete-guide.md](./ml-complete-guide.md) for real models
5. **Remote Access:** Configure Cloudflare Tunnel for HTTPS access from anywhere

---

*Last updated: July 2026 | Target: Raspberry Pi OS Trixie 64-bit | Compatible with Pi 3B+/4/5*