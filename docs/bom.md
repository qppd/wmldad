# Bill of Materials (BOM) — Water Meter with Fixture Leak Detection

> **System:** 1 inlet flow sensor + 4 fixture flow sensors → ESP32 → ML leak detection (Random Forest)
> **Supplier Priority:** [Makerlab Electronics](https://shopee.ph/makerlabelectronics) 🇵🇭 → 4–5 ⭐ alternatives
> **Prices:** Estimated in Philippine Peso (₱), 2026

---

## 1. Core Components

| # | Item | Qty | Unit Price (₱) | Total (₱) | Link |
|---|------|-----|----------------|-----------|------|
| 1 | **ESP32 38-Pin Development Board** (NodeMCU-32S / ESP-WROOM-32, CP2102) | 1 | ₱450 | ₱450 | [Makerlab Shopee](https://shopee.ph/search?keyword=esp32%2038pin%20makerlab) |
| 2 | **ESP32 38-Pin Expansion Board** (Breakout Board with Screw Terminals) | 1 | ₱180 | ₱180 | [Makerlab Shopee](https://shopee.ph/search?keyword=esp32%20expansion%20board%20makerlab) |
| 3 | **YF-S201 Water Flow Sensor** 1/2" Thread, Hall-Effect Pulse Output | 4 | ₱180 | ₱720 | [Makerlab Shopee](https://shopee.ph/search?keyword=yf-s201%20flow%20sensor%20makerlab) |
| 4 | **Check Valve** 1/2" Brass / PVC (Non-Return Valve) | 4 | ₱120 | ₱480 | [Makerlab Shopee](https://shopee.ph/search?keyword=check%20valve%201/2%20makerlab) |
| 5 | **1/2" PVC Pipe Fittings Kit** (Tees, elbows, couplers, threads) | 1 set | ₱250 | ₱250 | [Shopee Hardware Store](https://shopee.ph/search?keyword=1/2%20pvc%20pipe%20fitting%20set) |
| 6 | **PTFE Thread Seal Tape** (Teflon tape, 10m) | 2 | ₱20 | ₱40 | [Makerlab Shopee](https://shopee.ph/search?keyword=teflon%20tape%20makerlab) |

**Core Subtotal:** **₱2,120**

---

## 2. Power Supply

| # | Item | Qty | Unit Price (₱) | Total (₱) | Link |
|---|------|-----|----------------|-----------|------|
| 7 | **5V 2A USB Power Adapter** (phone charger grade) | 1 | ₱150 | ₱150 | [Makerlab Shopee](https://shopee.ph/search?keyword=5v%202a%20power%20adapter%20makerlab) |
| 8 | **USB to Micro USB Data Cable** (braided, 1m) | 1 | ₱120 | ₱120 | [Makerlab Shopee](https://shopee.ph/search?keyword=micro%20usb%20cable%20makerlab) |
| 9 | **LM2596 DC-DC Step-Down Regulator** (if using 12V supply) | 1 | ₱100 | ₱100 | [Makerlab Shopee](https://shopee.ph/search?keyword=lm2596%20makerlab) |
| 10 | **1000µF 25V Electrolytic Capacitor** (power smoothing) | 2 | ₱15 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=1000uf%20capacitor%20makerlab) |

**Power Subtotal:** **₱400**

---

## 3. Wiring & Prototyping

| # | Item | Qty | Unit Price (₱) | Total (₱) | Link |
|---|------|-----|----------------|-----------|------|
| 11 | **Breadboard 830 Points** + 65 Jumper Wires | 1 set | ₱150 | ₱150 | [Makerlab Shopee](https://shopee.ph/search?keyword=breadboard%20jumper%20wires%20makerlab) |
| 12 | **Jumper Wires M-M / M-F** (additional 40pc set) | 1 | ₱65 | ₱65 | [Makerlab Shopee](https://shopee.ph/search?keyword=jumper%20wire%2040pcs%20makerlab) |
| 13 | **Dupont Wire Kit** (male + female crimp pins, housing) | 1 | ₱80 | ₱80 | [Makerlab Shopee](https://shopee.ph/search?keyword=dupont%20wire%20crimp%20kit%20makerlab) |
| 14 | **Resistor Kit** 1/4W (assorted 10Ω–1MΩ, 200pc) | 1 | ₱80 | ₱80 | [Makerlab Shopee](https://shopee.ph/search?keyword=resistor%20kit%20200pcs%20makerlab) |
| 15 | **10kΩ Resistor** (pull-up for flow sensor signal, extra) | 10 | ₱2 | ₱20 | [Makerlab Shopee](https://shopee.ph/search?keyword=10k%20resistor%20makerlab) |
| 16 | **100nF Ceramic Capacitor** (decoupling, per sensor) | 10 | ₱3 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=ceramic%20capacitor%20makerlab) |
| 17 | **Perf / Prototype Board** (7×9cm, single-sided) | 2 | ₱35 | ₱70 | [Makerlab Shopee](https://shopee.ph/search?keyword=perf%20board%20makerlab) |
| 18 | **Terminal Block Screw Connectors** 2-pin / 3-pin (10pc set) | 2 | ₱40 | ₱80 | [Makerlab Shopee](https://shopee.ph/search?keyword=terminal%20block%20screw%20makerlab) |

**Wiring Subtotal:** **₱575**

---

## 4. Indicators & User Interface

| # | Item | Qty | Unit Price (₱) | Total (₱) | Link |
|---|------|-----|----------------|-----------|------|
| 19 | **OLED Display 128×64** I2C (SSD1306, 0.96") | 1 | ₱250 | ₱250 | [Makerlab Shopee](https://shopee.ph/search?keyword=oled%2012864%20ssd1306%20makerlab) |
| 20 | **RGB LED Module** (common cathode) | 2 | ₱35 | ₱70 | [Makerlab Shopee](https://shopee.ph/search?keyword=rgb%20led%20module%20makerlab) |
| 21 | **Active Buzzer Module** 5V | 1 | ₱30 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=active%20buzzer%20makerlab) |
| 22 | **LED 5mm (Red, Green, Yellow)** — 10pc each | 3 sets | ₱20 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=led%205mm%20assorted%20makerlab) |

**UI Subtotal:** **₱410**

---

## 5. Control & Automation

| # | Item | Qty | Unit Price (₱) | Total (₱) | Link |
|---|------|-----|----------------|-----------|------|
| 23 | **4-Channel Relay Module** 5V (active LOW, optocoupler) | 1 | ₱250 | ₱250 | [Makerlab Shopee](https://shopee.ph/search?keyword=4%20channel%20relay%20module%20makerlab) |
| 24 | **Solenoid Valve** 1/2" NC (Normally Closed, 12V) or **Motorized Ball Valve** | 4 | ₱350 | ₱1,400 | [Shopee 4-5⭐](https://shopee.ph/search?keyword=solenoid%20valve%201/2%20water) |
| 25 | **TIP120 Darlington Transistor** (for solenoid driver if needed) | 4 | ₱25 | ₱100 | [Makerlab Shopee](https://shopee.ph/search?keyword=tip120%20makerlab) |
| 26 | **1N4007 Diode** (flyback protection for relays/valves) | 10 | ₱3 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=1n4007%20makerlab) |

**Control Subtotal:** **₱1,780**

> ⚠️ **Note on Solenoid Valves:** Not always available at Makerlab. Check 4–5⭐ sellers on Shopee/Lazada. A **motorized ball valve** (12V) is more reliable for long-term use.

---

## 6. Enclosure & Mounting

| # | Item | Qty | Unit Price (₱) | Total (₱) | Link |
|---|------|-----|----------------|-----------|------|
| 27 | **Project Enclosure Box** ABS (200×120×70mm) | 1 | ₱250 | ₱250 | [Makerlab Shopee](https://shopee.ph/search?keyword=project%20enclosure%20box%20abs%20makerlab) |
| 28 | **Din Rail Mount** (for enclosure if using DIN) | 1 | ₱80 | ₱80 | [Shopee Hardware](https://shopee.ph/search?keyword=din%20rail%20mount) |
| 29 | **Cable Glands** PG9 / PG11 (waterproof entry) | 6 | ₱15 | ₱90 | [Shopee 4-5⭐](https://shopee.ph/search?keyword=cable%20gland%20pg9) |
| 30 | **Heat Shrink Tube Set** (assorted sizes, 1m each) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=heat%20shrink%20tube%20makerlab) |
| 31 | **Cable Ties** (100mm, 100pc) | 1 | ₱30 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=cable%20tie%20makerlab) |
| 32 | **Zinc-Plated Screws & Standoffs Kit** (M3, for PCB mounting) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=m3%20standoff%20makerlab) |

**Enclosure Subtotal:** **₱570**

---

## 7. Networking & Communication

| # | Item | Qty | Unit Price (₱) | Total (₱) | Link |
|---|------|-----|----------------|-----------|------|
| 33 | **Micro SD Card Module** (SPI, for data logging) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=micro%20sd%20card%20module%20makerlab) |
| 34 | **Micro SD Card** 16GB (Class 10) | 1 | ₱180 | ₱180 | [Shopee 4-5⭐](https://shopee.ph/search?keyword=micro%20sd%2016gb%20class10) |
| 35 | **Resistor 4.7kΩ** (I²C pull-up if needed) | 4 | ₱2 | ₱8 | [Makerlab Shopee](https://shopee.ph/search?keyword=4.7k%20resistor%20makerlab) |

**Networking Subtotal:** **₱248**

---

## 8. ML / Computation (Backend / Optional)

| # | Item | Qty | Unit Price (₱) | Total (₱) | Link |
|---|------|-----|----------------|-----------|------|
| 36 | **Raspberry Pi 4 / 5** (for on-prem ML inference) | 1 | ₱2,500 | ₱2,500 | [Shopee 4-5⭐](https://shopee.ph/search?keyword=raspberry%20pi%205) |
| 37 | **32GB Micro SD** (for Raspberry Pi OS) | 1 | ₱250 | ₱250 | [Shopee 4-5⭐](https://shopee.ph/search?keyword=32gb%20micro%20sd) |
| 38 | **5V 3A USB-C Power Supply** (for Raspberry Pi) | 1 | ₱250 | ₱250 | [Makerlab Shopee](https://shopee.ph/search?keyword=5v%203a%20power%20supply%20makerlab) |

> **Alternatively:** ML inference (Random Forest) can run **on the ESP32 itself** using [TensorFlow Lite Micro](https://www.tensorflow.org/lite/microcontrollers) or [EloquentTinyML](https://github.com/eloquentarduino/EloquentTinyML) — no Raspberry Pi needed. The ESP32 has enough RAM for a small Random Forest model (up to ~50 trees, ~5 features). See `firmware.md` for details.

**ML Subtotal (if RPi):** **₱3,000** | **ML Subtotal (ESP32-only):** **₱0**

---

## Total Cost Summary

| Category | With RPi (₱) | ESP32-Only (₱) |
|----------|--------------|----------------|
| Core Components | ₱2,120 | ₱2,120 |
| Power Supply | ₱400 | ₱400 |
| Wiring & Proto | ₱575 | ₱575 |
| Indicators & UI | ₱410 | ₱410 |
| Control & Automation | ₱1,780 | ₱1,780 |
| Enclosure & Mounting | ₱570 | ₱570 |
| Networking | ₱248 | ₱248 |
| ML / Computation | ₱3,000 | **₱0** |
| **Grand Total** | **₱9,103** | **₱6,103** |

---

## Recommended Seller: Makerlab Electronics

| Platform | Store Link | Rating |
|----------|-----------|--------|
| 🛒 **Shopee** | [Makerlab Electronics Official](https://shopee.ph/makerlabelectronics) | ⭐ 4.9 |
| 🛒 **Lazada** | [Makerlab Electronics Store](https://www.lazada.com.ph/shop/makerlab-electronics/) | ⭐ 4.8 |

**Backup Sellers (4–5⭐):**
- [e-Gizmo](https://shopee.ph/e-gizmo) — ⭐ 4.8, wide selection
- [DIY Electronics](https://shopee.ph/diy_electronics) — ⭐ 4.7
- [Cytron Technologies](https://shopee.ph/cytrontechnologies) — ⭐ 4.9

---

## Pin Allocation (ESP32 38-Pin)

| GPIO | Connected To | Notes |
|------|-------------|-------|
| GPIO 34 | Flow Sensor 1 — **Inlet** | Pulse input (input-only pin) |
| GPIO 35 | Flow Sensor 2 — **Fixture 1** | Pulse input (input-only pin) |
| GPIO 32 | Flow Sensor 3 — **Fixture 2** | Pulse input |
| GPIO 33 | Flow Sensor 4 — **Fixture 3** | Pulse input |
| GPIO 25 | Flow Sensor 5 — **Fixture 4** | Pulse input |
| GPIO 26 | Relay 1 — Inlet Valve | Active LOW |
| GPIO 27 | Relay 2 — Fixture 1 Valve | Active LOW |
| GPIO 14 | Relay 3 — Fixture 2 Valve | Active LOW |
| GPIO 12 | Relay 4 — Fixture 3 Valve | Active LOW (⚠️ boot pin, use with care) |
| GPIO 13 | Relay 5 — Fixture 4 Valve | Active LOW |
| GPIO 21 | OLED SDA | I²C Data |
| GPIO 22 | OLED SCL | I²C Clock |
| GPIO 4 | Buzzer | Active buzzer |
| GPIO 2 | Status LED | Onboard LED |
| GPIO 5 | RGB LED Data | Or separate R/G/B pins |
| GPIO 23 | SD Card MOSI | SPI |
| GPIO 19 | SD Card MISO | SPI |
| GPIO 18 | SD Card SCK | SPI |
| GPIO 5 | SD Card CS | SPI (shared with RGB if no conflict) |

> **Note:** GPIOs 34–39 are **input-only** (no internal pull-up) — use external 10kΩ pull-up resistors on flow sensor signal lines.

---

## Where to Save Money

1. **Skip the Raspberry Pi** — run Random Forest directly on ESP32 via TensorFlow Lite Micro
2. **Skip solenoid valves** for v1 — start with leak detection + alerts only (manual shutoff)
3. **Use cardboard box** instead of ABS enclosure for prototyping
4. **Skip OLED** — use LED indicators + serial monitor initially
5. **Buy ESP32 starter kit** (~₱650) — includes breadboard, jumpers, LEDs, resistors cheaper than separate

## Minimum Viable Prototype (₱1,690)

| Item | ₱ |
|------|---|
| ESP32 38-pin | ₱450 |
| Expansion Board | ₱180 |
| YF-S201 Flow Sensor × 2 | ₱360 |
| Breadboard + Jumpers | ₱150 |
| 5V Adapter + USB Cable | ₱250 |
| Resistors + Capacitors | ₱100 |
| Check Valve × 2 | ₱200 |
| **Total** | **~₱1,690** |
