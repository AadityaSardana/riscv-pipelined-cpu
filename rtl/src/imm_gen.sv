// ─────────────────────────────────────────────
//  Immediate Generator
//  Extracts and sign-extends immediates
//  for all 6 RV32I instruction formats
// ─────────────────────────────────────────────
module imm_gen (
    input  logic [31:0] instr,
    output logic [31:0] imm_i,   // I-type
    output logic [31:0] imm_s,   // S-type
    output logic [31:0] imm_b,   // B-type
    output logic [31:0] imm_u,   // U-type
    output logic [31:0] imm_j    // J-type
);

    // I-type: bits [31:20]
    assign imm_i = {{20{instr[31]}}, instr[31:20]};

    // S-type: bits [31:25] and [11:7]
    assign imm_s = {{20{instr[31]}}, instr[31:25], instr[11:7]};

    // B-type: bits [31],[7],[30:25],[11:8]
    assign imm_b = {{19{instr[31]}}, instr[31], instr[7],
                    instr[30:25], instr[11:8], 1'b0};

    // U-type: bits [31:12]
    assign imm_u = {instr[31:12], 12'd0};

    // J-type: bits [31],[19:12],[20],[30:21]
    assign imm_j = {{11{instr[31]}}, instr[31], instr[19:12],
                    instr[20], instr[30:21], 1'b0};

endmodule

