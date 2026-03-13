module decoder (
    input  logic [6:0] opcode,
    input  logic [2:0] funct3,
    input  logic [6:0] funct7,
    output logic       reg_write,
    output logic       mem_read,
    output logic       mem_write,
    output logic       mem_to_reg,
    output logic       alu_src,
    output logic       branch,
    output logic       jump,
    output logic       jalr,
    output logic [3:0] alu_op
);
    wire is_srai = (funct7 == 7'h20);

    always_comb begin
        reg_write=0; mem_read=0; mem_write=0; mem_to_reg=0;
        alu_src=0; branch=0; jump=0; jalr=0; alu_op=4'd0;

        if (opcode==7'h33) begin
            reg_write=1;
            if      (funct3==3'b000 && funct7==7'h00) alu_op=4'd0;
            else if (funct3==3'b000 && funct7==7'h20) alu_op=4'd1;
            else if (funct3==3'b111) alu_op=4'd2;
            else if (funct3==3'b110) alu_op=4'd3;
            else if (funct3==3'b100) alu_op=4'd4;
            else if (funct3==3'b001) alu_op=4'd5;
            else if (funct3==3'b101 && funct7==7'h00) alu_op=4'd6;
            else if (funct3==3'b101 && funct7==7'h20) alu_op=4'd7;
            else if (funct3==3'b010) alu_op=4'd8;
            else if (funct3==3'b011) alu_op=4'd9;
        end
        else if (opcode==7'h13) begin
            reg_write=1; alu_src=1;
            if      (funct3==3'b000) alu_op=4'd0;
            else if (funct3==3'b111) alu_op=4'd2;
            else if (funct3==3'b110) alu_op=4'd3;
            else if (funct3==3'b100) alu_op=4'd4;
            else if (funct3==3'b001) alu_op=4'd5;
            else if (funct3==3'b101 && is_srai) alu_op=4'd7;
            else if (funct3==3'b101) alu_op=4'd6;
            else if (funct3==3'b010) alu_op=4'd8;
            else if (funct3==3'b011) alu_op=4'd9;
        end
        else if (opcode==7'h03) begin
            reg_write=1; mem_read=1; mem_to_reg=1; alu_src=1;
        end
        else if (opcode==7'h23) begin
            mem_write=1; alu_src=1;
        end
        else if (opcode==7'h63) begin
            branch=1; alu_op=4'd1;
        end
        else if (opcode==7'h6F) begin
            reg_write=1; jump=1;
        end
        else if (opcode==7'h67) begin
            reg_write=1; jump=1; jalr=1; alu_src=1;
        end
        else if (opcode==7'h37) begin
            reg_write=1; alu_src=1;
        end
        else if (opcode==7'h17) begin
            reg_write=1; alu_src=1;
        end
    end
endmodule