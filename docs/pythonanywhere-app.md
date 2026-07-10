# PythonAnywhere Backend App

> **Purpose:** Flask web app running on PythonAnywhere that connects to Firebase via Pyrebase4, runs XGBoost + Isolation Forest ML models, serves a dashboard, and sends alerts.
> **Stack:** Flask + Pyrebase4 + XGBoost + scikit-learn + Chart.js

---

## Architecture

```
PythonAnywhere Web App
├── WSGI Entry: app.py (Flask)
├── Firebase Listener: firebase_listener.py (Pyrebase4 stream)
├── ML Inference: ml_inference.py (XGBoost + Isolation Forest)
├── Alert Engine: alert_engine.py (Telegram / Email)
├── Web Dashboard: templates/ (Jinja2 + Chart.js)
├── Models: models/ (xgboost_model.json, isolation_forest.pkl)
└── Data: training/ (incremental training data)
```

---

## File Structure

```
pythonanywhere/
├── app.py                           # Flask application entry point
├── firebase_listener.py             # Pyrebase4 stream listener (background thread)
├── ml_inference.py                  # XGBoost + Isolation Forest wrapper
├── alert_engine.py                  # Telegram bot + email notifications
├── config.py                        # Configuration (Firebase, Telegram, etc.)
├── requirements.txt                 # Python dependencies
├── serviceAccountKey.json           # Firebase service account (SECRET — do not commit)
├── models/
│   ├── xgboost_leak_model.json      # Trained XGBoost model
│   ├── isolation_forest.pkl         # Trained Isolation Forest
│   └── scaler.pkl                   # Feature scaler
├── templates/
│   ├── dashboard.html               # Main dashboard
│   ├── device_detail.html           # Per-device detail page
│   └── alerts.html                  # Alert history
├── static/
│   ├── css/style.css
│   └── js/dashboard.js              # Real-time updates (SSE)
└── training/
    └── training_data.csv            # Accumulated training data
```

---

## Quick Deploy on PythonAnywhere

### Step 1: Create Account

1. Go to [pythonanywhere.com](https://www.pythonanywhere.com/)
2. Sign up for a **Free** or **Hacker** ($5/month) account
3. Verify email

### Step 2: Upload Files

```bash
# Open a Bash console on PythonAnywhere
git clone https://github.com/qppd/water-meter.git
cd water-meter/pythonanywhere/

# Create virtual environment
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Firebase

1. Upload your Firebase service account key:
   - From your computer: use the **Files** tab → **Upload**
   - Or from console:
     ```bash
     # In PythonAnywhere Bash console
     nano serviceAccountKey.json
     # Paste your Firebase service account JSON, Ctrl+X, Y, Enter
     ```

2. Edit `config.py`:
   ```python
   # config.py
   import os
   
   class Config:
       FIREBASE_CONFIG = {
           "apiKey": "AIzaSy...",
           "authDomain": "your-project.firebaseapp.com",
           "databaseURL": "https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app",
           "storageBucket": "your-project.appspot.com",
           "serviceAccount": os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
       }
       
       DEVICE_ID = "wm_001"
       
       # Telegram Bot
       TELEGRAM_BOT_TOKEN = "your_bot_token"
       TELEGRAM_CHAT_ID = "your_chat_id"
       
       # Admin API key (for retraining endpoints)
       ADMIN_API_KEY = "your-secret-key-123"
       
       # Model paths
       XGB_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "xgboost_leak_model.json")
       IFOREST_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "isolation_forest.pkl")
       SCALER_PATH = os.path.join(os.path.dirname(__file__), "models", "scaler.pkl")
   ```

### Step 4: Set Up Web App

1. Go to **Web tab** → **Add a new web app**
2. Choose **Flask** as framework
3. Choose **Python 3.9** or **3.10**
4. Set source code path: `/home/youruser/water-meter/pythonanywhere/`
5. Click **Next** → wait for setup
6. Edit WSGI configuration:
   - Click on **WSGI configuration file** link
   - Replace content with:
     ```python
     import sys
     path = '/home/youruser/water-meter/pythonanywhere'
     if path not in sys.path:
         sys.path.append(path)
     
     from app import app as application
     ```
   - Save (Ctrl+X, Y, Enter)

### Step 5: Configure Background Task (Stream Listener)

PythonAnywhere Free accounts can run **one always-on task** (Hacker/Beta plans only):

```python
# In app.py — runs stream listener in a separate thread
from firebase_listener import start_listener
import threading

# Start Firebase stream listener in background
listener_thread = threading.Thread(target=start_listener, daemon=True)
listener_thread.start()
```

For Free accounts, use **Scheduled Tasks** instead:
- Every 5 minutes: run a script that reads recent Firebase data

### Step 6: Reload Web App

Click the **Reload** button in the Web tab
Visit: `https://youruser.pythonanywhere.com/`

---

## App Code

### app.py (Flask)

