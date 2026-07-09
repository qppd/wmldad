# Calibration Guide

## Overview

Water flow sensors output electrical pulses as water passes through. Each sensor model has a nominal **K-factor** (pulses per liter), but actual values vary due to:

- Manufacturing tolerances
- Pipe diameter and water pressure
- Flow rate (low vs high flow)
- Temperature

Calibration improves accuracy from ±10% to within ±2-3%.

---

## The K-Factor

```
K-Factor = pulses per liter (PPL)
```

Most YF-S201 sensors are rated at **450 pulses per liter**. This is the starting point.

---

## Method 1: Bucket Test (Recommended)

### What you need

- A precise container (1L, 5L, or 10L graduated container)
- Stopwatch or timer
- Working water meter setup with Serial Monitor access
- A faucet or water source

### Procedure

1. **Set initial K-factor** in `config.h`:
   ```cpp
   #define PULSE_PER_LITER 450
   ```

2. **Upload and monitor** — open Serial Monitor and note the pulse count.

3. **Run the test:**
   - Place the container under the faucet
   - Connect the flow sensor between faucet and container
   - Open the faucet at a steady rate
   - Collect exactly **5 liters** of water
   - Close the faucet
   - Record the pulse count from Serial Monitor

4. **Calculate actual K-factor:**
   ```
   Actual PPL = Total Pulse Count ÷ Volume Collected
   
   Example: You collected 2,320 pulses for 5 liters
   Actual PPL = 2320 ÷ 5 = 464 PPL
   ```

5. **Update config.h:**
   ```cpp
   #define PULSE_PER_LITER 464
   ```

6. **Repeat** the test to verify accuracy.

---

## Method 2: Known Volume Test

If you don't have a graduated container:

1. Use a **5-gallon (18.9L)** water jug
2. Fill the jug completely
3. Run the water through the sensor into a drain
4. Record total pulses from start to empty
5. Calculate:
   ```
   Actual PPL = Total Pulses ÷ 18.9
   ```

---

## Method 3: Two-Point Calibration (High Accuracy)

For better accuracy across different flow rates:

| Test | Flow Rate   | Volume | Start Pulse | End Pulse | Calculated PPL |
|------|-------------|--------|-------------|-----------|----------------|
| Low  | Slow drip   | 2L     | 0           | 920       | 460            |
| High | Full open   | 5L     | 0           | 2,310      | 462            |

**Average PPL = (460 + 462) ÷ 2 = 461**

---

## Verification

After calibration, run another test and check accuracy:

```
Error % = (Measured Volume - Actual Volume) ÷ Actual Volume × 100
```

| Accuracy   | Error Range |
|------------|-------------|
| Excellent  | < ±2%       |
| Good       | ±2% – ±5%   |
| Acceptable | ±5% – ±10%  |
| Needs work | > ±10%      |

---

## ESP32 Auto-Calibration Feature (Optional)

If implemented in firmware, the system can auto-calibrate:

1. Send a known volume command via MQTT/HTTP:
   ```json
   {
     "command": "calibrate",
     "known_volume_liters": 10.0
   }
   ```
2. Run exactly 10L through the sensor
3. The device calculates the new K-factor and saves it to flash

---

## Common K-Factors by Sensor

| Sensor Model | Nominal PPL | Notes                |
|--------------|-------------|----------------------|
| YF-S201      | 450         | 1/2" thread          |
| YF-S401      | 450         | 1/2" thread, smaller |
| YF-B1        | 2760        | High precision       |
| Sea YF-S201  | 450         | Common clone         |
| Hall-effect  | Varies      | Check datasheet      |

---

## Tips

- **Test at your typical flow rate** — calibration is most accurate at the rate you normally use
- **Warm water behaves differently** — calibrate at your actual water temperature
- **Re-calibrate after:** sensor cleaning, pipe changes, or yearly maintenance
- **Mark your K-factor** on the device with a sticker after calibration
