# Setup Guide — Step-by-Step from Zero to Working System

> **Target audience:** Students / researchers building a water monitoring project  
> **Estimated time:** 2–3 weeks (part-time)  
> **Prerequisites:** Basic electronics, basic programming

---

## Table of Contents

1. [Phase 1: Parts & Tools](#phase-1-parts--tools)
2. [Phase 2: Software Installation](#phase-2-software-installation)
3. [Phase 3: Hardware Assembly](#phase-3-hardware-assembly)
4. [Phase 4: ESP32 Firmware Upload](#phase-4-esp32-firmware-upload)
5. [Phase 5: Sensor Calibration](#phase-5-sensor-calibration)
6. [Phase 6: RPi Backend Setup](#phase-6-rpi-backend-setup)
7. [Phase 7: ML Model Training](#phase-7-ml-model-training)
8. [Phase 8: Testing the Full System](#phase-8-testing-the-full-system)
9. [Phase 9: Enclosure & Deployment](#phase-9-enclosure--deployment)

---

## Phase 1: Parts & Tools

### Required Parts

Check [BOM.md](./bom.md) for complete list with Shopee/Lazada links. Minimum essentials:

| Item | Qty | Estimated Cost (₱) |
|------|-----|-------------------|
| ESP32 38-pin Dev Board | 1 | ₱450 |
| ESP32 38-pin Expansion Board | 1 | ₱180 |
| YF-S201 Flow Sensor | 4 | ₱720 |
| Check Valve 1/2" | 3 | ₱360 |
| Perf board + soldering | 1 set | ₱115 |
| USB Micro Data Cable | 1 | ₱100 |
| **Minimum Total** | | **~₱2,035** |

### Required Tools

- Soldering iron + solder (for permanent setup)
- Multimeter (for checking connections)
- Wire stripper / cutter
- Small flathead screwdriver
- Hot glue gun (for mounting sensors)

### Software You Need

| Software | Purpose | Download |
|----------|---------|----------|
| **Arduino IDE 2.x** | ESP32 build, upload, Serial Monitor | [arduino.cc](https://www.arduino.cc/en/software) |
| **Python 3.11+** | ML training + backend | [python.org](https://www.python.org/) |
| **Git** | Version control | [git-scm.com](https://git-scm.com/) |
| **Google Chrome / Firefox** | Dashboard access | — |
| **RPi Account** | Local server | Already have one |

---

## Phase 2: Software Installation

### Step 2.1: Install Arduino IDE

1. Download Arduino IDE 2.x from [arduino.cc](https://www.arduino.cc/en/software)
2. Install and open Arduino IDE
3. Add ESP32 board support:
   - File -> Preferences -> Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools -> Board -> Boards Manager -> search **ESP32** -> install **ESP32 Arduino**
4. Install required libraries via Library Manager (Tools -> Manage Libraries):
   - `ArduinoJson` by Benoit Blanchon (v7+)

> **Note:** No Firebase-ESP-Client needed — we use plain USB Serial with ArduinoJson.

### Step 2.2: Install Python

1. Download Python 3.11+ from python.org
2. **Important:** Check **"Add Python to PATH"** during installation
3. Verify:
   ```bash
   python --version
   # Should show: Python 3.11.x or higher
   ```

### Step 2.3: Clone the Project

```bash
# Open terminal (Command Prompt or Git Bash)
git clone https://github.com/qppd/wmldad.git
cd wmldad
```

### Step 2.4: Install Python Dependencies (for ML Backend)

```bash
cd rpi/
pip install -r requirements.txt
# or manually:
pip install xgboost scikit-learn pandas numpy joblib flask pyserial
```

---

## Phase 3: Hardware Assembly

### Step 3.1: Prepare the Expansion Board

The ESP32 expansion board makes wiring much easier. It provides:
- Labeled screw terminals for each GPIO pin
- Power rails (5V and 3.3V)
- Reset and BOOT buttons

### Step 3.2: Connect One Flow Sensor (Test Circuit First)

Before connecting all 4 sensors, test with just one:

```
YF-S201 Sensor          ESP32 Expansion Board
┌──────────────┐
│  Red   ──────┼────── 5V (VIN pin)
│  Black ──────┼────── GND
│  Yellow ─────┼────── GPIO 26
└──────────────┘
```

**Note:** The YF-S201 Hall-effect sensor outputs a digital pulse signal. No external pull-up resistor or capacitor needed — connect signal wire directly to GPIO.

### Step 3.3: Connect All 4 Sensors

Once the test circuit works, connect all sensors:

| Sensor | GPIO | Notes |
|--------|------|-------|
| Inlet | 26 | Connect signal directly |
| Fixture 1 (Bidet) | 25 | Connect signal directly |
| Fixture 2 (Kitchen) | 33 | Connect signal directly |
| Fixture 3 (Bathroom Shower) | 32 | Connect signal directly |

**Wiring for each sensor:**
```
YF-S201 Sensor:
  Red   → 5V (VIN)
  Black → GND
  Yellow → GPIO (26, 25, 33, or 32)
```

### Step 3.4: Plumbing Setup

For testing without actual plumbing:
1. Connect flow sensors in series with a **garden hose or PVC pipe**
2. Inlet sensor at the water source end
3. Each fixture sensor followed by a check valve
4. End of each line: a valve or faucet to control flow

**For testing:**
- Fill a 20L container with water
- Connect pump or gravity-feed through the sensors
- Open/close valves to simulate fixtures

---

## Phase 4: ESP32 Firmware Upload

### Step 4.1: Configure Firmware

1. Open `src/config.example.h` in any text editor
2. Create `src/config.h` (copy the example)
3. Fill in your credentials:

```cpp
// === Device Identity ===
#define DEVICE_ID        "wmldad-001"
#define FIRMWARE_VERSION "v3.0.0-usb"

// === WiFi (for OTA + NTP only — not required for serial operation) ===
#define WIFI_SSID        "YOUR_WIFI_NAME"
#define WIFI_PASSWORD    "YOUR_WIFI_PASSWORD"

// === Sensor Calibration (PPL = Pulses Per Liter) ===
// UPDATE AFTER BUCKET TEST!
#define PPL_INLET        450
#define PPL_FIXTURE1     450
#define PPL_FIXTURE2     450
#define PPL_FIXTURE3     450

// === Sensor Pins ===
#define PIN_INLET        26
#define PIN_FIXTURE1     25
#define PIN_FIXTURE2     33
#define PIN_FIXTURE3     32

// === Timing ===
#define SEND_INTERVAL_MS 5000      // Serial output every 5 sec
```

### Step 4.2: Upload Firmware

1. Connect ESP32 via USB cable
2. In Arduino IDE, select your board:
   - **Tools -> Board -> ESP32 Arduino -> ESP32 Dev Module**
3. Select the correct port:
   - **Tools -> Port -> COMx** (check Windows Device Manager for the COM port)
4. Click **Sketch -> Verify/Compile** (Ctrl+R) to check for errors
5. Click **Sketch -> Upload** (Ctrl+U) to flash the ESP32
6. If upload fails:
   - Hold **BOOT** button on ESP32
   - Press **EN** (reset) while holding BOOT
   - Release EN, then release BOOT
   - Click Upload again

### Step 4.3: Monitor Serial Output

1. Open **Tools -> Serial Monitor** (Ctrl+Shift+M)
2. Set baud rate to **921600** (bottom-right of Serial Monitor window)
3. You should see:
   ```
   {"status":"ready","device_id":"wmldad-001","firmware":"v3.0.0-usb"}
   {"device_id":"wmldad-001","ts":123456,"sensor":1,"gpio":26,"pulses":127,"flow_rate_lpm":2.34,"volume_ml":456}
   {"device_id":"wmldad-001","ts":123456,"sensor":2,"gpio":25,"pulses":89,"flow_rate_lpm":1.65,"volume_ml":321}
   {"device_id":"wmldad-001","ts":123456,"sensor":3,"gpio":33,"pulses":0,"flow_rate_lpm":0.00,"volume_ml":0}
   {"device_id":"wmldad-001","ts":123456,"sensor":4,"gpio":32,"pulses":203,"flow_rate_lpm":3.80,"volume_ml":720}
   ```

---

## Phase 5: Sensor Calibration

> Detailed procedure: [Calibration Guide](./esp32-firmware-complete-guide.md#sensor-calibration-bucket-test)

### Quick Calibration (Bucket Test)

1. **Prepare:** Get a 5L graduated container
2. **Connect:** Run water from faucet through the inlet sensor into the container
3. **Open:** Turn on faucet at medium flow
4. **Collect:** Exactly 5 liters
5. **Read:** Get pulse count from Serial Monitor (watch `pulses` field)
6. **Calculate:**
   ```
   Actual PPL = Total Pulse Count ÷ 5
   ```
7. **Update:** Change `PPL_INLET` in `config.h`
8. **Repeat** for each sensor (move sensor to each fixture line)

---

## Phase 6: RPi Backend Setup

> **Detailed guide:** [RPi Backend App](./pi-complete-setup.md)

### Quick Setup

1. **Get a Raspberry Pi 3B+/4/5** with Raspberry Pi OS (64-bit, Trixie/Debian 13)
2. **SSH into the RPi** or connect a monitor/keyboard
3. **Clone the project:**
   ```bash
   git clone https://github.com/qppd/wmldad.git
   cd wmldad/rpi/
   ```
4. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. **Configure serial port (udev rule):**
   ```bash
   echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyESP32", MODE="0666", GROUP="dialout"' | sudo tee /etc/udev/rules.d/99-esp32.rules
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```
6. **Run the Flask app:**
   ```bash
   python app.py
   ```
7. **Test:** Open a browser and visit `http://<rpi-ip>:5000/`
8. **Set up auto-start (optional):**
   ```bash
   sudo cp water-meter.service /etc/systemd/system/
   sudo systemctl enable water-meter.service
   sudo systemctl start water-meter.service
   ```

> See [RPi Backend App](./pi-complete-setup.md) for complete setup instructions, systemd service config, touchscreen setup, and remote access setup.

---

## Phase 7: ML Model Training

> Complete details: [ML Model](./ml-complete-guide.md)

### Quick Training

```bash
# Option A: Google Colab (recommended - no setup needed)
#    1. Upload training/water_meter_ml_training.ipynb to Google Drive
#    2. Open with Google Colab (colab.research.google.com)
#    3. Runtime -> Run all
#    Models are saved to model/ folder automatically

# Option B: Jupyter Notebook (local)
cd training/
pip install -r requirements.txt
jupyter notebook water_meter_ml_training.ipynb
```

Expected output:
```
XGBoost Accuracy: 0.962
Classification Report:
              precision    recall  f1-score
    normal       0.98      0.99      0.98
 minor_leak      0.93      0.91      0.92
 major_leak      0.95      0.94      0.94
```

Move trained models to the RPi (after training in Colab/Jupyter):
```bash
# From Google Colab: download model files from the Files tab
# (they appear as xgboost_model.json, isolation_forest.pkl, scaler.pkl)

# From Jupyter (local):
cp training/xgboost_model.json rpi/models/
cp training/isolation_forest.pkl rpi/models/
cp training/scaler.pkl rpi/models/
```

---

## Phase 8: Testing the Full System

### Test 1: ESP32 → USB Serial
1. Turn water on through a fixture
2. Open Serial Monitor (921600 baud) on the RPi or computer
3. JSON data should stream every 5 seconds
4. Verify flow rate changes when you open/close faucets

### Test 2: RPi Backend → Dashboard
1. Open the RPi dashboard in a browser: `http://<rpi-ip>:5000/`
2. Click Dashboard → should show latest readings
3. Check the RPi logs:
   ```bash
   journalctl -u water-meter.service -f
   ```

### Test 3: ML Leak Detection
1. Simulate a **minor leak**: partially open a valve to produce 0.1–0.5 L/min
2. Wait 30+ seconds
3. Check if an alert appears on the dashboard
4. Check logs for detection

### Test 4: Command Flow
1. From dashboard, send a command (e.g., "calibrate")
2. ESP32 should respond via Serial
3. Check Serial Monitor for acknowledgment

### Test 5: Offline Mode
1. Disconnect USB cable from RPi
2. ESP32 should continue logging to SPIFFS (LED patterns show local alerts)
3. Reconnect USB → data should appear on dashboard

---

## Phase 9: Enclosure & Deployment

### Permanent Wiring
1. Solder components to perf board (instead of breadboard)
2. Mount expansion board inside ABS enclosure
3. Use cable glands for water sensor cables + USB cable gland for RPi link
4. Label all wires

### Final Calibration
1. Install sensors in actual plumbing
2. Perform bucket test on each sensor
3. Update PPL values in `config.h`, re-upload firmware
4. Verify total consumption matches water bill

### Monitoring
1. Set up dashboard as home page on touchscreen
2. Configure in-app alerts (via dashboard /api/alerts)
3. Set up a cron job on RPi for daily model retraining
4. Check system health periodically

---

## Quick Reference: Common Commands

```bash
# Arduino IDE: Verify/Compile
#   Sketch -> Verify/Compile  (Ctrl+R)

# Arduino IDE: Upload to ESP32
#   Sketch -> Upload  (Ctrl+U)

# Arduino IDE: Serial Monitor
#   Tools -> Serial Monitor  (Ctrl+Shift+M)  @ 921600 baud

# Train ML model (Google Colab)
#   Open training/water_meter_ml_training.ipynb
#   Runtime -> Run all

# Train ML model (Jupyter Notebook)
cd training/
jupyter notebook water_meter_ml_training.ipynb

# RPi: Start Flask
cd /home/pi/wmldad/rpi
source venv/bin/activate
python app.py

# RPi: View logs
journalctl -u water-meter.service -f
```

---

## Wiring Resources

### Interactive Wiring Diagram (Cirkit Designer)
**🔗 [View Interactive Wiring Diagram](https://app.cirkitdesigner.com/project/4f173a2b-5656-48ff-b98f-183483fecb1e)**

### Static Wiring Diagram (PNG)
![Wiring Diagram](../wiring/wmldad.png)

### Wiring Source File
[Download .ckt file](../wiring/wmldad.ckt) — Open in [Cirkit Designer](https://app.cirkitdesigner.com/)