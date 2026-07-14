# ML Model — Leak Detection & Anomaly Detection

> **Primary Model:** XGBoost (Gradient-Boosted Decision Trees)  
> **Secondary Model:** Isolation Forest (Unsupervised Anomaly Detection)  
> **Training Location:** Google Colab or Jupyter Notebook  
> **Inference Location:** RPi (Flask backend, server-side)

---

## Model Selection Analysis

### Why XGBoost over Random Forest?

| Criteria | XGBoost | Random Forest |
|----------|---------|---------------|
| **Accuracy (tabular data)** | **95–98%** | 92–95% |
| **Training speed** | **2–3× faster** | Slower (many trees) |
| **Model size** | ~500 KB (JSON) | ~5 MB (pickle) |
| **Calibrated probabilities** | **Better confidence scores** | Tends to be overconfident |
| **Overfitting control** | **Built-in regularization** | Needs careful tuning |
| **Feature importance** | **Native + SHAP** | Gini importance only |
| **RPi support** | **Runs on ARM: `pip install xgboost`** | Works on RPi |
| **Inference speed** | **< 1ms** | < 5ms |

**Verdict:** XGBoost wins for tabular time-series data with clear decision boundaries like water consumption patterns.

### Why Isolation Forest as Secondary?

- **Unsupervised** — doesn't need labeled data to find anomalies
- **Catches what XGBoost misses** — unknown patterns not in training data
- **Lightweight** — runs in < 1ms on RPi (ARM CPU)
- **Complementary** — XGBoost classifies known patterns, Isolation Forest flags unknowns

---

## Feature Engineering

### Feature Set (9 features)

| # | Feature | Type | Description | Engineering |
|---|---------|------|-------------|-------------|
| 1 | `flow_rate` | float | Current flow rate (L/min) | `pulse_count × 60 ÷ (PPL × interval)` |
| 2 | `duration_seconds` | int | Seconds since water started flowing | `now - flow_start_time` |
| 3 | `hour_of_day` | int | Hour (0–23) | Extract from timestamp |
| 4 | `day_of_week` | int | Day (0=Mon, 6=Sun) | Extract from timestamp |
| 5 | `fixture_id` | int | One-hot encoded fixture (0=inlet, 1–4=fixtures) | Sensor index |
| 6 | `inlet_ratio` | float | Inlet rate ÷ fixture rate | `inlet_rate / fixture_rate` |
| 7 | `rate_variance` | float | Variance over last 10 seconds | `var(rate[-10:])` |
| 8 | `is_night_time` | bool | 10PM–5AM flag | `hour >= 22 or hour < 5` |
| 9 | `pulse_trend` | float | Slope of pulses (last 5 readings) | `linear_regression_slope` |

### Feature Extraction Code

```python
import numpy as np
from collections import deque
from datetime import datetime

# Rolling buffers per sensor (size = 10 readings)
rate_buffer = {i: deque(maxlen=10) for i in range(5)}
pulse_buffer = {i: deque(maxlen=5) for i in range(5)}

# Track flow start times
flow_start_time = {i: None for i in range(5)}

def extract_features(data, sensor_id, fixture_count=5):
    """Extract 9 features from Firebase reading data."""
    
    inlet = data.get('inlet', {})
    fixture = data.get(f'fixture_{sensor_id}', {})
    
    # 1. Flow rate
    flow_rate = fixture.get('flow_rate', 0)
    
    # 2. Duration - track when flow started
    if flow_rate > 0.1 and flow_start_time[sensor_id] is None:
        flow_start_time[sensor_id] = datetime.now()
    elif flow_rate < 0.1:
        flow_start_time[sensor_id] = None
    
    if flow_start_time[sensor_id]:
        duration = (datetime.now() - flow_start_time[sensor_id]).total_seconds()
    else:
        duration = 0
    
    # 3-4. Time features
    now = datetime.now()
    hour = now.hour
    day = now.weekday()
    
    # 5. Fixture ID (one-hot compatible)
    fixture_id = sensor_id
    
    # 6. Inlet ratio
    inlet_rate = inlet.get('flow_rate', 0)
    inlet_ratio = inlet_rate / max(flow_rate, 0.01)  # Avoid div-by-zero
    
    # 7. Rate variance (last 10 readings)
    rate_buffer[sensor_id].append(flow_rate)
    rate_variance = np.var(rate_buffer[sensor_id]) if len(rate_buffer[sensor_id]) > 1 else 0
    
    # 8. Night time flag
    is_night = 1 if (hour >= 22 or hour < 5) else 0
    
    # 9. Pulse trend (slope of last 5 readings)
    pulse = fixture.get('pulse_count', 0)
    pulse_buffer[sensor_id].append(pulse)
    if len(pulse_buffer[sensor_id]) >= 3:
        x = np.arange(len(pulse_buffer[sensor_id]))
        y = np.array(pulse_buffer[sensor_id])
        slope = np.polyfit(x, y, 1)[0]
    else:
        slope = 0
    
    return np.array([
        flow_rate, duration, hour, day, fixture_id,
        inlet_ratio, rate_variance, is_night, slope
    ]).reshape(1, -1)
```

