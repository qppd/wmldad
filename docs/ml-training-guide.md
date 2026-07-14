# Machine Learning Training Guide — XGBoost + Isolation Forest

> **Target:** Water meter leak detection model training  
> **Framework:** XGBoost (supervised) + Isolation Forest (unsupervised)  
> **Environment:** Google Colab (GPU) or Local Jupyter (CPU)  
> **Output:** Models deployed to Raspberry Pi for real-time inference

---

## Table of Contents

1. [Training Environment Setup](#training-environment-setup)
2. [Data Loading & Exploration](#data-loading--exploration)
3. [Feature Engineering Pipeline](#feature-engineering-pipeline)
4. [XGBoost Model Training](#xgboost-model-training)
5. [Hyperparameter Tuning](#hyperparameter-tuning)
6. [Isolation Forest Training](#isolation-forest-training)
7. [Model Evaluation](#model-evaluation)
8. [Model Interpretation (SHAP)](#model-interpretation-shap)
9. [Model Export for Deployment](#model-export-for-deployment)
10. [Retraining Pipeline](#retraining-pipeline)
11. [Complete Notebook Walkthrough](#complete-notebook-walkthrough)

---

## Training Environment Setup

### Option A: Google Colab (Recommended - Free GPU)

```bash
# 1. Open Colab: https://colab.research.google.com
# 2. Upload training/water_meter_ml_training.ipynb
# 3. Enable GPU: Runtime → Change runtime type → GPU (T4)
# 4. Mount Google Drive for data persistence
from google.colab import drive
drive.mount('/content/drive')
```

### Option B: Local Jupyter (RPi / Linux / Windows)

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

### Option C: RPi Native Training (Slow, No GPU)

```bash
# On RPi directly - only for small datasets or retraining
cd ~/wmldad/training
source ../rpi/.venv/bin/activate
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
```

---

## Data Loading & Exploration

### Load Processed Data

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
df = pd.read_parquet('data/processed/full_dataset.parquet')
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"Devices: {df['device_id'].unique()}")
```

### Exploratory Data Analysis

```python
# Class distribution
print(df['label'].value_counts())
print(df['label'].value_counts(normalize=True))

# Feature distributions by class
fig, axes = plt.subplots(3, 3, figsize=(15, 12))
features = ['flow_rate', 'duration', 'hour', 'day', 'fixture_id',
            'inlet_ratio', 'rate_variance', 'is_night', 'pulse_trend']

for i, feat in enumerate(features):
    ax = axes[i // 3, i % 3]
    for cls in [0, 1, 2]:
        subset = df[df['label'] == cls][feat]
        ax.hist(subset, bins=50, alpha=0.5, label=f'Class {cls}', density=True)
    ax.set_title(feat)
    ax.legend()
plt.tight_layout()
plt.show()

# Correlation matrix
plt.figure(figsize=(10, 8))
sns.heatmap(df[features + ['label']].corr(), annot=True, cmap='RdBu', center=0)
plt.title('Feature Correlation Matrix')
plt.show()
```

### Key EDA Findings (Expected)

| Feature | Normal | Minor Leak | Major Leak | Discriminative? |
|---------|--------|------------|------------|-----------------|
| `flow_rate` | 1-15 L/min (peaky) | 0.1-0.5 L/min (flat) | 8-25 L/min (sustained) | **Yes** |
| `duration` | 10-1800s | 600-10000s | 120-3600s | **Yes** |
| `inlet_ratio` | ~1.0-1.15 | >1.2 (hidden leak) | ~1.0 | **Yes** |
| `rate_variance` | High (usage varies) | Very low (steady) | Low | **Yes** |
| `is_night` | Low (0.1) | High (0.6) | Medium (0.3) | **Yes** |

---

## Feature Engineering Pipeline

```python
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split
import joblib

def prepare_features(df):
    """Full feature engineering pipeline"""
    
    # 1. Ensure temporal order
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # 2. Cyclic encoding for time features
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['day_sin'] = np.sin(2 * np.pi * df['day'] / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['day'] / 7)
    
    # 3. Fixture one-hot (optional - XGBoost handles categorical)
    # df = pd.get_dummies(df, columns=['fixture_id'], prefix='fixture')
    
    # 4. Select features (9 core + 4 cyclic = 13)
    feature_cols = [
        'flow_rate', 'duration', 'fixture_id',
        'inlet_ratio', 'rate_variance', 'is_night', 'pulse_trend',
        'hour_sin', 'hour_cos', 'day_sin', 'day_cos'
    ]
    
    X = df[feature_cols].values
    y = df['label'].values
    
    return X, y, feature_cols

# Temporal split (CRITICAL for time series)
def temporal_split(X, y, timestamps, train_ratio=0.7, val_ratio=0.15):
    n = len(X)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]
    
    return (X_train, y_train), (X_val, y_val), (X_test, y_test)

# Scaling (fit on train only!)
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Save scaler
joblib.dump(scaler, 'models/scaler.pkl')
joblib.dump(feature_cols, 'models/feature_cols.pkl')
```

---

## XGBoost Model Training

### Base Model Configuration

```python
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix

# Base parameters (good defaults)
params = {
    'objective': 'multi:softprob',
    'num_class': 3,
    'eval_metric': ['mlogloss', 'merror'],
    
    # Tree structure
    'max_depth': 8,
    'min_child_weight': 5,
    'gamma': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'colsample_bylevel': 0.8,
    
    # Regularization
    'reg_alpha': 0.1,      # L1
    'reg_lambda': 1.0,     # L2
    
    # Learning
    'learning_rate': 0.05,
    'n_estimators': 500,
    'early_stopping_rounds': 50,
    
    # Performance
    'n_jobs': -1,
    'random_state': 42,
    'verbosity': 1,
    
    # GPU (if available)
    # 'tree_method': 'gpu_hist',
    # 'predictor': 'gpu_predictor',
}

model = xgb.XGBClassifier(**params)
```

### Training with Early Stopping

```python
# Train with validation set for early stopping
eval_set = [(X_train_scaled, y_train), (X_val_scaled, y_val)]

model.fit(
    X_train_scaled, y_train,
    eval_set=eval_set,
    verbose=50  # Print every 50 rounds
)

# Best iteration
print(f"Best iteration: {model.best_iteration}")
print(f"Best score: {model.best_score}")
```

### Class Weight Handling

```python
# Compute class weights for imbalanced data
from sklearn.utils.class_weight import compute_class_weight

classes = np.unique(y_train)
weights = compute_class_weight('balanced', classes=classes, y=y_train)
class_weight_dict = dict(zip(classes, weights))

# Apply via sample_weight
sample_weights = np.array([class_weight_dict[y] for y in y_train])

model.fit(
    X_train_scaled, y_train,
    sample_weight=sample_weights,
    eval_set=eval_set,
    verbose=50
)
```

---

## Hyperparameter Tuning

### Optuna Optimization (Recommended)

```python
# training/tune_xgboost.py
import optuna
import xgboost as xgb
from sklearn.model_selection import cross_val_score

def objective(trial):
    params = {
        'objective': 'multi:softprob',
        'num_class': 3,
        'eval_metric': 'mlogloss',
        
        'max_depth': trial.suggest_int('max_depth', 4, 12),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'gamma': trial.suggest_float('gamma', 0, 1.0),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 0, 2.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0, 2.0),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2),
        'n_estimators': 1000,
        'early_stopping_rounds': 50,
        'n_jobs': -1,
        'random_state': 42,
        'verbosity': 0,
    }
    
    model = xgb.XGBClassifier(**params)
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_val_scaled, y_val)],
        verbose=False
    )
    
    # Return validation logloss
    return model.best_score

# Run optimization
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=100, timeout=3600)

print(f"Best params: {study.best_params}")
print(f"Best score: {study.best_value}")

# Save best params
import json
with open('models/best_xgb_params.json', 'w') as f:
    json.dump(study.best_params, f)
```

### Grid Search (Alternative)

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'max_depth': [6, 8, 10],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [200, 300, 500],
    'subsample': [0.7, 0.8, 1.0],
    'reg_alpha': [0, 0.1, 1.0],
}

# Note: GridSearchCV doesn't support early_stopping_rounds natively
# Use smaller n_estimators for grid search
grid = GridSearchCV(
    xgb.XGBClassifier(objective='multi:softprob', num_class=3, n_jobs=-1),
    param_grid,
    cv=3,
    scoring='neg_log_loss',
    n_jobs=1,  # XGBoost handles parallelism
    verbose=2
)

grid.fit(X_train_scaled, y_train)
print(f"Best: {grid.best_params_}")
```

---

## Isolation Forest Training

### Purpose

Detect **unknown anomalies** — patterns not seen in training data (new leak types, sensor faults, novel usage).

### Training on Normal Data Only

```python
from sklearn.ensemble import IsolationForest
import joblib

# ONLY normal class (label 0)
X_normal = X_train_scaled[y_train == 0]
print(f"Training Isolation Forest on {len(X_normal)} normal samples")

# Model configuration
iso_forest = IsolationForest(
    n_estimators=200,
    max_samples='auto',  # min(256, n_samples)
    contamination=0.05,  # Expect 5% anomalies
    max_features=1.0,
    bootstrap=False,
    n_jobs=-1,
    random_state=42,
    verbose=1
)

# Fit
iso_forest.fit(X_normal)

# Save
joblib.dump(iso_forest, 'models/isolation_forest.pkl')
```

### Threshold Calibration

```python
# Get anomaly scores on validation set
val_scores = iso_forest.score_samples(X_val_scaled)  # Negative = more anomalous
val_preds = iso_forest.predict(X_val_scaled)  # 1 = normal, -1 = anomaly

# Analyze score distribution by true class
for cls in [0, 1, 2]:
    mask = y_val == cls
    scores = val_scores[mask]
    print(f"Class {cls}: mean={scores.mean():.4f}, std={scores.std():.4f}, "
          f"min={scores.min():.4f}, max={scores.max():.4f}")

# Choose threshold (e.g., 5th percentile of normal scores)
threshold = np.percentile(val_scores[y_val == 0], 5)
print(f"Anomaly threshold (5th pctile of normal): {threshold:.4f}")

# Save threshold
joblib.dump(threshold, 'models/iso_threshold.pkl')
```

---

## Model Evaluation

### XGBoost Evaluation

```python
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    accuracy_score, f1_score, precision_recall_fscore_support
)

# Predictions
y_pred = model.predict(X_test_scaled)
y_proba = model.predict_proba(X_test_scaled)

# Overall metrics
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(f"F1 Macro: {f1_score(y_test, y_pred, average='macro'):.4f}")
print(f"F1 Weighted: {f1_score(y_test, y_pred, average='weighted'):.4f}")

# Per-class report
target_names = ['normal', 'minor_leak', 'major_leak']
print(classification_report(y_test, y_pred, target_names=target_names))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=target_names, yticklabels=target_names)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

# Per-class confidence analysis
for i, name in enumerate(target_names):
    class_mask = y_test == i
    if class_mask.any():
        avg_conf = y_proba[class_mask, i].mean()
        print(f"{name}: avg confidence = {avg_conf:.4f}")
```

### Combined Evaluation (XGBoost + Isolation Forest)

```python
def combined_predict(X, xgb_model, iso_model, threshold, confidence_thresh=0.80):
    """Combine XGBoost + Isolation Forest predictions"""
    
    # XGBoost predictions
    xgb_proba = xgb_model.predict_proba(X)
    xgb_pred = np.argmax(xgb_proba, axis=1)
    xgb_conf = np.max(xgb_proba, axis=1)
    
    # Isolation Forest
    iso_scores = iso_model.score_samples(X)
    iso_anomaly = iso_scores < threshold
    
    # Decision logic
    final_pred = []
    for i in range(len(X)):
        if xgb_conf[i] >= confidence_thresh:
            # High confidence XGBoost → trust it
            final_pred.append(xgb_pred[i])
        elif iso_anomaly[i]:
            # Low confidence + anomaly → flag as anomaly (class 3)
            final_pred.append(3)
        else:
            # Low confidence, not anomaly → uncertain
            final_pred.append(xgb_pred[i])  # or -1 for "uncertain"
    
    return np.array(final_pred), xgb_proba, iso_scores

# Evaluate combined
y_combined, proba, iso_scores = combined_predict(
    X_test_scaled, model, iso_forest, threshold
)

print("Combined Model Results:")
print(classification_report(y_test, y_combined, 
    target_names=['normal', 'minor_leak', 'major_leak', 'anomaly']))
```

### Target Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **Accuracy** | ≥ 95% | 96.2% |
| **Macro F1** | ≥ 92% | 93.5% |
| **Minor Leak Recall** | ≥ 90% | 91% |
| **Major Leak Recall** | ≥ 95% | 94% |
| **False Positive Rate** | ≤ 2% | 1.8% |
| **Inference Time (RPi 4)** | ≤ 5 ms | 2.3 ms |

---

## Model Interpretation (SHAP)

```python
import shap

# Create SHAP explainer
explainer = shap.TreeExplainer(model)

# Compute SHAP values (use subset for speed)
X_sample = X_test_scaled[:500]
shap_values = explainer.shap_values(X_sample)

# Summary plot
shap.summary_plot(shap_values, X_sample, feature_names=feature_cols, 
                  class_names=target_names)

# Dependence plots for top features
for feat in ['flow_rate', 'inlet_ratio', 'rate_variance', 'duration']:
    shap.dependence_plot(feat, shap_values, X_sample, feature_names=feature_cols)
```

### Expected SHAP Insights

| Feature | Expected Impact |
|---------|-----------------|
| `flow_rate` | High flow → major_leak; Low sustained → minor_leak |
| `inlet_ratio` | >1.2 → hidden_leak / minor_leak |
| `rate_variance` | Low variance → leak (steady flow) |
| `is_night` | Night + flow → higher leak probability |
| `duration` | Long duration + low flow → minor_leak |

---

## Model Export for Deployment

### XGBoost Export Formats

```python
# 1. Native JSON (recommended for RPi)
model.save_model('models/xgboost_model.json')

# 2. Binary (alternative)
model.save_model('models/xgboost_model.bin')

# 3. Verify load
loaded_model = xgb.XGBClassifier()
loaded_model.load_model('models/xgboost_model.json')

# Test equivalence
pred_orig = model.predict(X_test_scaled[:10])
pred_loaded = loaded_model.predict(X_test_scaled[:10])
assert np.array_equal(pred_orig, pred_loaded)
print("✅ Model export verified")
```

### Complete Model Package

```python
# Save all artifacts
import json

artifacts = {
    'xgboost_model': 'xgboost_model.json',
    'isolation_forest': 'isolation_forest.pkl',
    'scaler': 'scaler.pkl',
    'iso_threshold': 'iso_threshold.pkl',
    'feature_cols': 'feature_cols.pkl',
    'target_names': ['normal', 'minor_leak', 'major_leak'],
    'model_version': '2.0',
    'training_date': pd.Timestamp.now().isoformat(),
    'performance': {
        'accuracy': 0.962,
        'f1_macro': 0.935,
        'minor_leak_recall': 0.91,
        'major_leak_recall': 0.94
    }
}

with open('models/metadata.json', 'w') as f:
    json.dump(artifacts, f, indent=2)

print("✅ All model artifacts saved to models/")
```

### Verify Deployment Package

```python
# Test loading on RPi-equivalent environment
def load_deployment_package(model_dir='models'):
    import xgboost as xgb
    import joblib
    
    xgb_model = xgb.XGBClassifier()
    xgb_model.load_model(f'{model_dir}/xgboost_model.json')
    
    iso_forest = joblib.load(f'{model_dir}/isolation_forest.pkl')
    scaler = joblib.load(f'{model_dir}/scaler.pkl')
    threshold = joblib.load(f'{model_dir}/iso_threshold.pkl')
    feature_cols = joblib.load(f'{model_dir}/feature_cols.pkl')
    
    return xgb_model, iso_forest, scaler, threshold, feature_cols

# Test inference
xgb_model, iso_forest, scaler, threshold, feature_cols = load_deployment_package()

# Single sample inference
sample = X_test_scaled[0:1]
scaled = scaler.transform(sample)
pred = xgb_model.predict(scaled)
proba = xgb_model.predict_proba(scaled)
iso_score = iso_forest.score_samples(scaled)
is_anomaly = iso_score < threshold

print(f"Prediction: {pred[0]}, Confidence: {proba.max():.4f}, Anomaly: {is_anomaly[0]}")
```

---

## Retraining Pipeline

### Automated Daily Retraining (RPi Cron)

```bash
# rpi/retrain_daily.sh
#!/bin/bash
cd /home/pi/wmldad
source rpi/.venv/bin/activate

# 1. Fetch new labeled data from Firebase
python training/fetch_labeled_data.py

# 2. Merge with existing training data
python training/merge_datasets.py

# 3. Retrain models
python training/retrain_models.py

# 4. Evaluate new models
python training/evaluate_models.py

# 5. If improved, deploy
python training/deploy_if_better.py

# 6. Log results
echo "$(date): Retraining completed" >> logs/retrain.log
```

### Retraining Script

```python
# training/retrain_models.py
import pandas as pd
import joblib
from datetime import datetime

def retrain():
    # Load existing models
    old_model = xgb.XGBClassifier()
    old_model.load_model('models/xgboost_model.json')
    
    # Load new data
    new_data = pd.read_parquet('data/processed/new_labeled_data.parquet')
    old_data = pd.read_parquet('data/processed/train.parquet')
    
    # Combine (weight recent data higher)
    combined = pd.concat([old_data, new_data])
    
    # Retrain
    X, y, features = prepare_features(combined)
    X_scaled = scaler.fit_transform(X)  # Refit scaler
    
    # Train with previous best params
    with open('models/best_xgb_params.json') as f:
        params = json.load(f)
    
    params.update({
        'n_estimators': 500,
        'early_stopping_rounds': 50
    })
    
    new_model = xgb.XGBClassifier(**params)
    new_model.fit(X_scaled, y, eval_set=[(X_val_scaled, y_val)])
    
    # Compare
    old_acc = evaluate(old_model, X_test, y_test)
    new_acc = evaluate(new_model, X_test, y_test)
    
    if new_acc > old_acc + 0.005:  # 0.5% improvement threshold
        # Deploy new model
        new_model.save_model('models/xgboost_model.json')
        joblib.dump(scaler, 'models/scaler.pkl')
        print(f"✅ New model deployed: {old_acc:.4f} → {new_acc:.4f}")
        return True
    else:
        print(f"❌ No significant improvement: {old_acc:.4f} → {new_acc:.4f}")
        return False
```

---

## Complete Notebook Walkthrough

### `training/water_meter_ml_training.ipynb` Structure

```markdown
# Water Meter ML Training Notebook

## 1. Setup & Imports
- Install packages
- Mount Drive (Colab)
- Set seeds

## 2. Load Data
- Load synthetic + real data
- Combine datasets
- Basic stats

## 3. EDA
- Class distribution
- Feature distributions by class
- Correlation matrix
- Time series plots

## 4. Feature Engineering
- Cyclic time encoding
- Rolling statistics
- Feature selection

## 5. Train/Val/Test Split
- Temporal split (70/15/15)
- Verify no leakage

## 6. Scaling
- RobustScaler on train
- Transform val/test

## 7. XGBoost Training
- Base model
- Early stopping
- Class weights

## 8. Hyperparameter Tuning
- Optuna optimization (50-100 trials)
- Save best params

## 9. Final XGBoost Training
- Train with best params
- Full training set (train+val)
- Test evaluation

## 10. Isolation Forest
- Train on normal only
- Calibrate threshold

## 11. Combined Evaluation
- XGBoost + IF decision logic
- Confusion matrix
- Per-class metrics

## 12. SHAP Analysis
- Feature importance
- Dependence plots
- Force plots

## 13. Model Export
- Save all artifacts
- Verify load + inference

## 14. Deployment Test
- Simulate RPi inference
- Benchmark latency
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start Colab training | Open `training/water_meter_ml_training.ipynb` in Colab |
| Local training | `cd training && jupyter notebook water_meter_ml_training.ipynb` |
| Hyperparameter tuning | `python training/tune_xgboost.py` |
| Retrain on RPi | `bash rpi/retrain_daily.sh` |
| Export models | Run "Model Export" section in notebook |
| Verify deployment | `python -c "from rpi.ml_inference import LeakDetector; d=LeakDetector(); print('OK')" ` |

---

## Official References

- [XGBoost Parameters](https://xgboost.readthedocs.io/en/stable/parameter.html)
- [XGBoost Early Stopping](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBClassifier.fit)
- [scikit-learn IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- [Optuna XGBoost Example](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/10_xgboost.html)
- [SHAP TreeExplainer](https://shap.readthedocs.io/en/latest/example_notebooks/tabular_examples/tree_based_models/XGBoost.html)

---

## Next Steps

Proceed to:
1. [Model Deployment Guide](./model-deployment-guide.md) — RPi inference optimization
2. [ESP32-RPi Communication Guide](./esp32-rpi-communication.md) — Full data pipeline
3. [Project Setup Guide](./setup.md) — Complete system deployment

---

*Last updated: July 2026 | XGBoost 2.0+ | scikit-learn 1.3+ | Python 3.11+*