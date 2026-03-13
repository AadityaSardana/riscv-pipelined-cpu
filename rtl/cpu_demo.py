#!/usr/bin/env python3
import subprocess, os, sys

BANNER = """
╔══════════════════════════════════════════════════════╗
║         RISC-V RV32I CPU — Interactive Demo          ║
║   5-Stage Pipeline | L1 Cache | Branch Predictor     ║
║         Built from scratch in SystemVerilog          ║
╚══════════════════════════════════════════════════════╝
"""

def compile_cpu():
    r = subprocess.run([
        "iverilog", "-g2012", "-o", "sim_interactive",
        "src/pipeline.sv", "src/alu.sv", "src/regfile.sv",
        "src/imm_gen.sv", "src/decoder.sv",
        "src/hazard_unit.sv", "src/forward_unit.sv",
        "src/icache.sv", "src/dcache.sv", "src/bht.sv",
        "tb/tb_interactive.sv"
    ], capture_output=True, text=True)
    return r.returncode == 0

def run_sim():
    r = subprocess.run(["vvp", "sim_interactive"],
                      capture_output=True, text=True)
    stats = {}
    for line in r.stdout.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            try: stats[k.strip()] = int(v.strip())
            except: pass
    return stats

def show_stats(stats, result, expected, program, n):
    ih = stats.get("ICACHE_HITS", 0)
    im = stats.get("ICACHE_MISSES", 0)
    dh = stats.get("DCACHE_HITS", 0)
    dm = stats.get("DCACHE_MISSES", 0)
    bp = stats.get("BHT_PREDS", 0)
    bm = stats.get("BHT_MISS", 0)
    total_i = ih + im
    total_b = bp
    i_pct = int(ih*100/total_i) if total_i > 0 else 0
    b_pct = int((bp-bm)*100/total_b) if total_b > 0 else 0
    ok = result == expected
    status = "✅ CORRECT" if ok else f"❌ WRONG (expected {expected})"

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print(f"║  Program  : {program}({n})".ljust(55) + "║")
    print(f"║  Input    : N = {n}".ljust(55) + "║")
    print(f"║  Output   : {result}".ljust(55) + "║")
    print(f"║  Status   : {status}".ljust(55) + "║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║  HARDWARE PERFORMANCE:                               ║")
    print(f"║  I-Cache  : {ih} hits / {im} misses ({i_pct}% hit rate)".ljust(55) + "║")
    print(f"║  D-Cache  : {dh} hits / {dm} misses".ljust(55) + "║")
    print(f"║  BHT      : {bp} predictions / {bm} mispredicts ({b_pct}% accuracy)".ljust(55) + "║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║  CHIP INFO:                                          ║")
    print("║  Process  : Sky130 130nm PDK                         ║")
    print("║  Pipeline : 5-stage (IF/ID/EX/MEM/WB)               ║")
    print("║  Cache    : 256-line L1 I$ + D$                      ║")
    print("║  Predictor: 2-bit Bimodal BHT (256 entries)          ║")
    print("╚══════════════════════════════════════════════════════╝")

def write_sum_tb(n):
    tb = f"""`timescale 1ns/1ps
module tb_interactive;
    logic clk=0,rst;
    logic [31:0] pc_out;
    logic halt;
    always #5 clk=~clk;
    pipeline dut(.clk(clk),.rst(rst),.pc_out(pc_out),.halt(halt));
    integer i;
    initial begin
        for(i=0;i<1024;i=i+1) begin dut.imem[i]=32'h00000013; dut.dmem[i]=0; end
        dut.imem[0] = 32'h00000093;
        dut.imem[1] = 32'h00000113;
        dut.imem[2] = 32'h{((n&0xFFF)<<20)|0x00000193:08X};
        dut.imem[3] = 32'h00108093;
        dut.imem[4] = 32'h00110133;
        dut.imem[5] = 32'hFE309CE3;
        dut.imem[6] = 32'h00000073;
        rst=1; repeat(4) @(posedge clk); rst=0;
        repeat(500) @(posedge clk);
        $display("RESULT:%0d", dut.regfile0.regs[2]);
        $display("ICACHE_HITS:%0d",   dut.icache0.perf_hits);
        $display("ICACHE_MISSES:%0d", dut.icache0.perf_misses);
        $display("DCACHE_HITS:%0d",   dut.dcache0.perf_hits);
        $display("DCACHE_MISSES:%0d", dut.dcache0.perf_misses);
        $display("BHT_PREDS:%0d",     dut.bht0.perf_predictions);
        $display("BHT_MISS:%0d",      dut.bht0.perf_mispredicts);
        $finish;
    end
endmodule"""
    with open("tb/tb_interactive.sv", "w") as f:
        f.write(tb)

