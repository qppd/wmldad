# WMLDAD — Smart Water Monitoring System

> **A Research Project** — Smart Water Monitoring System that detects leaks, anomalies, and per-fixture consumption using ESP32, Raspberry Pi, USB Serial communication, and Machine Learning (XGBoost + Isolation Forest).

---

## Developer Quick-Start: Step-by-Step Process

Follow these steps **in order**. Each step links to the detailed guide.

### Phase 1: Prepare (Do First)

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 1 | **Buy parts** — Order from BOM (Makerlab Electronics on Shopee/Lazada) | [BOM.md](./docs/bom.md) | 1–2 weeks shipping |
| 2 | **Flash Raspberry Pi OS** — Trixie 64-bit, enable SSH + WiFi in Imager | [pi-complete-setup.md](./docs/pi-complete-setup.md) | 30 min |
| 3 | **Clone project repo** — Get code on Pi and your computer | [setup.md](./docs/setup.md#phase-2-software-installation) | 5 min |

> ⚠️ **Do Step 1–2 in parallel.** Hardware shipping takes longest.

---

### Phase 2: Hardware Assembly

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 4 | **Wire ESP32 + 4× YF-S201** on expansion board (GPIO 26, 25, 33, 32) | [block-diagram.md](./docs/block-diagram.md) | 1 hr |
| 5 | **Plumbing** — Install sensors in-line with check valves (arrow = flow direction) | [setup.md](./docs/setup.md#phase-4-hardware-assembly) | 2–4 hrs |
| 6 | **Enclosure** — Mount in IP67 box with cable glands + USB cable gland | [block-diagram.md](./docs/block-diagram.md) | 1 hr |

---

### Phase 3: ESP32 Firmware (USB Serial)

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 7 | **Install Arduino IDE 2.x** via `pip install arduino` on RPi (or Windows/macOS) | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 15 min |
| 8 | **Add ESP32 board support** — Board Manager URL + install `esp32 by Espressif Systems` | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 10 min |
| 9 | **Install library** — `ArduinoJson` (for JSON serialization) | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 5 min |
| 10 | **Configure `config.h`** — WiFi (for OTA only), device ID, sensor pins, PPL calibration | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 10 min |
| 11 | **Upload firmware** — Select ESP32 Dev Module, correct port, Upload (Ctrl+U) | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 5 min |
| 12 | **Verify** — Serial Monitor (115200): JSON sensor data streaming every 5 sec | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 5 min |

---

### Phase 4: Sensor Calibration (Required Before ML)

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 13 | **Bucket test each sensor** — 5L measured, calculate PPL, update `config.h` | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md#sensor-calibration-bucket-test) | 30 min/sensor |

> 🎯 Target: < 3% error per sensor. Uncalibrated sensors = false leaks / missed leaks.

---

### Phase 5: Raspberry Pi Backend (with 800×480 Touchscreen LCD)

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 14 | **SSH into RPi** — `ssh pi@water-meter.local` | [pi-complete-setup.md](./docs/pi-complete-setup.md) | 5 min |
| 15 | **Clone repo + create venv + install deps** | [pi-complete-setup.md](./docs/pi-complete-setup.md) | 10 min |
| 16 | **Configure serial port** — udev rule for `/dev/ttyESP32` symlink | [pi-complete-setup.md](./docs/pi-complete-setup.md) | 5 min |
| 17 | **Run Flask** — `python app.py`, verify dashboard at `http://water-meter.local:5000/` | [pi-complete-setup.md](./docs/pi-complete-setup.md) | 5 min |
| 18 | **Enable systemd service** for auto-start on boot | [pi-complete-setup.md](./docs/pi-complete-setup.md) | 5 min |
| 19 | **Configure 800×480 Touchscreen** — Auto-launch Chromium kiosk to dashboard | [pi-complete-setup.md](./docs/pi-complete-setup.md) | 10 min |

---

### Phase 6: ML Model (Can Defer)

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 20 | **Train XGBoost + Isolation Forest** — Use Google Colab (GPU) | [ml-complete-guide.md](./docs/ml-complete-guide.md) | 30 min |
| 21 | **Export models** — `xgboost_model.json`, `isolation_forest.pkl`, `scaler.pkl` to `rpi/models/` | [ml-complete-guide.md](./docs/ml-complete-guide.md) | 5 min |
| 22 | **Verify inference** — Dashboard shows leak classifications | [ml-complete-guide.md](./docs/ml-complete-guide.md) | 5 min |

> 💡 **Skip for initial bring-up.** System works with local ESP32 rules (inlet balance, continuous flow, drip detection) without ML. Add ML after hardware + data pipeline verified.

---

### Phase 7: Remote Access (Optional)

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 23 | **Router port forward** — External 8443 → RPi:5000 | [pi-complete-setup.md](./docs/pi-complete-setup.md) | 10 min |
| 24 | **DDNS** (DuckDNS free) or **Cloudflare Tunnel** (HTTPS) | [pi-complete-setup.md](./docs/pi-complete-setup.md) | 15 min |

---

## Essential Guides Only (Bookmark These)

| Guide | Purpose |
|-------|---------|
| [BOM.md](./docs/bom.md) | Parts list with Shopee links, prices |
| [pi-complete-setup.md](./docs/pi-complete-setup.md) | **Complete Pi OS → Backend deployment** (Flash → SSH/VNC → Venv → Deps → Backend files → ML models → Systemd → Touchscreen) |
| [block-diagram.md](./docs/block-diagram.md) | Pinout, wiring, enclosure layout, 3D models |
| [setup.md](./docs/setup.md) | Full phased walkthrough (reference) |
| [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | **Complete ESP32 firmware** (Arduino IDE → ESP32 Board → ArduinoJson → Config → Upload → Verify → Calibration) |
| [esp32-rpi-communication.md](./docs/esp32-rpi-communication.md) | USB serial auto-detection on `/dev/ttyUSB0/1`, JSON protocol |
| [troubleshooting.md](./docs/troubleshooting.md) | Serial commands, LED codes, common fixes |

---

## Hardware Summary

| Component | Qty | Key Spec |
|-----------|-----|----------|
| ESP32 38-pin Dev Module | 1 | CP2102/CH340 USB-UART, 4 MB Flash |
| ESP32 Expansion Board | 1 | Screw terminals |
| YF-S201 Flow Sensor | 4 | 1/2" NPT, Hall effect |
| Check Valve 1/2" | 3 | Brass/PVC, prevent backflow |
| 12V 5A PSU + LM2596S buck | 1 | 220V → 12V → 5V |
| IP67 ABS Enclosure | 1 | 175×125×75mm |
| **7" Touchscreen LCD** | **1** | **800×480, HDMI + USB touch** |
| JST-XH 3-pin M/F | 4 each | Pre-crimped, no crimp tool needed |
| Perf board 20×80mm | 2 | Soldered connections |

---

## Quick Verification Checklist

After each phase, verify:

- [ ] **Phase 1:** Pi boots, `ssh pi@water-meter.local` works
- [ ] **Phase 2:** All 4 sensors show pulses in Serial Monitor when water flows
- [ ] **Phase 3:** JSON data streaming every 5 sec on Serial Monitor (115200 baud)
- [ ] **Phase 4:** 5L bucket test → < 3% error on each sensor
- [ ] **Phase 5:** Dashboard at `:5000` shows live flow rates per fixture on **touchscreen LCD**
- [ ] **Phase 6:** Leak simulation (slow drip) → alert appears in dashboard
- [ ] **Phase 7:** Remote URL (DDNS:8443 or Cloudflare) loads dashboard

---

## License

MIT

## Author

[qppd](https://github.com/qppd) — Quezon Province, Philippines