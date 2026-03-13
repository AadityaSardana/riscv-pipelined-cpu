import subprocess
# Read the existing pipeline
with open('src/pipeline.sv', 'r') as f:
    code = f.read()

# 1. Add cache ports to module declaration
code = code.replace(
    'output logic        halt',
    '''output logic        halt,
    // I-Cache performance counters
    output logic [31:0] ic_hits,
    output logic [31:0] ic_misses,
    output logic [31:0] ic_accesses,
    // D-Cache performance counters
    output logic [31:0] dc_hits,
    output logic [31:0] dc_misses,
    output logic [31:0] dc_accesses'''
)

# 2. Replace imem/dmem declarations with cache wires
code = code.replace(
    '// — Memories ————————————————————\n    logic [31:0] imem [0:1023];\n    logic [31:0] dmem [0:1023];',
    '''// — Memories ————————————————————
    // imem kept for testbench program loading
    logic [31:0] imem [0:1023];
    // Cache interface wires
    logic [31:0] ic_data_out;
    logic        ic_stall;
    logic [31:0] dc_data_out;
    logic        dc_stall;'''
)

# 3. Add cache stall to stall signal - find the hazard unit instantiation
code = code.replace(
    'logic        stall;',
    '''logic        stall;
    logic        haz_stall;  // stall from hazard unit only
    logic        cache_stall; // stall from either cache miss'''
)

# 4. Add cache_stall assignment after flush assignment
code = code.replace(
    'assign flush   = (id_ex_branch & branch_taken) | id_ex_jump;',
    '''assign flush       = (id_ex_branch & branch_taken) | id_ex_jump;
    assign cache_stall = ic_stall | dc_stall;
    assign stall       = haz_stall | cache_stall;'''
)

# 5. Fix hazard unit output to use haz_stall
code = code.replace(
    '.stall(stall)',
    '.stall(haz_stall)'
)

# 6. Add icache and dcache instantiation before endmodule
cache_inst = '''
    // — I-Cache ————————————————————————
    icache icache0 (
        .clk          (clk),
        .rst          (rst),
        .addr         (pc),
        .rd_en        (!halt_reg),
        .data_out     (ic_data_out),
        .stall        (ic_stall),
        .perf_hits    (ic_hits),
        .perf_misses  (ic_misses),
        .perf_accesses(ic_accesses)
    );

    // — D-Cache ————————————————————————
    dcache dcache0 (
        .clk          (clk),
        .rst          (rst),
        .addr         (ex_mem_alu_result),
        .rd_en        (ex_mem_mem_read),
        .wr_en        (ex_mem_mem_write),
        .wr_data      (ex_mem_rs2_data),
        .funct3       (ex_mem_funct3),
        .data_out     (dc_data_out),
        .stall        (dc_stall),
        .perf_hits    (dc_hits),
        .perf_misses  (dc_misses),
        .perf_accesses(dc_accesses)
    );

'''
code = code.replace('endmodule', cache_inst + 'endmodule')

# 7. In IF stage: use icache when no flush/stall from hazard
# Replace direct imem fetch with icache data
code = code.replace(
    'if_id_instr <= imem[pc[31:2]];',
    '''if_id_instr <= ic_stall ? if_id_instr : ic_data_out;
            // Also sync icache main_mem with imem for testbench loading
            icache0.main_mem[pc[13:2]] <= imem[pc[31:2]];'''
)

# 8. Replace dmem reads with dcache output
code = code.replace(
    '''if (ex_mem_mem_read) begin
            case (ex_mem_funct3)
                3'b000: mem_wb_mem_data <= {{24{dmem[ex_mem_alu_result[31:2]][7]}},  dmem[ex_mem_alu_result[31:2]][7:0]};
                3'b001: mem_wb_mem_data <= {{16{dmem[ex_mem_alu_result[31:2]][15]}}, dmem[ex_mem_alu_result[31:2]][15:0]};
                3'b010: mem_wb_mem_data <= dmem[ex_mem_alu_result[31:2]];
                3'b100: mem_wb_mem_data <= {24'd0, dmem[ex_mem_alu_result[31:2]][7:0]};
                3'b101: mem_wb_mem_data <= {16'd0, dmem[ex_mem_alu_result[31:2]][15:0]};
                default:mem_wb_mem_data <= dmem[ex_mem_alu_result[31:2]];
            endcase
        end''',
    '''if (ex_mem_mem_read) begin
            // D-Cache handles sign/zero extension internally
            mem_wb_mem_data <= dc_data_out;
        end'''
)

# 9. Remove old dmem write block (dcache handles it now)
code = code.replace(
    '''// Memory write
        if (ex_mem_mem_write) begin
            case (ex_mem_funct3)
                3'b000: dmem[ex_mem_alu_result[31:2]][7:0]  <= ex_mem_rs2_data[7:0];
                3'b001: dmem[ex_mem_alu_result[31:2]][15:0] <= ex_mem_rs2_data[15:0];
                3'b010: dmem[ex_mem_alu_result[31:2]]        <= ex_mem_rs2_data;
                default: dmem[ex_mem_alu_result[31:2]]       <= ex_mem_rs2_data;
            endcase
        end''',
    '// Memory writes handled by D-Cache'
)

with open('src/pipeline.sv', 'w') as f:
    f.write(code)
print('pipeline.sv updated with caches!')
