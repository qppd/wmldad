# RPi Backend App — Deploying the Flask + ML Backend on Raspberry Pi

> **Hardware:** Raspberry Pi 3B+/4/5  
> **OS:** Raspberry Pi OS (64-bit) Bookworm  
> **Stack:** Flask + Firebase Admin SDK + XGBoost + Isolation Forest

---

## Quick Start

```bash
# 1. Clone the project
git clone https://github.com/qppd/wmldad.git
cd wmldad/rpi/

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Upload Firebase service account key
#    Copy serviceAccountKey.json to this directory

# 5. Run Flask app
python app.py

# 6. Test: Open browser to http://<rpi-ip>:5000/
```

---

## Detailed Setup

### 1. Raspberry Pi Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+ and venv
sudo apt install -y python3 python3-venv python3-pip

# Enable SSH (for headless access)
sudo systemctl enable ssh
sudo systemctl start ssh
```

### 2. Project Setup

```bash
# Clone repository
git clone https://github.com/qppd/wmldad.git
cd wmldad/rpi/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 3. Firebase Service Account

1. In Firebase Console → **Project Settings → Service Accounts**
2. Click **Generate new private key**
3. Save as `serviceAccountKey.json` in `rpi/` directory

```bash
# Verify file exists
ls -la serviceAccountKey.json
```

### 4. Environment Configuration

Create `.env` file (or edit `app.py` directly):

```python
# app.py configuration
DEVICE_ID = "wm_001"
FIREBASE_DB_URL = "https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app"
SERVICE_ACCOUNT_PATH = "serviceAccountKey.json"
```

### 5. ML Model Files

Copy trained models from training phase:

```bash
# From Google Colab / Jupyter training
cp training/xgboost_leak_model.json rpi/models/
cp training/isolation_forest.pkl rpi/models/
cp training/scaler.pkl rpi/models/
```

Verify:
```bash
ls -la models/
# Should show: xgboost_leak_model.json, isolation_forest.pkl, scaler.pkl
```

---

## Running the Backend

### Development Mode

```bash
cd rpi/
source venv/bin/activate
python app.py
```

Output:
```
 * Running on all addresses (0.0.0.0:5000)
 * Running on http://192.168.1.xxx:5000
 * Running on http://127.0.0.1:5000
```

Access dashboard at: `http://<rpi-ip>:5000/`

### Production Mode (systemd Service)

Create service file:

```bash
sudo tee /etc/systemd/system/water-meter.service > /dev/null <<'EOF'
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

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable water-meter.service
sudo systemctl start water-meter.service

# Check status
sudo systemctl status water-meter.service

# View logs
journalctl -u water-meter.service -f
```

---

## Requirements.txt

```
flask>=2.3
firebase-admin>=6.2
xgboost>=2.0
scikit-learn>=1.3
pandas>=2.0
numpy>=1.24
joblib>=1.3
gunicorn>=21.0
python-dotenv>=1.0
requests>=2.31
```

---

## Project Structure (rpi/)

```
rpi/
├── app.py                 # Main Flask application
├── firebase_listener.py   # Firebase Admin SDK polling
├── ml_inference.py        # XGBoost + Isolation Forest inference
├── alert_engine.py        # Notification system (Telegram, Email)
├── models/                # Trained ML models
│   ├── xgboost_leak_model.json
│   ├── isolation_forest.pkl
│   └── scaler.pkl
├── templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   └── alerts.html
├── static/                # CSS, JS, Chart.js
│   ├── css/
│   ├── js/
│   └── lib/
├── requirements.txt
├── serviceAccountKey.json # Firebase service account (gitignored)
├── .env                   # Environment variables (gitignored)
└── water-meter.service    # systemd service file
```

---

## Key Components

### app.py — Flask Entry Point

