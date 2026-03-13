`timescale 1ns/1ps
module tb_demo;
    logic clk, rst;
    logic [31:0] pc_out;
    logic        halt;
    initial clk = 0;
    always #5 clk = ~clk;

    pipeline dut(.clk(clk),.rst(rst),.pc_out(pc_out),.halt(halt));

    integer i;
    initial begin
        for (i=0;i<1024;i=i+1) begin
            dut.imem[i] = 32'h00000013;
            dut.dmem[i] = 32'h00000000;
        end

        // PROGRAM: Sum 1+2+3+...+10 = 55
        // x1=i(0→10), x2=sum, x3=10(limit)
        // Uses BNE — same as Fibonacci, known to work!
        dut.imem[0] = 32'h00000093; // addi x1, x0, 0   → i=0
        dut.imem[1] = 32'h00000113; // addi x2, x0, 0   → sum=0
        dut.imem[2] = 32'h00A00193; // addi x3, x0, 10  → limit=10
        // loop:
        dut.imem[3] = 32'h00108093; // addi x1, x1, 1   → i++
        dut.imem[4] = 32'h00110133; // add  x2, x2, x1  → sum+=i
        dut.imem[5] = 32'hFE309CE3; // bne  x1, x3, -8  → if i!=10 loop
        dut.imem[6] = 32'h00000073; // ecall

        rst=1; repeat(4) @(posedge clk); rst=0;
        repeat(300) @(posedge clk);

        $display("");
        $display("╔══════════════════════════════════════════╗");
        $display("║    RISC-V CPU DEMO — SUM 1 to 10         ║");
        $display("╠══════════════════════════════════════════╣");
        $display("║  Formula: 1+2+3+4+5+6+7+8+9+10          ║");
        $display("║  Expected: 55                            ║");
        $display("╠══════════════════════════════════════════╣");
        $display("║  x1 (counter) = %2d  (expect 10)          ║",
            dut.regfile0.regs[1]);
        $display("║  x2 (sum)     = %2d  (expect 55)          ║",
            dut.regfile0.regs[2]);
        $display("╠══════════════════════════════════════════╣");
        if (dut.regfile0.regs[2] == 55)
            $display("║         ✅  CPU TEST PASSED!              ║");
        else
            $display("║         ❌  FAILED (expect 55)            ║");
        $display("╠══════════════════════════════════════════╣");
        $display("║  HARDWARE STATS:                         ║");
        $display("║  I-Cache: %0d hits  / %0d misses           ║",
            dut.icache0.perf_hits, dut.icache0.perf_misses);
        $display("║  D-Cache: %0d hits  / %0d misses            ║",
            dut.dcache0.perf_hits, dut.dcache0.perf_misses);
        $display("║  BHT:     %0d preds / %0d mispredicts       ║",
            dut.bht0.perf_predictions, dut.bht0.perf_mispredicts);
        $display("╚══════════════════════════════════════════╝");
        $finish;
    end
endmodule
