# Troubleshooting Guide

## No Power / No Serial Output

| Possible Cause        | Solution                                        |
|-----------------------|--------------------------------------------------|
| USB cable is charge-only | Use a data-capable USB cable                   |
| Wrong COM port selected | Check Device Manager for correct port          |
| Baud rate mismatch    | Set Serial Monitor to **115200 baud**            |
| Board not in flash mode | Hold BOOT button while connecting USB          |
| Driver missing        | Install [CP210x](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) or CH340 driver |
| ESP32 damaged         | Check 3.3V pin voltage with multimeter           |

---

## WiFi Connection Issues

| Symptom                      | Solution                                        |
|------------------------------|-------------------------------------------------|
| "Connecting..." timeout      | Check SSID and password in `config.h`           |
| Intermittent disconnection   | Move ESP32 closer to router                     |
| Wrong IP address             | Set static IP or check DHCP range               |
| Router not showing device    | ESP32 may be in deep sleep — wake it up         |
| WiFiManager portal won't open| Scan for "WaterMeter-AP" SSID on your phone     |

**Signal strength guide:**

| RSSI       | Quality  |
|------------|----------|
| > -50 dBm  | Excellent|
| -51 to -65 | Good     |
| -66 to -75 | Fair     |
| < -75 dBm  | Poor     |

---

## No Pulse / Sensor Not Reading

| Possible Cause          | Solution                                     |
|-------------------------|----------------------------------------------|
| Wrong GPIO pin          | Verify `FLOW_SENSOR_PIN` matches wiring      |
| Loose connection        | Check jumper wires, push firmly              |
| Sensor not powered      | Measure VCC pin — should be 4.5V – 5V       |
| Air in sensor           | Tap gently or let water flow to purge air    |
| Flow too low            | Minimum flow rate: ~0.5 L/min               |
| Sensor orientation wrong| Arrow on sensor should point with flow       |
| Debounce too aggressive | Check `DEBOUNCE_MS` — try reducing to 3ms    |

**Quick test:** Connect sensor OUT pin directly to 3.3V momentarily. If Serial Monitor shows pulses, the ESP32 is working — problem is with the sensor or flow.

---

## Wrong Volume Readings

| Issue                 | Likely Cause           | Fix                                     |
|-----------------------|------------------------|-----------------------------------------|
| Reading too high      | K-factor too low       | Increase `PULSE_PER_LITER`              |
| Reading too low       | K-factor too high      | Decrease `PULSE_PER_LITER`              |
| Inconsistent readings | Air bubbles / turbulent | Add a straight pipe section before sensor|
| Drifts over time      | Temperature change     | Re-calibrate at operating temperature   |
| Zero when water flows | Interrupt not firing   | Check `pinMode()` setting               |

---

## Server / Upload Failures

| Error              | Cause                          | Solution                          |
|--------------------|--------------------------------|-----------------------------------|
| `401 Unauthorized` | Invalid API key                | Check `API_KEY` in config          |
| `404 Not Found`    | Wrong endpoint URL             | Verify `SERVER_URL`                |
| `Connection refused`| Server is offline              | Check server status                |
| `Timeout`          | Network issue / slow server    | Increase timeout, check connection  |
| Empty response     | Server error                   | Check server logs                  |

### Data Queue Backup

If the server is unreachable, readings are stored locally in SPIFFS. To check:

```cpp
// In Serial Monitor:
// Look for: "Queue size: X readings pending"
// If growing, server connection is broken
```

**Clearing stale data:**
- Via command: publish `{"command": "clear_buffer"}` to command topic
- Via hardware: hold the reset button for 10 seconds

---

## MQTT Issues

| Symptom                  | Solution                                 |
|--------------------------|------------------------------------------|
| Cannot connect to broker | Check broker address and port (1883/8883) |
| "Connection refused"     | MQTT broker not running                  |
| No data published        | Check topic name case-sensitivity        |
| Cert errors (TLS)        | Update CA certificate                    |

---

## ESP32 Crashes / Reboot Loops

1. **Check power** — brownouts cause reboots. Use a stable 5V supply (≥1A).
2. **Disable WiFi** temporarily — if stable, it's a WiFi issue.
3. **Watchdog timeout** — long operations blocking the loop:
   ```cpp
   // Add yield() or delay(0) in long loops
   ```
4. **Stack overflow** — move large buffers to global scope or use `static`
5. **Serial Monitor garbage** — baud rate mismatch or bad USB connection

---

## LED Indicator Reference

| LED Pattern               | Meaning                   |
|---------------------------|---------------------------|
| Solid on                  | Powered, sensor ready     |
| Blink slow (1s)           | WiFi connecting           |
| Blink fast (200ms)        | Transmitting data         |
| Blink 3x then pause       | Successful upload         |
| Blink 5x then pause       | Upload failed             |
| Off                       | Deep sleep or no power    |

---

## Diagnostic Commands

On Serial Monitor (115200 baud):

| Command      | Response                  |
|--------------|---------------------------|
| `status`     | Device status + readings  |
| `reset`      | Reboot ESP32              |
| `config`     | Print current config      |
| `queue`      | Show pending uploads      |
| `calibrate`  | Start calibration mode    |
| `wifi`       | Show WiFi signal + IP     |
| `format`     | Format SPIFFS storage     |

---

## Still Stuck?

1. Enable verbose debug logging in `config.h`:
   ```cpp
   #define DEBUG true
   ```
2. Capture the full Serial Monitor log
3. Open a GitHub issue with:
   - ESP32 board model
   - Sensor model
   - Config settings (redact API keys)
   - Full serial output from boot to failure
