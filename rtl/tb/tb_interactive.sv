`timescale 1ns/1ps
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
        dut.imem[2] = 32'h00500193;
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
endmodule