```python
from flask import Flask, render_template, jsonify, request
from config import Config
from ml_inference import LeakDetector
from firebase_listener import FirebaseListener
from alert_engine import AlertEngine
import threading

app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
detector = LeakDetector()
listener = FirebaseListener()
alert_engine = AlertEngine()

# Start Firebase stream listener
listener_thread = threading.Thread(target=listener.start_stream, daemon=True)
listener_thread.start()

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html', device_id=Config.DEVICE_ID)

@app.route('/api/readings/latest')
def latest_readings():
    """Get latest sensor readings."""
    data = listener.get_latest_readings()
    return jsonify(data)

@app.route('/api/readings/history')
def reading_history():
    """Get reading history."""
    hours = request.args.get('hours', 24, type=int)
    data = listener.get_reading_history(hours)
    return jsonify(data)

@app.route('/api/alerts')
def get_alerts():
    """Get active alerts."""
    active_only = request.args.get('active', 'true').lower() == 'true'
    alerts = listener.get_alerts(active_only)
    return jsonify(alerts)

@app.route('/api/valve/control', methods=['POST'])
def valve_control():
    """Send valve command to ESP32 via Firebase."""
    data = request.json
    command = data.get('command')
    if not command:
        return jsonify({"error": "No command specified"}), 400
    
    listener.send_command(command)
    return jsonify({"status": "ok", "command": command})

@app.route('/api/predict', methods=['POST'])
def predict():
    """Run ML inference on provided data."""
    data = request.json
    features = data.get('features')
    if not features:
        return jsonify({"error": "No features provided"}), 400
    
    result = detector.predict(features)
    return jsonify(result)

@app.route('/api/retrain', methods=['POST'])
def retrain():
    """Trigger model retraining (admin only)."""
    api_key = request.headers.get('X-API-Key')
    if api_key != Config.ADMIN_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Run retraining in background
    threading.Thread(target=detector.retrain, daemon=True).start()
    return jsonify({"status": "retraining_started"})

@app.route('/alerts')
def alerts_page():
    """Alert history page."""
    return render_template('alerts.html')

@app.route('/device/<device_id>')
def device_detail(device_id):
    """Per-device detail page."""
    return render_template('device_detail.html', device_id=device_id)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### firebase_listener.py

```python
import pyrebase
import json
from datetime import datetime
from config import Config
from ml_inference import detector
from alert_engine import alert_engine

class FirebaseListener:
    def __init__(self):
        self.firebase = pyrebase.initialize_app(Config.FIREBASE_CONFIG)
        self.db = self.firebase.database()
        self.latest_readings = {}
        self.stream = None
    
    def handle_readings_stream(self, message):
        """Called when new data arrives in Firebase /readings/."""
        if message['event'] in ('put', 'patch'):
            path = message['path']
            data = message['data']
            
            if data:
                # Store latest
                self.latest_readings = data
                
                # Extract features per sensor
                for sensor_key in ['inlet', 'fixture_1', 'fixture_2', 'fixture_3', 'fixture_4']:
                    if sensor_key in data:
                        sensor_data = data[sensor_key]
                        features = extract_features(sensor_data, sensor_key)
                        
                        # Run ML inference
                        result = detector.predict(features)
                        
                        # Check for leak
                        if result['final'] in ('minor_leak', 'major_leak', 'anomaly'):
                            self.handle_leak(result, sensor_key, sensor_data)
    
    def handle_leak(self, ml_result, sensor_key, sensor_data):
        """Handle a detected leak by writing alert and notifying."""
        alert_data = {
            "fixture_index": sensor_key,
            "alert_type": ml_result['final'],
            "confidence": ml_result['xgboost']['confidence'],
            "source": "xgboost",
            "details": {
                "flow_rate": sensor_data.get('flow_rate', 0),
                "xgboost_probs": ml_result['xgboost']['probabilities'],
                "isolation_forest_score": ml_result['isolation_forest']['score']
            },
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "resolved": False
        }
        
        # Write alert to Firebase
        self.db.child("alerts").child(Config.DEVICE_ID).push(alert_data)
        
        # Send notification
        alert_engine.send_alert(alert_data)
        
        # Send valve close command
        self.send_command(f"close_{sensor_key}")
    
    def send_command(self, command):
        """Write a command for ESP32 to read."""
        cmd_data = {
            "command": command,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "source": "ml_model"
        }
        self.db.child("commands").child(Config.DEVICE_ID).push(cmd_data)
    
    def get_latest_readings(self):
        """Get latest readings from cache."""
        return self.latest_readings
    
    def get_reading_history(self, hours=24):
        """Get historical readings."""
        # Read from Firebase, limit to last N hours
        readings = self.db.child("readings").child(Config.DEVICE_ID)\
            .order_by_key().limit_to_last(100).get()
        return readings.val() if readings.val() else {}
    
    def get_alerts(self, active_only=True):
        """Get alerts from Firebase."""
        alerts = self.db.child("alerts").child(Config.DEVICE_ID).get()
        result = {}
        if alerts.val():
            for key, val in alerts.val().items():
                if active_only and val.get('resolved', True):
                    continue
                result[key] = val
        return result
    
    def start_stream(self):
        """Start the Firebase stream listener."""
        self.stream = self.db.child("readings").child(Config.DEVICE_ID)\
            .stream(self.handle_readings_stream, stream_id="readings_stream")

