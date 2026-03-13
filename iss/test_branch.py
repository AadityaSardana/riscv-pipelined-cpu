
import sys
sys.path.insert(0, '.')
from riscv_iss import RV32I_ISS

iss = RV32I_ISS()
iss.mem_write_word(0,  0x00000093)  # addi x1, x0, 0
iss.mem_write_word(4,  0x00500113)  # addi x2, x0, 5
iss.mem_write_word(8,  0x00108093)  # addi x1, x1, 1   (loop:)
iss.mem_write_word(12, 0xFE209EE3)  # bne  x1, x2, loop
iss.mem_write_word(16, 0x00000073)  # ecall

iss.run()

