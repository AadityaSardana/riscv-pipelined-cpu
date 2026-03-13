# RISC-V Pipelined CPU — RV32I on Sky130 130nm

A fully functional 5-stage pipelined RISC-V CPU designed from scratch in SystemVerilog, 
synthesized and taped out using OpenLane on the SkyWater Sky130 130nm open-source PDK.

## Features
- Full RV32I base integer instruction set
- 5-stage pipeline: IF → ID → EX → MEM → WB
- Data hazard detection and forwarding unit
- Control hazard handling with branch prediction
- 2-bit saturating counter Branch History Table (BHT)
- L1 Instruction Cache and L1 Data Cache
- Complete GDS layout generated via OpenLane
- Verified with simulation testbench

## Project Structure
- rtl/src/ — All SystemVerilog RTL source files
- rtl/tb/  — Testbenches for simulation
- iss/     — Instruction Set Simulator in Python
- tests/   — Test programs

## RTL Modules
| Module | Description |
|--------|-------------|
| alu.sv | 10-operation Arithmetic Logic Unit |
| regfile.sv | 32×32-bit Register File with forwarding |
| imm_gen.sv | Immediate Generator for all 5 formats |
| decoder.sv | Control signal decoder |
| hazard_unit.sv | Pipeline hazard detection |
| forward_unit.sv | Data forwarding unit |
| icache.sv | L1 Instruction Cache |
| dcache.sv | L1 Data Cache |
| bht.sv | Branch History Table |
| pipeline.sv | Top-level pipeline integration |

## How to Run Simulation
Install Icarus Verilog, then run:
cd rtl
iverilog -g2012 -o sim src/*.sv tb/testbench.sv
vvp sim

## Results
- All RV32I instructions verified in simulation
- Demo program computing sum 1 to 10 = 55 passes correctly
- GDS file successfully generated with OpenLane on Sky130 PDK
- Design ready for Google MPW submission

## Tools Used
- SystemVerilog — Hardware description language
- Icarus Verilog — Open source RTL simulator
- OpenLane — RTL to GDS flow
- SkyWater Sky130 — Open source 130nm PDK
- GTKWave — Waveform viewer

## Author
Aaditya Sardana
