# Calibration Guide — Sensor K-Factor Calibration

> **Importance:** Accurate calibration is critical for leak detection accuracy. An uncalibrated sensor with ±10% error will trigger false positives or miss real leaks.
> **Goal:** Determine the exact **K-factor** (pulses per liter / PPL) for each of the 5 flow sensors.

---

## The K-Factor

```
K-Factor (PPL) = Number of electrical pulses generated per liter of water
Volume (L) = Total Pulse Count ÷ K-Factor
Flow Rate (L/min) = (Pulse Count × 60) ÷ (K-Factor × Interval Seconds)
```

Most YF-S201 sensors are rated at **450 PPL**, but actual values vary by ±10% due to:
- Manufacturing tolerances (±5%)
- Pipe diameter and water pressure
- Flow rate (low vs high behave differently)
- Temperature
- Wear over time

---

## Calibration Method: Bucket Test

### What You Need

- **Graduated container** (1L, 5L, or 10L — the bigger, the more accurate)
- **Smartphone stopwatch** (optional for flow rate)
- **ESP32** flashed with firmware, Serial Monitor open
- **Water source** (faucet / hose)
- **One YF-S201 sensor** at a time

### Procedure (Per Sensor)

**Step 1:** Connect only the sensor being calibrated.

**Step 2:** Set initial K-factor in `config.h`:
```cpp
#define PULSE_PER_LITER 450
```
Upload to ESP32.

**Step 3:** Open Serial Monitor (115200 baud). Type `status` to see pulse count.

**Step 4:** Run the test:
1. Place container under faucet
2. Connect flow sensor between faucet and container
3. Open faucet at a **steady medium flow**
4. Collect exactly **5 liters** (or more for accuracy)
5. Close faucet
6. Note the pulse count from Serial Monitor

**Step 5:** Calculate:
```
Actual PPL = Total Pulse Count ÷ Volume Collected

Example: 2,320 pulses for 5 liters
Actual PPL = 2,320 ÷ 5 = 464 PPL
```

**Step 6:** Repeat 3 times and average:
```
Test 1: 2,320 pulses ÷ 5L = 464 PPL
Test 2: 2,310 pulses ÷ 5L = 462 PPL 
Test 3: 2,340 pulses ÷ 5L = 468 PPL

Average PPL = (464 + 462 + 468) ÷ 3 = 464.7 → round to 465
```

**Step 7:** Update firmware:
```cpp
// Per-sensor calibration (config.h)
#define PPL_INLET    465
#define PPL_FIXTURE1 450
#define PPL_FIXTURE2 458
#define PPL_FIXTURE3 452
#define PPL_FIXTURE4 460
```

---

## Two-Point Calibration (Best Accuracy)

For different flow rates, the K-factor changes slightly:

| Test | Flow Rate | Volume | Start Pulse | End Pulse | Calculated PPL |
|------|-----------|--------|-------------|-----------|----------------|
| Low | Drip (~0.3 L/min) | 2L | 0 | 920 | 460 |
| Medium | Faucet (~6 L/min) | 5L | 0 | 2,310 | 462 |
| High | Full open (~15 L/min) | 5L | 0 | 2,355 | 471 |

**Recommended:** Use the **medium flow** PPL and apply a correction factor:
```python
if flow_rate < 1.0:
    ppl = medium_ppl * 0.98
elif flow_rate > 10.0:
    ppl = medium_ppl * 1.02
else:
    ppl = medium_ppl
```

---

## Calibration Verification

After calibration, verify accuracy:

| Accuracy | Error Range | Impact on Leak Detection |
|----------|-------------|-------------------------|
| Excellent | < ±2% | Reliable leak detection |
| Good | ±2% – ±5% | Minor false positive risk |
| Acceptable | ±5% – ±10% | May miss small leaks |
| Needs work | > ±10% | Unreliable for leak detection |

**Formula:**
```
Error % = |(Measured Volume - Actual Volume) ÷ Actual Volume| × 100
```

---

## Calibration via Firebase (Optional)

If you've implemented the calibration endpoint:

```json
// POST to Flask API or write to Firebase:
{
  "command": "calibrate",
  "sensor_id": "inlet",
  "known_volume": 5.0
}
```

1. Run exactly 5L through the inlet sensor
2. The system calculates the K-factor and updates `/config/device_id/pulse_per_liter_inlet`

---

## Calibration Log Template

```
Sensor Calibration Log
──────────────────────
Date: 2026-07-10
Device: wm_001

INLET SENSOR (GPIO 34):
  Test 1: 2320 pulses / 5L = 464 PPL
  Test 2: 2310 pulses / 5L = 462 PPL
  Test 3: 2340 pulses / 5L = 468 PPL
  Average: 465 PPL ← USE THIS

FIXTURE 1 (GPIO 35):
  Test 1: 2250 pulses / 5L = 450 PPL
  Average: 450 PPL

FIXTURE 2 (GPIO 32):
  Test 1: 2290 pulses / 5L = 458 PPL
  Average: 458 PPL

FIXTURE 3 (GPIO 33):
  Test 1: 2260 pulses / 5L = 452 PPL
  Average: 452 PPL

FIXTURE 4 (GPIO 25):
  Test 1: 2300 pulses / 5L = 460 PPL
  Average: 460 PPL
```

---

## Common Pitfalls

| Problem | Why | Fix |
|---------|-----|-----|
| Air bubbles in sensor | Gives wrong pulse count | Tap sensor, purge air first |
| Sensor installed backwards | Zero reading | Arrow must point WITH flow |
| Low flow gives different PPL | Non-linear sensor response | Use 2-point calibration |
| Temperature change | K-factor shifts slightly | Re-calibrate seasonally |
| Using different pipe diameter | Changes flow profile | Calibrate with actual plumbing |
| Multiple sensors sharing same calibration | Each sensor is different | Calibrate EACH sensor individually |

---

## Quick Reference

| Sensor Model | Nominal PPL (start here) | Typical Range |
|-------------|-------------------------|---------------|
| YF-S201 | 450 | 440–480 |
| YF-S401 | 450 | 440–470 |
| YF-B1 | 2760 | 2600–2900 |
| Generic clone | 450 | 420–500 (test carefully) |

> **Tip:** After calibration, write the PPL value on each sensor with a permanent marker so you don't forget which sensor has which value!