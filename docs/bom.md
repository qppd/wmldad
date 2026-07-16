# Bill of Materials (BOM) — Water Meter with Leak Detection

> **System:** 1 inlet flow sensor + 3 fixture flow sensors → ESP32 → USB Serial → RPi → XGBoost ML  
> **Supplier Priority:** [Makerlab Electronics](https://shopee.ph/makerlabelectronics) → 4–5 alternatives  
> **Prices:** Estimated in Philippine Peso (₱), July 2026

---

## 1. Core Components

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 1 | **ESP32 38-Pin Dev Board** (ESP32 Dev Module, CP2102, WiFi + BLE) | 1 | ₱450 | ₱450 | [Makerlab Shopee](https://shopee.ph/search?keyword=esp32%2038pin%20makerlab) |
| 2 | **ESP32 38-Pin Expansion Board** (screw terminals, labeled) | 1 | ₱180 | ₱180 | [Makerlab Shopee](https://shopee.ph/search?keyword=esp32%20expansion%20board%20makerlab) |
| 3 | **YF-S201 Water Flow Sensor** 1/2" thread, Hall-effect | **4** | ₱180 | **₱720** | [Makerlab Shopee](https://shopee.ph/search?keyword=yf-s201%20flow%20sensor%20makerlab) |
| 4 | **Check Valve** 1/2" Brass / PVC (non-return) | 3 | ₱120 | ₱360 | [Makerlab Shopee](https://shopee.ph/search?keyword=check%20valve%201%2F2%20makerlab) |
| 5 | **1/2" PVC Pipe Fittings** (tees, elbows, couplers, nipples) | 1 set | ₱250 | ₱250 | [Shopee Hardware](https://shopee.ph/search?keyword=1%2F2%20pvc%20pipe%20fitting%20set) |
| 6 | **PTFE Thread Seal Tape** (Teflon, 10m roll) | 2 | ₱20 | ₱40 | [Makerlab Shopee](https://shopee.ph/search?keyword=teflon%20tape%20makerlab) |
| 7 | **PVC Pipe Cement / Glue** (for permanent joints) | 1 | ₱80 | ₱80 | [Shopee Hardware](https://shopee.ph/search?keyword=pvc%20pipe%20cement) |

**Core Subtotal:** **₱2,080**

---

## 2. Prototyping & Wiring

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 8 | **Perf Board 20×80mm** (for permanent soldering) | 2 | ₱25 | ₱50 | [Makerlab Shopee](https://shopee.ph/search?keyword=perf%20board%2020x80%20makerlab) |
| 9 | **JST-XH 3-pin Male** (for flow sensor side) | 4 | ₱10 | ₱40 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%203pin%20male%20makerlab) |
| 10 | **JST-XH 3-pin Female** (for board/perf board side) | 4 | ₱12 | ₱48 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%203pin%20female%20makerlab) |
| 11 | **Terminal Block 2-pin Blue** (5mm pitch, power input) | 1 | ₱15 | ₱15 | [Makerlab Shopee](https://shopee.ph/search?keyword=terminal%20block%202pin%20blue%20makerlab) |

**Wiring Subtotal:** **₱163**

> **Note:** JST-XH connectors are purchased **pre-crimped / ready-to-use** — no crimp kit or crimping tool needed. Just solder the female connectors to the perf board and plug in the sensor cables.

---

## 3. Power Supply

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 12 | **220V AC to 12V 5A Switching Power Supply** (S-60-12, 60W, LRS-50/60-12) | 1 | ₱280 | ₱280 | [Shopee](https://shopee.ph/Switching-Power-Supply-(S-60-12)-12V-5A-60W-LRS-50-5V-10A-12V-4.2A-24V-2.1A-50W-i.18252381.363361010?extraParams=%7B%22display_model_id%22%3A164466543878%2C%22model_selection_logic%22%3A3%7D) |
| 13 | **12V to 5V Buck Converter** (LM2596S, DC-DC Step-Down Module, USB output) | 1 | ₱65 | ₱65 | [Shopee](https://shopee.ph/24V-12V-to-5V-Buck-Converter-USB-Mobile-Phone-DC-DC-Step-Down-Module-LM2596S-HW-688-HCW-P715-i.18252381.1920327681?extraParams=%7B%22display_model_id%22%3A80023951201%2C%22model_selection_logic%22%3A3%7D) |
| 14 | **USB to Micro USB Data Cable** (braided, 1m) | 1 | ₱120 | ₱120 | [Makerlab Shopee](https://shopee.ph/search?keyword=micro%20usb%20cable%20makerlab) |

**Power Subtotal:** **₱465**

> **Note:** The 12V 5A supply powers both the buck converter (for ESP32 + sensors at 5V) and can directly power 12V components if needed. The LM2596S buck converter steps down 12V → 5V for the ESP32 and flow sensors.

---

## 4. Enclosure & Mounting

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 15 | **Waterproof ABS Enclosure Box IP67** 175×125×75mm | 1 | ₱280 | ₱280 | [Shopee](https://shopee.ph/Waterproof-Plastic-Enclosure-Box-Electronic-IP67-Project-Instrument-Case-Electrical-Project-Box-ABS-Outdoor-Junction-Box-Housing-i.291988242.6261564475?extraParams=%7B%22display_model_id%22%3A22547988641%2C%22model_selection_logic%22%3A3%7D) |
| 16 | **Cable Glands** PG9 / PG11 (waterproof entry) | 6 | ₱15 | ₱90 | [Shopee Hardware](https://shopee.ph/search?keyword=cable%20gland%20pg9) |
| 17 | **Heat Shrink Tube Set** (assorted sizes) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=heat%20shrink%20tube%20makerlab) |
| 18 | **Cable Ties** 100mm (100pc) | 1 | ₱30 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=cable%20tie%20makerlab) |
| 19 | **M3 Screws + Standoffs Kit** (PCB mounting) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=m3%20standoff%20makerlab) |
| 20 | **Double-sided Tape / Velcro** (mounting sensors) | 1 | ₱30 | ₱30 | [Shopee Hardware](https://shopee.ph/search?keyword=double%20sided%20tape%20heavy%20duty) |

**Enclosure Subtotal:** **₱550**

> **Note:** IP67 waterproof enclosure provides excellent protection for outdoor/wet environments. 175×125×75mm size fits ESP32, expansion board, buck converter, terminal block, and perf board with room for cable management.

---

## 5. Raspberry Pi Backend

| # | Item | Qty | Unit (₱) | Total (₱) | Note |
|---|------|-----|----------|-----------|------|
| 21 | **Raspberry Pi 4/5** (or 3B+, if on hand) | 1 | ₱2,500 | ₱2,500 | One-time cost, runs Flask + ML locally |

**Backend Subtotal:** **₱2,500**

---

## Already Purchased (Not in BOM)

| Item | Qty | Notes |
|------|-----|-------|
| **Raspberry Pi 4/5** | 1 | Runs Flask + ML backend |
| **Official Raspberry Pi Touchscreen LCD** (7" 800×480) | 1 | Dashboard display (replaces OLED) |
| **Official Raspberry Pi Power Supply** (5V 3A USB-C) | 1 | Powers Pi + screen |
| **HDMI Cable** (micro-HDMI to HDMI) | 1 | Pi to external monitor |
| **Micro SD Card** 32GB Class 10 (A1/A2) | 1 | OS + data storage |

---

## Total Cost Summary

| Tier | Category | ₱ | Notes |
|------|----------|---|-------|
| **MVP** | Core + perf board + power | **~₱1,803** | ESP32 + 1 sensor (prove concept) |
| **Standard** | All ESP32-side components + enclosure | **~₱3,143** | Full 4-sensor system |
| **Complete** | Standard + Raspberry Pi (one-time) | **~₱5,643** | Production-ready with ML backend |

> **Note:** Raspberry Pi, touchscreen LCD, PSU, HDMI, and SD card are **already purchased** — excluded from cost totals above.

---

## Recommended Seller: Makerlab Electronics

| Platform | Store | Rating | Notes |
|----------|-------|--------|-------|
| **Shopee** | [Makerlab Electronics](https://shopee.ph/makerlabelectronics) | 4.9 | Fast shipping, good stock |
| **Lazada** | [Makerlab Electronics](https://www.lazada.com.ph/shop/makerlab-electronics/) | 4.8 | Wider payment options |

### Alternative Sellers (4–5)

| Store | Platform | Rating | Specializes In |
|-------|----------|--------|---------------|
| [e-Gizmo](https://shopee.ph/e-gizmo) | Shopee | 4.8 | Arduino/ESP32 parts, sensors |
| [Cytron Technologies](https://shopee.ph/cytrontechnologies) | Shopee | 4.9 | Robotics, IoT, sensors |
| [DIY Electronics](https://shopee.ph/diy_electronics) | Shopee | 4.7 | General electronics |
| [Handson Technology](https://www.lazada.com.ph/shop/handsome-technology/) | Lazada | 4.8 | Sensors, power supplies |

---

## Wiring Summary for 4 Flow Sensors

Each YF-S201 sensor has 3 wires: **Red (VCC)**, **Black (GND)**, **Yellow (Signal)**

| Connection | JST-XH 3-pin | Wire Color | Pin |
|------------|--------------|------------|-----|
| VCC | Pin 1 | Red | 5V |
| GND | Pin 2 | Black | GND |
| Signal | Pin 3 | Yellow | GPIO (26, 25, 33, 32) |

**Connector Setup:**
- **Sensor side:** JST-XH 3-pin **Male** (crimped to sensor wires)
- **Board/perf board side:** JST-XH 3-pin **Female** (soldered to perf board)
- **Power input:** Terminal Block 2-pin Blue (5mm pitch) for 5V/GND from buck converter

> **Note:** JST-XH connectors are purchased **pre-crimped / ready-to-use** — no crimp kit or crimping tool needed. Just solder the female connectors to the perf board and plug in the sensor cables.