# Read current pipeline.sv and fix the flush line
with open('pipeline.sv', 'r') as f:
    content = f.read()

# Fix flush to use id_ex (same cycle as PC update)
content = content.replace(
    'assign flush   = ex_mem_branch & ex_mem_branch_taken | ex_mem_jump;',
    'assign flush   = (id_ex_branch & branch_taken) | id_ex_jump;'
)

with open('pipeline.sv', 'w') as f:
    f.write(content)

print('Done! Flush logic fixed.')
