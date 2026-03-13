// ─────────────────────────────────────────────
//  Register File — 32 x 32-bit registers
//  x0 hardwired to zero
//  Write-before-read (same cycle forwarding)
// ─────────────────────────────────────────────
module regfile (
    input  logic        clk,
    input  logic        rst,
    // Read ports (combinational)
    input  logic [4:0]  rs1_addr,
    input  logic [4:0]  rs2_addr,
    output logic [31:0] rs1_data,
    output logic [31:0] rs2_data,
    // Write port (clocked)
    input  logic [4:0]  rd_addr,
    input  logic [31:0] rd_data,
    input  logic        rd_wen    // write enable
);

    logic [31:0] regs [0:31];

    // Write on rising clock edge
    always_ff @(posedge clk) begin
        if (rst) begin
            integer i;
            for (i = 0; i < 32; i++)
                regs[i] <= 32'd0;
        end else if (rd_wen && rd_addr != 5'd0) begin
            regs[rd_addr] <= rd_data;
        end
    end

    // Read with write-before-read forwarding
    assign rs1_data = (rs1_addr == 5'd0) ? 32'd0 :
                      (rd_wen && rd_addr == rs1_addr) ? rd_data :
                      regs[rs1_addr];

    assign rs2_data = (rs2_addr == 5'd0) ? 32'd0 :
                      (rd_wen && rd_addr == rs2_addr) ? rd_data :
                      regs[rs2_addr];

endmodule

