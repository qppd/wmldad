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
7. [Phase 7: PythonAnywhere Backend](#phase-7-pythonanywhere-backend)
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
| **VS Code** | Code editor | [code.visualstudio.com](https://code.visualstudio.com/) |
| **Arduino IDE 2.x** | ESP32 build & upload, Serial Monitor | [arduino.cc](https://www.arduino.cc/en/software) |
| **Python 3.9+** | ML training + backend | [python.org](https://www.python.org/) |
| **Git** | Version control | [git-scm.com](https://git-scm.com/) |
| **Google Chrome / Firefox** | Firebase console | — |
| **PythonAnywhere Account** | Cloud hosting | [pythonanywhere.com](https://www.pythonanywhere.com/) |

---

## Phase 2: Software Installation

### Step 2.1: Install VS Code + Arduino IDE

1. Download and install VS Code
2. Open VS Code → Extensions (Ctrl+Shift+X)
3. Search **"Arduino IDE IDE"** → Install
4. Wait for installation (Arduino IDE downloads toolchains — may take 5–10 min)
5. Restart VS Code

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
git clone https://github.com/qppd/water-meter.git
cd water-meter

# Open in VS Code
code .
```

### Step 2.4: Install Python Dependencies

```bash
cd training/
pip install -r requirements.txt
# or manually:
pip install xgboost scikit-learn pandas numpy joblib flask pyrebase4
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

### Step 3.4: Create Service Account for PythonAnywhere

1. Go to **Project Settings → Service accounts**
2. Click **Generate new private key**
3. **Save** the downloaded JSON file as `serviceAccountKey.json`
4. This will be used by the PythonAnywhere backend

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
| Inlet | 34 |  Required (input-only pin) |
| Fixture 1 | 35 |  Required (input-only pin) |
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

Relay Module (for solenoid valves):
  VCC → 5V
  GND → GND
  IN1 → GPIO 26 (Inlet valve)
  IN2 → GPIO 27 (Fixture 1 valve)
  IN3 → GPIO 14 (Fixture 2 valve)
  IN4 → GPIO 12 (Fixture 3 valve — boot pin!)
  IN5 → GPIO 13 (Fixture 4 valve — if 5-ch relay)
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

1. In VS Code, open `src/config.example.h`
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
2. In VS Code, click the **Arduino IDE icon** (alien head in sidebar)
3. Click **Build** ( checkmark) or press Ctrl+Alt+B
4. Wait for compilation to finish
5. Click **Upload** (→ arrow) or press Ctrl+Alt+U
6. If upload fails:
   - Hold **BOOT** button on ESP32
   - Press **EN** (reset) while holding BOOT
   - Release EN, then release BOOT
   - Click Upload again

### Step 5.3: Monitor Serial Output

1. Click the **Serial Monitor** plug icon in Arduino IDE (or Ctrl+Alt+M)
2. Set baud rate to **115200**
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

## Phase 7: PythonAnywhere Backend

> Detailed guide: [PythonAnywhere App](./pythonanywhere-app.md)

### Quick Deploy

1. **Log in** to [pythonanywhere.com](https://www.pythonanywhere.com/)
2. **Open a Bash console**
3. **Upload project files:**
   ```bash
   git clone https://github.com/qppd/water-meter.git
   cd water-meter/pythonanywhere/
   ```
4. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. **Upload Firebase service account key** (`serviceAccountKey.json`)
6. **Configure Flask app:**
   - Go to **Web tab → Add a new web app**
   - Select **Flask** → Python 3.9
   - Set source code: `/home/youruser/water-meter/pythonanywhere/`
   - Set WSGI file: click and edit to point to `app.py`
7. **Reload web app**
8. **Test:** Visit `https://youruser.pythonanywhere.com/`

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

Move trained models to PythonAnywhere (after training in Colab/Jupyter):
```bash
# From Google Colab: download model files from the Files tab
# (they appear as xgboost_leak_model.json, isolation_forest.pkl, scaler.pkl)

# From Jupyter (local):
cp training/xgboost_leak_model.json pythonanywhere/models/
cp training/isolation_forest.pkl pythonanywhere/models/
cp training/scaler.pkl pythonanywhere/models/
```

---

## Phase 9: Testing the Full System

### Test 1: ESP32 → Firebase

1. Turn water on through a fixture
2. Check Firebase Console → Data tab → `/readings/wm_001/`
3. Readings should update every 5 seconds
4. Verify flow rate changes when you open/close faucets

### Test 2: Firebase → PythonAnywhere

1. Open your PythonAnywhere web app
2. Click Dashboard → should show latest readings
3. Check PythonAnywhere console logs:
   ```bash
   tail -f /var/log/youruser.pythonanywhere.com.access.log
   ```

### Test 3: ML Leak Detection

1. Simulate a **minor leak**: partially open a valve to produce 0.1–0.5 L/min
2. Wait 30+ seconds
3. Check if an alert appears on the dashboard
4. Check Firebase `/alerts/` path

### Test 4: Remote Valve Control

1. In Firebase Console, write to `/commands/wm_001/cmd_test`:
   ```json
   {
     "command": "close_fix1",
     "source": "test"
   }
   ```
2. ESP32 should respond by activating the relay
3. (If solenoid valve installed) Valve should close
4. Valve state should update on the OLED display

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
3. Set PythonAnywhere task scheduler for daily model retraining
4. Check Firebase usage dashboard monthly

---

## Quick Reference: Common Commands

```bash
# Arduino IDE build
Compile in Arduino IDE (Sketch -> Verify/Compile)

# Arduino IDE upload
Compile in Arduino IDE (Sketch -> Verify/Compile) --target upload

# Arduino IDE monitor
Open Serial Monitor (Tools -> Serial Monitor, 115200 baud)

# Train ML model
Run the `water_meter_ml_training.ipynb` notebook
in Google Colab or Jupyter Notebook

# Run Flask app locally
cd pythonanywhere/ && python app.py

# View PythonAnywhere logs
# Web tab → Logs → view server/error log

# Firebase backup (via CLI)
firebase database:get /readings > backup.json
```
