# Machine Learning Dataset Guide — Water Meter Leak Detection

> **Target:** XGBoost + Isolation Forest training pipeline  
> **Data Source:** ESP32 flow sensors → Firebase → RPi  
> **Audience:** Students, researchers, developers building ML datasets for IoT water monitoring

---

## Table of Contents

1. [Dataset Planning](#dataset-planning)
2. [Data Collection Strategy](#data-collection-strategy)
3. [Labeling & Annotation](#labeling--annotation)
4. [Data Cleaning](#data-cleaning)
5. [Normalization & Scaling](#normalization--scaling)
6. [Class Balancing](#class-balancing)
7. [Train/Validation/Test Split](#trainvalidationtest-split)
8. [Feature Engineering](#feature-engineering)
9. [Data Augmentation](#data-augmentation)
10. [Dataset Versioning](#dataset-versioning)
11. [Storage & Folder Structure](#storage--folder-structure)
12. [Best Practices](#best-practices)
13. [Project-Specific Implementation](#project-specific-implementation)

---

## Dataset Planning

### Problem Definition

| Aspect | Specification |
|--------|---------------|
| **Task** | 3-class classification + anomaly detection |
| **Classes** | `normal` (0), `minor_leak` (1), `major_leak` (2), `anomaly` (3) |
| **Input** | 9 engineered features per sensor reading |
| **Output** | Class probabilities + anomaly score |
| **Latency** | < 5 ms inference on RPi 4/5 |
| **Accuracy Target** | ≥ 95% overall, ≥ 90% leak recall |

### Data Requirements

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Total Samples** | ≥ 50,000 | Sufficient for XGBoost + Isolation Forest |
| **Per Class (min)** | 5,000 | Avoid severe imbalance |
| **Time Span** | ≥ 30 days | Capture daily/weekly patterns |
| **Sensors** | 4 (1 inlet + 3 fixtures) | Fixture-level resolution |
| **Sampling Rate** | 1 reading / 5 sec | Matches ESP32 upload interval |

### Feature Set (9 Features)

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
df.to_csv('training_data_synthetic.csv', index=False)
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

**Data Logging:**
```python
# On RPi: firebase_listener.py logs all readings
# Also save raw Firebase data daily
import json
from datetime import datetime

def save_daily_backup():
    readings = db.child(f"readings/{DEVICE_ID}").get()
    filename = f"data/raw/readings_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, 'w') as f:
        json.dump(readings.val(), f)
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

### Annotation Tool (Simple CSV-Based)

```csv
# data/annotations/leak_events.csv
timestamp,device_id,fixture_index,label,confidence,annotator,notes
2026-07-10T08:15:00Z,wm_001,1,minor_leak,0.95,student1,"Simulated drip leak - bidet valve partially open"
2026-07-10T14:30:00Z,wm_001,2,major_leak,0.99,student1,"Simulated burst - kitchen faucet fully open"
2026-07-11T02:00:00Z,wm_001,0,hidden_leak,0.90,student2,"Inlet flow with all fixtures closed"
```

### Labeling Guidelines

| Class | Criteria | Examples |
|-------|----------|----------|
| **normal** (0) | Typical usage: faucet, shower, toilet, dishwasher | Flow > 1 L/min, duration 10s-30min, matches fixture pattern |
| **minor_leak** (1) | Continuous low flow 0.1-0.5 L/min > 10 min | Dripping faucet, running toilet, small pipe leak |
| **major_leak** (2) | High continuous flow > 5 L/min > 2 min | Burst pipe, stuck valve, hose left running |
| **anomaly** (3) | Pattern not matching known classes | Sensor glitch, unusual usage, new fixture type |

---

## Data Cleaning

### Common Issues

| Issue | Detection | Fix |
|-------|-----------|-----|
| **Missing timestamps** | `df['timestamp'].isna().sum()` | Drop rows or interpolate |
| **Zero flow with pulses** | `flow_rate == 0 and pulse_count > 0` | Recalculate from pulses |
| **Negative values** | `(df < 0).any().any()` | Clip at 0 or drop |
| **Outliers (sensor glitch)** | `flow_rate > 100` (impossible) | Cap at physical max (40 L/min for YF-S201) |
| **Duplicate timestamps** | `df['timestamp'].duplicated().sum()` | Keep first/last |
| **Clock drift** | Large time jumps between readings | Use NTP-synced timestamps |

### Cleaning Pipeline

```python
# training/clean_data.py
import pandas as pd
import numpy as np

def clean_dataset(df):
    """Clean raw Firebase data for training"""
    
    # 1. Parse timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values('timestamp')
    
    # 2. Remove duplicates
    df = df.drop_duplicates(subset='timestamp', keep='first')
    
    # 3. Handle missing values
    df = df.dropna(subset=['inlet', 'fixture_1', 'fixture_2', 'fixture_3'])
    
    # 4. Physical constraints
    for col in ['inlet', 'fixture_1', 'fixture_2', 'fixture_3']:
        for metric in ['flow_rate', 'volume', 'total']:
            key = f'{col}.{metric}'
            if key in df.columns:
                df[key] = df[key].clip(lower=0, upper=50)  # Max 50 L/min
    
    # 5. Remove sensor glitches (sudden impossible spikes)
    for col in ['fixture_1', 'fixture_2', 'fixture_3']:
        fr_key = f'{col}.flow_rate'
        if fr_key in df.columns:
            # Rolling median filter
            df[fr_key] = df[fr_key].rolling(3, center=True).median().fillna(df[fr_key])
    
    # 6. Feature engineering (creates features from raw)
    df = engineer_features(df)
    
    # 7. Remove rows where feature engineering failed
    df = df.dropna()
    
    return df

def engineer_features(df):
    """Extract 9 features from raw sensor data"""
    # Implementation matches ml_inference.py extract_features()
    # ...
    return df
```

---

## Normalization & Scaling

### Why Normalize?

| Algorithm | Needs Scaling? | Reason |
|-----------|----------------|--------|
| **XGBoost** | No (tree-based) | Split points invariant to scale |
| **Isolation Forest** | **Yes** | Distance-based anomaly scoring |
| **Neural Networks** | Yes | Gradient descent convergence |
| **SVM / KNN** | Yes | Distance metrics |

### Scaling Approach

```python
# training/scale_features.py
from sklearn.preprocessing import StandardScaler, RobustScaler
import joblib

# Use RobustScaler (less sensitive to outliers)
scaler = RobustScaler()

# Fit on training data ONLY
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Save scaler for inference
joblib.dump(scaler, 'models/scaler.pkl')
```

### Feature Statistics (Typical Ranges)

| Feature | Mean | Std | Min | Max | Scaler |
|---------|------|-----|-----|-----|--------|
| `flow_rate` | 3.2 | 4.1 | 0 | 35 | Robust |
| `duration` | 180 | 450 | 0 | 3600 | Robust |
| `hour` | 11.5 | 6.9 | 0 | 23 | None (cyclic) |
| `day` | 3 | 2 | 0 | 6 | None |
| `fixture_id` | 1.5 | 1.1 | 0 | 3 | None (categorical) |
| `inlet_ratio` | 1.08 | 0.05 | 0.8 | 1.5 | Robust |
| `rate_variance` | 0.8 | 1.2 | 0 | 15 | Robust |
| `is_night` | 0.29 | 0.45 | 0 | 1 | None (binary) |
| `pulse_trend` | 0 | 0.5 | -3 | 3 | Standard |

---

## Class Balancing

### Initial Distribution (Typical)

| Class | Count | % | Problem |
|-------|-------|---|---------|
| normal | 85,000 | 85% | Dominates |
| minor_leak | 10,000 | 10% | Underrepresented |
| major_leak | 5,000 | 5% | Severely underrepresented |

### Balancing Techniques

#### 1. XGBoost Built-in (Recommended)

```python
# Use scale_pos_weight for binary, but for multi-class:
model = xgb.XGBClassifier(
    objective='multi:softprob',
    num_class=3,
    # Weight per class: n_samples / (n_classes * class_count)
    # Computed automatically with sample_weight
)
```

#### 2. SMOTE (Synthetic Minority Oversampling)

```python
from imblearn.over_sampling import SMOTE

smote = SMOTE(sampling_strategy={
    1: 50000,  # minor_leak → 50k
    2: 50000   # major_leak → 50k
}, random_state=42)

X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
```

#### 3. Class Weights (Simple)

```python
from sklearn.utils.class_weight import compute_class_weight

classes = np.unique(y_train)
weights = compute_class_weight('balanced', classes=classes, y=y_train)
class_weight_dict = dict(zip(classes, weights))

model.fit(X_train, y_train, sample_weight=[class_weight_dict[y] for y in y_train])
```

#### 4. Isolation Forest: Train on Normal Only

```python
# Isolation Forest ONLY trains on normal data (label 0)
normal_data = X_train[y_train == 0]
iso_forest = IsolationForest(contamination=0.05)
iso_forest.fit(normal_data)
```

---

## Train/Validation/Test Split

### Split Strategy

| Set | % | Purpose | Size (100k samples) |
|-----|---|---------|---------------------|
| **Train** | 70% | Model fitting | 70,000 |
| **Validation** | 15% | Hyperparameter tuning | 15,000 |
| **Test** | 15% | Final evaluation | 15,000 |

### Temporal Split (Critical for Time Series)

```python
# DON'T use random shuffle — leaks future info!
# DO use temporal split:

df = df.sort_values('timestamp')

# Split by time (first 70% train, next 15% val, last 15% test)
n = len(df)
train_end = int(n * 0.7)
val_end = int(n * 0.85)

train_df = df.iloc[:train_end]
val_df = df.iloc[train_end:val_end]
test_df = df.iloc[val_end:]

# Verify no temporal leakage
print(f"Train: {train_df['timestamp'].min()} to {train_df['timestamp'].max()}")
print(f"Val: {val_df['timestamp'].min()} to {val_df['timestamp'].max()}")
print(f"Test: {test_df['timestamp'].min()} to {test_df['timestamp'].max()}")
```

### Stratified Split (If Random Necessary)

```python
from sklearn.model_selection import train_test_split

# Only if data is IID (not time series)
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42
)
```

---

## Feature Engineering

### Core Features (9)

Already defined in [Dataset Planning](#dataset-planning). Implementation:

```python
def extract_features(reading, sensor_id, inlet_reading, buffers):
    """Extract 9 features from single reading"""
    
    # 1. Flow rate (L/min)
    flow_rate = reading['flow_rate']
    
    # 2. Duration (seconds since flow started)
    if flow_rate > 0.1 and buffers['flow_start'][sensor_id] is None:
        buffers['flow_start'][sensor_id] = reading['timestamp']
    elif flow_rate < 0.1:
        buffers['flow_start'][sensor_id] = None
    
    duration = 0
    if buffers['flow_start'][sensor_id]:
        duration = (reading['timestamp'] - buffers['flow_start'][sensor_id]).total_seconds()
    
    # 3-4. Time features
    hour = reading['timestamp'].hour
    day = reading['timestamp'].weekday()
    
    # 5. Fixture ID
    fixture_id = sensor_id
    
    # 6. Inlet ratio
    inlet_rate = inlet_reading['flow_rate']
    inlet_ratio = inlet_rate / max(flow_rate, 0.01)
    
    # 7. Rate variance (last 10 readings)
    buffers['rate_buffer'][sensor_id].append(flow_rate)
    rate_variance = np.var(buffers['rate_buffer'][sensor_id]) if len(buffers['rate_buffer'][sensor_id]) > 1 else 0
    
    # 8. Night flag
    is_night = 1 if (hour >= 22 or hour < 5) else 0
    
    # 9. Pulse trend (slope of last 5)
    buffers['pulse_buffer'][sensor_id].append(reading['pulse_count'])
    if len(buffers['pulse_buffer'][sensor_id]) >= 3:
        x = np.arange(len(buffers['pulse_buffer'][sensor_id]))
        y = np.array(buffers['pulse_buffer'][sensor_id])
        pulse_trend = np.polyfit(x, y, 1)[0]
    else:
        pulse_trend = 0
    
    return np.array([
        flow_rate, duration, hour, day, fixture_id,
        inlet_ratio, rate_variance, is_night, pulse_trend
    ])
```

### Advanced Features (Future)

| Feature | Description | Benefit |
|---------|-------------|---------|
| `flow_rate_rolling_mean_5` | 5-sample moving average | Smoother signal |
| `flow_rate_rolling_std_10` | 10-sample rolling std | Variability measure |
| `inlet_fixture_diff` | inlet - sum(fixtures) | Hidden leak indicator |
| `pressure_estimate` | Derived from flow curve | Physics-informed |
| `hour_sin`, `hour_cos` | Cyclic encoding of hour | Better time representation |
| `day_sin`, `day_cos` | Cyclic encoding of day | Weekly patterns |

---

## Data Augmentation

### For Time Series Sensor Data

| Technique | Implementation | When to Use |
|-----------|----------------|-------------|
| **Jitter** | Add Gaussian noise to flow_rate | Small dataset |
| **Scaling** | Multiply flow_rate by 0.9-1.1 | Sensor calibration variance |
| **Time Warping** | Stretch/compress duration | Variable usage patterns |
| **Window Slicing** | Random 30-min windows | Increase sample count |
| **Mixup** | Blend two normal samples | Regularization |

```python
# training/augment.py
import numpy as np

def augment_sample(X, y, n_augments=3):
    """Augment minority class samples"""
    augmented_X, augmented_y = [], []
    
    for _ in range(n_augments):
        X_aug = X.copy()
        
        # Jitter (1% noise)
        X_aug[:, 0] += np.random.normal(0, 0.01 * X_aug[:, 0])  # flow_rate
        
        # Scaling (±5%)
        scale = np.random.uniform(0.95, 1.05)
        X_aug[:, 0] *= scale
        X_aug[:, 5] *= scale  # inlet_ratio
        
        # Duration warping (±10%)
        X_aug[:, 1] *= np.random.uniform(0.9, 1.1)
        
        augmented_X.append(X_aug)
        augmented_y.append(y)
    
    return np.vstack(augmented_X), np.hstack(augmented_y)

# Apply only to minority classes
for class_id in [1, 2]:  # minor_leak, major_leak
    mask = y_train == class_id
    X_class = X_train[mask]
    y_class = y_train[mask]
    
    X_aug, y_aug = augment_sample(X_class, y_class, n_augments=5)
    X_train = np.vstack([X_train, X_aug])
    y_train = np.hstack([y_train, y_aug])
```

---

## Dataset Versioning

### DVC (Data Version Control) Setup

```bash
# Install DVC
pip install dvc[gs]  # or [s3], [azure], [oss]

# Initialize
cd water-meter
dvc init

# Track data
dvc add data/raw/
dvc add data/processed/
dvc add models/

# Configure remote (Google Drive example)
dvc remote add -d myremote gdrive://my-folder-id

# Push
dvc push

# Commit .dvc files to git
git add .dvc/ data/.gitignore models/.gitignore
git commit -m "Add DVC tracking for data and models"
```

### Version Tags

```bash
# Tag dataset versions
git tag -a dataset-v1.0 -m "Initial synthetic + 1 week real data"
git tag -a dataset-v1.1 -m "Added 2 weeks real data + leak simulations"
git tag -a dataset-v2.0 -m "Full 30-day deployment, 50k+ samples"

# Push tags
git push origin --tags
```

### Dataset Metadata (data/metadata.yaml)

```yaml
version: "2.0"
created: "2026-07-14"
description: "Water meter leak detection dataset"
sources:
  - synthetic: 100000 samples
  - real_deployment: 25000 samples (21 days)
  - leak_simulations: 5000 samples (controlled)
classes:
  normal: 85000
  minor_leak: 10000
  major_leak: 5000
  anomaly: 5000
features: 9
split:
  train: 70%
  val: 15%
  test: 15%
  temporal: true
preprocessing:
  scaler: RobustScaler
  outlier_clip: true
  missing_drop: true
model_performance:
  xgboost_accuracy: 0.962
  xgboost_f1_macro: 0.935
  iforest_auc: 0.94
```

---

## Storage & Folder Structure

```
water-meter/
├── data/
│   ├── raw/                    # Raw Firebase exports (JSON)
│   │   ├── readings_20260701.json
│   │   ├── readings_20260702.json
│   │   └── ...
│   ├── processed/              # Cleaned, featurized CSV/Parquet
│   │   ├── train.parquet
│   │   ├── val.parquet
│   │   ├── test.parquet
│   │   └── full_dataset.parquet
│   ├── annotations/            # Human labels
│   │   └── leak_events.csv
│   ├── synthetic/              # Generated data
│   │   └── training_data_synthetic.csv
│   └── metadata.yaml           # Dataset documentation
├── models/
│   ├── xgboost_model.json
│   ├── isolation_forest.pkl
│   ├── scaler.pkl
│   └── metadata.json           # Model version info
├── training/
│   ├── water_meter_ml_training.ipynb
│   ├── generate_synthetic_data.py
│   ├── clean_data.py
│   ├── scale_features.py
│   ├── augment.py
│   └── requirements.txt
└── rpi/
    └── models/                 # Copied for inference
        ├── xgboost_model.json
        ├── isolation_forest.pkl
        └── scaler.pkl
```

### File Formats

| Stage | Format | Reason |
|-------|--------|--------|
| Raw | JSON | Firebase native export |
| Processed | Parquet | Fast I/O, columnar, compression |
| Models | JSON (XGBoost) / PKL (sklearn) | Native serialization |
| Metadata | YAML | Human-readable, version control friendly |

---

## Best Practices

### 1. Data Quality Checklist

- [ ] No missing timestamps in sequence
- [ ] All flow rates ≥ 0
- [ ] Inlet ≈ sum(fixtures) within 15% (physics check)
- [ ] No duplicate timestamps
- [ ] Labels verified for simulated leaks
- [ ] Class distribution documented
- [ ] Feature distributions plotted and reviewed
- [ ] Temporal split verified (no leakage)

### 2. Reproducibility

```python
# Set all seeds
import random
import numpy as np
import tensorflow as tf  # if used

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

# In XGBoost
model = xgb.XGBClassifier(random_state=SEED, ...)

# In train_test_split
train_test_split(..., random_state=SEED)
```

### 3. Monitoring Data Drift

```python
# training/monitor_drift.py
from scipy.stats import ks_2samp

def check_data_drift(reference_data, new_data, features, threshold=0.05):
    """KS test for distribution drift"""
    drift_detected = {}
    for feat in features:
        stat, p_value = ks_2samp(reference_data[feat], new_data[feat])
        drift_detected[feat] = p_value < threshold
    return drift_detected
```

### 4. Documentation Template

Every dataset version must have:

```markdown
# Dataset v{X.Y} - {Date}

## Summary
- Total samples: N
- Date range: YYYY-MM-DD to YYYY-MM-DD
- Devices: N (device IDs)
- Collection method: [synthetic / real / mixed]

## Class Distribution
| Class | Train | Val | Test | Total |
|-------|-------|-----|------|-------|
| normal | X | Y | Z | N |

## Feature Statistics
[Table with mean, std, min, max per feature]

## Preprocessing
- Scaler: RobustScaler
- Outlier handling: clip at 99th percentile
- Missing: drop rows

## Model Performance (on this version)
| Model | Accuracy | F1-macro | Leak Recall |
|-------|----------|----------|-------------|
| XGBoost | 0.962 | 0.935 | 0.94 |
| Isolation Forest | - | - | 0.91 (AUC) |

## Known Issues
- [ ] Sensor 3 has calibration drift after day 14
- [ ] Night class underrepresented
```

---

## Project-Specific Implementation

### Training Notebook Structure

```
training/water_meter_ml_training.ipynb
├── 1. Imports & Setup
├── 2. Load Data (raw → processed)
├── 3. Exploratory Data Analysis
├── 4. Feature Engineering
├── 5. Train/Val/Test Split (temporal)
├── 6. XGBoost Training + Hyperparameter Tuning
├── 7. Isolation Forest Training
├── 8. Evaluation (metrics, confusion matrix, SHAP)
├── 9. Save Models + Scaler
├── 10. Export for RPi Deployment
```

### Key Files to Create

```bash
# training/requirements.txt
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
```

### RPi Inference Requirements

```bash
# rpi/requirements.txt (minimal)
xgboost>=2.0
scikit-learn>=1.3
pandas>=2.0
numpy>=1.24
joblib>=1.3
flask>=3.0
pyrebase4>=4.5
gunicorn>=21.0
python-dotenv>=1.0
requests>=2.31
```

---

## Official References

| Resource | URL |
|----------|-----|
| **XGBoost Documentation** | https://xgboost.readthedocs.io/ |
| **scikit-learn Isolation Forest** | https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html |
| **Pandas Time Series** | https://pandas.pydata.org/docs/user_guide/timeseries.html |
| **DVC Data Versioning** | https://dvc.org/doc |
| **Imbalanced-learn** | https://imbalanced-learn.org/stable/ |
| **SHAP Explainer** | https://shap.readthedocs.io/ |
| **Kaggle Water Datasets** | https://www.kaggle.com/datasets?search=water+flow |
| **UCI ML Repository** | https://archive.ics.uci.edu/ |

---

## Next Steps

Proceed to:
1. [ML Training Guide](./ml-training-guide.md) — Complete training pipeline
2. [Model Deployment Guide](./model-deployment-guide.md) — RPi inference optimization
3. [Project Setup Guide](./setup.md) — Full system deployment

---

*Last updated: July 2026 | Dataset schema v2.0 | Compatible with XGBoost 2.0+, scikit-learn 1.3+, Python 3.11+*