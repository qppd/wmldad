# Block Diagram — Water Meter with Fixture Leak Detection

## System Overview

```mermaid
block-beta
    columns 6
    
    block:plumbing:6
        columns 6
        
        Inlet["Inlet<br/>Water Supply"]:2
        
        block:sensors1:4
            columns 4
            FS1["Flow Sensor 1<br/>INLET"]
            FS2["Flow Sensor 2<br/>Fixture 1"]
            FS3["Flow Sensor 3<br/>Fixture 2"]
            FS4["Flow Sensor 4<br/>Fixture 3"]
            FS5["Flow Sensor 5<br/>Fixture 4"]
        end
        
        CV1["Check<br/>Valve"] CV2["Check<br/>Valve"] CV3["Check<br/>Valve"] CV4["Check<br/>Valve"] 
        
        F1["Fixture 1"] F2["Fixture 2"] F3["Fixture 3"] F4["Fixture 4"]
    end
    
    space:6
    
    block:esp32_system:6
        columns 6
        
        block:pulses:5
            columns 5
            P1["Pulse<br/>Counter 1"] 
            P2["Pulse<br/>Counter 2"] 
            P3["Pulse<br/>Counter 3"] 
            P4["Pulse<br/>Counter 4"] 
            P5["Pulse<br/>Counter 5"]
        end
        
        block:esp32:6
            columns 6
            
            ESP["ESP32<br/>38-Pin"]:2
            Features["Feature<br/>Extractor"]:2
            ML["Random Forest<br/>Classifier<br/>TFLite Micro"]:2
            
            RelayCtrl["Relay<br/>Controller"]:2
            Logging["SD Card<br/>Logger"]:2
            Display["OLED<br/>Display"]:2
        end
        
        P1 --> ESP
        P2 --> ESP
        P3 --> ESP
        P4 --> ESP
        P5 --> ESP
    end
    
    space:6
    
    block:output:6
        columns 6
        
        Relays["4-Ch Relay<br/>Module"]:2
        
        Valves["Solenoid Valves<br/>×4"]:2
        
        Comms["WiFi<br/>HTTP / MQTT"]:2
    end
    
    RelayCtrl --> Relays
    Relays --> Valves
    ESP --> Comms
    ESP --> Display
    ESP --> Logging
```

## Pin Connections (ESP32 38-Pin)

| Component | ESP32 Pin | Notes |
|-----------|-----------|-------|
| **Flow Sensor 1 (Inlet)** | GPIO 34 | Pulse input, 10kΩ pull-up to 3.3V |
| **Flow Sensor 2 (Fixture 1)** | GPIO 35 | Pulse input, 10kΩ pull-up to 3.3V |
| **Flow Sensor 3 (Fixture 2)** | GPIO 32 | Pulse input, 10kΩ pull-up to 3.3V |
| **Flow Sensor 4 (Fixture 3)** | GPIO 33 | Pulse input, 10kΩ pull-up to 3.3V |
| **Flow Sensor 5 (Fixture 4)** | GPIO 25 | Pulse input, 10kΩ pull-up to 3.3V |
| **Relay 1 (Inlet Valve)** | GPIO 26 | Active LOW |
| **Relay 2 (Fixture 1 Valve)** | GPIO 27 | Active LOW |
| **Relay 3 (Fixture 2 Valve)** | GPIO 14 | Active LOW |
| **Relay 4 (Fixture 3 Valve)** | GPIO 12 | ⚠️ Boot pin — use with pull-down |
| **Relay 5 (Fixture 4 Valve)** | GPIO 13 | Active LOW |
| **OLED SDA** | GPIO 21 | I²C Data |
| **OLED SCL** | GPIO 22 | I²C Clock |
| **Buzzer** | GPIO 4 | Active buzzer (alert on leak) |
| **Status LED** | GPIO 2 | Onboard LED heartbeat |
| **RGB LED** | GPIO 5 | Normal=Green, Warning=Yellow, Leak=Red |
| **SD Card CS** | GPIO 5 | ⚠️ Shared — use mux or change pin |
| **SD Card MOSI** | GPIO 23 | SPI |
| **SD Card MISO** | GPIO 19 | SPI |
| **SD Card SCK** | GPIO 18 | SPI |

> **Important:** GPIOs 34 & 35 are **input-only** — no internal pull-up. Always use external 10kΩ pull-up resistors.

## Power Distribution

```mermaid
block-beta
    columns 4
    
    AC["220V AC"] --> PSU["5V 2A<br/>Adapter"]
    PSU --> ESPV["ESP32<br/>VIN (5V)"]
    PSU --> RELAYV["Relay Module<br/>5V"]
    PSU --> VALVEV["Solenoid Valves<br/>(via relay)"]
    PSU --> OLEDV["OLED / Sensors<br/>3.3V (regulator)"]
```

## Component Layout (Enclosure)

```mermaid
block-beta
    columns 3
    
    block:enclosure:3
        columns 3
        
        ESP32Board["ESP32 +<br/>Expansion Board"]:1
        
        RelayBoard["4-Channel<br/>Relay Module"]:1
        
        SDCardSD["SD Card<br/>Module"]:1
        
        OLEDDisp["OLED<br/>Display"]:1
        
        TerminalBlock["Terminal<br/>Blocks<br/>(Sensor Inputs)"]:2
    end
```

## Bill of Materials (Key Items)

| Component | Qty | Purpose |
|-----------|-----|---------|
| ESP32 38-Pin Dev Board | 1 | Main microcontroller |
| ESP32 38-Pin Expansion Board | 1 | Breakout + screw terminals |
| YF-S201 Flow Sensor | 5 | 1 inlet + 4 fixtures |
| Check Valve 1/2" | 4 | Prevent backflow per fixture |
| 4-Ch Relay Module | 1 | Valve control |
| Solenoid Valve 1/2" | 4 | Shutoff per fixture |
| OLED 128×64 | 1 | Display readings |
| Micro SD Card Module | 1 | Local data logging |
| Active Buzzer | 1 | Leak alarm |
| Breadboard + Jumpers | 1 set | Prototyping |

> See [BOM](./bom.md) for complete list with prices and links.
