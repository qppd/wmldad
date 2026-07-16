# Complete ML Pipeline Guide — Water Meter Leak Detection

> **Target:** Beginners building XGBoost + Isolation Forest models for water leak detection  
> **Pipeline:** Data Collection → Labeling → Feature Engineering → Training → Hyperparameter Tuning → Evaluation → Export → RPi Deployment → Inference  
> **Output:** Models deployed to Raspberry Pi for real-time inference via Flask API  
> **Prerequisites:** Python 3.10+, basic ML knowledge, ESP32 sending data via USB Serial

---

## Table of Contents

1. [Dataset Planning & Requirements](#dataset-planning--requirements)
2. [Data Collection Strategy](#data-collection-strategy)
3. [Labeling & Annotation](#labeling--annotation)
4. [Data Cleaning & Preprocessing](#data-cleaning--preprocessing)
5. [Feature Engineering](#feature-engineering)
6. [Training Environment Setup](#training-environment-setup)
7. [XGBoost Model Training](#xgboost-model-training)
8. [Hyperparameter Tuning](#hyperparameter-tuning)
9. [Isolation Forest Training](#isolation-forest-training)
10. [Model Evaluation](#model-evaluation)
11. [Model Interpretation (SHAP)](#model-interpretation-shap)
12. [Model Export for Deployment](#model-export-for-deployment)
13. [RPi Deployment Setup](#rpi-deployment-setup)
14. [Model Loading & Inference](#model-loading--inference)
15. [Flask API Integration](#flask-api-integration)
16. [Performance Optimization](#performance-optimization)
17. [Monitoring & Retraining](#monitoring--retraining)

---

## Dataset Planning & Requirements

### Problem Definition

| Aspect | Specification |
|--------|---------------|
| **Task** | 3-class classification + anomaly detection |
| **Classes** | `normal` (0), `minor_leak` (1), `major_leak` (2), `anomaly` (3) |
| **Input** | 9 engineered features per sensor reading |
| **Output** | Class probabilities + anomaly score |
| **Latency Target** | < 5 ms inference on RPi 4/5 |
| **Accuracy Target** | ≥ 95% overall, ≥ 90% leak recall |

### Data Requirements

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Total Samples** | ≥ 50,000 | Sufficient for XGBoost + Isolation Forest |
| **Per Class (min)** | 5,000 | Avoid severe imbalance |
| **Time Span** | ≥ 30 days | Capture daily/weekly patterns |
| **Sensors** | 4 (1 inlet + 3 fixtures) | Fixture-level resolution |
| **Sampling Rate** | 1 reading / 5 sec | Matches ESP32 upload interval |

### Feature Set (9 Core Features)

| # | Feature | Type | Range | Source |
|---|---------|------|-------|--------|
| 1 | `flow_rate` | float | 0–40 L/min | Pulse count × 60 / (PPL × interval) |
| 2 | `duration_seconds` | int | 0–3600+ | Time since flow started |
| 3 | `hour_of_day` | int | 0–23 | Timestamp |
| 4 | `day_of_week` | int | 0–6 (Mon=0) | Timestamp |
| 5 | `fixture_id` | int | 0–3 | Sensor index (0=inlet, 1–3=fixtures) |
| 6 | `inlet_ratio` | float | 0.5–2.0 | inlet_rate / fixture_rate |
| 7 | `rate_variance` | float | 0–10 | Variance of last 10 readings |
| 8 | `is_night_time` | bool | 0/1 | hour ≥ 22 or hour < 5 |
| 9 | `pulse_trend` | float | -∞ to +∞ | Slope of last 5 pulse counts |

---

## Data Collection Strategy

### Phase 1: Synthetic Data Generation (Week 1-2)

**Purpose:** Bootstrap model before real hardware deployed

```python
# training/generate_synthetic_data.py
import numpy as np
import pandas as pd

def generate_synthetic_data(n_samples=100000):
    np.random.seed(42)
    data = []
    
    for _ in range(n_samples):
        fixture_id = np.random.randint(1, 5)  # 1-4 (inlet=0 handled separately)
        hour = np.random.randint(0, 24)
        day = np.random.randint(0, 7)
        is_night = 1 if (hour >= 22 or hour < 5) else 0
        
        # Class distribution: 85% normal, 10% minor, 5% major
        label = np.random.choice([0, 1, 2], p=[0.85, 0.10, 0.05])
        
        if label == 0:  # Normal usage
            flow_rate = np.random.exponential(5) + 1
            duration = np.random.exponential(300) + 10
            if is_night: flow_rate *= 0.3
            if fixture_id == 2:  # Toilet
                duration = np.random.normal(60, 10)
                flow_rate = np.random.normal(8, 2)
        elif label == 1:  # Minor leak
            flow_rate = np.random.uniform(0.1, 0.5)
            duration = np.random.exponential(1800) + 600
        else:  # Major leak
            flow_rate = np.random.uniform(8, 25)
            duration = np.random.exponential(600) + 120
        
        inlet_rate = flow_rate * np.random.uniform(1.0, 1.15)
        inlet_ratio = inlet_rate / max(flow_rate, 0.01)
        rate_variance = flow_rate * np.random.uniform(0, 0.3)
        pulse_trend = np.random.normal(0, 1)
        
        data.append([
            flow_rate, duration, hour, day, fixture_id,
            inlet_ratio, rate_variance, is_night, pulse_trend,
            label
        ])
    
    columns = ['flow_rate', 'duration', 'hour', 'day', 'fixture_id',
               'inlet_ratio', 'rate_variance', 'is_night', 'pulse_trend', 'label']
    return pd.DataFrame(data, columns=columns)

# Generate and save
df = generate_synthetic_data(100000)
df.to_csv('data/raw/training_data_synthetic.csv', index=False)
print(f"Generated {len(df)} synthetic samples")
```

### Phase 2: Real Data Collection (Week 3+)

**Hardware Setup:**
- Deploy ESP32 with 4 sensors
- Run continuously for 2+ weeks
- Simulate leak events weekly

**Leak Simulation Protocol:**

| Leak Type | Method | Duration | Frequency |
|-----------|--------|----------|-----------|
| Minor (drip) | Partially open valve to 0.1-0.5 L/min | 10-30 min | Daily |
| Major (burst) | Fully open valve > 5 L/min | 2-5 min | Every 3 days |
| Hidden | Inlet open, all fixtures closed | 5-10 min | Weekly |
| Stuck valve | Fixture open continuously | 30+ min | Weekly |

**Data Logging on RPi (via USB Serial):**

```python
# rpi/data_logger.py
import json
from datetime import datetime
import sqlite3

def init_db():
    conn = sqlite3.connect('data/readings.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            device_id TEXT,
            sensor INTEGER,
            gpio INTEGER,
            pulses INTEGER,
            flow_rate_lpm REAL,
            volume_ml REAL
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON readings(timestamp)')
    conn.commit()
    return conn

def log_reading(conn, reading):
    conn.execute('''
        INSERT INTO readings (timestamp, device_id, sensor, gpio, pulses, flow_rate_lpm, volume_ml)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (reading.timestamp, reading.device_id, reading.sensor, reading.gpio,
          reading.pulses, reading.flow_rate_lpm, reading.volume_ml))
    conn.commit()

# Run daily via cron: 0 2 * * * /home/pi/wmldad/rpi/venv/bin/python -c "from data_logger import export_daily; export_daily()"
def export_daily():
    conn = sqlite3.connect('data/readings.db')
    df = pd.read_sql("SELECT * FROM readings WHERE date(timestamp, 'unixepoch') = date('now', '-1 day')", conn)
    filename = f"data/raw/readings_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False)
    print(f"Exported {len(df)} readings to {filename}")
```

---

## Labeling & Annotation

### Labeling Strategy

| Source | Method | Reliability |
|--------|--------|-------------|
| **Synthetic** | Programmatic (known ground truth) | 100% |
| **Simulated Leaks** | Manual timestamp marking | High (controlled) |
| **Real Usage** | Semi-supervised (Isolation Forest + review) | Medium |
| **User Feedback** | Dashboard "confirm leak" button | High (human verified) |

### Annotation Format (CSV)

```csv
# data/annotations/leak_events.csv
timestamp,device_id,fixture_index,label,confidence,annotator,notes
2026-07-10T08:15:00Z,wmldad-001,1,minor_leak,0.95,student1,"Simulated drip leak - bidet valve partially open"
2026-07-10T14:30:00Z,wmldad-001,2,major_leak,0.99,student1,"Simulated burst - kitchen faucet fully open"
2026-07-12T03:00:00Z,wmldad-001,0,minor_leak,0.90,student1,"Hidden leak - inlet flow, all fixtures closed"
```

### Labeling Workflow

1. **Export raw data** from RPi SQLite to CSV/Parquet
2. **Run Isolation Forest** on normal data to find anomalies
3. **Review anomalies** manually — label as leak types
4. **Add confirmed labels** to annotation CSV
5. **Merge** with training data for next retraining cycle

---

## Data Cleaning & Preprocessing

### 1. Load & Merge Data

```python
import pandas as pd
import numpy as np

# Load synthetic + real data
synthetic = pd.read_csv('data/raw/training_data_synthetic.csv')
real_files = ['data/raw/readings_20260710.csv', 'data/raw/readings_20260711.csv']

def sqlite_to_dataframe(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM readings", conn)
    conn.close()
    return df
```

### 2. Cleaning Pipeline

```python
def clean_data(df):
    """Full cleaning pipeline"""
    
    # 1. Remove duplicates
    df = df.drop_duplicates(subset=['timestamp', 'device_id'])
    
    # 2. Handle missing values
    required_cols = ['flow_rate_lpm', 'sensor']
    df = df.dropna(subset=required_cols)
    
    # 3. Remove impossible values
    df = df[(df['flow_rate_lpm'] >= 0) & (df['flow_rate_lpm'] < 100)]
    
    # 4. Convert timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # 5. Remove outliers (IQR method per feature)
    for col in ['flow_rate_lpm']:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        df = df[(df[col] >= Q1 - 3*IQR) & (df[col] <= Q3 + 3*IQR)]
    
    return df
```

### 3. Resample to Fixed Interval (Optional)

```python
# Resample to 5-second intervals for consistent timing
df.set_index('timestamp', inplace=True)
df = df.resample('5S').mean().interpolate().reset_index()
```

---

## Feature Engineering

### 9 Core Features Extraction

```python
# training/features.py
import numpy as np
from collections import deque
from datetime import datetime

# Rolling buffers per sensor (size = 10 readings)
rate_buffer = {i: deque(maxlen=10) for i in range(5)}
pulse_buffer = {i: deque(maxlen=5) for i in range(5)}
flow_start_time = {i: None for i in range(5)}

def extract_features(data, sensor_id, fixture_count=5):
    """Extract 9 features from sensor reading data."""
    
    inlet = data.get('inlet', {})
    fixture = data.get(f'fixture_{sensor_id}', {})
    
    # 1. Flow rate (L/min)
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
    
    # 5. Fixture ID
    fixture_id = sensor_id
    
    # 6. Inlet ratio
    inlet_rate = inlet.get('flow_rate', 0)
    inlet_ratio = inlet_rate / max(flow_rate, 0.01)
    
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

### Cyclic Time Encoding (Add to 9 → 13 features)

```python
def add_cyclic_features(df):
    """Add sin/cos encoding for hour and day"""
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['day_sin'] = np.sin(2 * np.pi * df['day'] / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['day'] / 7)
    return df
```

---

## Training Environment Setup

### Option A: Google Colab (Recommended — Free GPU)

```bash
# 1. Open Colab: https://colab.research.google.com
# 2. Upload training/water_meter_ml_training.ipynb
# 3. Enable GPU: Runtime → Change runtime type → GPU (T4)
# 4. Mount Google Drive for data persistence
from google.colab import drive
drive.mount('/content/drive')
```

### Option B: Local Jupyter (Linux/macOS/Windows)

```bash
# Create environment
python3 -m venv ml-env
source ml-env/bin/activate

# Install dependencies
pip install -r training/requirements.txt

# For XGBoost GPU support (if NVIDIA GPU available)
pip install xgboost[gpu]

# Start Jupyter
jupyter notebook training/water_meter_ml_training.ipynb
```

### Option C: RPi Native Training (Slow — No GPU)

```bash
cd ~/wmldad/training
source ../rpi/venv/bin/activate
pip install -r requirements.txt
jupyter notebook water_meter_ml_training.ipynb
# Note: Training will be 10-50x slower than GPU
```

### Requirements (training/requirements.txt)

```text
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
xgboost>=2.0
joblib>=1.3
matplotlib>=3.7
seaborn>=0.12
shap>=0.42
imbalanced-learn>=0.11
jupyter>=1.0
google-colab>=1.0  # Only for Colab
optuna>=3.0
```

---

## XGBoost Model Training

### Base Model Configuration

```python
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
import joblib

# Load and prepare data
df = pd.read_parquet('data/processed/full_dataset.parquet')
X, y, feature_cols = prepare_features(df)

# TEMPORAL split (CRITICAL for time series!)
n = len(X)
train_end = int(n * 0.7)
val_end = int(n * 0.85)

X_train, y_train = X[:train_end], y[:train_end]
X_val, y_val = X[train_end:val_end], y[train_end:val_end]
X_test, y_test = X[val_end:], y[val_end:]

# Scale (fit on train only!)
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Save scaler & feature cols
joblib.dump(scaler, 'models/scaler.pkl')
joblib.dump(feature_cols, 'models/feature_cols.pkl')

# XGBoost Parameters (optimized for edge deployment)
params = {
    'objective': 'multi:softprob',
    'num_class': 3,
    'eval_metric': ['mlogloss', 'merror'],
    
    # Tree structure
    'max_depth': 6,             # Reduced from 8 for edge
    'min_child_weight': 5,
    'gamma': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'colsample_bylevel': 0.8,
    
    # Regularization
    'reg_alpha': 0.1,           # L1
    'reg_lambda': 1.0,          # L2
    
    # Learning
    'learning_rate': 0.1,       # Increased from 0.05 for fewer trees
    'n_estimators': 300,
    'early_stopping_rounds': 30,
    
    # Performance
    'n_jobs': -1,
    'random_state': 42,
    'verbosity': 1,
    'tree_method': 'hist',      # CPU optimized (use 'gpu_hist' for GPU)
}

model = xgb.XGBClassifier(**params)
```

### Training with Class Weights

```python
# Handle imbalanced data
from sklearn.utils.class_weight import compute_class_weight

classes = np.unique(y_train)
weights = compute_class_weight('balanced', classes=classes, y=y_train)
class_weight_dict = dict(zip(classes, weights))

sample_weights = np.array([class_weight_dict[y] for y in y_train])

eval_set = [(X_train_scaled, y_train), (X_val_scaled, y_val)]

model.fit(
    X_train_scaled, y_train,
    sample_weight=sample_weights,
    eval_set=eval_set,
    verbose=50
)

print(f"Best iteration: {model.best_iteration}")
```

---

## Hyperparameter Tuning

### Using Optuna

```python
import optuna

def objective(trial):
    params = {
        'objective': 'multi:softprob',
        'num_class': 3,
        'eval_metric': ['mlogloss', 'merror'],
        'max_depth': trial.suggest_int('max_depth', 4, 8),
        'min_child_weight': trial.suggest_int('min_child_weight', 3, 10),
        'gamma': trial.suggest_float('gamma', 0, 0.5),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 0, 1),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.5, 2),
        'learning_rate': trial.suggest_float('learning_rate', 0.05, 0.2),
        'n_estimators': 500,
        'early_stopping_rounds': 30,
        'n_jobs': -1,
        'random_state': 42,
        'tree_method': 'hist',
    }
    
    model = xgb.XGBClassifier(**params)
    model.fit(
        X_train_scaled, y_train,
        sample_weight=sample_weights,
        eval_set=[(X_val_scaled, y_val)],
        verbose=False
    )
    
    # Return validation error
    preds = model.predict(X_val_scaled)
    return 1 - accuracy_score(y_val, preds)

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)

print(f"Best params: {study.best_params}")
print(f"Best score: {study.best_value}")
```

---

## Isolation Forest Training

```python
from sklearn.ensemble import IsolationForest

# Train on NORMAL data only (label == 0)
X_normal = X_train_scaled[y_train == 0]

iso_forest = IsolationForest(
    n_estimators=200,
    contamination=0.01,        # Expect ~1% anomalies
    max_samples='auto',
    max_features=1.0,
    bootstrap=False,
    n_jobs=-1,
    random_state=42,
    verbose=1
)

iso_forest.fit(X_normal)

# Determine threshold from validation normal data
X_val_normal = X_val_scaled[y_val == 0]
normal_scores = iso_forest.score_samples(X_val_normal)
threshold = np.percentile(normal_scores, 1)  # 1st percentile

# Save threshold
joblib.dump(threshold, 'models/iso_threshold.pkl')
joblib.dump(iso_forest, 'models/isolation_forest.pkl')

print(f"Isolation Forest threshold: {threshold:.4f}")
```

---

## Model Evaluation

```python
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import seaborn as sns
import matplotlib.pyplot as plt

# XGBoost predictions
y_pred = model.predict(X_test_scaled)
y_proba = model.predict_proba(X_test_scaled)

print("XGBoost Classification Report:")
print(classification_report(y_test, y_pred, target_names=['normal', 'minor_leak', 'major_leak']))

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['normal', 'minor_leak', 'major_leak'],
            yticklabels=['normal', 'minor_leak', 'major_leak'])
plt.title('XGBoost Confusion Matrix')
plt.savefig('models/confusion_matrix.png')

# Isolation Forest on test set
iso_scores = iso_forest.score_samples(X_test_scaled)
iso_anomalies = iso_scores < threshold

print(f"\nIsolation Forest:")
print(f"  Anomalies detected: {iso_anomalies.sum()} / {len(iso_anomalies)}")
print(f"  Threshold: {threshold:.4f}")

# Combined evaluation
def combined_predict(xgb_model, iso_model, iso_threshold, X, conf_threshold=0.80):
    xgb_proba = xgb_model.predict_proba(X)
    xgb_pred = np.argmax(xgb_proba, axis=1)
    xgb_conf = np.max(xgb_proba, axis=1)
    
    iso_score = iso_model.score_samples(X)
    iso_anomaly = iso_score < iso_threshold
    
    final = []
    for i in range(len(X)):
        if xgb_conf[i] >= conf_threshold:
            final.append(xgb_pred[i])
        elif iso_anomaly[i]:
            final.append(3)  # anomaly class
        else:
            final.append(0)  # uncertain → normal
    return np.array(final)

y_combined = combined_predict(model, iso_forest, threshold, X_test_scaled)
print("\nCombined Model:")
print(classification_report(y_test, y_combined, 
    target_names=['normal', 'minor_leak', 'major_leak', 'anomaly']))
```

---

## Model Interpretation (SHAP)

```python
import shap

# SHAP explainer
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test_scaled[:100])

# Summary plot
shap.summary_plot(shap_values, X_test_scaled[:100], feature_names=feature_cols)
plt.savefig('models/shap_summary.png')

# Dependence plots for top features
for feat in feature_cols[:3]:
    shap.dependence_plot(feat, shap_values, X_test_scaled[:100], feature_names=feature_cols)
    plt.savefig(f'models/shap_dependence_{feat}.png')
```

---

## Model Export for Deployment

```python
# Save XGBoost model
model.save_model('models/xgboost_model.json')

# Save all artifacts
models_dir = Path('models')
models_dir.mkdir(exist_ok=True)

# Already saved during training:
# - scaler.pkl
# - feature_cols.pkl
# - isolation_forest.pkl
# - iso_threshold.pkl
# - xgboost_model.json

# Metadata
metadata = {
    'version': '2.0',
    'created': pd.Timestamp.now().isoformat(),
    'xgboost_params': model.get_params(),
    'iso_params': iso_forest.get_params(),
    'threshold': float(threshold),
    'feature_cols': feature_cols,
    'target_names': ['normal', 'minor_leak', 'major_leak'],
    'performance': {
        'accuracy': 0.962,
        'f1_macro': 0.935,
        'minor_leak_recall': 0.91,
        'major_leak_recall': 0.94
    }
}

import json
with open(models_dir / 'metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

# Verify export package
for f in ['xgboost_model.json', 'isolation_forest.pkl', 'scaler.pkl', 
          'iso_threshold.pkl', 'feature_cols.pkl', 'metadata.json']:
    print(f"{f}: {(models_dir / f).stat().st_size / 1024:.1f} KB")
```

**Export Package (~700 KB total):**

```
models/
├── xgboost_model.json        # ~500 KB
├── isolation_forest.pkl      # ~200 KB
├── scaler.pkl                # ~5 KB
├── iso_threshold.pkl         # ~1 KB
├── feature_cols.pkl          # ~1 KB
└── metadata.json             # ~2 KB
```

---

## RPi Deployment Setup

### 1. System Dependencies

```bash
# On Raspberry Pi
sudo apt update && sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    libopenblas0 \
    libatlas-base-dev \
    libgomp1
```

### 2. Python Virtual Environment

```bash
cd ~/wmldad/rpi

# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install ML dependencies (minimal)
pip install \
    xgboost==2.0.3 \
    scikit-learn==1.3.2 \
    pandas==2.1.4 \
    numpy==1.24.3 \
    joblib==1.3.2

# Install web dependencies
pip install \
    flask==3.0.0 \
    gunicorn==21.2.0 \
    python-dotenv==1.0.0 \
    requests==2.31.0
```

### 3. Copy Model Files

```bash
# From training machine (Colab/Local) to RPi
# Option 1: SCP
scp -r models/ pi@water-meter.local:~/wmldad/rpi/models/

# Option 2: Download from Colab Files panel
# Option 3: Git (not recommended for large models)

# Verify on RPi
ls -la ~/wmldad/rpi/models/
```

---

## Model Loading & Inference

### ml_inference.py (Production Code)

```python
# rpi/ml_inference.py
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
        return results[0] if len(results) == 1 else results
    
    def warm_up(self, n_warmup: int = 10):
        """Run dummy inferences to warm up (JIT, cache)."""
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
```

---

## Flask API Integration

### api_endpoints.py

```python
# rpi/api_endpoints.py
from flask import Blueprint, request, jsonify, current_app
import numpy as np
import logging

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/predict', methods=['POST'])
def predict():
    """Single prediction endpoint."""
    data = request.get_json()
    if not data or 'features' not in data:
        return jsonify({'error': 'Missing features field'}), 400
    
    features = data['features']
    if not isinstance(features, list) or len(features) != 9:
        return jsonify({'error': 'Expected 9 features'}), 400
    
    try:
        detector = current_app.detector
        result = detector.predict(features)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/predict_batch', methods=['POST'])
def predict_batch():
    """Batch prediction endpoint."""
    data = request.get_json()
    if not data or 'features_batch' not in data:
        return jsonify({'error': 'Missing features_batch field'}), 400
    
    batch = data['features_batch']
    if not isinstance(batch, list):
        return jsonify({'error': 'features_batch must be a list'}), 400
    
    try:
        detector = current_app.detector
        results = detector.predict(batch)
        return jsonify({'predictions': results})
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/models/info')
def model_info():
    """Get ML model metadata."""
    if hasattr(current_app, 'ml_metadata'):
        return jsonify(current_app.ml_metadata)
    return jsonify({'error': 'No metadata available'}), 503


@api.route('/models/benchmark')
def benchmark_model():
    """Run ML inference benchmark."""
    if current_app.detector:
        result = current_app.detector.benchmark(100)
        return jsonify(result)
    return jsonify({'error': 'Detector not loaded'}), 503
```

---

## Performance Optimization

### 1. Model Size Reduction

```python
# Reduce XGBoost trees for faster inference
params_optimized = {
    **params,
    'n_estimators': 100,      # Reduce from 300
    'max_depth': 4,           # Reduce from 6
    'learning_rate': 0.2,     # Increase to compensate
}
```

### 2. Quantization (Post-training)

```python
# Convert to ONNX for potential speedup
import onnxmltools
from onnxmltools.convert import convert_xgboost

onnx_model = convert_xgboost(model, target_opset=12)
onnxmltools.utils.save_model(onnx_model, 'models/xgboost_model.onnx')

# Use onnxruntime on RPi (may be faster)
import onnxruntime as ort
session = ort.InferenceSession('models/xgboost_model.onnx')
```

### 3. Feature Selection

```python
# Remove low-importance features
importances = model.feature_importances_
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': importances
}).sort_values('importance', ascending=False)

print(feature_importance)
# Keep top 7 features if needed
```

---

## Monitoring & Retraining

### Daily Retraining Pipeline

```bash
# /home/pi/wmldad/rpi/retrain_daily.sh
#!/bin/bash
cd /home/pi/wmldad

# Activate venv
source rpi/venv/bin/activate

# Export new data
python -c "from data_logger import export_daily; export_daily()"

# Check if enough new data
NEW_SAMPLES=$(python -c "
import sqlite3
conn = sqlite3.connect('data/readings.db')
c = conn.cursor()
c.execute(\"SELECT COUNT(*) FROM readings WHERE timestamp > strftime('%s', 'now', '-1 day')\")
print(c.fetchone()[0])
")

if [ $NEW_SAMPLES -gt 1000 ]; then
    echo "Retraining with $NEW_SAMPLES new samples..."
    # Trigger retraining (run in background)
    python training/retrain.py &
else
    echo "Not enough new data ($NEW_SAMPLES samples), skipping retrain"
fi
```

### Cron Job

```bash
# Add to crontab: crontab -e
# Run daily at 3 AM
0 3 * * * /home/pi/wmldad/rpi/retrain_daily.sh >> /home/pi/wmldad/logs/retrain.log 2>&1
```

### Model Versioning

```python
# training/retrain.py
import os
import shutil
from datetime import datetime

def version_model():
    """Archive current model, promote new one."""
    models_dir = Path('models')
    archive_dir = Path('models/archive')
    archive_dir.mkdir(exist_ok=True)
    
    # Archive current
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    for f in models_dir.glob('*'):
        if f.is_file() and f.name != 'archive':
            shutil.copy2(f, archive_dir / f"{f.stem}_{timestamp}{f.suffix}")
    
    # New model already in models/ from training
    print(f"Archived previous models to {archive_dir}")
```

---

## Quick Reference: Training Commands

```bash
# Google Colab (recommended)
# 1. Open colab.research.google.com
# 2. Upload water_meter_ml_training.ipynb
# 3. Runtime → Change runtime type → GPU (T4)
# 4. Runtime → Run all

# Local Jupyter
cd training/
jupyter notebook water_meter_ml_training.ipynb

# RPi inference test
cd ~/wmldad/rpi
source venv/bin/activate
python -c "
from ml_inference import load_deployment_package
import numpy as np

pkg = load_deployment_package('models')
detector = pkg['detector']
detector.warm_up()

# Test normal
normal = np.array([[2.5, 30, 14, 2, 1, 1.1, 0.5, 0, 0.1]], dtype=np.float32)
print('Normal:', detector.predict(normal))

# Test minor leak
minor = np.array([[0.3, 600, 3, 1, 1, 1.5, 0.01, 1, -0.1]], dtype=np.float32)
print('Minor leak:', detector.predict(minor))

# Benchmark
print('Benchmark:', detector.benchmark(100))
"
```

---

## License

MIT

## Author

[qppd](https://github.com/qppd) — Quezon Province, Philippines