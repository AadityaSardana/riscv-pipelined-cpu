content = """module testbench;
    logic        clk, rst;
    logic [31:0] pc_out;
    logic        halt;

    pipeline dut (
        .clk(clk), .rst(rst),
        .pc_out(pc_out), .halt(halt)
    );

    // Clock: toggle every 5ns
    initial clk = 0;
    always #5 clk = ~clk;

    // Load program and run
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, testbench);

        // Load test program into instruction memory
        // Test: addi x1,x0,10 | addi x2,x0,20 | add x3,x1,x2 | ecall
        dut.imem[0] = 32'h00A00093; // addi x1, x0, 10
        dut.imem[1] = 32'h01400113; // addi x2, x0, 20
        dut.imem[2] = 32'h002081B3; // add  x3, x1, x2
        dut.imem[3] = 32'h00000073; // ecall

        // Reset
        rst = 1;
        repeat(3) @(posedge clk);
        rst = 0;

        // Run until halt or timeout
        repeat(50) begin
            @(posedge clk);
            if (halt) begin
                $display("--- Simulation Complete ---");
                $display("PC  = 0x%08h", pc_out);
                $display("x1  = %0d (expect 10)",  dut.regfile0.regs[1]);
                $display("x2  = %0d (expect 20)",  dut.regfile0.regs[2]);
                $display("x3  = %0d (expect 30)",  dut.regfile0.regs[3]);
                if (dut.regfile0.regs[3] == 32'd30)
                    $display("TEST PASSED");
                else
                    $display("TEST FAILED");
                $finish;
            end
        end
        $display("TIMEOUT - halt never reached");
        $finish;
    end

endmodule"""

open('../tb/testbench.sv', 'w').write(content)
print('Done!')

