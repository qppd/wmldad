# Project Timeline — Student Capstone Guide

> **Project:** Smart Water Meter with Leak Detection & Anomaly Detection
> **Duration:** 16 weeks (1 semester)
> **Team Size:** 2–4 students

---

## Overview

This timeline is designed for undergraduate students (BS Computer Engineering, BS Electronics Engineering, BS Computer Science, BS Information Technology) completing a capstone or thesis project.

Each week includes:
- 🎯 **Goal** — What should be accomplished
- 📝 **Tasks** — Specific activities
- ✅ **Deliverable** — Tangible output to submit
- ⚠️ **Risk** — Common problems to watch out for

---

## Phase 1: Research & Planning (Weeks 1–3)

### Week 1: Project Definition

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Define project scope and requirements |
| 📝 **Tasks** | • Research existing smart water meters<br/>• Identify problem statement<br/>• Define system requirements<br/>• Study related literature (at least 10 papers)<br/>• Compare YF-S201 vs other flow sensors<br/>• Research XGBoost vs Random Forest for water data |
| ✅ **Deliverable** | Chapter 1: Introduction (Problem, Objectives, Scope) |
| ⚠️ **Risk** | Scope creep — keep focused on 1 inlet + 4 fixtures maximum |

### Week 2: System Design

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Complete system architecture and component selection |
| 📝 **Tasks** | • Draw system architecture diagram<br/>• Select all hardware (ESP32, sensors, valves)<br/>• Select software stack (Firebase, PythonAnywhere, XGBoost)<br/>• Create block diagram<br/>• Assign GPIO pins on ESP32<br/>• Draft plumbing layout |
| ✅ **Deliverable** | System Architecture Document, Block Diagram, BOM |
| ⚠️ **Risk** | Start ordering parts NOW — shipping from Shopee/Lazada can take 1–2 weeks |

### Week 3: Component Acquisition

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Order and receive all components |
| 📝 **Tasks** | • Order from Makerlab Electronics (Shopee/Lazada)<br/>• Buy PVC fittings from local hardware store<br/>• Download all software (VS Code, PlatformIO, Python)<br/>• Create Firebase project<br/>• Sign up for PythonAnywhere |
| ✅ **Deliverable** | All hardware received, software tools installed, Firebase project created |
| ⚠️ **Risk** | Use 4–5⭐ sellers only. Check reviews before ordering. Have backup sellers. |

---

## Phase 2: Hardware & Firmware (Weeks 4–7)

### Week 4: Basic Hardware Setup

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Assemble ESP32 with 1 flow sensor and verify reading |
| 📝 **Tasks** | • Mount ESP32 on expansion board<br/>• Wire 1 YF-S201 sensor to GPIO 34 with pull-up resistor<br/>• Install PlatformIO, clone repo<br/>• Upload test firmware<br/>• Verify pulse counting via Serial Monitor<br/>• Test with manual switch (touch sensor wire to 3.3V) |
| ✅ **Deliverable** | Working ESP32 + 1 flow sensor, Serial Monitor showing pulse counts |
| ⚠️ **Risk** | Common: wrong GPIO, missing pull-up resistor, charge-only USB cable |

### Week 5: All 5 Sensors + Peripherals

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Wire all 5 sensors + OLED + buzzer + SD card |
| 📝 **Tasks** | • Wire sensors 2–5 to GPIO 35, 32, 33, 25<br/>• Add 10kΩ pull-ups to all sensor lines<br/>• Connect OLED (I²C: GPIO 21/22)<br/>• Connect buzzer (GPIO 4)<br/>• Connect SD card module (SPI GPIO 18/19/23)<br/>• Verify all 5 sensors show readings on OLED |
| ✅ **Deliverable** | Breadboard with all 5 sensors + OLED showing live readings |
| ⚠️ **Risk** | GPIO 34 & 35 are input-only — external pull-up REQUIRED. GPIO 12 is boot pin — be careful. |

### Week 6: Firebase Integration

| Item | Activity |
|------|----------|
| 🎯 **Goal** | ESP32 pushes data to Firebase Realtime DB |
| 📝 **Tasks** | • Install Firebase-ESP-Client library<br/>• Configure Firebase credentials in `config.h`<br/>• Implement `Firebase.pushJSON()` for readings<br/>• Implement `Firebase.stream()` for commands<br/>• Test: data appears in Firebase Console<br/>• Test: command received from Firebase |
| ✅ **Deliverable** | ESP32 → Firebase data pipeline working. Data visible in Firebase Console. |
| ⚠️ **Risk** | Firebase Authentication setup is tricky. Double-check API key and email/password. |

