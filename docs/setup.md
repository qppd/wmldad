# Setup Guide

## Prerequisites

- ESP32 development board
- Water flow sensor (YF-S201 or equivalent)
- USB cable (micro USB)
- 5V power adapter
- Jumper wires
- Computer with Windows / macOS / Linux

---

## 1. Hardware Setup

### Wiring

| Flow Sensor | ESP32 Pin |
|-------------|-----------|
| Red (VCC)   | 5V (VIN)  |
| Black (GND) | GND       |
| Yellow (OUT)| GPIO 34   |

> **Note:** Some sensors require a 10kΩ pull-up resistor on the signal line to 3.3V or 5V. Check your sensor datasheet.

### Power

- **Option A:** USB power from a phone charger (5V / 1A minimum)
- **Option B:** 5V adapter connected to VIN pin
- **Option C:** Battery with voltage regulator (for remote installations)

---

## 2. Software Setup

### Option A: Arduino IDE

1. Download and install [Arduino IDE](https://www.arduino.cc/en/software)
2. Add ESP32 board support:
   - File → Preferences → Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools → Board → Board Manager → Search "ESP32" → Install
3. Select your board: Tools → Board → ESP32 Dev Module
4. Select the correct COM port

### Option B: PlatformIO (Recommended)

1. Install [VS Code](https://code.visualstudio.com/)
2. Install [PlatformIO Extension](https://platformio.org/install)
3. Clone or download this project
4. Open the project folder in VS Code
5. PlatformIO will auto-detect and install dependencies

```bash
git clone https://github.com/qppd/water-meter.git
cd water-meter
code .
```

### Required Libraries

Install these via Library Manager (Arduino IDE) or platformio.ini (PlatformIO):

| Library           | Version | Purpose              |
|-------------------|---------|----------------------|
| ArduinoJson       | ≥ 6.x   | JSON serialization   |
| PubSubClient      | ≥ 2.8   | MQTT communication   |
| WiFiManager       | ≥ 2.0   | WiFi configuration   |
| NTPClient         | ≥ 3.2   | Time synchronization |

---

## 3. Configuration

Create a copy of `config.example.h` as `config.h` and fill in:

```cpp
// WiFi
#define WIFI_SSID     "YourWiFiName"
#define WIFI_PASSWORD "YourWiFiPassword"

// Server
#define SERVER_URL    "http://your-server.com/api/v1"
#define API_KEY       "your-api-key-here"

// Sensor
#define FLOW_SENSOR_PIN  34
#define PULSE_PER_LITER  450   // Calibration value

// Timing
#define READ_INTERVAL_MS   60000    // 1 minute
#define UPLOAD_INTERVAL_MS 300000   // 5 minutes
```

---

## 4. Upload Firmware

1. Connect ESP32 via USB
2. Select the correct COM port and board
3. Click **Upload** (→ button)
4. Wait for "Connecting..." then "Done uploading"
5. Open Serial Monitor (Tools → Serial Monitor, 115200 baud)

---

## 5. Verify Operation

After upload, the Serial Monitor should show:

```
Connecting to WiFi...
WiFi connected! IP: 192.168.1.100
Flow sensor initialized on GPIO 34
Reading: 0.00 L/min | Total: 0.00 L
Reading: 0.00 L/min | Total: 0.00 L
--- Water detected! ---
Reading: 5.20 L/min | Total: 0.85 L
```

Run some water through the sensor and confirm readings appear.

---

## 6. Backend Setup (Optional)

### Quick Start with Docker

```bash
docker run -d \
  --name water-meter-api \
  -p 3000:3000 \
  -e DB_CONNECTION=sqlite:///data/db.sqlite \
  -v ./data:/data \
  yourusername/water-meter-api:latest
```

### Manual Setup

1. Install Node.js ≥ 18 or Python ≥ 3.9
2. Install dependencies
3. Configure database connection
4. Start the server

---

## Troubleshooting

| Problem                  | Solution                              |
|--------------------------|---------------------------------------|
| No serial output         | Check USB cable, COM port, baud rate  |
| WiFi not connecting      | Check SSID/password, router range     |
| No pulse reading         | Verify wiring, sensor voltage         |
| Wrong volume             | Re-calibrate `PULSE_PER_LITER` value  |
| Server returns 401       | Check API key in config.h             |
