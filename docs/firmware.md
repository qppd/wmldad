# Firmware Architecture

## File Structure

```
water-meter/
├── src/
│   ├── main.cpp              # Entry point, setup() and loop()
│   ├── config.h              # User configuration (WiFi, pins, interval)
│   ├── config.example.h      # Template configuration file
│   ├── wifi_manager.h        # WiFi connection handler
│   ├── flow_sensor.h         # Pulse counter and flow calculation
│   ├── mqtt_client.h         # MQTT publish / subscribe
│   ├── http_client.h         # HTTP REST client
│   ├── data_logger.h         # Local storage (SPIFFS)
│   ├── ntp_sync.h            # NTP time synchronization
│   └── led_indicator.h       # Status LED feedback
├── platformio.ini            # PlatformIO project config
└── README.md
```

---

## Main Loop Flow

```
loop()
├── Read flow sensor pulse count
├── Calculate flow rate (L/min) and volume (L)
├── Update total cumulative volume
├── Check if read interval reached?
│   └── Log reading to local buffer
├── Check if upload interval reached?
│   ├── Build JSON payload
│   ├── Connect to server (HTTP/MQTT)
│   ├── Send data
│   └── On success → clear buffer
│   └── On failure → queue for retry
├── Check for commands (MQTT subscribe)
├── Update status LED
└── Deep sleep (battery mode) → wake on interrupt
```

---

## Key Modules

### `flow_sensor.h` — Pulse Counter

```cpp
// Uses hardware interrupt on GPIO pin
// ISR increments pulse counter on rising edge
// Debounce guard: ignore pulses < 5ms apart

void IRAM_ATTR pulseCounter() {
    if (millis() - lastPulseTime > DEBOUNCE_MS) {
        pulseCount++;
        lastPulseTime = millis();
    }
}
```

**Formula:**
```
Flow Rate (L/min) = (Pulse Count × 60) ÷ (Pulse per Liter × Interval Seconds)
Volume (L)        = Pulse Count ÷ Pulse per Liter
```

### `wifi_manager.h` — Connectivity

- Station mode connection to existing WiFi
- Auto-reconnect on disconnect
- Configurable static IP or DHCP
- Optional WiFiManager portal for first-time setup

### `data_logger.h` — Local Storage

- Uses SPIFFS for persistent storage
- JSON file per day or single rolling file
- Automatic cleanup when storage > 90% full

### `mqtt_client.h` — Real-time Data

- Publish readings topic: `water-meter/{device_id}/reading`
- Subscribe command topic: `water-meter/{device_id}/cmd`
- Available commands: `reset`, `calibrate`, `interval`, `reboot`

---

## Configuration (`config.h`)

| Parameter          | Default    | Description                     |
|--------------------|------------|---------------------------------|
| `WIFI_SSID`        | —          | WiFi network name               |
| `WIFI_PASSWORD`    | —          | WiFi password                   |
| `FLOW_SENSOR_PIN`  | 34         | GPIO pin for sensor signal      |
| `PULSE_PER_LITER`  | 450        | Sensor calibration factor       |
| `READ_INTERVAL_MS` | 60000      | Read sensor every N ms          |
| `UPLOAD_INTERVAL`  | 300000     | Upload data every N ms          |
| `SERVER_URL`       | —          | Backend API endpoint            |
| `MQTT_BROKER`      | —          | MQTT broker address             |
| `DEEP_SLEEP_SEC`   | 0          | Seconds in deep sleep (0=disabled) |

---

## Power Modes

| Mode        | Consumption     | Use Case                     |
|-------------|-----------------|------------------------------|
| Active      | ~80 mA          | Reading + uploading          |
| Light Sleep | ~10 mA          | Idle between intervals       |
| Deep Sleep  | ~10 µA          | Battery-powered (wake on RTC)|

---

## Build Instructions

### PlatformIO

```bash
# Install dependencies
pio pkg install

# Build
pio run

# Upload to board
pio run --target upload

# Monitor serial output
pio device monitor --baud 115200
```

### Arduino IDE

1. Open `main.cpp`
2. Install required libraries (see `setup.md`)
3. Select board: **ESP32 Dev Module**
4. Click **Upload**