### Week 7: Local Leak Rules + Relay Control

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Local leak detection (non-ML fallback) + valve control |
| 📝 **Tasks** | • Implement local leak rules (inlet balance, continuous flow, drip)<br/>• Wire 4-channel relay module<br/>• Connect LED indicators for leak status<br/>• Test: simulate a leak and verify relay activation<br/>• Test: remote valve command via Firebase |
| ✅ **Deliverable** | ESP32 detects leaks locally and controls relays. Verified with simulated leaks. |
| ⚠️ **Risk** | Solenoid valves draw high current — use separate 12V supply. Never power from ESP32 5V. |

---

## Phase 3: Backend & ML (Weeks 8–10)

### Week 8: PythonAnywhere Backend

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Flask web app running on PythonAnywhere with Firebase connection |
| 📝 **Tasks** | • Deploy Flask app skeleton<br/>• Configure Pyrebase4 with service account<br/>• Implement Firebase listener (stream or poll)<br/>• Create dashboard template (HTML + Chart.js)<br/>• Serve dashboard at pythonanywhere.com | 
| ✅ **Deliverable** | Flask app live at `yourname.pythonanywhere.com` showing sensor data |
| ⚠️ **Risk** | Free PythonAnywhere can't run background threads. Use Hacker plan or scheduled tasks. |

### Week 9: ML Model Training

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Train XGBoost + Isolation Forest on simulated data |
| 📝 **Tasks** | • Generate synthetic training data (100K samples)<br/>• Implement feature extraction<br/>• Train XGBoost classifier<br/>• Train Isolation Forest for anomaly detection<br/>• Export models (JSON + PKL)<br/>• Evaluate: accuracy, precision, recall, F1<br/>• Move models to PythonAnywhere |
| ✅ **Deliverable** | XGBoost model with ≥ 95% accuracy on validation set. Isolation Forest trained on normal data. |
| ⚠️ **Risk** | Synthetic data ≠ real data. Model will need retraining after collecting real usage data. |

### Week 10: End-to-End Integration

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Complete data pipeline working: Sensor → ESP32 → Firebase → PythonAnywhere → ML → Alert |
| 📝 **Tasks** | • Wire ML inference into Flask app<br/>• Test: simulate leak, verify ML detects it<br/>• Test: alert appears in web dashboard<br/>• Test: Telegram/email notification sent<br/>• Verify valve command flow (dashboard → Firebase → ESP32 → relay) |
| ✅ **Deliverable** | Full system working end-to-end with all 5 sensors |
| ⚠️ **Risk** | Combine all components one at a time. Test each integration step before adding the next. |

---

## Phase 4: Testing & Refinement (Weeks 11–13)

### Week 11: Calibration & Accuracy

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Calibrate all 5 sensors and verify measurement accuracy |
| 📝 **Tasks** | • Perform bucket test on each sensor (3× repeats)<br/>• Calculate average K-factor per sensor<br/>• Update firmware with calibrated PPL values<br/>• Verify: measure 10L, error should be < 3%<br/>• Log calibration results |
| ✅ **Deliverable** | All 5 sensors calibrated. Measurement error < 3%. Calibration log completed. |
| ⚠️ **Risk** | Run at your actual operating flow rate. Low flow and high flow give different K-factors. |

### Week 12: Real-World Testing

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Test with real plumbing over 24+ hours |
| 📝 **Tasks** | • Install system at test location (lab or home)<br/>• Run for 24 hours continuous<br/>• Simulate leaks: partially open valve, drip, full burst<br/>• Collect real usage data for ML retraining<br/>• Document findings |
| ✅ **Deliverable** | 24-hour test log with at least 3 leak simulation scenarios |
| ⚠️ **Risk** | Use a safe test environment. Have manual shutoff valve nearby. Place sensors over a drain. |

### Week 13: Refinements

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Fix bugs, improve accuracy, optimize performance |
| 📝 **Tasks** | • Retune ML model with real data<br/>• Adjust confidence thresholds<br/>• Fix any Firebase stream issues<br/>• Optimize ESP32 power consumption<br/>• Improve dashboard UI<br/>• Add missing features |
| ✅ **Deliverable** | Refined system v2 ready for documentation |
| ⚠️ **Risk** | Focus on critical fixes only. Don't add new features this late. |

---

## Phase 5: Documentation & Presentation (Weeks 14–16)

### Week 14: Technical Documentation

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Complete all technical documentation |
| 📝 **Tasks** | • Write/update all docs/ files<br/>• Create user manual<br/>• Write API documentation<br/>• Add code comments<br/>• Document test results<br/>• Prepare system diagram images |
| ✅ **Deliverable** | Complete repository documentation. All docs/ files final. |
| ⚠️ **Risk** | Use screenshots of Firebase Console, dashboard, and hardware setup. Visuals are important. |