---

## XGBoost Model Training

### Training Notebook (Google Colab / Jupyter)

The complete training pipeline is in `training/water_meter_ml_training.ipynb`.

Open this notebook in Google Colab or local Jupyter Notebook:

1. **Google Colab (recommended):** Upload the notebook to Google Drive, open with Colab, enable GPU runtime (Runtime → Change runtime type → T4 GPU)
2. **Jupyter Notebook (local):** `cd training/ && pip install -r requirements.txt && jupyter notebook water_meter_ml_training.ipynb`

### Key Training Cells

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb
import joblib

def train_xgboost(features_csv='training_data.csv'):
    """Train XGBoost classifier for leak detection."""
    
    # Load labeled data
    df = pd.read_csv(features_csv)
    # Columns: flow_rate, duration, hour, day, fixture_id, inlet_ratio,
    #          rate_variance, is_night, pulse_trend, label
    
    X = df.drop('label', axis=1).values
    y = df['label'].values  # 0=normal, 1=minor_leak, 2=major_leak
    
    # Train/val split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    
    # XGBoost model
    model = xgb.XGBClassifier(
        n_estimators=200,           # Number of trees
        max_depth=8,                # Tree depth (prevent overfitting)
        learning_rate=0.05,         # Step size shrinkage
        subsample=0.8,              # Row sampling
        colsample_bytree=0.8,       # Column sampling
        reg_alpha=0.1,              # L1 regularization
        reg_lambda=1.0,             # L2 regularization
        objective='multi:softprob', # Multi-class probability
        num_class=3,                # 3 classes (excluding 'anomaly' for now)
        eval_metric=['mlogloss', 'merror'],
        random_state=42,
        n_jobs=-1
    )
    
    # Train with early stopping
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=20,
        verbose=False
    )
    
    # Evaluate
    y_pred = model.predict(X_val)
    print(classification_report(y_val, y_pred,
          target_names=['normal', 'minor_leak', 'major_leak']))
    
    # Save model + scaler
    model.save_model('xgboost_leak_model.json')
    joblib.dump(scaler, 'scaler.pkl')
    
    print("Model saved: xgboost_leak_model.json")
    print(f"Accuracy: {model.score(X_val, y_val):.3f}")
    
    return model, scaler
```

### Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'max_depth': [6, 8, 10],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [100, 200, 300],
    'subsample': [0.7, 0.8, 1.0],
    'reg_alpha': [0.01, 0.1, 1.0]
}

grid = GridSearchCV(
    xgb.XGBClassifier(objective='multi:softprob', num_class=3),
    param_grid,
    cv=5,
    scoring='f1_weighted',
    n_jobs=-1,
    verbose=1
)
grid.fit(X_train, y_train)
print(f"Best params: {grid.best_params_}")
```

---

## Isolation Forest (Anomaly Detection)

```python
from sklearn.ensemble import IsolationForest

def train_isolation_forest(normal_data_csv='normal_usage.csv'):
    """Train Isolation Forest on normal usage data only."""
    
    df = pd.read_csv(normal_data_csv)
    X_normal = df.drop('label', axis=1).values
    
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,        # Expected 5% anomalies
        random_state=42,
        bootstrap=True
    )
    model.fit(X_normal)
    
    joblib.dump(model, 'isolation_forest.pkl')
    print("Isolation Forest trained on", len(X_normal), "normal samples")
    return model
```

### Inference (Combined)

```python
class LeakDetector:
    def __init__(self):
        self.xgb = xgb.XGBClassifier()
        self.xgb.load_model('xgboost_leak_model.json')
        self.iforest = joblib.load('isolation_forest.pkl')
        self.scaler = joblib.load('scaler.pkl')
        self.confidence_threshold = 0.80
    
    def predict(self, features_raw):
        # Scale features
        features = self.scaler.transform(features_raw.reshape(1, -1))
        
        # 1. XGBoost prediction
        xgb_probs = self.xgb.predict_proba(features)[0]
        xgb_class = np.argmax(xgb_probs)
        xgb_confidence = xgb_probs[xgb_class]
        
        # 2. Isolation Forest anomaly score
        iforest_score = self.iforest.score_samples(features.reshape(1, -1))[0]
        is_anomaly = self.iforest.predict(features.reshape(1, -1))[0] == -1
        
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

---

## Training Data Generation

For initial training (before real data exists), generate synthetic data:

```python
import numpy as np
import pandas as pd