```python
from flask import Flask, render_template, jsonify, request
from firebase_listener import FirebaseListener
from ml_inference import LeakDetector
from alert_engine import AlertEngine
import threading
import os

app = Flask(__name__)

# Initialize components
listener = FirebaseListener(
    db_url=os.getenv("FIREBASE_DB_URL"),
    cred_path=os.getenv("SERVICE_ACCOUNT_PATH"),
    device_id=os.getenv("DEVICE_ID", "wm_001")
)
detector = LeakDetector(
    xgb_path="models/xgboost_leak_model.json",
    iforest_path="models/isolation_forest.pkl",
    scaler_path="models/scaler.pkl"
)
alert_engine = AlertEngine(
    telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
    telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID")
)

# Start background listener
listener.start()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/latest')
def api_latest():
    latest = listener.get_latest_reading()
    return jsonify(latest)

@app.route('/api/alerts')
def api_alerts():
    alerts = listener.get_recent_alerts(limit=20)
    return jsonify(alerts)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.json
    features = extract_features_from_request(data)
    result = detector.predict(features)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### firebase_listener.py — Firebase Admin SDK Polling

```python
import firebase_admin
from firebase_admin import credentials, db as firebase_db
import threading
import time
from datetime import datetime

class FirebaseListener:
    def __init__(self, db_url, cred_path, device_id):
        self.device_id = device_id
        self.last_timestamp = None
        
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            "databaseURL": db_url
        })
        
        self.readings_ref = firebase_db.reference(f"readings/{device_id}")
        self.alerts_ref = firebase_db.reference(f"alerts/{device_id}")
        self.commands_ref = firebase_db.reference(f"commands/{device_id}")
        
    def start(self):
        """Start polling thread"""
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        
    def _poll_loop(self):
        while True:
            try:
                self._check_new_readings()
            except Exception as e:
                print(f"Poll error: {e}")
            time.sleep(5)  # Poll every 5 seconds
            
    def _check_new_readings(self):
        # Get latest reading
        readings = self.readings_ref.order_by_key().limit_to_last(1).get()
        if readings:
            for ts, data in readings.items():
                if ts != self.last_timestamp:
                    self.last_timestamp = ts
                    self.process_reading(data)
                    
    def process_reading(self, data):
        # Extract features and run ML inference
        features = self.extract_features(data)
        result = detector.predict(features)
        
        if result['final'] != 'normal':
            # Write alert to Firebase
            alert_data = {
                "alert_type": result['final'],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "confidence": result.get('confidence', 0),
                "fixture_index": data.get('fixture_index', -1),
                "valve_action": "monitoring"
            }
            self.alerts_ref.push(alert_data)
            
            # Send notification
            alert_engine.send_telegram(alert_data)
            
    def get_latest_reading(self):
        return self.readings_ref.order_by_key().limit_to_last(1).get()
        
    def get_recent_alerts(self, limit=20):
        return self.alerts_ref.order_by_key().limit_to_last(limit).get()
        
    def send_command(self, command):
        self.commands_ref.push({
            "command": command,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "dashboard"
        })
```

### ml_inference.py — XGBoost + Isolation Forest

```python
import xgboost as xgb
import joblib
import numpy as np

class LeakDetector:
    def __init__(self, xgb_path, iforest_path, scaler_path):
        self.xgb = xgb.XGBClassifier()
        self.xgb.load_model(xgb_path)
        self.iforest = joblib.load(iforest_path)
        self.scaler = joblib.load(scaler_path)
        self.confidence_threshold = 0.80
        self.model_loaded = True
        self.n_features = 9
        
    def predict(self, features_raw):
        # Scale features
        features = self.scaler.transform(features_raw.reshape(1, -1))
        
        # 1. XGBoost prediction
        xgb_probs = self.xgb.predict_proba(features)[0]
        xgb_class = np.argmax(xgb_probs)
        xgb_confidence = xgb_probs[xgb_class]
        
        # 2. Isolation Forest anomaly score
        iforest_score = self.iforest.score_samples(features)[0]
        is_anomaly = self.iforest.predict(features)[0] == -1
        
        result = {
            'xgboost': {
                'class': ['normal', 'minor_leak', 'major_leak'][xgb_class],
                'confidence': float(xgb_confidence),
                'probabilities': {
                    'normal': float(xgb_probs[0]),
                    'minor_leak': float(xgb_probs[1]),
                    'major_leak': float(xgb_probs[2])
                }
            },
            'isolation_forest': {
                'anomaly': bool(is_anomaly),
                'score': float(iforest_score)
            }
        }
        
        # Decision logic
        if xgb_confidence >= self.confidence_threshold:
            result['final'] = result['xgboost']['class']
        elif is_anomaly:
            result['final'] = 'anomaly'
        else:
            result['final'] = 'uncertain'
            
        return result
