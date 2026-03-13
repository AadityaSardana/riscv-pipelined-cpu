module pipeline (
    input  logic clk,
    input  logic rst,
    output logic [31:0] pc_out,
    output logic        halt
);
    // ── Memories ──────────────────────────────────
    logic [31:0] imem [0:1023];
    logic [31:0] dmem [0:1023];

    // ── PC ────────────────────────────────────────
    logic [31:0] pc, pc_next;

    // ── IF/ID Register ────────────────────────────
    logic [31:0] if_id_instr, if_id_pc;

    // ── Decode wires ──────────────────────────────
    logic [6:0] opcode, funct7;
    logic [2:0] funct3;
    logic [4:0] rs1_addr, rs2_addr, rd_addr;
    logic [31:0] imm_i, imm_s, imm_b, imm_u, imm_j;
    logic [31:0] rs1_data, rs2_data;
    logic        reg_write_d, mem_read_d, mem_write_d;
    logic        mem_to_reg_d, alu_src_d, branch_d, jump_d, jalr_d;
    logic [3:0]  alu_op_d;

    // ── ID/EX Register ────────────────────────────
    logic [31:0] id_ex_pc;
    logic [31:0] id_ex_rs1_data, id_ex_rs2_data;
    logic [31:0] id_ex_imm_i, id_ex_imm_s, id_ex_imm_b;
    logic [31:0] id_ex_imm_u, id_ex_imm_j;
    logic [4:0]  id_ex_rs1, id_ex_rs2, id_ex_rd;
    logic [2:0]  id_ex_funct3;
    logic        id_ex_reg_write, id_ex_mem_read, id_ex_mem_write;
    logic        id_ex_mem_to_reg, id_ex_alu_src, id_ex_branch;
    logic        id_ex_jump, id_ex_jalr;
    logic [3:0]  id_ex_alu_op;
    logic        id_ex_predicted_taken;
    logic [31:0] id_ex_predicted_target;

    // ── EX wires ──────────────────────────────────
    logic [31:0] alu_a, alu_b;
    logic [31:0] alu_result;
    logic        alu_zero;
    logic [1:0]  forward_a, forward_b;
    logic [31:0] fwd_rs2;
    logic        branch_taken;
    logic [31:0] branch_target, jump_target;

    // ── EX/MEM Register ───────────────────────────
    logic [31:0] ex_mem_alu_result, ex_mem_rs2_data;
    logic [4:0]  ex_mem_rd;
    logic        ex_mem_reg_write, ex_mem_mem_read;
    logic        ex_mem_mem_write, ex_mem_mem_to_reg;
    logic [2:0]  ex_mem_funct3;

    // ── MEM/WB Register ───────────────────────────
    logic [31:0] mem_wb_alu_result, mem_wb_mem_data;
    logic [4:0]  mem_wb_rd;
    logic        mem_wb_reg_write, mem_wb_mem_to_reg;

    // ── WB ────────────────────────────────────────
    logic [31:0] wb_data;

    // ── Cache signals ─────────────────────────────
    logic [31:0] icache_data;
    logic        icache_stall;
    logic [31:0] dcache_data;
    logic        dcache_stall;
    logic [31:0] dc_mem_wr_data, dc_mem_wr_addr;
    logic        dc_mem_wr_en;
    logic [31:0] ic_hits, ic_misses, ic_acc;
    logic [31:0] dc_hits, dc_misses, dc_acc;

    // ── BHT signals ───────────────────────────────
    logic        bht_predict_taken;
    logic [31:0] bht_predict_target;
    logic        bht_update_en;
    logic        mispredict;
    logic [31:0] bht_preds, bht_mispreds;

    // ── Stall / Flush ─────────────────────────────
    logic stall_ldu;
    logic stall;
    logic flush;
    assign stall = stall_ldu | icache_stall | dcache_stall;

    // ══ Submodules ═══════════════════════════════

    // ── BHT ───────────────────────────────────────
    bht #(.ENTRIES(256)) bht0 (
        .clk              (clk),
        .rst              (rst),
        .pc               (pc),
        .predict_taken    (bht_predict_taken),
        .predict_target   (bht_predict_target),
        .imm_b            (imm_b),
        .update_en        (bht_update_en),
        .update_pc        (id_ex_pc),
        .actually_taken   (branch_taken),
        .perf_predictions (bht_preds),
        .perf_mispredicts (bht_mispreds)
    );

    // ── I-Cache ───────────────────────────────────
    logic [9:0]  ic_mem_rd_addr;
    logic [31:0] ic_mem_rd_data;
    assign ic_mem_rd_data = imem[ic_mem_rd_addr];

    icache #(.LINES(256), .MEM_DELAY(3)) icache0 (
        .clk         (clk),
        .rst         (rst),
        .addr        (pc),
        .rd_en       (!flush),
        .data_out    (icache_data),
        .stall       (icache_stall),
        .mem_rd_addr (ic_mem_rd_addr),
        .mem_rd_data (ic_mem_rd_data),
        .perf_hits   (ic_hits),
        .perf_misses (ic_misses),
        .perf_acc    (ic_acc)
    );

    // ── D-Cache ───────────────────────────────────
    logic [9:0]  dc_mem_rd_addr;
    logic [31:0] dc_mem_rd_data;
    assign dc_mem_rd_data = dmem[dc_mem_rd_addr];

    dcache #(.LINES(256), .MEM_DELAY(3)) dcache0 (
        .clk         (clk),
        .rst         (rst),
        .addr        (ex_mem_alu_result),
        .rd_en       (ex_mem_mem_read),
        .wr_en       (ex_mem_mem_write),
        .funct3      (ex_mem_funct3),
        .wr_data     (ex_mem_rs2_data),
        .data_out    (dcache_data),
        .stall       (dcache_stall),
        .mem_rd_addr (dc_mem_rd_addr),
        .mem_rd_data (dc_mem_rd_data),
        .mem_wr_data (dc_mem_wr_data),
        .mem_wr_addr (dc_mem_wr_addr),
        .mem_wr_en   (dc_mem_wr_en),
        .perf_hits   (dc_hits),
        .perf_misses (dc_misses),
        .perf_acc    (dc_acc)
    );

    // Write-through dcache → dmem
    always_ff @(posedge clk) begin
        if (dc_mem_wr_en)
            dmem[dc_mem_wr_addr[11:2]] <= dc_mem_wr_data;
    end

    imm_gen imm_gen0 (
        .instr(if_id_instr),
        .imm_i(imm_i), .imm_s(imm_s), .imm_b(imm_b),
        .imm_u(imm_u), .imm_j(imm_j)
    );

    decoder decoder0 (
        .opcode(opcode), .funct7(funct7), .funct3(funct3),
        .reg_write(reg_write_d), .mem_read(mem_read_d),
        .mem_write(mem_write_d), .mem_to_reg(mem_to_reg_d),
        .alu_src(alu_src_d), .branch(branch_d),
        .jump(jump_d), .jalr(jalr_d), .alu_op(alu_op_d)
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
        .stall(stall_ldu)
    );

    alu alu0 (
        .a(alu_a), .b(alu_b),
        .alu_op(id_ex_alu_op),
        .result(alu_result), .zero(alu_zero)
    );

    // ══ Decode fields ════════════════════════════
    assign opcode   = if_id_instr[6:0];
    assign rd_addr  = if_id_instr[11:7];
    assign funct3   = if_id_instr[14:12];
    assign rs1_addr = if_id_instr[19:15];
    assign rs2_addr = if_id_instr[24:20];
    assign funct7   = if_id_instr[31:25];

    // ══ Forwarding MUXes ═════════════════════════
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

    // ══ Branch logic ═════════════════════════════
    always_comb begin
        branch_taken  = 0;
        branch_target = id_ex_pc + id_ex_imm_b;
        if (id_ex_jump && id_ex_jalr)
            jump_target = (alu_a + id_ex_imm_i) & ~32'd1;
        else
            jump_target = id_ex_pc + id_ex_imm_j;
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

    // ── BHT update + mispredict detection ─────────
    assign bht_update_en = id_ex_branch;
    assign mispredict    = id_ex_branch &&
                           (branch_taken != id_ex_predicted_taken);

    // ══ Flush ════════════════════════════════════
    // Flush on: mispredict OR jump
    assign flush = mispredict | id_ex_jump;

    // ══ PC ═══════════════════════════════════════
    always_comb begin
        if (mispredict)
            // Correct the wrong prediction
            pc_next = branch_taken ? branch_target
                                   : id_ex_pc + 4;
        else if (id_ex_jump)
            pc_next = jump_target;
        else if (bht_predict_taken && !stall)
            // BHT says take branch speculatively
            pc_next = bht_predict_target;
        else if (stall)
            pc_next = pc;
        else
            pc_next = pc + 4;
    end

    always_ff @(posedge clk) begin
        if (rst) pc <= 32'd0;
        else     pc <= pc_next;
    end

    // ══ WB data ══════════════════════════════════
    assign wb_data = mem_wb_mem_to_reg ? mem_wb_mem_data
                                       : mem_wb_alu_result;

    // ══ IF/ID ════════════════════════════════════
    always_ff @(posedge clk) begin
        if (rst || flush) begin
            if_id_instr <= 32'd0;
            if_id_pc    <= 32'd0;
        end else if (!stall) begin
            if_id_instr <= icache_stall ? 32'd0 : icache_data;
            if_id_pc    <= pc;
        end
    end

    // ══ ID/EX ════════════════════════════════════
    always_ff @(posedge clk) begin
        if (rst || flush || stall) begin
            id_ex_pc              <= 32'd0;
            id_ex_rs1_data        <= 32'd0;
            id_ex_rs2_data        <= 32'd0;
            id_ex_imm_i           <= 32'd0;
            id_ex_imm_s           <= 32'd0;
            id_ex_imm_b           <= 32'd0;
            id_ex_imm_u           <= 32'd0;
            id_ex_imm_j           <= 32'd0;
            id_ex_rs1             <= 5'd0;
            id_ex_rs2             <= 5'd0;
            id_ex_rd              <= 5'd0;
            id_ex_funct3          <= 3'd0;
            id_ex_reg_write       <= 0;
            id_ex_mem_read        <= 0;
            id_ex_mem_write       <= 0;
            id_ex_mem_to_reg      <= 0;
            id_ex_alu_src         <= 0;
            id_ex_branch          <= 0;
            id_ex_jump            <= 0;
            id_ex_jalr            <= 0;
            id_ex_alu_op          <= 4'd0;
            id_ex_predicted_taken <= 0;
            id_ex_predicted_target<= 32'd0;
        end else begin
            id_ex_pc              <= if_id_pc;
            id_ex_rs1_data        <= rs1_data;
            id_ex_rs2_data        <= rs2_data;
            id_ex_imm_i           <= imm_i;
            id_ex_imm_s           <= imm_s;
            id_ex_imm_b           <= imm_b;
            id_ex_imm_u           <= imm_u;
            id_ex_imm_j           <= imm_j;
            id_ex_rs1             <= rs1_addr;
            id_ex_rs2             <= rs2_addr;
            id_ex_rd              <= rd_addr;
            id_ex_funct3          <= funct3;
            id_ex_reg_write       <= reg_write_d;
            id_ex_mem_read        <= mem_read_d;
            id_ex_mem_write       <= mem_write_d;
            id_ex_mem_to_reg      <= mem_to_reg_d;
            id_ex_alu_src         <= alu_src_d;
            id_ex_branch          <= branch_d;
            id_ex_jump            <= jump_d;
            id_ex_jalr            <= jalr_d;
            id_ex_alu_op          <= alu_op_d;
            id_ex_predicted_taken <= bht_predict_taken;
            id_ex_predicted_target<= bht_predict_target;
        end
    end

    // ══ EX/MEM ═══════════════════════════════════
    always_ff @(posedge clk) begin
        if (rst) begin
            ex_mem_alu_result <= 32'd0;
            ex_mem_rs2_data   <= 32'd0;
            ex_mem_rd         <= 5'd0;
            ex_mem_reg_write  <= 0;
            ex_mem_mem_read   <= 0;
            ex_mem_mem_write  <= 0;
            ex_mem_mem_to_reg <= 0;
            ex_mem_funct3     <= 3'd0;
        end else begin
            ex_mem_alu_result <= id_ex_jump ? id_ex_pc + 4 : alu_result;
            ex_mem_rs2_data   <= fwd_rs2;
            ex_mem_rd         <= id_ex_rd;
            ex_mem_reg_write  <= id_ex_reg_write;
            ex_mem_mem_read   <= id_ex_mem_read;
            ex_mem_mem_write  <= id_ex_mem_write;
            ex_mem_mem_to_reg <= id_ex_mem_to_reg;
            ex_mem_funct3     <= id_ex_funct3;
        end
    end

    // ══ MEM/WB ═══════════════════════════════════
    always_ff @(posedge clk) begin
        if (rst) begin
            mem_wb_alu_result <= 32'd0;
            mem_wb_mem_data   <= 32'd0;
            mem_wb_rd         <= 5'd0;
            mem_wb_reg_write  <= 0;
            mem_wb_mem_to_reg <= 0;
        end else begin
            mem_wb_alu_result <= ex_mem_alu_result;
            mem_wb_mem_data   <= dcache_data;
            mem_wb_rd         <= ex_mem_rd;
            mem_wb_reg_write  <= ex_mem_reg_write;
            mem_wb_mem_to_reg <= ex_mem_mem_to_reg;
        end
    end

    assign pc_out = pc;
    assign halt   = (if_id_instr == 32'h00000073);

endmodule
