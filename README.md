# Project overview

This is the project of MECHTRON 3K04 in McMaster University, done by Johnson Ji, Hongliang Qi, Kelby To, Arian Nik and Ryan Wang in 2025 fall.
This repository contains the software and firmware implementation for a safety-critical Pacemaker System. The project bridges high-level software control with low-level hardware actuation through a custom serial protocol.

## Key Components

### Device Controller-Monitor (DCM):

GUI: Built with Python (Tkinter), providing an intuitive interface for doctors/technicians.

User Management: Secure local registration and login system (max 10 users) with secure password hashing.

Parameter Control: Validation and transmission of programmable parameters (e.g., LRL, URL, Amplitude, Pulse Width) with strict range and step enforcement.

Real-Time Visualization: Live Egram (Electrogram) plotting using Matplotlib, displaying Atrial and Ventricular signals streamed from the hardware.

### Embedded Pacemaker - Simulink & Hardware

Hardware Platform: NXP FRDM-K64F (K64P144M120SF5).

Model-Based Design: The firmware drivers and control logic are strictly modeled in Simulink.

Stateflow Logic: Utilizes finite state machines to manage 8 pacing modes: AOO, VOO, AAI, VVI and their rate-adaptive variants AOOR, VOOR, AAIR, VVIR.

Hardware Hiding: Implements an abstraction layer (Hardware Hiding Module) to map logical signals to physical I/O pins (GPIO, PWM) and sensors (accelerometer).

Real-Time Safety: Enforces critical timing constraints (refractory periods, blanking windows) directly within the model structure.

### Communication Interface

Serial Protocol: A robust UART-based protocol connecting the Python DCM and the K64F board.

Packet Structure: Uses fixed-length packets with SYNC/SOH headers and checksum validation for reliable parameter transmission and live Egram data streaming.