### Week 15: Paper / Report Writing

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Write final capstone paper or thesis chapter |
| 📝 **Tasks** | • Chapter 1: Introduction<br/>• Chapter 2: Review of Related Literature<br/>• Chapter 3: Methodology (System Design)<br/>• Chapter 4: Results and Discussion<br/>• Chapter 5: Conclusion and Recommendations<br/>• Add references (IEEE/APA format) |
| ✅ **Deliverable** | Complete capstone paper (5 chapters) |
| ⚠️ **Risk** | Cite at least 15–20 references. Compare your results with existing literature. |

### Week 16: Presentation & Defense

| Item | Activity |
|------|----------|
| 🎯 **Goal** | Present and defend the project |
| 📝 **Tasks** | • Create presentation slides (15–20 slides)<br/>• Prepare live demo (record video backup!)<br/>• Anticipate panel questions<br/>• Practice timing (15 min presentation + 10 min Q&A)<br/>• Prepare system for live demo |
| ✅ **Deliverable** | Presentation slides, recorded demo video, successful defense |
| ⚠️ **Risk** | **Always have a backup video!** Live demos can fail. Record a smooth demo video just in case. |

---

## Milestone Summary

| Week | Milestone | Status Indicator |
|------|-----------|------------------|
| 3 | 🟢 Parts received, tools installed | 🟢 |
| 5 | 🟢 ESP32 reading all 5 sensors | 🟢 |
| 7 | 🟢 Local leak detection + valve control | 🟢 |
| 8 | 🟢 Flask app live on PythonAnywhere | 🟢 |
| 10 | 🟢 End-to-end: Sensor → Firebase → ML → Alert | 🟢🟢 |
| 11 | 🟢 All sensors calibrated (< 3% error) | 🟢 |
| 13 | 🟢 System refined with real data | 🟢 |
| 14 | 🟢 Documentation complete | 🟢 |
| 16 | 🏆 Defense! | 🏆 |

---

## Recommended Team Roles

| Role | Responsibility | Team Member |
|------|---------------|-------------|
| **Hardware Lead** | Sensors, wiring, plumbing, enclosure | Student 1 |
| **Firmware Lead** | ESP32 code, Firebase-ESP-Client, local rules | Student 2 |
| **Backend Lead** | PythonAnywhere, Flask, Pyrebase4, dashboard | Student 3 |
| **ML Lead** | XGBoost training, feature engineering, model evaluation | Student 4 |

> 3-person team: combine Backend + ML roles. 2-person team: combine Firmware + Hardware, Backend + ML.

---

## Common Pitfalls to Avoid

| Pitfall | How to Avoid |
|---------|-------------|
| **Ordering parts too late** | Order by Week 2. Use Shopee/Lazada (2–7 day delivery). Have backups. |
| **Not testing incrementally** | Test each component separately before integrating. Sensor → ESP32 → Firebase → PythonAnywhere → ML. |
| **Skipping calibration** | Uncalibrated sensors give ±10% error → ML detects leaks that aren't there or misses real ones. |
| **Overcomplicated ML** | Start with simple rules + XGBoost. Don't try deep learning on ESP32. |
| **No offline fallback** | ESP32 must work without internet. SD card logging + local leak rules. |
| **Bad demo day** | Record a video demo in advance. Have a backup ESP32. Test projector compatibility. |

---

## Cost Summary for Students

| Item | ₱ (Estimated) |
|------|--------------|
| ESP32 + Expansion Board | ₱630 |
| 5× YF-S201 Flow Sensors | ₱900 |
| Check Valves + PVC Fittings | ₱730 |
| Relay + Solenoid Valves | ₱1,780 |
| OLED + Buzzer + LEDs | ₱375 |
| Breadboard + Jumpers + Resistors | ₱375 |
| Enclosure + Hardware | ₱520 |
| Power Supplies | ₱600 |
| **Total Hardware** | **~₱5,910** |
| PythonAnywhere (1 month Hacker) | ₱285 |
| **Grand Total** | **~₱6,195** |

> 💡 **Tip:** Request budget from department. Many schools have ₱5,000–₱10,000 capstone budget per group.

---

## References for Students

1. Firebase-ESP-Client Library: https://github.com/mobizt/Firebase-ESP-Client
2. Pyrebase4: https://github.com/nhorvath/Pyrebase4
3. XGBoost Documentation: https://xgboost.readthedocs.io/
4. Scikit-learn Isolation Forest: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
5. YF-S201 Datasheet: https://www.adafruit.com/product/828
6. ESP32 Arduino Core: https://github.com/espressif/arduino-esp32
7. PythonAnywhere: https://www.pythonanywhere.com/
8. Firebase Console: https://console.firebase.google.com/
9. Makerlab Electronics: https://shopee.ph/makerlabelectronics
