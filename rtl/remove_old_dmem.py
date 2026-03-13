with open('src/pipeline.sv', 'r') as f:
    lines = f.readlines()

# Find and remove old dmem write block lines
new_lines = []
skip = False
for line in lines:
    if '// Memory write' in line and 'dmem' not in line:
        skip = True
    if 'dmem[ex_mem_alu_result' in line and '<=' in line:
        skip = True
    if skip and 'endcase' in line:
        skip = False
        continue
    if not skip:
        new_lines.append(line)

with open('src/pipeline.sv', 'w') as f:
    f.writelines(new_lines)
print('Old dmem write block removed!')