def write_fib_tb(n):
    tb = f"""`timescale 1ns/1ps
module tb_interactive;
    logic clk=0,rst;
    logic [31:0] pc_out;
    logic halt;
    always #5 clk=~clk;
    pipeline dut(.clk(clk),.rst(rst),.pc_out(pc_out),.halt(halt));
    integer i;
    initial begin
        for(i=0;i<1024;i=i+1) begin dut.imem[i]=32'h00000013; dut.dmem[i]=0; end
        dut.imem[0] = 32'h00000093;
        dut.imem[1] = 32'h00100113;
        dut.imem[2] = 32'h{((n&0xFFF)<<20)|0x00000193:08X};
        dut.imem[3] = 32'h00208233;
        dut.imem[4] = 32'h00010093;
        dut.imem[5] = 32'h00020113;
        dut.imem[6] = 32'hFFF18193;
        dut.imem[7] = 32'hFE019CE3;
        dut.imem[8] = 32'h00000073;
        rst=1; repeat(4) @(posedge clk); rst=0;
        repeat(600) @(posedge clk);
        $display("RESULT:%0d", dut.regfile0.regs[1]);
        $display("ICACHE_HITS:%0d",   dut.icache0.perf_hits);
        $display("ICACHE_MISSES:%0d", dut.icache0.perf_misses);
        $display("DCACHE_HITS:%0d",   dut.dcache0.perf_hits);
        $display("DCACHE_MISSES:%0d", dut.dcache0.perf_misses);
        $display("BHT_PREDS:%0d",     dut.bht0.perf_predictions);
        $display("BHT_MISS:%0d",      dut.bht0.perf_mispredicts);
        $finish;
    end
endmodule"""
    with open("tb/tb_interactive.sv", "w") as f:
        f.write(tb)

def write_mul_tb(a, b):
    # multiply a*b using repeated addition
    tb = f"""`timescale 1ns/1ps
module tb_interactive;
    logic clk=0,rst;
    logic [31:0] pc_out;
    logic halt;
    always #5 clk=~clk;
    pipeline dut(.clk(clk),.rst(rst),.pc_out(pc_out),.halt(halt));
    integer i;
    initial begin
        for(i=0;i<1024;i=i+1) begin dut.imem[i]=32'h00000013; dut.dmem[i]=0; end
        // x1=a, x2=b, x3=result=0, x4=counter
        dut.imem[0] = 32'h{((a&0xFFF)<<20)|0x00000093:08X}; // addi x1,x0,a
        dut.imem[1] = 32'h{((b&0xFFF)<<20)|0x00000113:08X}; // addi x2,x0,b
        dut.imem[2] = 32'h00000193; // addi x3,x0,0 result=0
        dut.imem[3] = 32'h00000213; // addi x4,x0,0 counter=0
        // loop: result += a, counter++
        dut.imem[4] = 32'h00118133; // add x2,x3,x1  -- wait rewrite
        dut.imem[4] = 32'h00118193; // x3 = x3 + x1
        dut.imem[4] = 32'h001181B3; // x3 = x3 + x1
        dut.imem[5] = 32'h00120213; // addi x4,x4,1
        dut.imem[6] = 32'hFE2208E3; // beq x4,x2,-8 -- if counter!=b loop
        dut.imem[6] = 32'hFE209CE3; // bne x4,x2,-8
        dut.imem[7] = 32'h00000073;
        rst=1; repeat(4) @(posedge clk); rst=0;
        repeat(1000) @(posedge clk);
        $display("RESULT:%0d", dut.regfile0.regs[3]);
        $display("ICACHE_HITS:%0d",   dut.icache0.perf_hits);
        $display("ICACHE_MISSES:%0d", dut.icache0.perf_misses);
        $display("DCACHE_HITS:%0d",   dut.dcache0.perf_hits);
        $display("DCACHE_MISSES:%0d", dut.dcache0.perf_misses);
        $display("BHT_PREDS:%0d",     dut.bht0.perf_predictions);
        $display("BHT_MISS:%0d",      dut.bht0.perf_mispredicts);
        $finish;
    end
endmodule"""
    with open("tb/tb_interactive.sv", "w") as f:
        f.write(tb)

def fib(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, a+b
    return a

def main():
    print(BANNER)
    print("  Your RISC-V CPU chip has been taped out on Sky130 130nm PDK!")
    print("  GDS file: runs/RUN_2026-03-11_04-58-39/pipeline.klayout.gds")
    print()

    while True:
        print("─" * 56)
        print("  Choose a program to run on YOUR CPU:")
        print("  1. Sum  →  compute 1+2+3+...+N")
        print("  2. Fibonacci  →  compute fib(N)")
        print("  3. Exit")
        print("─" * 56)

        choice = input("  Enter choice (1-3): ").strip()

        if choice == "3":
            print()
            print("  Your chip layout: pipeline.klayout.gds")
            print("  Post it on LinkedIn! 🚀")
            break

        elif choice == "1":
            try:
                n = int(input("  Enter N (1-20): "))
                n = max(1, min(20, n))
                expected = n*(n+1)//2
                print(f"\n  Loading program onto CPU...")
                write_sum_tb(n)
                if compile_cpu():
                    print(f"  Executing sum(1..{n}) on 5-stage pipeline...")
                    stats = run_sim()
                    show_stats(stats, stats.get("RESULT",0),
                               expected, "sum_1_to", n)
                else:
                    print("  Compile error!")
            except ValueError:
                print("  Please enter a valid number!")

        elif choice == "2":
            try:
                n = int(input("  Enter N (1-12): "))
                n = max(1, min(12, n))
                expected = fib(n)
                print(f"\n  Loading Fibonacci program onto CPU...")
                write_fib_tb(n)
                if compile_cpu():
                    print(f"  Executing fib({n}) on 5-stage pipeline...")
                    stats = run_sim()
                    show_stats(stats, stats.get("RESULT",0),
                               expected, "fibonacci", n)
                else:
                    print("  Compile error!")
            except ValueError:
                print("  Please enter a valid number!")
        print()

if __name__ == "__main__":
    main()
