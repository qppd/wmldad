# Firmware Architecture — Water Meter with Leak Detection

## File Structure

```
water-meter/
├── src/
│   ├── main.cpp                  # Entry point, setup() and loop()
│   ├── config.h                  # User configuration (WiFi, pins, intervals)
│   ├── config.example.h          # Template configuration file
│   ├── sensor_manager.h          # Manages all 5 flow sensor interrupts
│   ├── flow_sensor.h             # Single flow sensor pulse counter
│   ├── feature_extractor.h       # Builds feature vector for ML inference
│   ├── ml_inference.h            # Random Forest → TFLite Micro inference
│   ├── leak_detector.h           # Combines ML + rules to confirm leaks
│   ├── valve_controller.h        # Relay control for solenoid valves
│   ├── wifi_manager.h            # WiFi connection handler
│   ├── mqtt_client.h             # MQTT publish / subscribe
│   ├── http_client.h             # HTTP REST client
│   ├── data_logger.h             # Local storage (SD card + SPIFFS)
│   ├── ntp_sync.h                # NTP time synchronization
│   ├── display_manager.h         # OLED display
│   ├── alert_manager.h           # Buzzer + LED alerts
│   ├── ota_updater.h             # Firmware + model OTA updates
│   └── led_indicator.h           # Status LED feedback
├── model/
│   ├── leak_model.tflite         # Random Forest TFLite model
│   └── model_config.h            # Model parameters (num features, classes)
├── training/
│   ├── train_model.py            # scikit-learn training script
│   ├── feature_engineering.py    # Feature extraction from raw data
│   ├── export_tflite.py          # sklearn → ONNX → TFLite conversion
│   └── simulate.py               # Simulate data for testing
├── platformio.ini                # PlatformIO project config
└── README.md
```

---

## Main Loop Flow

```
loop()
├── Read all 5 flow sensors (pulse counters)
├── Extract features per fixture
├── Run Random Forest inference (TFLite Micro)
├── Check classification:
│   ├── Normal → log, update display
│   ├── Minor Leak → increment counter, if 3+ consecutive → ALERT
│   ├── Major Leak → immediate ALERT
│   └── Anomaly → log features for review
├── If leak confirmed → close valve + alert
├── Update OLED display (live flow per fixture)
├── Check upload interval → send data
├── Check OTA updates
├── Check command topic (MQTT)
├── Update status LED
└── Light sleep until next read cycle
```

---

## ML Inference Module

### Loading the Model

```cpp
#include <TensorFlowLite.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "model/leak_model.tflite"  // Compiled into firmware

// Model is compiled as a C array (xxd -i)
extern const unsigned char leak_model_tflite[];
extern const int leak_model_tflite_len;

// Initialize interpreter
static tflite::MicroInterpreter* interpreter;
static constexpr int kTensorArenaSize = 32 * 1024;  // 32 KB
static uint8_t tensor_arena[kTensorArenaSize];
```

### Running Inference

```cpp
float features[9];  // 9 features from extractor
TfLiteTensor* input = interpreter->input(0);
TfLiteTensor* output = interpreter->output(0);

// Copy features to input tensor
for (int i = 0; i < 9; i++) {
    input->data.f[i] = features[i];
}

// Run inference
interpreter->Invoke();

// Read output probabilities
float normal_prob = output->data.f[0];
float minor_leak_prob = output->data.f[1];
float major_leak_prob = output->data.f[2];

// Confidence check
if (max_prob > 0.80) {
    return classification;
} else {
    return "uncertain";
}
```

### Model Training (Python)

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

rf = RandomForestClassifier(
    n_estimators=50,
    max_depth=10,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)
rf.fit(X_train, y_train)

# Convert to TFLite via ONNX
# See training/export_tflite.py
```

---

## Sensor Manager (5 Sensors)

```cpp
#define NUM_SENSORS 5

struct SensorConfig {
    uint8_t gpio;
    const char* name;
    const char* fixture;
};

SensorConfig sensors[NUM_SENSORS] = {
    {34, "inlet", "main_inlet"},
    {35, "fix1", "kitchen_sink"},
    {32, "fix2", "toilet"},
    {33, "fix3", "wash_basin"},
    {25, "fix4", "shower"}
};

// ISR per sensor — one handler function
void IRAM_ATTR pulseCounterISR(void* arg) {
    int index = (int)arg;
    if (millis() - lastPulseTime[index] > DEBOUNCE_MS) {
        pulseCount[index]++;
        lastPulseTime[index] = millis();
    }
}
```

---

## Leak Confirmation Logic

| Condition | Classification | Action |
|-----------|---------------|--------|
| ML says `normal` AND confidence > 0.8 | ✅ Normal | Log + continue |
| ML says `minor_leak` × 1 | ⏳ Watch | Increment counter |
| ML says `minor_leak` × 3 consecutive | ⚠️ Minor Leak | Close valve + alert owner |
| ML says `major_leak` | 🚨 Major Leak | Close valve + alarm + emergency alert |
| ML says `anomaly` | ❓ Unknown | Log features + notify for review |
| Inlet >> Sum(fixtures) by >10% | ⚠️ Hidden Leak | Alert (unknown fixture) |

---

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `WIFI_SSID` | — | WiFi network name |
| `NUM_SENSORS` | 5 | Number of flow sensors |
| `SENSOR_PINS[]` | {34, 35, 32, 33, 25} | GPIO pins per sensor |
| `RELAY_PINS[]` | {26, 27, 14, 12, 13} | GPIO pins per valve relay |
| `PULSE_PER_LITER` | 450 | Calibration factor per sensor |
| `READ_INTERVAL_MS` | 1000 | Read sensors every 1s |
| `UPLOAD_INTERVAL_MS` | 60000 | Upload every 60s |
| `LEAK_CONFIRM_COUNT` | 3 | Consecutive minor leak readings to confirm |
| `CONFIDENCE_THRESHOLD` | 0.80 | Minimum ML confidence |
| `MODEL_PATH` | /model/leak_model.tflite | Model location |

---

## Power Modes

| Mode | Consumption | Use Case |
|------|-------------|----------|
| Active (reading) | ~80 mA | 1s every 60s |
| Light Sleep | ~10 mA | Between read cycles |
| Deep Sleep | ~10 µA | Not recommended (need fast leak response) |

---

## Build Instructions

### PlatformIO

```bash
# Install dependencies
pio pkg install

# Build with model
pio run

# Upload firmware + model
pio run --target upload
pio run --target uploadfs   # Upload model to SPIFFS

# Monitor
pio device monitor --baud 115200
```

### Train & Export Model

```bash
cd training
pip install -r requirements.txt
python train_model.py            # Train Random Forest
python export_tflite.py          # Export to TFLite
cp leak_model.tflite ../data/    # Copy to data folder
```