# Global instance
listener = FirebaseListener()
```

### dashboard.html (Template Snippet)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Water Meter Dashboard — {{ device_id }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #1a1a2e; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
        .card { background: #16213e; border: 1px solid #0f3460; border-radius: 12px; }
        .card-title { color: #e94560; }
        .value { font-size: 2em; font-weight: bold; }
        .unit { font-size: 0.8em; color: #888; }
        .leak-active { animation: pulse 1s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="container py-4">
        <h1>💧 Water Meter Monitor</h1>
        <p class="text-muted">Device: {{ device_id }} | <span id="status">Loading...</span></p>
        
        <div class="row" id="sensor-cards">
            <!-- Dynamically populated by JS -->
        </div>
        
        <div class="row mt-4">
            <div class="col-md-8">
                <div class="card p-3">
                    <h5 class="card-title">Flow Rate History (L/min)</h5>
                    <canvas id="flowChart" height="200"></canvas>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card p-3" id="alerts-card">
                    <h5 class="card-title">🚨 Active Alerts</h5>
                    <div id="alerts-list">No active alerts</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const deviceId = '{{ device_id }}';
        const flowChart = new Chart(document.getElementById('flowChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Inlet', data: [], borderColor: '#e94560', fill: false },
                    { label: 'Fixture 1', data: [], borderColor: '#0f3460', fill: false },
                    { label: 'Fixture 2', data: [], borderColor: '#533483', fill: false },
                    { label: 'Fixture 3', data: [], borderColor: '#16213e', fill: false },
                    { label: 'Fixture 4', data: [], borderColor: '#1a1a2e', fill: false }
                ]
            },
            options: { responsive: true }
        });
        
        function updateDashboard() {
            fetch('/api/readings/latest')
                .then(r => r.json())
                .then(data => {
                    // Update sensor cards
                    const container = document.getElementById('sensor-cards');
                    container.innerHTML = '';
                    
                    const sensors = [
                        {id: 'inlet', name: 'Main Inlet', icon: '🚰'},
                        {id: 'fixture_1', name: 'Kitchen Sink', icon: '🍳'},
                        {id: 'fixture_2', name: 'Toilet', icon: '🚽'},
                        {id: 'fixture_3', name: 'Wash Basin', icon: '🧼'},
                        {id: 'fixture_4', name: 'Shower', icon: '🚿'}
                    ];
                    
                    sensors.forEach(s => {
                        if (data[s.id]) {
                            const card = `
                                <div class="col-md mb-3">
                                    <div class="card p-3 text-center">
                                        <div class="display-6">${s.icon}</div>
                                        <h6>${s.name}</h6>
                                        <div class="value">${data[s.id].flow_rate.toFixed(1)}</div>
                                        <div class="unit">L/min</div>
                                        <small>Total: ${data[s.id].total.toFixed(1)} L</small>
                                    </div>
                                </div>
                            `;
                            container.innerHTML += card;
                        }
                    });
                    
                    // Update chart
                    const now = new Date().toLocaleTimeString();
                    flowChart.data.labels.push(now);
                    sensors.forEach((s, i) => {
                        if (data[s.id]) {
                            flowChart.data.datasets[i].data.push(data[s.id].flow_rate);
                        }
                    });
                    if (flowChart.data.labels.length > 20) {
                        flowChart.data.labels.shift();
                        flowChart.data.datasets.forEach(d => d.data.shift());
                    }
                    flowChart.update();
                });
        }
        
        // Update every 5 seconds
        setInterval(updateDashboard, 5000);
        updateDashboard();
    </script>
</body>
</html>
```

---

## requirements.txt

```
flask>=2.3.0
pyrebase4>=4.6.0
xgboost>=2.0.0
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
joblib>=1.3.0
requests>=2.31.0
python-telegram-bot>=20.0
gunicorn>=21.2.0
```

---

## Troubleshooting PythonAnywhere

| Problem | Solution |
|---------|----------|
| **App not loading** | Check Web tab → Logs → Error log |
| **Pyrebase4 stream not working** | Free accounts can't run background threads — use Hacker plan or scheduled tasks |
| **"Module not found"** | Make sure venv is activated and `pip install -r requirements.txt` ran successfully |
| **Firebase authentication fails** | Verify `serviceAccountKey.json` is correct and in the right path |
| **Memory limit exceeded** | Free: 512 MB RAM. Upgrade to Hacker ($5/mo): 1024 MB |
| **Daily request limit** | Free: 100 requests/day. Upgrade for unlimited |
| **Model file not found** | Check `models/` path in config.py — use absolute paths |

> **Note:** For a production deployment, run the Firebase stream listener on a separate **always-on task** (Hacker plan feature). Or use Flask's scheduler for periodic polling.