```

### alert_engine.py — Notifications

```python
import requests
import smtplib
from email.mime.text import MIMEText

class AlertEngine:
    def __init__(self, telegram_token=None, telegram_chat_id=None):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        
    def send_telegram(self, alert_data):
        if not self.telegram_token or not self.telegram_chat_id:
            return
            
        message = f"""
🚨 *Water Meter Alert*
*Type:* {alert_data['alert_type']}
*Confidence:* {alert_data.get('confidence', 0):.2f}
*Fixture:* {alert_data.get('fixture_name', 'Unknown')}
*Time:* {alert_data['timestamp']}
        """
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, data=data)
        
    def send_email(self, alert_data, to_email):
        # Configure with your SMTP settings
        pass
```

---

## Telegram Bot Setup

1. Open Telegram, search for **@BotFather**
2. Send `/newbot` → follow prompts
3. Save the **API token**
4. Get your **Chat ID**:
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find `"chat":{"id":123456789}`
5. Add to environment:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token_here"
   export TELEGRAM_CHAT_ID="123456789"
   ```

---

## Dashboard Templates

### templates/dashboard.html

```html
<!DOCTYPE html>
<html>
<head>
    <title>Water Meter Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-6">Water Meter Dashboard</h1>
        
        <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
            <div class="bg-white p-4 rounded shadow">
                <h3 class="text-gray-500">Inlet</h3>
                <p id="inlet-rate" class="text-2xl font-bold">0.0 L/min</p>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <h3 class="text-gray-500">Kitchen</h3>
                <p id="fix1-rate" class="text-2xl font-bold">0.0 L/min</p>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <h3 class="text-gray-500">Toilet</h3>
                <p id="fix2-rate" class="text-2xl font-bold">0.0 L/min</p>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <h3 class="text-gray-500">Basin</h3>
                <p id="fix3-rate" class="text-2xl font-bold">0.0 L/min</p>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <h3 class="text-gray-500">Shower</h3>
                <p id="fix4-rate" class="text-2xl font-bold">0.0 L/min</p>
            </div>
        </div>
        
        <canvas id="flowChart" class="bg-white rounded shadow"></canvas>
    </div>
    
    <script>
        // Fetch data every 5 seconds
        setInterval(fetchData, 5000);
        fetchData();
        
        function fetchData() {
            fetch('/api/latest')
                .then(r => r.json())
                .then(data => updateUI(data));
        }
        
        function updateUI(data) {
            // Update readings...
        }
    </script>
</body>
</html>
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **App not loading** | Check Flask output: `journalctl -u water-meter.service -f` |
| **"Internal Server Error"** | View error log: `sudo journalctl -u water-meter.service --since "5 min ago"` |
| **Module not found** | Activate venv → `pip install -r requirements.txt` |
| **Memory error** | RPi 4 has 2-8GB RAM — check `free -h`. Reduce `n_estimators` in XGBoost if needed. |
| **RPi not reachable** | Check network: `ping <rpi-ip>`. Ensure port 5000 is not blocked by firewall |
| **RPi auto-start not working** | Check systemd: `sudo systemctl status water-meter.service` |
| **SD card corruption** | Use a UPS and `sudo raspi-config` → Performance → Overlay File System for read-only root |

---

## Remote Access

### SSH Tunneling (for dashboard access)

```bash
# From your laptop
ssh -L 5000:localhost:5000 pi@<rpi-ip>

# Then open http://localhost:5000 in browser
```

### Ngrok (public URL)

```bash
# Install ngrok
# Then:
ngrok http 5000
# Gives you a public https://xxx.ngrok.io URL
```

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