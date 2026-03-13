module alu (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [3:0]  alu_op,
    output logic [31:0] result,
    output logic        zero
);
    wire [4:0] shamt = b[4:0];

    always_comb begin
        case (alu_op)
            4'd0:    result = a + b;
            4'd1:    result = a - b;
            4'd2:    result = a & b;
            4'd3:    result = a | b;
            4'd4:    result = a ^ b;
            4'd5:    result = a << shamt;
            4'd6:    result = a >> shamt;
            4'd7:    result = $signed(a) >>> shamt;
            4'd8:    result = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            4'd9:    result = (a < b) ? 32'd1 : 32'd0;
            default: result = 32'd0;
        endcase
    end

    assign zero = (result == 32'd0);

endmodule