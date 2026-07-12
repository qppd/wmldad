# Bill of Materials (BOM) — Water Meter with Leak Detection

> **System:** 1 inlet flow sensor + 4 fixture flow sensors → ESP32 → Firebase → RPi → XGBoost ML  
> **Supplier Priority:** [Makerlab Electronics](https://shopee.ph/makerlabelectronics) → 4–5 alternatives  
> **Prices:** Estimated in Philippine Peso (₱), July 2026

---

## 1. Core Components

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 1 | **ESP32 38-Pin Dev Board** (NodeMCU-32S, CP2102, WiFi + BLE) | 1 | ₱450 | ₱450 | [Makerlab Shopee](https://shopee.ph/search?keyword=esp32%2038pin%20makerlab) |
| 2 | **ESP32 38-Pin Expansion Board** (screw terminals, labeled) | 1 | ₱180 | ₱180 | [Makerlab Shopee](https://shopee.ph/search?keyword=esp32%20expansion%20board%20makerlab) |
| 3 | **YF-S201 Water Flow Sensor** 1/2" thread, Hall-effect | **5** | ₱180 | **₱900** | [Makerlab Shopee](https://shopee.ph/search?keyword=yf-s201%20flow%20sensor%20makerlab) |
| 4 | **Check Valve** 1/2" Brass / PVC (non-return) | 4 | ₱120 | ₱480 | [Makerlab Shopee](https://shopee.ph/search?keyword=check%20valve%201%2F2%20makerlab) |
| 5 | **1/2" PVC Pipe Fittings** (tees, elbows, couplers, nipples) | 1 set | ₱250 | ₱250 | [Shopee Hardware](https://shopee.ph/search?keyword=1%2F2%20pvc%20pipe%20fitting%20set) |
| 6 | **PTFE Thread Seal Tape** (Teflon, 10m roll) | 2 | ₱20 | ₱40 | [Makerlab Shopee](https://shopee.ph/search?keyword=teflon%20tape%20makerlab) |
| 7 | **PVC Pipe Cement / Glue** (for permanent joints) | 1 | ₱80 | ₱80 | [Shopee Hardware](https://shopee.ph/search?keyword=pvc%20pipe%20cement) |

**Core Subtotal:** **₱2,380**

---

## 2. Prototyping & Wiring

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 8 | **Jumper Wires M-M / M-F** (additional 40pc) | 1 | ₱65 | ₱65 | [Makerlab Shopee](https://shopee.ph/search?keyword=jumper%20wire%2040pcs%20makerlab) |
| 9 | **Resistor Kit 1/4W** (assorted, 200pc) | 1 | ₱80 | ₱80 | [Makerlab Shopee](https://shopee.ph/search?keyword=resistor%20kit%20200pcs%20makerlab) |
| 10 | **100nF Ceramic Capacitor** (decoupling per sensor) | 10 | ₱3 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=ceramic%20capacitor%20makerlab) |
| 11 | **Perf Board 7×9cm** (for permanent soldering) | 2 | ₱35 | ₱70 | [Makerlab Shopee](https://shopee.ph/search?keyword=perf%20board%20makerlab) |
| 12 | **Terminal Block Screw Connectors** (2/3-pin, 10pc) | 2 sets | ₱40 | ₱80 | [Makerlab Shopee](https://shopee.ph/search?keyword=terminal%20block%20screw%20makerlab) |
| 13 | **Dupont Crimp Pin Kit** (male+female pins, housing) | 1 | ₱80 | ₱80 | [Makerlab Shopee](https://shopee.ph/search?keyword=dupont%20crimp%20kit%20makerlab) |
| 14 | **24AWG Tinned Copper Stranded Hook up Wire 5 Color Spool** | 1 | ₱80 | ₱80 | [Makerlab Shopee](https://shopee.ph/Model-1007-18AWG-20AWG-22-AWG-24AWG-Tinned-Copper-Stranded-Hook-up-Wire-5-Color-Spool-i.18252381.18116267956?extraParams=%7B%22display_model_id%22%3A164880739356%2C%22model_selection_logic%22%3A3%7D&sp_atk=606bce60-49cf-4d8e-a110-9ed85429ef75&xptdk=606bce60-49cf-4d8e-a110-9ed85429ef75) |

**Wiring Subtotal:** **₱575**

---

## 3. Power Supply

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 15 | **Allan Superstore 12V 10A Power Supply** | 1 | ₱150 | ₱150 | [Allan Superstore Shopee](https://shopee.ph/Allan-Superstore-12v2a-12v5a-12v10a-12v15a-12v20a-12v30a-Power-Supply-For-Led-Sign-Signage-i.609565947.18030939950?extraParams=%7B%22display_model_id%22%3A191594807415%2C%22model_selection_logic%22%3A3%7D&sp_atk=8b44f1f9-e481-402b-a4b6-b68a26987663&xptdk=8b44f1f9-e481-402b-a4b6-b68a26987663) |
| 16 | **USB to Micro USB Data Cable** (braided, 1m) | 1 | ₱120 | ₱120 | [Makerlab Shopee](https://shopee.ph/search?keyword=micro%20usb%20cable%20makerlab) |
| 17 | **12V 2A Power Adapter** (for solenoid valves) | 1 | ₱200 | ₱200 | [Shopee Hardware](https://shopee.ph/search?keyword=12v%202a%20power%20adapter) |
| 18 | **LM2596 DC-DC Step-Down Regulator** (optional, 12V→5V) | 1 | ₱100 | ₱100 | [Makerlab Shopee](https://shopee.ph/search?keyword=lm2596%20makerlab) |
| 19 | **1000µF 25V Electrolytic Capacitor** (power smoothing) | 2 | ₱15 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=1000uf%20capacitor%20makerlab) |

**Power Subtotal:** **₱600**

---

## 4. Valve Control

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 20 | **5-Channel Relay Module** 5V (optocoupler, active LOW, for 5 valves) | 1 | ₱350 | ₱350 | [Makerlab Shopee](https://shopee.ph/search?keyword=5%20channel%20relay%20makerlab) |
| 21 | **Latching (Bistable) Solenoid Valve** 1/2" 12V (pulse to open/close, zero holding current) | 5 | ₱350 | ₱1,750 | [Lazada: latching bistable](https://www.lazada.com.ph/search/?q=latching%20bistable%20solenoid%20valve%2012v%201%2F2) / [Shopee: latching bistable](https://shopee.ph/search?keyword=latching%20bistable%20solenoid%20valve%2012v%201%2F2) |
| 22 | **1N4007 Diode** (flyback protection for relays) | 10 | ₱3 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=1n4007%20makerlab) |
| 23 | **TIP120 Darlington Transistor** (solenoid driver) | 5 | ₱25 | ₱125 | [Makerlab Shopee](https://shopee.ph/search?keyword=tip120%20makerlab) |

**Valve Control Subtotal:** **₱2,225**

> **Note:** Latching solenoid valves only need a pulse to switch state (no continuous power to hold). Requires H-bridge or dual-coil drive circuit — adjust driver circuitry accordingly.

---

## 5. Enclosure & Mounting

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 24 | **ABS Project Enclosure Box** 200×120×70mm | 1 | ₱250 | ₱250 | [Makerlab Shopee](https://shopee.ph/search?keyword=project%20enclosure%20box%20abs%20makerlab) |
| 25 | **Cable Glands** PG9 / PG11 (waterproof entry) | 6 | ₱15 | ₱90 | [Shopee Hardware](https://shopee.ph/search?keyword=cable%20gland%20pg9) |
| 26 | **Heat Shrink Tube Set** (assorted sizes) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=heat%20shrink%20tube%20makerlab) |
| 27 | **Cable Ties** 100mm (100pc) | 1 | ₱30 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=cable%20tie%20makerlab) |
| 28 | **M3 Screws + Standoffs Kit** (PCB mounting) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=m3%20standoff%20makerlab) |
| 29 | **Double-sided Tape / Velcro** (mounting sensors) | 1 | ₱30 | ₱30 | [Shopee Hardware](https://shopee.ph/search?keyword=double%20sided%20tape%20heavy%20duty) |

**Enclosure Subtotal:** **₱520**

---

## Already Purchased (Not in BOM)

| Item | Qty | Notes |
|------|-----|-------|
| **Raspberry Pi 4/5** | 1 | Runs Flask + ML backend |
| **Official Raspberry Pi Touchscreen LCD** (7" 800×480) | 1 | Dashboard display |
| **Official Raspberry Pi Power Supply** (5V 3A USB-C) | 1 | Powers Pi + screen |
| **HDMI Cable** (micro-HDMI to HDMI) | 1 | Pi to external monitor |
| **Micro SD Card** 32GB Class 10 (A1/A2) | 1 | OS + data storage |

---

## Total Cost Summary

| Tier | Category | ₱ | Notes |
|------|----------|---|-------|
| **MVP** | Core + breadboard + power | **~₱2,410** | ESP32 + 1 sensor + web dashboard (prove concept) |
| **Standard** | All ESP32-side components + enclosure | **~₱6,915** | Full 5-sensor system with latching valves |
| **Complete** | Standard + Pi backend (already owned) | **~₱6,915** | Production-ready with ML backend (Pi hardware excluded) |

> **Note:** Raspberry Pi, touchscreen, PSU, HDMI, and SD card are **already purchased** — excluded from cost totals above.

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