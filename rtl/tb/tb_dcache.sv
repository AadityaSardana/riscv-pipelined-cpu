`timescale 1ns/1ps
module tb_dcache;
    logic clk, rst;
    initial clk = 0;
    always #5 clk = ~clk;
    logic [31:0] addr;
    logic        rd_en, wr_en;
    logic [2:0]  funct3;
    logic [31:0] wr_data;
    logic [31:0] data_out;
    logic        stall;
    logic [31:0] main_mem [0:1023];
    logic [31:0] mem_wr_data, mem_wr_addr;
    logic        mem_wr_en;
    logic [31:0] perf_hits, perf_misses, perf_acc;

    dcache #(.LINES(256), .MEM_DELAY(3)) dut (
        .clk(clk), .rst(rst),
        .addr(addr), .rd_en(rd_en), .wr_en(wr_en),
        .funct3(funct3), .wr_data(wr_data),
        .data_out(data_out), .stall(stall),
        .main_mem(main_mem),
        .mem_wr_data(mem_wr_data),
        .mem_wr_addr(mem_wr_addr),
        .mem_wr_en(mem_wr_en),
        .perf_hits(perf_hits),
        .perf_misses(perf_misses),
        .perf_acc(perf_acc)
    );

    task wait_ready;
        integer t;
        begin
            t = 0;
            while (stall && t < 20) begin
                @(posedge clk); #1; t = t+1;
            end
        end
    endtask

    integer i;
    initial begin
        for (i=0;i<1024;i=i+1) main_mem[i] = 32'hDEAD0000 + i;
        main_mem[0]  = 32'h12345678;
        main_mem[1]  = 32'hAABBCCDD;
        main_mem[25] = 32'hCAFEBABE;
        rst=1; rd_en=0; wr_en=0;
        addr=0; funct3=3'b010; wr_data=0;
        repeat(4) @(posedge clk); rst=0;
        @(posedge clk); #1;

        $display("=== DCACHE TESTBENCH ===");

        // TEST 1: Cold miss
        $display("\nTEST 1: Cold miss");
        addr=32'h0; rd_en=1; wr_en=0; funct3=3'b010;
        @(posedge clk); #1;
        if (stall) $display("  COLD MISS stall=1 PASS ✅");
        else       $display("  COLD MISS stall=0 FAIL ❌");
        wait_ready(); rd_en=0; @(posedge clk); #1;

        // TEST 2: Hit same address
        $display("TEST 2: Cache hit");
        addr=32'h0; rd_en=1; wr_en=0; funct3=3'b010;
        @(posedge clk); #1;
        if (!stall && data_out===32'h12345678)
            $display("  HIT PASS data=0x%08X ✅", data_out);
        else
            $display("  HIT FAIL stall=%0d data=0x%08X ❌", stall, data_out);
        rd_en=0; @(posedge clk); #1;

        // TEST 3: SW then LW
        $display("TEST 3: Write then Read");
        addr=32'h4; rd_en=1; wr_en=0; funct3=3'b010;
        @(posedge clk); #1; wait_ready(); rd_en=0; @(posedge clk); #1;
        addr=32'h4; wr_en=1; rd_en=0; funct3=3'b010; wr_data=32'hDEADBEEF;
        @(posedge clk); #1; wait_ready(); wr_en=0; @(posedge clk); #1;
        addr=32'h4; rd_en=1; wr_en=0; funct3=3'b010;
        @(posedge clk); #1; wait_ready();
        if (data_out===32'hDEADBEEF)
            $display("  SW->LW PASS data=0x%08X ✅", data_out);
        else
            $display("  SW->LW FAIL expected=0xDEADBEEF got=0x%08X ❌", data_out);
        rd_en=0; @(posedge clk); #1;

        // TEST 4: SB then LW
        $display("TEST 4: Write byte then Read word");
        addr=32'h0; wr_en=1; rd_en=0; funct3=3'b000; wr_data=32'h000000AB;
        @(posedge clk); #1; wait_ready(); wr_en=0; @(posedge clk); #1;
        addr=32'h0; rd_en=1; wr_en=0; funct3=3'b010;
        @(posedge clk); #1; wait_ready();
        if (data_out===32'h123456AB)
            $display("  SB->LW PASS data=0x%08X ✅", data_out);
        else
            $display("  SB->LW FAIL expected=0x123456AB got=0x%08X ❌", data_out);
        rd_en=0; @(posedge clk); #1;

        // SUMMARY
        $display("\n=== PERFORMANCE ===");
        $display("  Accesses : %0d", perf_acc);
        $display("  Hits     : %0d", perf_hits);
        $display("  Misses   : %0d", perf_misses);
        $display("=== DONE ===");
        $finish;
    end
endmodule
