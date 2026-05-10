# CY16 Use Cases and Implementation Plan

This document outlines the strategic use cases for the CY7C67200 (EZ-OTG) USB controller on the Terasic DE2-115 board and defines a phased roadmap for implementation.

## 1. Technical Constraints & Environment

Understanding the resource limitations is critical for developing efficient CY16 software.

*   **Processor:** 16-bit RISC (CY16 core) @ 48 MHz.
*   **Memory Architecture:**
    *   **Total Address Space:** 64 KB (0x0000 - 0xFFFF).
    *   **Internal RAM:** 16 KB (8K x 16-bit words). Shared between code, stack, and data.
    *   **Internal ROM:** 8 KB (4K x 16-bit words). Contains the fixed BIOS.
*   **Memory Map (Standard BIOS Layout):**
    *   `0x0000 - 0x0400`: BIOS Vectors and Stack (Stack grows down from 0x0400).
    *   `0x0400 - 0x04A4`: BIOS variables and LCP (Local Control Processor) state.
    *   `0x04A4 - 0x3FFF`: **User RAM (approx. 15 KB)**. Primary area for user code and heap.
    *   `0xC000 - 0xC0FF`: Memory-mapped CPU and Peripheral registers.
    *   `0xE000 - 0xFFFF`: BIOS Mask ROM.
*   **Loading & Persistence:**
    *   **HPI (Host Processor Interface):** The DE2-115 connects the CY7C67200 to the FPGA via a 16-bit parallel interface. An FPGA soft-core (Nios II or VexRiscv) can load code directly into CY16 RAM.
    *   **SCAN Images:** The project's `cy16-scanwrap` tool generates BIOS-compatible records.
    *   **Persistence:** Code can be persisted in an external I2C EEPROM (connected to CY16 GPIOs) or stored in the FPGA's configuration flash and reloaded by the FPGA on every boot.

---

## 2. Identified Use Cases

### A. USB Stack Offload (FPGA Acceleration)
*   **Description:** Move the massive complexity of USB enumeration and protocol handling from FPGA hardware (Verilog) to the CY16 C environment.
*   **FPGA Interface:** A high-level command/response protocol over HPI (e.g., "GET_REPORT", "WRITE_ENDPOINT").
*   **Compatibility:** Can co-exist with **Bridge Mode**.

### B. Custom USB HID Device Emulation
*   **Description:** Use the DE2-115 as a Peripheral (Slave). The C compiler allows for complex HID descriptors (Joysticks, MIDI, specialized sensors).
*   **FPGA Interface:** FPGA logic generates raw data; CY16 packages it into USB packets.
*   **Compatibility:** Independent mode; usually mutually exclusive with Host mode during a single session.

### C. Standalone Host (Headless Operation)
*   **Description:** The CY16 acts as a Host to read configuration from a USB thumb drive or receive input from a USB keyboard without an external PC.
*   **FPGA Interface:** CY16 sends configuration data or keypresses to the FPGA.
*   **Compatibility:** Can co-exist with **Smart I/O**.

### D. Smart I/O & System Watchdog
*   **Description:** The CY16 monitors FPGA health and environmental sensors. It can perform an FPGA reconfiguration or system reset if the main logic hangs.
*   **Compatibility:** High; should be integrated as a background task in most use cases.

---

## 3. Implementation Roadmap

### Phase 1: The HPI Bridge (Foundational)
*   **Goal:** Establish bidirectional communication between the DE2-115 soft-core and the CY16.
*   **Tasks:**
    *   Implement a "Mailbox" driver in C for the CY16.
    *   Implement a companion driver in the FPGA (Nios II/RISC-V) to write to CY16 RAM.
    *   **Success:** FPGA loads a "Hello World" that toggles a CY16 GPIO.

### Phase 2: HID Peripheral Skeleton
*   **Goal:** Emulate a standard USB Mouse or Keyboard.
*   **Tasks:**
    *   Develop a minimal USB Framework in C for the CY16 (Endpoint management).
    *   Define HID descriptors in a C header.
    *   **Success:** A PC recognizes the DE2-115 as a generic HID device.

### Phase 3: Host Lite (Mass Storage / Keyboard)
*   **Goal:** Read a file from a FAT32-formatted USB stick.
*   **Tasks:**
    *   Port a minimal FAT library (e.g., Petit FatFs) to CY16.
    *   Implement basic USB Host enumeration for Mass Storage Class (MSC).
    *   **Success:** FPGA registers change based on a `config.txt` file on a USB drive.

### Phase 4: Full Stack Integration (The "libcy16-usb" library)
*   **Goal:** Create a robust, reusable C library for all CY16 USB operations.
*   **Tasks:**
    *   Abstract hardware registers into a clean C API.
    *   Support concurrent Peripheral/Host operations (if supported by hardware strapping).
    *   **Success:** A unified "driver" that future DE2-115 students can use without knowing CY16 assembly.
