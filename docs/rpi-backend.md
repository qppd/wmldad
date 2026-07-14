# RPi Backend Setup Guide — Flask + ML + Firebase on Raspberry Pi

> **Hardware:** Raspberry Pi 3B+/4/5  
> **OS:** Raspberry Pi OS Trixie 64-bit (Debian 13)  
> **Stack:** Flask + Pyrebase4 + XGBoost + Isolation Forest + systemd  
> **Purpose:** Create all backend files from scratch for water meter leak detection

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Setup](#system-setup)
3. [Project Structure Creation](#project-structure-creation)
4. [Python Environment & Dependencies](#python-environment--dependencies)
5. [Firebase Configuration](#firebase-configuration)
6. [Create Application Files](#create-application-files)
7. [ML Model Files](#ml-model-files)
8. [Systemd Service (Auto-start)](#systemd-service-auto-start)
9. [Remote Access (Optional)](#remote-access-optional)
10. [Verification & Testing](#verification--testing)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Raspberry Pi 3B+ / 4 / 5 with **Raspberry Pi OS Trixie 64-bit** installed
- SSH access enabled (see [raspberry-pi-installation.md](./raspberry-pi-installation.md))
- Firebase project created (see [firebase-setup-guide.md](./firebase-setup-guide.md))
- ESP32 firmware uploaded and sending data (see [esp32-setup-guide.md](./esp32-setup-guide.md))
- ML models trained (see [ml-complete-guide.md](./ml-complete-guide.md))

---

## System Setup

```bash
# 1. Update system
sudo apt update && sudo apt full-upgrade -y

# 2. Install Python 3.12+ and tools
sudo apt install -y python3 python3-venv python3-pip git

# 3. Verify Python version (should be 3.12+ on Trixie)
python3 --version
# Python 3.12.x

# 4. Enable SSH (if not already)
sudo systemctl enable ssh
sudo systemctl start ssh
```

---

## Project Structure Creation

```bash
# 1. Clone or create project directory
cd /home/pi
git clone https://github.com/qppd/wmldad.git
cd wmldad

# 2. Create rpi/ directory structure
mkdir -p rpi/{models,templates,static/css,static/js,static/lib}

# 3. Verify structure
tree rpi/
# rpi/
# ├── models/
# ├── templates/
# ├── static/
# │   ├── css/
# │   ├── js/
# │   └── lib/
```

---

## Python Environment & Dependencies

### 1. Create Virtual Environment

```bash
cd /home/pi/wmldad/rpi
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 2. Create requirements.txt

```bash
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

### 3. Install Dependencies

```bash
# This takes 5-10 minutes on RPi (compiling xgboost/numpy from source)
pip install --no-cache-dir -r requirements.txt

# Verify key packages
python -c "import xgboost, sklearn, pandas, numpy, flask, pyrebase; print('All packages OK')"
```

> **Note:** On Raspberry Pi (ARM64), `xgboost` and `numpy` compile from source. This is normal and takes time.

---

## Firebase Configuration

### 1. Get Firebase Web Config

1. Open [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. **Project Settings** (gear icon) → **General** tab
4. Scroll to **Your apps** → Click **Web app** (</>) or create one
5. Copy the `firebaseConfig` object

### 2. Create firebase_config.json

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

> **Important:** Replace all values with your actual Firebase config. This file is gitignored.

### 3. Create .env File

```bash
cat > .env << 'EOF'
FIREBASE_EMAIL=esp32@your-project.iam.gserviceaccount.com
FIREBASE_PASSWORD=your-strong-password-here
DEVICE_ID=wm_001
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
EOF
```

> **Note:** The email/password must match a user created in Firebase Console → **Authentication** → **Sign-in method** → **Email/Password** → **Add user**.

### 4. Verify Firebase Config

```bash
python3 -c "
import json, os
with open('firebase_config.json') as f:
    config = json.load(f)
print('Firebase config loaded:')
for k, v in config.items():
    print(f'  {k}: {v[:20]}...' if len(v) > 20 else f'  {k}: {v}')
"
```

---

## Create Application Files

### 1. Create ml_inference.py (XGBoost + Isolation Forest)

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

### 2. Create firebase_listener.py (Pyrebase4 Polling)

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

### 3. Create alert_engine.py (In-App Notifications)

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

### 4. Create app.py (Flask Entry Point)

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

### 5. Create api_endpoints.py (API Blueprint)

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

### 6. Create templates/dashboard.html

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

### 7. Create static/css/dashboard.css

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

### 8. Create static/js/dashboard.js

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

## ML Model Files

### If you have trained models (from Colab/local):

```bash
# Copy from training machine to RPi
scp -r models/ pi@water-meter.local:~/wmldad/rpi/models/

# Verify
ls -la ~/wmldad/rpi/models/
# xgboost_model.json  isolation_forest.pkl  scaler.pkl  iso_threshold.pkl  feature_cols.pkl  metadata.json
```

### If you DON'T have trained models yet:

Create placeholder models for testing:

```bash
cd ~/wmldad/rpi

python3 << 'PYEOF'
import xgboost as xgb
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
import joblib

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
import json
with open('models/metadata.json', 'w') as f:
    json.dump({
        'version': '1.0-placeholder',
        'created': '2026-07-14T00:00:00Z',
        'feature_cols': feature_cols,
        'target_names': ['normal', 'minor_leak', 'major_leak'],
        'note': 'PLACEHOLDER - Replace with real trained models'
    }, f, indent=2)

print("Placeholder models created")
PYEOF
```

> ⚠️ **Important:** Replace with real trained models from [ml-complete-guide.md](./ml-complete-guide.md) for production use.

---

## Systemd Service (Auto-start)

### 1. Create Service File

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

### 2. Enable & Start

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

---

## Remote Access (Optional)

### Port Forwarding + DDNS

| Setting | Value |
|---------|-------|
| External Port | 8443 |
| Internal IP | Raspberry Pi LAN IP (e.g., 192.168.1.100) |
| Internal Port | 5000 |
| Protocol | TCP |

**DuckDNS (Free):**
```bash
# Create account at duckdns.org
# Add cron for auto-update:
crontab -e
# */5 * * * * curl "https://www.duckdns.org/update?domains=yourdomain&token=yourtoken&ip="
```

### Cloudflare Tunnel (Recommended - Free HTTPS)

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create water-meter

# Route DNS
cloudflared tunnel route dns water-meter yourdomain.com

# Install as service
sudo cloudflared service install
```

**Access URLs:**
- Local: `http://<rpi-ip>:5000/`
- Remote (Port Forward): `http://<public-ip>:8443/`
- Remote (DDNS): `http://yourdomain.duckdns.org:8443/`
- Remote (Cloudflare): `https://yourdomain.com/`

---

## Verification & Testing

### 1. Health Check

```bash
curl http://localhost:5000/api/health
# {"status":"healthy","firebase_connected":true,"model_loaded":true,"device_id":"wm_001"}
```

### 2. Dashboard

Open browser: `http://<rpi-ip>:5000/`

Verify:
- ✅ Flow rate cards update every 5 seconds
- ✅ Chart shows live data
- ✅ Alerts table populates
- ✅ Calibrate/Reboot buttons work

### 3. API Test

```bash
# Benchmark inference
curl http://localhost:5000/api/benchmark
# {"avg_time_ms": 2.3, "throughput_fps": 430, ...}

# Test prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [[5.0, 120, 14, 2, 1, 1.05, 0.1, 0, 0.1]]}'
```

### 4. Verify Firebase Data Flow

1. Open Firebase Console → Realtime Database
2. Check `/readings/wm_001/` — new data every 5 seconds
3. Check `/alerts/wm_001/` — alerts appear when leaks detected
4. Check `/commands/wm_001/` — commands sent from dashboard

### 5. Test ESP32 Communication

```bash
# On RPi, monitor serial (if USB connected for testing)
screen /dev/ttyUSB0 115200
# Should see JSON lines every 5 seconds
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **App not loading** | Check Flask output: `journalctl -u water-meter.service -f` |
| **"Internal Server Error"** | View Flask error log: `sudo journalctl -u water-meter.service --since "5 min ago"` |
| **Module not found** | Activate venv → `pip install -r requirements.txt` |
| **Memory error** | RPi 4 has 2-8GB RAM — check `free -h`. Reduce `n_estimators` in XGBoost. |
| **RPi not reachable** | Check network: `ping <rpi-ip>`. Ensure port 5000 not blocked by firewall. |
| **RPi auto-start not working** | Check systemd: `sudo systemctl status water-meter.service` |
| **SD card corruption** | Use UPS and `sudo raspi-config` → Performance → Overlay File System for read-only root |
| **Firebase permission denied** | Check Security Rules in Firebase Console. Verify email/password user exists. |
| **esptool.py not found** | `pip3 install esptool` |

---

## Backup & Maintenance

```bash
# Backup models
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/

# Backup Firebase data (via CLI)
firebase database:get /readings > backup_readings.json

# Check disk space
df -h

# Update system
sudo apt update && sudo apt upgrade -y
```

---

## Complete File Checklist

After this guide, your `rpi/` should contain:

```
rpi/
├── app.py                      # Flask entry point
├── firebase_listener.py        # Pyrebase4 polling
├── ml_inference.py             # XGBoost + IF inference
├── alert_engine.py             # Notifications
├── api_endpoints.py            # REST API blueprint
├── models/                     # ML artifacts
│   ├── xgboost_model.json
│   ├── isolation_forest.pkl
│   ├── scaler.pkl
│   ├── iso_threshold.pkl
│   ├── feature_cols.pkl
│   └── metadata.json
├── templates/
│   └── dashboard.html          # Bootstrap + Chart.js
├── static/
│   ├── css/dashboard.css
│   └── js/dashboard.js
├── requirements.txt
├── firebase_config.json        # Gitignored
├── .env                        # Gitignored
├── water-meter.service         # systemd (copy to /etc/systemd/system/)
├── venv/                       # Virtual environment
```

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| Start service | `sudo systemctl start water-meter.service` |
| Stop service | `sudo systemctl stop water-meter.service` |
| Restart service | `sudo systemctl restart water-meter.service` |
| View logs | `journalctl -u water-meter.service -f` |
| Run manually | `cd ~/wmldad/rpi && source venv/bin/activate && python app.py` |
| Install deps | `cd ~/wmldad/rpi && source venv/bin/activate && pip install -r requirements.txt` |
| Copy models | `scp -r models/ pi@water-meter.local:~/wmldad/rpi/` |
| Benchmark | `curl http://localhost:5000/api/benchmark` |
| Health check | `curl http://localhost:5000/api/health` |
| Manual retrain | `cd ~/wmldad/rpi && source venv/bin/activate && python retrain.py` |

---

*Last updated: July 2026 | Target: Raspberry Pi OS Trixie 64-bit | Flask 3.x + XGBoost 2.x + Pyrebase4 | Compatible with Pi 3B+/4/5*