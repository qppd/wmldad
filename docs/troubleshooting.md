# Troubleshooting Guide

> Complete guide for diagnosing and fixing issues with the Water Meter + Leak Detection system.

---

## 1. ESP32 Hardware Issues

### No Power / No Lights

| Cause | Check | Fix |
|-------|-------|-----|
| USB cable is charge-only | Try a known good data cable | Use cable rated for data transfer |
| Wrong USB port | Device Manager → Ports | Use USB 2.0 or 3.0 port directly on computer |
| ESP32 damaged | Check 3.3V pin with multimeter | Replace ESP32 |
| Expansion board short | Check for solder bridges | Remove expansion board, test ESP32 alone |

### No Serial Output

| Cause | Check | Fix |
|-------|-------|-----|
| Wrong COM port | Device Manager → Ports | Select correct COM port |
| Baud rate mismatch | Set to 115200 | In Serial Monitor, set baud to 115200 |
| Driver missing | Device Manager → yellow exclamation | Install [CP210x](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) or CH340 driver |
| Board not in flash mode | Hold BOOT while connecting USB | Hold BOOT → press EN → release BOOT |

### ESP32 Crashes / Reboot Loops

```cpp
// Add this to setup() to diagnose
Serial.println("Free heap: " + String(ESP.getFreeHeap()));
Serial.println("Reset reason: " + String(esp_reset_reason()));
```

| Symptom | Cause | Fix |
|---------|-------|-----|
| Brownout detector triggered | Unstable power supply | Use ≥2A adapter, add 1000µF capacitor |
| Guru Meditation Error | Stack overflow / memory issue | Reduce buffer sizes, add `yield()` in loops |
| Watchdog reset | Task blocking > 5 seconds | Add `delay(0)` or `yield()` |
| WiFi disconnect loop | Weak signal | Move router closer, add antenna |
| Flash corruption | Power loss during write | Use `SPIFFS.format()` in setup |

---

## 2. Flow Sensor Issues

### No Pulse Reading

| Cause | Check | Fix |
|-------|-------|-----|
| Wrong GPIO pin | Verify `SENSOR_PINS[]` in config.h | Match config to actual wiring |
| Loose connection | Inspect jumper wires | Push firmly or re-seat |
| Sensor not powered | Measure VCC pin | Should be 4.5V–5V |
| Arrow wrong direction | Arrow on sensor body | Install with flow direction |
| Air trapped | Bubbles in sensor chamber | Tap sensor, purge air |
| Pull-up resistor missing | GPIO 34/35 are input-only | Add 10kΩ to 3.3V |
| Debounce too high | Pulses < 5ms apart missed | Reduce `DEBOUNCE_MS` to 3 |
| Flow too slow | Minimum ~0.5 L/min | Increase flow rate |

**Quick test:** Connect sensor OUT directly to 3.3V momentarily. If Serial Monitor shows pulses, ESP32 is OK — problem is with sensor or water flow.

### Wrong Volume Readings

| Symptom | Likely K-factor | Fix |
|---------|----------------|------|
| Reading too high (overcounts) | PPL too low | Increase `PULSE_PER_LITER` |
| Reading too low (undercounts) | PPL too high | Decrease `PULSE_PER_LITER` |
| Inconsistent readings | Air / turbulent flow | Add straight pipe before sensor |
| Drifts over time | Temperature change | Re-calibrate seasonally |
| Zero when water flows | Interrupt not firing | Check `pinMode()`, try `INPUT_PULLUP` |

### Fixture Balance Error

If sum of 4 fixtures doesn't match inlet reading:

```
Inlet balance = Inlet volume - (Fixture 1 + 2 + 3 + 4)
Normal: balance < 10% of inlet
```

| Balance | Meaning | Action |
|---------|---------|--------|
| < 10% | Normal | No action needed |
| 10–20% | Leak suspected | Investigate fixtures |
| > 20% | Hidden leak or sensor fault | Check all connections |

---

## 3. WiFi Issues

| Symptom | Check | Fix |
|---------|-------|-----|
| "Connecting..." timeout | SSID/password correct? | Double-check in `config.h` |
| Intermittent drops | Signal strength | Check RSSI: > -65 dBm is good |
| Router not showing device | ESP32 in deep sleep? | Wake by sending serial data |
| Wrong IP address | DHCP conflict | Set static IP in config |

**Signal strength:**

| RSSI | Quality |
|------|---------|
| > -50 dBm | Excellent |
| -51 to -65 dBm | Good |
| -66 to -75 dBm | Fair |
| < -75 dBm | Poor — move router closer |

---

## 4. Firebase Issues

### ESP32 → Firebase

| Error | Cause | Fix |
|-------|-------|-----|
| "Firebase not ready" | Auth not complete | Check `Firebase.begin()` response |
| "401 Unauthorized" | Wrong API key or email/password | Verify in Firebase Console |
| "Firebase database URL is not set" | Missing URL in config | Copy from Firebase Console → Realtime DB |
| "Connection timed out" | Network issue | Check WiFi, try pinging database URL |
| Token generation failed | Auth provider not enabled | Enable Email/Password in Firebase Auth |
| PushJSON returned error | Payload too large | Reduce data per push (limit to ~16KB) |
| Stream not receiving | Permission denied | Check security rules |

