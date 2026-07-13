# Bill of Materials (BOM) — Water Meter with Leak Detection

> **System:** 1 inlet flow sensor + 3 fixture flow sensors → ESP32 → Firebase → RPi → XGBoost ML  
> **Supplier Priority:** [Makerlab Electronics](https://shopee.ph/makerlabelectronics) → 4–5 alternatives  
> **Prices:** Estimated in Philippine Peso (₱), July 2026

---

## 1. Core Components

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 1 | **ESP32 38-Pin Dev Board** (NodeMCU-32S, CP2102, WiFi + BLE) | 1 | ₱450 | ₱450 | [Makerlab Shopee](https://shopee.ph/search?keyword=esp32%2038pin%20makerlab) |
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
| 8 | **Breadboard 830 Points** + 65 Jumper Wires | 1 set | ₱150 | ₱150 | [Makerlab Shopee](https://shopee.ph/search?keyword=breadboard%20jumper%20wires%20makerlab) |
| 9 | **Jumper Wires M-M / M-F** (additional 40pc) | 1 | ₱65 | ₱65 | [Makerlab Shopee](https://shopee.ph/search?keyword=jumper%20wire%2040pcs%20makerlab) |
| 10 | **Resistor Kit 1/4W** (assorted, 200pc) | 1 | ₱80 | ₱80 | [Makerlab Shopee](https://shopee.ph/search?keyword=resistor%20kit%20200pcs%20makerlab) |
| 11 | **10kΩ Resistor** (pull-ups for 4 sensors, extra) | 10 | ₱2 | ₱20 | [Makerlab Shopee](https://shopee.ph/search?keyword=10k%20resistor%20makerlab) |
| 12 | **100nF Ceramic Capacitor** (decoupling per sensor) | 10 | ₱3 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=ceramic%20capacitor%20makerlab) |
| 13 | **Perf Board 7×9cm** (for permanent soldering) | 2 | ₱35 | ₱70 | [Makerlab Shopee](https://shopee.ph/search?keyword=perf%20board%20makerlab) |
| 14 | **JST-XH Connector Kit** (2/3/4/5/6-pin assorted, with crimp pins & housing) | 1 set | ₱120 | ₱120 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%20connector%20kit%20makerlab) |
| 15 | **JST-XH 2-pin** (for flow sensor power/signal) | 10 pairs | ₱8 | ₱80 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%202pin%20makerlab) |
| 16 | **JST-XH 4-pin** (for sensor bundles) | 5 sets | ₱12 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%204pin%20makerlab) |
| 17 | **JST-XH 5-pin** (for expansion board connections) | 5 sets | ₱15 | ₱75 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%205pin%20makerlab) |
| 18 | **Dupont Crimp Pin Kit** (male+female pins, housing) | 1 | ₱80 | ₱80 | [Makerlab Shopee](https://shopee.ph/search?keyword=dupont%20crimp%20kit%20makerlab) |

**Wiring Subtotal:** **₱810**

---

## 3. Power Supply

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 19 | **Allan Superstore 12V 10A Power Supply** | 1 | ₱150 | ₱150 | [Allan Superstore Shopee](https://shopee.ph/Allan-Superstore-12v2a-12v5a-12v10a-12v15a-12v20a-12v30a-Power-Supply-For-Led-Sign-Signage-i.609565947.18030939950?extraParams=%7B%22display_model_id%22%3A191594807415%2C%22model_selection_logic%22%3A3%7D&sp_atk=8b44f1f9-e481-402b-a4b6-b68a26987663&xptdk=8b44f1f9-e481-402b-a4b6-b68a26987663) |
| 20 | **USB to Micro USB Data Cable** (braided, 1m) | 1 | ₱120 | ₱120 | [Makerlab Shopee](https://shopee.ph/search?keyword=micro%20usb%20cable%20makerlab) |
| 21 | **LM2596 DC-DC Step-Down Regulator** (optional, 12V→5V) | 1 | ₱100 | ₱100 | [Makerlab Shopee](https://shopee.ph/search?keyword=lm2596%20makerlab) |
| 22 | **1000µF 25V Electrolytic Capacitor** (power smoothing) | 2 | ₱15 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=1000uf%20capacitor%20makerlab) |

**Power Subtotal:** **₱400**

---

## 4. Indicators

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 23 | **RGB LED Module** (common cathode) | 1 | ₱35 | ₱35 | [Makerlab Shopee](https://shopee.ph/search?keyword=rgb%20led%20module%20makerlab) |
| 24 | **Active Buzzer Module** 5V | 1 | ₱30 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=active%20buzzer%20makerlab) |
| 25 | **LED 5mm Assorted** (red, green, yellow, 10pc each) | 3 sets | ₱20 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=led%205mm%20assorted%20makerlab) |

**Indicators Subtotal:** **₱125**

---

## 5. Data Storage & Networking

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 26 | **Micro SD Card Module** SPI | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=micro%20sd%20card%20module%20makerlab) |
| 27 | **Micro SD Card** 16GB Class 10 | 1 | ₱180 | ₱180 | [Shopee Hardware](https://shopee.ph/search?keyword=micro%20sd%2016gb%20class10) |

**Storage Subtotal:** **₱240**

---

## 6. Enclosure & Mounting

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 28 | **ABS Project Enclosure Box** 200×120×70mm | 1 | ₱250 | ₱250 | [Makerlab Shopee](https://shopee.ph/search?keyword=project%20enclosure%20box%20abs%20makerlab) |
| 29 | **Cable Glands** PG9 / PG11 (waterproof entry) | 6 | ₱15 | ₱90 | [Shopee Hardware](https://shopee.ph/search?keyword=cable%20gland%20pg9) |
| 30 | **Heat Shrink Tube Set** (assorted sizes) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=heat%20shrink%20tube%20makerlab) |
| 31 | **Cable Ties** 100mm (100pc) | 1 | ₱30 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=cable%20tie%20makerlab) |
| 32 | **M3 Screws + Standoffs Kit** (PCB mounting) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=m3%20standoff%20makerlab) |
| 33 | **Double-sided Tape / Velcro** (mounting sensors) | 1 | ₱30 | ₱30 | [Shopee Hardware](https://shopee.ph/search?keyword=double%20sided%20tape%20heavy%20duty) |

**Enclosure Subtotal:** **₱520**

---

## 7. Raspberry Pi Backend

| # | Item | Qty | Unit (₱) | Total (₱) | Note |
|---|------|-----|----------|-----------|------|
| 34 | **Raspberry Pi 4/5** (or 3B+, if on hand) | 1 | ₱2,500 | ₱2,500 | One-time cost, runs Flask + ML locally |
| 35 | **Telegram Bot** (free) | 1 | ₱0 | ₱0 | Alerts via [@BotFather](https://t.me/BotFather) |

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
| **MVP** | Core + breadboard + power | **~₱2,110** | ESP32 + 1 sensor + buzzer (prove concept) |
| **Standard** | All ESP32-side components + enclosure | **~₱4,175** | Full 4-sensor system |
| **Complete** | Standard + Raspberry Pi (one-time) | **~₱6,675** | Production-ready with ML backend |

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