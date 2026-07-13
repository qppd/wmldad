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
| 8 | **Perf Board 7×9cm** (for permanent soldering) | 2 | ₱35 | ₱70 | [Makerlab Shopee](https://shopee.ph/search?keyword=perf%20board%20makerlab) |
| 9 | **JST-XH Connector Kit** (2/3/4/5/6-pin assorted, with crimp pins & housing) | 1 set | ₱120 | ₱120 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%20connector%20kit%20makerlab) |
| 10 | **JST-XH 2-pin** (for flow sensor power/signal) | 10 pairs | ₱8 | ₱80 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%202pin%20makerlab) |
| 11 | **JST-XH 4-pin** (for sensor bundles) | 5 sets | ₱12 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%204pin%20makerlab) |
| 12 | **JST-XH 5-pin** (for expansion board connections) | 5 sets | ₱15 | ₱75 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%205pin%20makerlab) |
| 13 | **Crimp Pin Kit** (male+female pins, housing, crimping tool) | 1 | ₱150 | ₱150 | [Makerlab Shopee](https://shopee.ph/search?keyword=crimp%20pin%20kit%20makerlab) |

**Wiring Subtotal:** **₱555**

---

## 3. Power Supply

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 14 | **220V AC to 12V 5A Switching Power Supply** (S-60-12, 60W, LRS-50/60-12) | 1 | ₱280 | ₱280 | [Shopee](https://shopee.ph/Switching-Power-Supply-(S-60-12)-12V-5A-60W-LRS-50-5V-10A-12V-4.2A-24V-2.1A-50W-i.18252381.363361010?extraParams=%7B%22display_model_id%22%3A164466543878%2C%22model_selection_logic%22%3A3%7D) |
| 15 | **12V to 5V Buck Converter** (LM2596S, DC-DC Step-Down Module, USB output) | 1 | ₱65 | ₱65 | [Shopee](https://shopee.ph/24V-12V-to-5V-Buck-Converter-USB-Mobile-Phone-DC-DC-Step-Down-Module-LM2596S-HW-688-HCW-P715-i.18252381.1920327681?extraParams=%7B%22display_model_id%22%3A80023951201%2C%22model_selection_logic%22%3A3%7D) |
| 16 | **USB to Micro USB Data Cable** (braided, 1m) | 1 | ₱120 | ₱120 | [Makerlab Shopee](https://shopee.ph/search?keyword=micro%20usb%20cable%20makerlab) |

**Power Subtotal:** **₱465**

> **Note:** The 12V 5A supply powers both the buck converter (for ESP32 + sensors at 5V) and can directly power 12V components if needed. The LM2596S buck converter steps down 12V → 5V for the ESP32 and flow sensors.

---

## 4. Enclosure & Mounting

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 17 | **ABS Project Enclosure Box** 200×120×70mm | 1 | ₱250 | ₱250 | [Makerlab Shopee](https://shopee.ph/search?keyword=project%20enclosure%20box%20abs%20makerlab) |
| 18 | **Cable Glands** PG9 / PG11 (waterproof entry) | 6 | ₱15 | ₱90 | [Shopee Hardware](https://shopee.ph/search?keyword=cable%20gland%20pg9) |
| 19 | **Heat Shrink Tube Set** (assorted sizes) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=heat%20shrink%20tube%20makerlab) |
| 19 | **Cable Ties** 100mm (100pc) | 1 | ₱30 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=cable%20tie%20makerlab) |
| 20 | **M3 Screws + Standoffs Kit** (PCB mounting) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=m3%20standoff%20makerlab) |
| 20 | **Double-sided Tape / Velcro** (mounting sensors) | 1 | ₱30 | ₱30 | [Shopee Hardware](https://shopee.ph/search?keyword=double%20sided%20tape%20heavy%20duty) |

**Enclosure Subtotal:** **₱520**

---

## 5. Raspberry Pi Backend

| # | Item | Qty | Unit (₱) | Total (₱) | Note |
|---|------|-----|----------|-----------|------|
| 21 | **Raspberry Pi 4/5** (or 3B+, if on hand) | 1 | ₱2,500 | ₱2,500 | One-time cost, runs Flask + ML locally |
| 22 | **Telegram Bot** (free) | 1 | ₱0 | ₱0 | Alerts via [@BotFather](https://t.me/BotFather) |

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
| **MVP** | Core + perf board + power | **~₱2,185** | ESP32 + 1 sensor (prove concept) |
| **Standard** | All ESP32-side components + enclosure | **~₱3,620** | Full 4-sensor system |
| **Complete** | Standard + Raspberry Pi (one-time) | **~₱6,120** | Production-ready with ML backend |

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