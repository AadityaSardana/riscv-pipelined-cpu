module testbench;
    logic        clk, rst;
    logic [31:0] pc_out;
    logic        halt;

    pipeline dut (
        .clk(clk), .rst(rst),
        .pc_out(pc_out), .halt(halt)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, testbench);

        // Fibonacci: fib(10) = 55
        // addr 0:  addi x1, x0, 10    n=10
        // addr 4:  addi x2, x0, 0     a=0
        // addr 8:  addi x3, x0, 1     b=1
        // addr 12: addi x4, x0, 0     counter=0
        // addr 16: beq  x4, x1, +24   if counter==10 goto done (addr 40)
        // addr 20: add  x5, x2, x3    temp = a+b
        // addr 24: addi x2, x3, 0     a = b
        // addr 28: addi x3, x5, 0     b = temp
        // addr 32: addi x4, x4, 1     counter++
        // addr 36: beq  x0, x0, -20   goto loop (addr 16)
        // addr 40: ecall

        dut.imem[0]  = 32'h00A00093; // addi x1, x0, 10
        dut.imem[1]  = 32'h00000113; // addi x2, x0, 0
        dut.imem[2]  = 32'h00100193; // addi x3, x0, 1
        dut.imem[3]  = 32'h00000213; // addi x4, x0, 0
        dut.imem[4]  = 32'h00120C63; // beq  x4, x1, +24
        dut.imem[5]  = 32'h003102B3; // add  x5, x2, x3
        dut.imem[6]  = 32'h00018113; // addi x2, x3, 0
        dut.imem[7]  = 32'h00028193; // addi x3, x5, 0
        dut.imem[8]  = 32'h00120213; // addi x4, x4, 1
        dut.imem[9]  = 32'hFE0006E3; // beq  x0, x0, -20  ← FIXED
        dut.imem[10] = 32'h00000073; // ecall

        rst = 1;
        repeat(3) @(posedge clk);
        rst = 0;

        repeat(300) @(posedge clk);

        $display("--- Fibonacci Test ---");
        $display("fib(10) in x2 = %0d (expect 55)", dut.regfile0.regs[2]);
        $display("fib(11) in x3 = %0d (expect 89)", dut.regfile0.regs[3]);
        $display("counter in x4 = %0d (expect 10)", dut.regfile0.regs[4]);

        if (dut.regfile0.regs[2]==32'd55 &&
            dut.regfile0.regs[3]==32'd89 &&
            dut.regfile0.regs[4]==32'd10)
            $display("FIBONACCI TEST PASSED");
        else
            $display("FIBONACCI TEST FAILED");

        $finish;
    end
endmodule