def generate_training_data(n_samples=100000):
    np.random.seed(42)
    data = []
    
    for _ in range(n_samples):
        fixture_id = np.random.randint(1, 5)
        hour = np.random.randint(0, 24)
        day = np.random.randint(0, 7)
        is_night = 1 if (hour >= 22 or hour < 5) else 0
        
        # Determine base flow rate by class
        label = np.random.choice(['normal', 'minor_leak', 'major_leak'], 
                                  p=[0.85, 0.10, 0.05])
        
        if label == 'normal':
            # Normal usage: typically 5–15 min, higher flow
            flow_rate = np.random.exponential(5) + 1
            duration = np.random.exponential(300) + 10
            
            # Lower flow at night
            if is_night:
                flow_rate *= 0.3
              
            # Shorter duration for faucets, longer for showers
            if fixture_id == 2:  # Toilet
                duration = np.random.normal(60, 10)
                flow_rate = np.random.normal(8, 2)
        
        elif label == 'minor_leak':
            # Slow continuous leak
            flow_rate = np.random.uniform(0.1, 0.5)
            duration = np.random.exponential(1800) + 600  # 10+ minutes
        
        elif label == 'major_leak':
            # High continuous flow
            flow_rate = np.random.uniform(8, 25)
            duration = np.random.exponential(600) + 120  # 2+ minutes
        
        inlet_rate = flow_rate * np.random.uniform(1.0, 1.15)
        inlet_ratio = inlet_rate / max(flow_rate, 0.01)
        rate_variance = flow_rate * np.random.uniform(0, 0.3)
        pulse_trend = np.random.normal(0, 1)
        
        data.append([
            flow_rate, duration, hour, day, fixture_id,
            inlet_ratio, rate_variance, is_night, pulse_trend,
            0 if label == 'normal' else (1 if label == 'minor_leak' else 2)
        ])
    
    columns = ['flow_rate', 'duration', 'hour', 'day', 'fixture_id',
               'inlet_ratio', 'rate_variance', 'is_night', 'pulse_trend', 'label']
    
    df = pd.DataFrame(data, columns=columns)
    df.to_csv('training_data.csv', index=False)
    print(f"Generated {n_samples} training samples")
    return df
```

---

## Model Performance Targets

| Metric | XGBoost Target | Isolation Forest Target |
|--------|----------------|------------------------|
| **Accuracy** | ≥ 95% | N/A (unsupervised) |
| **Precision (leak)** | ≥ 90% | ≥ 85% |
| **Recall (leak)** | ≥ 95% | ≥ 90% |
| **F1-Score** | ≥ 92% | ≥ 87% |
| **False Positive Rate** | ≤ 2% | ≤ 5% |
| **Inference Time** | ≤ 5ms | ≤ 5ms |
| **Model Size** | ≤ 1 MB | ≤ 1 MB |

---

## Model Retraining Pipeline

Models are retrained in **Google Colab or Jupyter Notebook** using `training/water_meter_ml_training.ipynb`.

After retraining, copy the model files to the RPi.

```python
# Scheduled daily on RPi (via cron)
def daily_retrain():
    # 1. Query new labeled data from Firebase
    new_data = query_firebase_labeled_data()
    
    # 2. Merge with existing training data
    existing = pd.read_csv('training_data.csv')
    combined = pd.concat([existing, new_data])
    
    # 3. Retrain XGBoost
    model = train_xgboost(combined)
    
    # 4. Retrain Isolation Forest (normal data only)
    normal_data = combined[combined['label'] == 0]
    train_isolation_forest(normal_data)
    
    # 5. Publish model metadata to Firebase
    db.child('models/metadata').update({
        "active_xgboost": "xgboost_v4",
        "last_trained": get_timestamp(),
        "accuracy": evaluate_accuracy(),
        "training_samples": len(combined)
    })
```

---

## Dashboard Integration (Flask)

```python
@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    
    # Extract features from request
    features = extract_features_from_request(data)
    
    # Run inference
    result = detector.predict(features)
    
    return jsonify(result)

@app.route('/api/retrain', methods=['POST'])
def retrain():
    # Trigger retraining (admin only)
    if request.headers.get('X-API-Key') != ADMIN_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    daily_retrain()
    return jsonify({"status": "retraining_started"})
```

---

## Next Steps

Proceed to:
1. [ML Dataset Guide](./ml-dataset-guide.md) — Complete dataset creation guide
2. [Model Deployment Guide](./model-deployment-guide.md) — RPi inference optimization
3. [Project Setup Guide](./setup.md) — Full system deployment