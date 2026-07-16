# Troubleshooting Guide

> Complete guide for diagnosing and fixing issues with the Water Meter + Leak Detection system (ESP32 → USB Serial → RPi).

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
| Baud rate mismatch | Set to 921600 | In Serial Monitor, set baud to 921600 |
| Driver missing | Device Manager → yellow exclamation | Install [CP210x](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) or CH340 driver |
| Board not in flash mode | Hold BOOT → press EN → release BOOT | Hold BOOT → press EN → release BOOT → Upload |

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
| Loose connection | Inspect connections | Push firmly or re-seat |
| Sensor not powered | Measure VCC pin | Should be 4.5V–5V |
| Arrow wrong direction | Arrow on sensor body | Install with flow direction |
| Air trapped | Bubbles in sensor chamber | Tap sensor, purge air |
| Debounce too high | Pulses < 5ms apart missed | Reduce `DEBOUNCE_MS` to 3 |
| Flow too slow | Minimum ~0.5 L/min | Increase flow rate |

**Quick test:** Connect sensor OUT directly to 3.3V momentarily. If Serial Monitor shows pulses, ESP32 is OK — problem is sensor or water flow.

### Wrong Volume Readings

| Symptom | Likely K-factor | Fix |
|---------|----------------|-----|
| Reading too high (overcounts) | PPL too low | Increase `PULSE_PER_LITER` |
| Reading too low (undercounts) | PPL too high | Decrease `PULSE_PER_LITER` |
| Inconsistent readings | Air / turbulent flow | Add straight pipe before sensor |
| Drifts over time | Temperature change | Re-calibrate seasonally |

### Fixture Balance Error

```
Inlet balance = Inlet volume - (Fixture 1 + 2 + 3)
Normal: balance < 10% of inlet
```

| Balance | Meaning | Action |
|---------|---------|--------|
| < 10% | Normal | No action needed |
| 10–20% | Leak suspected | Investigate fixtures |
| > 20% | Hidden leak or sensor fault | Check all connections |

---

## 3. USB Serial Issues

### ESP32 Not Detected on RPi

```bash
# Check if device appears
ls /dev/ttyUSB*
ls /dev/ttyACM*

# Check kernel messages
dmesg | grep -i usb
```

| Issue | Fix |
|-------|-----|
| No `/dev/ttyUSB*` | Use data cable, not charge-only |
| Permission denied | `sudo usermod -a -G dialout $USER && newgrp dialout` |
| Wrong VID:PID | Check `lsusb` — should show `10c4:ea60` (CP2102) or `1a86:7523` (CH340) |
| Multiple devices | Use udev rule for persistent `/dev/ttyESP32` symlink |

### Serial Connection Drops

```python
# Test connection
python3 -c "
from serial_port import find_esp32_port, get_serial_connection
port = find_esp32_port()
print(f'Port: {port}')
ser = get_serial_connection()
print('Connected!')
for _ in range(3):
    print(ser.readline().decode().strip())
"
```

| Symptom | Cause | Fix |
|---------|-------|-----|
| Random disconnects | Loose USB cable | Secure cable, use strain relief |
| `SerialException` on read | ESP32 reset | Handle reconnect in reader (auto-reconnect built-in) |
| Garbage characters | Baud mismatch | Both sides must use **921600** |
| Partial JSON lines | Buffer fragmentation | Reader accumulates until newline (built-in) |

### udev Rule Not Working

```bash
# Check rule
cat /etc/udev/rules.d/99-esp32.rules

# Test rule
udevadm test /dev/ttyUSB0

# Reload
sudo udevadm control --reload-rules
sudo udevadm trigger

# Verify symlink
ls -la /dev/ttyESP32
```

---

## 4. RPi (Raspberry Pi) Issues

### App Not Loading

```bash
# Check Flask output
journalctl -u water-meter.service -f

# Check if port 5000 is listening
sudo netstat -tlnp | grep 5000
```

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Activate venv → `pip install -r requirements.txt` |
| `ImportError: ml_inference` | Check `models/` files exist |
| `Address already in use` | Kill existing process: `sudo fuser -k 5000/tcp` |
| `Permission denied` on serial | Add user to dialout group, reboot |

### Memory Error

```bash
# Check RAM
free -h

# Reduce XGBoost memory
# In ml_inference.py: reduce n_estimators, max_depth
```

| Problem | Solution |
|---------|----------|
| `MemoryError` loading model | Use smaller model (fewer trees), add swap |
| RPi freezes during inference | Reduce `n_estimators` to 100, `max_depth` to 4 |

### Model Not Found

