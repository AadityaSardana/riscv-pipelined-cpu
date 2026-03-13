with open('src/pipeline.sv', 'r') as f:
    code = f.read()

# Fix icache instantiation
old_ic = '''    icache icache0 (
        .clk          (clk),
        .rst          (rst),
        .addr         (pc),
        .rd_en        (!halt_reg),
        .data_out     (ic_data_out),
        .stall        (ic_stall),
        .perf_hits    (ic_hits),
        .perf_misses  (ic_misses),
        .perf_accesses(ic_accesses)
    );'''

new_ic = '''    icache icache0 (
        .clk          (clk),
        .rst          (rst),
        .addr         (pc),
        .rd_en        (1\'b1),
        .data_out     (ic_data_out),
        .stall        (ic_stall),
        .perf_hits    (ic_hits),
        .perf_misses  (ic_misses),
        .perf_accesses(ic_accesses)
    );'''

# Fix dcache instantiation
old_dc = '''    dcache dcache0 (
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
    );'''

new_dc = '''    dcache dcache0 (
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
    );'''

if old_ic in code:
    code = code.replace(old_ic, new_ic)
    print('icache fixed!')
else:
    print('icache block not found - checking pipeline...')
    # Find and print what icache instantiation looks like
    idx = code.find('icache icache0')
    if idx >= 0:
        print('Found icache at:', code[idx:idx+400])

if old_dc in code:
    code = code.replace(old_dc, new_dc)
    print('dcache fixed!')

with open('src/pipeline.sv', 'w') as f:
    f.write(code)

# Now check lines 305-325 to see the actual instantiation
lines = code.split('\n')
print('\nLines 300-330 of pipeline.sv:')
for i, l in enumerate(lines[299:330], 300):
    print(f'{i}: {l}')