### RPi → Firebase

| Error | Cause | Fix |
|-------|-------|-----|
| firebase-admin ImportError | Not installed | `pip install firebase-admin` |
| "Invalid service account" | Wrong JSON key | Re-download from Firebase Console |
| Stream not working | firebase-admin uses polling | Poll `/readings/` every 5s instead |
| "403 Forbidden" | Security rules blocking | Check rules in Firebase Console |
| Rate limited | Too many connections | Reduce polling frequency |

---

## 5. ML Model Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| All predictions are "normal" | Model not trained / loaded | Check model file exists |
| Too many false positives | Threshold too low | Increase `confidence_threshold` to 0.85 |
| Misses all leaks | Training data doesn't include leaks | Add leak samples, retrain |
| XGBoost error on import | Wrong version | `pip install xgboost==2.0.0` |
| Isolation Forest always says anomaly | `contamination` too high | Reduce to 0.01 or lower |
| Model takes too long | Too many trees | Reduce `n_estimators` to 100 |
| NaN in features | Division by zero | Add `max(rate, 0.01)` guard |

### Model Evaluation Commands

```python
# On RPi or local
from ml_inference import LeakDetector
detector = LeakDetector()
print(f"Model loaded: {detector.model_loaded}")
print(f"Feature count: {detector.n_features}")

# Test a normal reading
import numpy as np
normal_features = np.array([2.5, 30, 14, 2, 0, 1.1, 0.5, 0, 0.1])
result = detector.predict(normal_features)
print(result)
```

---

## 6. RPi (Raspberry Pi) Issues

| Problem | Solution |
|---------|----------|
| **App not loading** | Check Flask output: `journalctl -u water-meter.service -f` |
| **"Internal Server Error"** | View Flask error log: `sudo journalctl -u water-meter.service --since "5 min ago"` |
| **Module not found** | Activate venv → `pip install -r requirements.txt` |
| **Memory error** | RPi 4 has 2-8GB RAM — check `free -h`. Reduce `n_estimators` in XGBoost if needed. |
| **RPi not reachable** | Check network: `ping <rpi-ip>`. Ensure port 5000 is not blocked by firewall |
| **RPi auto-start not working** | Check systemd: `sudo systemctl status water-meter.service` |
| **SD card corruption** | Use a UPS and `sudo raspi-config` → Performance → Overlay File System for read-only root |

---

## 7. Plumbing / Mechanical Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| Water hammer | Fast valve closing | Install water hammer arrestor |
| Sensor not spinning | Debris in turbine | Remove and clean with soft brush |
| Check valve stuck | Debris or hard water | Disassemble and clean |

---

## 8. Diagnostic Commands (Serial Monitor)

| Command | Response | Use Case |
|---------|----------|----------|
| `status` | All sensor readings + device state | Quick health check |
| `sensors` | Raw pulse counts per sensor | Debug ISR issues |
| `config` | Current configuration | Verify settings |
| `wifi` | WiFi status + IP + RSSI | Network troubleshooting |
| `firebase` | Firebase connection status | Check cloud connectivity |
| `queue` | Number of readings pending upload | See if buffer is growing |
| `calibrate` | Start calibration mode | For bucket test |
| `reset` | Reboot ESP32 | Quick restart |
| `format` | Format SPIFFS storage | Clear corrupted data |
| `heap` | Free heap memory | Check for memory leaks |
| `uptime` | Device uptime in seconds | Know when last rebooted |

---

## 9. LED Indicator Reference

| LED Pattern | Meaning |
|-------------|---------|
| Solid green | Normal operation, all OK |
| Blink green (1s) | WiFi connecting |
| Blink blue (fast) | Transmitting data to Firebase |
| Solid yellow | Minor leak detected (alert) |
| Solid red | Major leak detected (critical) |
| Red flash | Emergency — urgent action needed |
| Blink white (3x + pause) | Successful data upload |
| Blink red (5x + pause) | Upload failed / Firebase error |
| Off | Deep sleep or no power |

---

## 10. Checklist Before Panicking

- [ ] Is ESP32 getting power? (LED on?)
- [ ] Is USB cable a data cable? (not charge-only)
- [ ] Is Serial Monitor baud set to 115200?
- [ ] Are pull-up resistors installed on GPIO 34 & 35?
- [ ] Is the flow sensor arrow pointing WITH the water flow?
- [ ] Are WiFi SSID and password correct?
- [ ] Is Firebase Auth (Email/Password) enabled?
- [ ] Is the Firebase service account key on the RPi?
- [ ] Is the virtual environment activated?
- [ ] Did you run `pip install -r requirements.txt`?
- [ ] Are the ML model files in the right path?
- [ ] Is `PULSE_PER_LITER` calibrated for each sensor?