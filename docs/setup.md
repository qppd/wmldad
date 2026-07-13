# Setup Guide — Step-by-Step from Zero to Working System

> **Target audience:** Students / researchers building a capstone project  
> **Estimated time:** 2–3 weeks (part-time)  
> **Prerequisites:** Basic electronics (solderless breadboard), basic programming

---

## Table of Contents

1. [Phase 1: Parts & Tools](#phase-1-parts--tools)
2. [Phase 2: Software Installation](#phase-2-software-installation)
3. [Phase 3: Firebase Setup](#phase-3-firebase-setup)
4. [Phase 4: Hardware Assembly](#phase-4-hardware-assembly)
5. [Phase 5: ESP32 Firmware Upload](#phase-5-esp32-firmware-upload)
6. [Phase 6: Sensor Calibration](#phase-6-sensor-calibration)
7. [Phase 7: RPi Backend Setup](#phase-7-rpi-backend-setup)
8. [Phase 8: ML Model Training](#phase-8-ml-model-training)
9. [Phase 9: Testing the Full System](#phase-9-testing-the-full-system)
10. [Phase 10: Enclosure & Deployment](#phase-10-enclosure--deployment)

---

## Phase 1: Parts & Tools

### Required Parts

Check [BOM.md](./bom.md) for complete list with Shopee/Lazada links. Minimum essentials:

| Item | Qty | Estimated Cost (₱) |
|------|-----|-------------------|
| ESP32 38-pin Dev Board | 1 | ₱450 |
| ESP32 38-pin Expansion Board | 1 | ₱180 |
| YF-S201 Flow Sensor | 5 | ₱900 |
| Check Valve 1/2" | 4 | ₱480 |
| Breadboard + Jumper Wires | 1 set | ₱150 |
| USB Micro Data Cable | 1 | ₱100 |
| 5V 2A USB Power Adapter | 1 | ₱150 |
| 10kΩ Resistors | 10 | ₱20 |
| **Minimum Total** | | **~₱1,950** |

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
| **Python 3.9+** | ML training + backend | [python.org](https://www.python.org/) |
| **Git** | Version control | [git-scm.com](https://git-scm.com/) |
| **Google Chrome / Firefox** | Firebase console | — |
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
   - `Firebase ESP Client` by mobizt
   - `ArduinoJson` by bblanchon
   - `Adafruit SSD1306` by Adafruit
   - `Adafruit GFX Library` by Adafruit

### Step 2.2: Install Python

1. Download Python 3.9+ from python.org
2. **Important:** Check  **"Add Python to PATH"** during installation
3. Verify:
   ```bash
   python --version
   # Should show: Python 3.9.x or higher
   ```

### Step 2.3: Clone the Project

```bash
# Open terminal (Command Prompt or Git Bash)
git clone https://github.com/qppd/wmldad.git
cd wmldad
```

### Step 2.4: Install Python Dependencies (for ML Backend)

```bash
cd training/
pip install -r requirements.txt
# or manually:
pip install xgboost scikit-learn pandas numpy joblib flask firebase-admin
```

---

## Phase 3: Firebase Setup

### Step 3.1: Create Firebase Project

1. Go to [console.firebase.google.com](https://console.firebase.google.com/)
2. Click **Create a project**
3. Name: **water-meter-leak-detection** (or your preferred name)
4. Disable Google Analytics (optional)
5. Click **Create project**

### Step 3.2: Enable Realtime Database

1. In Firebase Console, go to **Build → Realtime Database**
2. Click **Create Database**
3. Choose location (closest to you — e.g., `asia-southeast1`)
4. Start in **test mode** (we'll secure it later)
5. Click **Enable**

### Step 3.3: Create Authentication (Email/Password)

1. Go to **Build → Authentication → Sign-in method**
2. Click **Email/Password** → **Enable** → **Save**
3. Go to **Users** tab → **Add user**
   - Email: `esp32@your-project.iam.gserviceaccount.com`
   - Password: Create a strong password
   - Click **Add user**
4. **Save these credentials** for firmware config:
   ```
   API Key (Web API Key): AIzaSy... (from Project Settings → General)
   Database URL: https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app/
   User Email: esp32@your-project.iam.gserviceaccount.com
   User Password: [the password you set]
   ```

### Step 3.4: Create Firebase Service Account

1. Go to **Project Settings → Service accounts**
2. Click **Generate new private key**
3. **Save** the downloaded JSON file as `serviceAccountKey.json`
4. This will be used by the RPi backend

### Step 3.5: Set Up Database Structure

Create initial data manually or let the ESP32 create it automatically. To verify:

1. In Firebase Console → Realtime Database → **Data** tab
2. You should see the root node. When ESP32 starts pushing, it will appear automatically.

---

## Phase 4: Hardware Assembly

### Step 4.1: Prepare the Expansion Board

The ESP32 expansion board makes wiring much easier. It provides:

- Labeled screw terminals for each GPIO pin
- Power rails (5V and 3.3V)
- Reset and BOOT buttons

### Step 4.2: Connect One Flow Sensor (Test Circuit First)

Before connecting all 5 sensors, test with just one:

```
YF-S201 Sensor          ESP32 Expansion Board
┌──────────────┐
│  Red   ──────┼────── 5V (VIN pin)
│  Black ──────┼────── GND
│  Yellow ─────┼────── GPIO 34 (via 10kΩ to 3.3V)
└──────────────┘
```

**Critical:** The yellow signal wire needs a **10kΩ pull-up resistor** connected to 3.3V:

```
GPIO 34 ──── 10kΩ resistor ──── 3.3V
         │
         └─── YF-S201 Yellow wire
```

### Step 4.3: Connect All 5 Sensors

Once the test circuit works, connect all sensors:

| Sensor | GPIO | Pull-up (10kΩ to 3.3V) |
|--------|------|------------------------|
| Inlet | 34 | Required (input-only pin) |
| Fixture 1 | 35 | Required (input-only pin) |
| Fixture 2 | 32 | Recommended |
| Fixture 3 | 33 | Recommended |
| Fixture 4 | 25 | Recommended |

### Step 4.4: Connect Peripherals

```
OLED:
  SDA → GPIO 21
  SCL → GPIO 22
  VCC → 3.3V
  GND → GND

Buzzer (Active):
  Positive → GPIO 4
  Negative → GND (via 100Ω resistor optional)

RGB LED (optional):
  Red → GPIO 5 (via driver)
  Green → GPIO 18 (via driver)
  Blue → GPIO 19 (via driver)
  Common → GND
```

### Step 4.5: Plumbing Setup

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

## Phase 5: ESP32 Firmware Upload

### Step 5.1: Configure Firmware

1. Open `src/config.example.h` in any text editor
2. Create `src/config.h` (copy the example)
3. Fill in your credentials:

```cpp
// === WiFi ===
#define WIFI_SSID        "YOUR_WIFI_NAME"
#define WIFI_PASSWORD    "YOUR_WIFI_PASSWORD"

// === Firebase ===
#define FIREBASE_API_KEY       "AIzaSy..."  // From Firebase Project Settings
#define FIREBASE_DATABASE_URL  "https://your-project.asia-southeast1.firebasedatabase.app"
#define FIREBASE_USER_EMAIL    "esp32@your-project.iam.gserviceaccount.com"
#define FIREBASE_USER_PASSWORD "your-password"
#define DEVICE_ID              "wm_001"
```

### Step 5.2: Upload Firmware

1. Connect ESP32 via USB cable
2. In Arduino IDE, select your board:
   - **Tools -> Board -> ESP32 Arduino -> NodeMCU-32S**
3. Select the correct port:
   - **Tools -> Port -> COMx** (check Windows Device Manager for the COM port)
4. Click **Sketch -> Verify/Compile** (Ctrl+R) to check for errors
5. Click **Sketch -> Upload** (Ctrl+U) to flash the ESP32
6. If upload fails:
   - Hold **BOOT** button on ESP32
   - Press **EN** (reset) while holding BOOT
   - Release EN, then release BOOT
   - Click Upload again

### Step 5.3: Monitor Serial Output

1. Open **Tools -> Serial Monitor** (Ctrl+Shift+M)
2. Set baud rate to **115200** (bottom-right of Serial Monitor window)
3. You should see:
   ```
   Connecting to WiFi...
   WiFi connected! IP: 192.168.1.100
   Firebase initialized successfully
   Starting stream on: /commands/wm_001
   Sensor 0 (inlet): ISR attached on GPIO 34
   Sensor 1 (fix1): ISR attached on GPIO 35
   Sensor 2 (fix2): ISR attached on GPIO 32
   ...
   Reading: inlet=0.00 L/min fix1=0.00 L/min fix2=0.00 L/min fix3=0.00 L/min fix4=0.00 L/min
   Data uploaded to Firebase
   ```

### Step 5.4: Check Firebase

1. Go to Firebase Console → Realtime Database
2. You should see data appearing under `/readings/wm_001/`

---

## Phase 6: Sensor Calibration

> Detailed procedure: [Calibration Guide](./calibration.md)

### Quick Calibration (Bucket Test)

1. **Prepare:** Get a 5L graduated container
2. **Connect:** Run water from faucet through the inlet sensor into the container
3. **Open:** Turn on faucet at medium flow
4. **Collect:** Exactly 5 liters
5. **Read:** Get pulse count from Serial Monitor (command: `status`)
6. **Calculate:**
   ```
   Actual PPL = Total Pulse Count ÷ 5
   ```
7. **Update:** Change `PULSE_PER_LITER` in `config.h`
8. **Repeat** for each sensor

---

## Phase 7: RPi Backend Setup

> **Detailed guide:** [RPi Backend App](./rpi-backend.md)

### Quick Setup

1. **Get a Raspberry Pi 3B+/4/5** with Raspberry Pi OS (64-bit)
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
5. **Upload Firebase service account key** (`serviceAccountKey.json`) to the RPi
6. **Run the Flask app:**
   ```bash
   python app.py
   ```
7. **Test:** Open a browser and visit `http://<rpi-ip>:5000/`
8. **Set up auto-start** (optional):
   ```bash
   sudo cp water-meter.service /etc/systemd/system/
   sudo systemctl enable water-meter.service
   sudo systemctl start water-meter.service
   ```

> See [RPi Backend App](./rpi-backend.md) for complete setup instructions, systemd service config, and remote access setup.

---

## Phase 8: ML Model Training

> Complete details: [ML Model](./ml-model.md)

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
# (they appear as xgboost_leak_model.json, isolation_forest.pkl, scaler.pkl)

# From Jupyter (local):
cp training/xgboost_leak_model.json rpi/models/
cp training/isolation_forest.pkl rpi/models/
cp training/scaler.pkl rpi/models/
```

---

## Phase 9: Testing the Full System

### Test 1: ESP32 → Firebase

1. Turn water on through a fixture
2. Check Firebase Console → Data tab → `/readings/wm_001/`
3. Readings should update every 5 seconds
4. Verify flow rate changes when you open/close faucets

### Test 2: Firebase → RPi

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
4. Check Firebase `/alerts/` path

### Test 4: Command Flow

1. In Firebase Console, write to `/commands/wm_001/cmd_test`:
   ```json
   {
     "command": "calibrate",
     "source": "test"
   }
   ```
2. ESP32 should respond by entering calibration mode
3. OLED should show calibration status

### Test 5: Offline Mode

1. Disconnect WiFi from router
2. ESP32 should continue logging to SD card
3. Readings should buffer locally
4. When WiFi reconnects, data should sync to Firebase

---

## Phase 10: Enclosure & Deployment

### Permanent Wiring

1. Solder components to perf board (instead of breadboard)
2. Mount expansion board inside ABS enclosure
3. Use cable glands for water sensor cables
4. Label all wires

### Final Calibration

1. Install sensors in actual plumbing
2. Perform bucket test on each sensor
3. Update k-factor values in Firebase config
4. Verify total consumption matches water bill

### Monitoring

1. Set up dashboard as home page
2. Configure Telegram bot for mobile alerts
3. Set up a cron job on RPi for daily model retraining
4. Check Firebase usage dashboard monthly

---

## Quick Reference: Common Commands

```bash
# Arduino IDE: Verify/Compile
#   Sketch -> Verify/Compile  (Ctrl+R)

# Arduino IDE: Upload to ESP32
#   Sketch -> Upload  (Ctrl+U)

# Arduino IDE: Serial Monitor
#   Tools -> Serial Monitor  (Ctrl+Shift+M)  @ 115200 baud

# Train ML model (Google Colab)
#   Open training/water_meter_ml_training.ipynb
#   Runtime -> Run all

# Train ML model (Jupyter Notebook)
cd training/
jupyter notebook water_meter_ml_training.ipynb

# Run Flask app locally
cd rpi/ && python app.py

# View RPi logs
# Web tab -> Logs -> view server/error log

# Firebase backup (via CLI)
firebase database:get /readings > backup.json
```