```bash
# Verify model files
ls -la /home/pi/wmldad/rpi/models/
# Should see: xgboost_model.json, isolation_forest.pkl, scaler.pkl, iso_threshold.pkl, feature_cols.pkl, metadata.json

# If missing, train or copy from training/
cp /home/pi/wmldad/training/*.json /home/pi/wmldad/rpi/models/
cp /home/pi/wmldad/training/*.pkl /home/pi/wmldad/rpi/models/
```

---

## 5. ML Model Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| All predictions "normal" | Model not trained / loaded | Check `detector.model_loaded` |
| Too many false positives | Threshold too low | Increase `confidence_threshold` to 0.85 |
| Misses all leaks | Training data lacks leaks | Add leak samples, retrain |
| `XGBoost error on import` | Version mismatch | `pip install xgboost==2.0.3` |
| Isolation Forest always anomaly | `contamination` too high | Reduce to 0.01 or lower |
| Inference too slow | Too many trees | Reduce `n_estimators` to 100 |

### Model Evaluation Commands

```bash
# On RPi
cd /home/pi/wmldad/rpi
source venv/bin/activate

python3 -c "
from ml_inference import load_deployment_package
import numpy as np

pkg = load_deployment_package('models')
detector = pkg['detector']
detector.warm_up()

# Test normal
normal = np.array([[2.5, 30, 14, 2, 1, 1.1, 0.5, 0, 0.1]], dtype=np.float32)
print('Normal:', detector.predict(normal))

# Test minor leak
minor = np.array([[0.3, 600, 3, 1, 1, 1.5, 0.01, 1, -0.1]], dtype=np.float32)
print('Minor leak:', detector.predict(minor))

# Benchmark
print('Benchmark:', detector.benchmark(100))
"
```

---

## 6. Plumbing / Mechanical Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| Water hammer | Fast valve closing | Install water hammer arrestor |
| Sensor not spinning | Debris in turbine | Remove and clean with soft brush |
| Check valve stuck | Debris or hard water | Disassemble and clean |
| Leaks at threads | Insufficient Teflon tape | Re-wrap with 3–5 turns PTFE tape |
| PVC cement failure | Wrong cement / dirty pipe | Use correct PVC cement, clean with primer |

---

## 7. Diagnostic Commands (Serial Monitor)

Connect ESP32 via USB, open Serial Monitor at **921600 baud**, send:

| Command | Response | Use Case |
|---------|----------|----------|
| `status` | All sensor readings + device state | Quick health check |
| `sensors` | Raw pulse counts per sensor | Debug ISR issues |
| `config` | Current configuration | Verify settings |
| `wifi` | WiFi status + IP + RSSI | Network troubleshooting |
| `firebase` | *(Removed — no Firebase)* | N/A |
| `queue` | Number of readings pending upload | N/A (local only) |
| `calibrate` | Start calibration mode | For bucket test |
| `reset` | Reboot ESP32 | Quick restart |
| `format` | Format SPIFFS storage | Clear corrupted data |
| `heap` | Free heap memory | Check for memory leaks |
| `uptime` | Device uptime in seconds | Know when last rebooted |

---

## 8. Built-in LED Indicator Reference

| LED Pattern | Meaning |
|-------------|---------|
| Solid green | Normal operation, all OK |
| Blink green (1s) | WiFi connecting |
| Blink blue (fast) | Transmitting serial data |
| Solid yellow | Minor leak detected (alert) |
| Solid red | Major leak detected (critical) |
| Red flash | Emergency — urgent action needed |
| Blink white (3x + pause) | Successful data send |
| Blink red (5x + pause) | Send failed / error |
| Off | Deep sleep or no power |

---

## 9. Checklist Before Panicking

- [ ] Is ESP32 getting power? (LED on?)
- [ ] Is USB cable a **data cable**? (not charge-only)
- [ ] Is Serial Monitor baud set to **921600**?
- [ ] Is the flow sensor arrow pointing **WITH** water flow?
- [ ] Are WiFi SSID and password correct? (for OTA only)
- [ ] Is `PULSE_PER_LITER` calibrated for each sensor?
- [ ] Is the virtual environment activated on RPi?
- [ ] Did you run `pip install -r requirements.txt`?
- [ ] Are ML model files in `rpi/models/`?
- [ ] Is `PULSE_PER_LITER` calibrated for each sensor?

---

## 10. Getting Help

If stuck:
1. Check `journalctl -u water-meter.service -f` on RPi
2. Check ESP32 Serial Monitor at 921600 baud
3. Run the diagnostic commands above
4. Open GitHub Issue with:
   - Serial Monitor output (last 50 lines)
   - RPi logs (`journalctl -u water-meter -n 100`)
   - Your `config.h` (remove WiFi passwords!)
   - Sensor types and plumbing layout