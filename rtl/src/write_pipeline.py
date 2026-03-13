content = """module pipeline (
    input  logic        clk,
    input  logic        rst,
    output logic [31:0] pc_out,
    output logic        halt
);
    // ── Memories ─────────────────────────────
    logic [31:0] imem [0:1023];
    logic [31:0] dmem [0:1023];

    // ── PC ───────────────────────────────────
    logic [31:0] pc, pc_next;

    // ── IF/ID register ────────────────────────
    logic [31:0] if_id_pc, if_id_instr;

    // ── ID/EX register ────────────────────────
    logic [31:0] id_ex_pc;
    logic [31:0] id_ex_rs1_data, id_ex_rs2_data;
    logic [31:0] id_ex_imm_i, id_ex_imm_s;
    logic [31:0] id_ex_imm_b, id_ex_imm_u, id_ex_imm_j;
    logic [4:0]  id_ex_rs1, id_ex_rs2, id_ex_rd;
    logic [2:0]  id_ex_funct3;
    logic [6:0]  id_ex_funct7;
    logic        id_ex_reg_write, id_ex_mem_read;
    logic        id_ex_mem_write, id_ex_mem_to_reg;
    logic        id_ex_alu_src, id_ex_branch;
    logic        id_ex_jump, id_ex_jalr;
    logic [3:0]  id_ex_alu_op;

    // ── EX/MEM register ───────────────────────
    logic [31:0] ex_mem_alu_result, ex_mem_rs2_data;
    logic [31:0] ex_mem_pc_plus4;
    logic [4:0]  ex_mem_rd;
    logic        ex_mem_reg_write, ex_mem_mem_read;
    logic        ex_mem_mem_write, ex_mem_mem_to_reg;
    logic        ex_mem_branch, ex_mem_jump;
    logic        ex_mem_branch_taken;
    logic [31:0] ex_mem_branch_target;
    logic [2:0]  ex_mem_funct3;

    // ── MEM/WB register ───────────────────────
    logic [31:0] mem_wb_alu_result, mem_wb_mem_data;
    logic [31:0] mem_wb_pc_plus4;
    logic [4:0]  mem_wb_rd;
    logic        mem_wb_reg_write, mem_wb_mem_to_reg;

    // ── Wires ─────────────────────────────────
    logic [31:0] instr;
    logic [6:0]  opcode;
    logic [4:0]  rs1_addr, rs2_addr, rd_addr;
    logic [2:0]  funct3;
    logic [6:0]  funct7;
    logic [31:0] imm_i, imm_s, imm_b, imm_u, imm_j;
    logic [31:0] rs1_data, rs2_data;
    logic        reg_write, mem_read, mem_write;
    logic        mem_to_reg, alu_src, branch, jump, jalr;
    logic [3:0]  alu_op;
    logic [31:0] alu_a, alu_b, alu_result;
    logic        alu_zero;
    logic [1:0]  forward_a, forward_b;
    logic        stall;
    logic [31:0] wb_data;
    logic [31:0] fwd_rs2;
    logic        flush;
    logic        halt_reg;

    assign pc_out = pc;
    assign halt   = halt_reg;
    assign opcode = if_id_instr[6:0];
    assign rd_addr = if_id_instr[11:7];
    assign funct3  = if_id_instr[14:12];
    assign rs1_addr= if_id_instr[19:15];
    assign rs2_addr= if_id_instr[24:20];
    assign funct7  = if_id_instr[31:25];
    assign flush   = ex_mem_branch & ex_mem_branch_taken | ex_mem_jump;

    // ── Submodules ────────────────────────────
    imm_gen imm_gen0 (
        .instr(if_id_instr),
        .imm_i(imm_i), .imm_s(imm_s),
        .imm_b(imm_b), .imm_u(imm_u), .imm_j(imm_j)
    );

    decoder decoder0 (
        .opcode(opcode), .funct3(funct3), .funct7(funct7),
        .reg_write(reg_write), .mem_read(mem_read),
        .mem_write(mem_write), .mem_to_reg(mem_to_reg),
        .alu_src(alu_src), .branch(branch),
        .jump(jump), .jalr(jalr), .alu_op(alu_op)
    );

    regfile regfile0 (
        .clk(clk), .rst(rst),
        .rs1_addr(rs1_addr), .rs2_addr(rs2_addr),
        .rs1_data(rs1_data), .rs2_data(rs2_data),
        .rd_addr(mem_wb_rd), .rd_data(wb_data),
        .rd_wen(mem_wb_reg_write)
    );

    forward_unit fwd0 (
        .id_ex_rs1(id_ex_rs1), .id_ex_rs2(id_ex_rs2),
        .ex_mem_rd(ex_mem_rd), .ex_mem_reg_write(ex_mem_reg_write),
        .mem_wb_rd(mem_wb_rd), .mem_wb_reg_write(mem_wb_reg_write),
        .forward_a(forward_a), .forward_b(forward_b)
    );

    hazard_unit haz0 (
        .id_ex_rd(id_ex_rd), .id_ex_mem_read(id_ex_mem_read),
        .if_id_rs1(rs1_addr), .if_id_rs2(rs2_addr),
        .stall(stall)
    );

    alu alu0 (
        .a(alu_a), .b(alu_b),
        .alu_op(id_ex_alu_op),
        .result(alu_result), .zero(alu_zero)
    );

    // ── Forwarding MUXes ─────────────────────
    always_comb begin
        case (forward_a)
            2'b10:   alu_a = ex_mem_alu_result;
            2'b01:   alu_a = wb_data;
            default: alu_a = id_ex_rs1_data;
        endcase
        case (forward_b)
            2'b10:   fwd_rs2 = ex_mem_alu_result;
            2'b01:   fwd_rs2 = wb_data;
            default: fwd_rs2 = id_ex_rs2_data;
        endcase
        alu_b = id_ex_alu_src ? id_ex_imm_i : fwd_rs2;
    end

    // ── WB MUX ───────────────────────────────
    assign wb_data = mem_wb_mem_to_reg ? mem_wb_mem_data
                   : mem_wb_alu_result;

    // ── Branch logic ─────────────────────────
    logic branch_taken;
    always_comb begin
        branch_taken = 0;
        if (id_ex_branch) begin
            case (id_ex_funct3)
                3'b000: branch_taken = (alu_a == fwd_rs2);
                3'b001: branch_taken = (alu_a != fwd_rs2);
                3'b100: branch_taken = ($signed(alu_a) <  $signed(fwd_rs2));
                3'b101: branch_taken = ($signed(alu_a) >= $signed(fwd_rs2));
                3'b110: branch_taken = (alu_a <  fwd_rs2);
                3'b111: branch_taken = (alu_a >= fwd_rs2);
                default: branch_taken = 0;
            endcase
        end
    end

    // ── PC logic ─────────────────────────────
    logic [31:0] branch_target, jump_target;
    assign branch_target = id_ex_pc + id_ex_imm_b;
    assign jump_target   = id_ex_jalr ? (id_ex_rs1_data + id_ex_imm_i) & ~32'd1
                                      : id_ex_pc + id_ex_imm_j;

    always_comb begin
        if (branch_taken)     pc_next = branch_target;
        else if (id_ex_jump)  pc_next = jump_target;
        else if (stall)       pc_next = pc;
        else                  pc_next = pc + 4;
    end

    // ── HALT detection ───────────────────────
    logic is_ecall;
    assign is_ecall = (if_id_instr == 32'h00000073);

    // ── Pipeline registers (clocked) ─────────
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            pc          <= 32'd0;
            halt_reg    <= 0;
            if_id_pc    <= 0; if_id_instr <= 0;
            id_ex_pc    <= 0;
            id_ex_rs1_data<=0; id_ex_rs2_data<=0;
            id_ex_imm_i <=0; id_ex_imm_s<=0;
            id_ex_imm_b <=0; id_ex_imm_u<=0; id_ex_imm_j<=0;
            id_ex_rs1   <=0; id_ex_rs2<=0; id_ex_rd<=0;
            id_ex_funct3<=0; id_ex_funct7<=0;
            id_ex_reg_write<=0; id_ex_mem_read<=0;
            id_ex_mem_write<=0; id_ex_mem_to_reg<=0;
            id_ex_alu_src<=0; id_ex_branch<=0;
            id_ex_jump<=0; id_ex_jalr<=0; id_ex_alu_op<=0;
            ex_mem_alu_result<=0; ex_mem_rs2_data<=0;
            ex_mem_pc_plus4<=0; ex_mem_rd<=0;
            ex_mem_reg_write<=0; ex_mem_mem_read<=0;
            ex_mem_mem_write<=0; ex_mem_mem_to_reg<=0;
            ex_mem_branch<=0; ex_mem_jump<=0;
            ex_mem_branch_taken<=0; ex_mem_branch_target<=0;
            ex_mem_funct3<=0;
            mem_wb_alu_result<=0; mem_wb_mem_data<=0;
            mem_wb_pc_plus4<=0; mem_wb_rd<=0;
            mem_wb_reg_write<=0; mem_wb_mem_to_reg<=0;
        end else begin
            pc <= pc_next;

            if (is_ecall) halt_reg <= 1;

            // ── IF/ID ──────────────────────────
            if (!stall && !flush) begin
                if_id_instr <= imem[pc[31:2]];
                if_id_pc    <= pc;
            end else if (flush) begin
                if_id_instr <= 32'd0;
                if_id_pc    <= 32'd0;
            end

            // ── ID/EX ──────────────────────────
            if (stall || flush) begin
                id_ex_reg_write<=0; id_ex_mem_read<=0;
                id_ex_mem_write<=0; id_ex_branch<=0;
                id_ex_jump<=0; id_ex_jalr<=0;
                id_ex_rd<=0;
            end else begin
                id_ex_pc        <= if_id_pc;
                id_ex_rs1_data  <= rs1_data;
                id_ex_rs2_data  <= rs2_data;
                id_ex_imm_i     <= imm_i;
                id_ex_imm_s     <= imm_s;
                id_ex_imm_b     <= imm_b;
                id_ex_imm_u     <= imm_u;
                id_ex_imm_j     <= imm_j;
                id_ex_rs1       <= rs1_addr;
                id_ex_rs2       <= rs2_addr;
                id_ex_rd        <= rd_addr;
                id_ex_funct3    <= funct3;
                id_ex_funct7    <= funct7;
                id_ex_reg_write <= reg_write;
                id_ex_mem_read  <= mem_read;
                id_ex_mem_write <= mem_write;
                id_ex_mem_to_reg<= mem_to_reg;
                id_ex_alu_src   <= alu_src;
                id_ex_branch    <= branch;
                id_ex_jump      <= jump;
                id_ex_jalr      <= jalr;
                id_ex_alu_op    <= alu_op;
            end

            // ── EX/MEM ─────────────────────────
            ex_mem_alu_result   <= id_ex_jump ? (id_ex_pc + 4) : alu_result;
            ex_mem_rs2_data     <= fwd_rs2;
            ex_mem_pc_plus4     <= id_ex_pc + 4;
            ex_mem_rd           <= id_ex_rd;
            ex_mem_reg_write    <= id_ex_reg_write;
            ex_mem_mem_read     <= id_ex_mem_read;
            ex_mem_mem_write    <= id_ex_mem_write;
            ex_mem_mem_to_reg   <= id_ex_mem_to_reg;
            ex_mem_branch       <= id_ex_branch;
            ex_mem_jump         <= id_ex_jump;
            ex_mem_branch_taken <= branch_taken;
            ex_mem_branch_target<= branch_target;
            ex_mem_funct3       <= id_ex_funct3;

            // ── MEM/WB ─────────────────────────
            mem_wb_rd           <= ex_mem_rd;
            mem_wb_reg_write    <= ex_mem_reg_write;
            mem_wb_mem_to_reg   <= ex_mem_mem_to_reg;
            mem_wb_alu_result   <= ex_mem_alu_result;
            mem_wb_pc_plus4     <= ex_mem_pc_plus4;

            // Memory read
            if (ex_mem_mem_read) begin
                case (ex_mem_funct3)
                    3'b000: mem_wb_mem_data <= {{24{dmem[ex_mem_alu_result[31:2]][7]}},
                                               dmem[ex_mem_alu_result[31:2]][7:0]};
                    3'b001: mem_wb_mem_data <= {{16{dmem[ex_mem_alu_result[31:2]][15]}},
                                               dmem[ex_mem_alu_result[31:2]][15:0]};
                    3'b010: mem_wb_mem_data <= dmem[ex_mem_alu_result[31:2]];
                    3'b100: mem_wb_mem_data <= {24'd0, dmem[ex_mem_alu_result[31:2]][7:0]};
                    3'b101: mem_wb_mem_data <= {16'd0, dmem[ex_mem_alu_result[31:2]][15:0]};
                    default:mem_wb_mem_data <= dmem[ex_mem_alu_result[31:2]];
                endcase
            end

            // Memory write
            if (ex_mem_mem_write) begin
                case (ex_mem_funct3)
                    3'b000: dmem[ex_mem_alu_result[31:2]][7:0]  <= ex_mem_rs2_data[7:0];
                    3'b001: dmem[ex_mem_alu_result[31:2]][15:0] <= ex_mem_rs2_data[15:0];
                    3'b010: dmem[ex_mem_alu_result[31:2]]       <= ex_mem_rs2_data;
                    default: dmem[ex_mem_alu_result[31:2]]      <= ex_mem_rs2_data;
                endcase
            end
        end
    end

endmodule"""

open('pipeline.sv', 'w').write(content)
print('Done!')

