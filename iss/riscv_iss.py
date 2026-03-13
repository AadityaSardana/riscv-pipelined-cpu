
# ─────────────────────────────────────────────
#  RISC-V RV32I  Instruction Set Simulator
#  Python ISS
# ─────────────────────────────────────────────

import sys
#sys means system,class is a blueprint,def is used to define a function, __INIT__ is a speacial function , which is run Automaticaly 
#when an object of a class is created(without this no intialization of components happen),self refers to current object instance 
#without self the object variable ( like regs,pc,mem etc. here becames a local variable and and not a object variable)
class RV32I_ISS:


    def __init__(self):
        self.regs    = [0] * 32 #makes a list of 32 zeroes,riscv has exactly 32 zeroes,0 because intially,cpu starts->all reg are0 
        self.pc      = 0 #this means this object pc(program counter)variable is zero,0 bcoz if cpu rst/start->all reg are 0
        self.mem     = {} #creates a empty directory of cpu mmry,drctry bcz it only stores mmry that are written,rest->0 
        self.running = True #flag that controls the loop , true means you can run the instr, all 4 commands run simultanoesuly

    def reg_write(self, rd, value): #rd is the reg where the value is stored,value stores the result of instruction 
        if rd != 0: #this is imp,if we dont run this the rd can be also stored to x0<which is hardwired to 0>,giving error
            self.regs[rd] = value & 0xFFFFFFFF #this cmnd writes the rd,self.regs was (0)*32 a list of 32 0's,[rd] gives the 
#index value regs[0],regs[2] etc. , thus self.regs[rd] select the designated reg,ex.->self.regs[2] selects the register x3
#value&0xFFFFFFFF truncate the extra bits from 32 bit this is exactly 32 bit , keeps all the lower bits (F..F) means 32 1's 

    def reg_read(self, rs): #read the value stored in the register
        return self.regs[rs] & 0xFFFFFFFF #read the value first written with truncated with 32 1's

    def mem_write_byte(self, addr, value): #it writes one byte to memory , addr means adress ( which value into which adress)
       self.mem[addr] = value & 0xFF #store value at adress(addr) , making sure only last 8 bits are stored(1 byte)

    def mem_read_byte(self, addr): #it writes one byte to the memory
        return self.mem.get(addr, 0) #self.mem(key,default_Value),if key exist give the value else return the deafult value(here0)

    def mem_write_word(self, addr, value): #this fn writes a word in the memory(1 word = 4 bytes)
        for i in range(4): #produces a loop for i->0to3
            self.mem_write_byte(addr + i, (value >> (8 * i)) & 0xFF) #adder+i moves to the next memory adress value>>(8*i) means 
#right shifiting the value , ex a 32 bit value=0x12345678 is be stored then for i=0 no shift thus,addres x stores 78 (lsb first)
#when i=1 addres x+1 stores 56 as there will be a right shift of 8 bits thus the value bcame x000123456 and similarly the loop 
#goes on untill a complete word is written

    def mem_read_word(self, addr): #it reads a 32 bit word from the memory 
        result = 0 #intialize a variable to store the value of the word
        for i in range(4): #LOOP 
            result |= self.mem_read_byte(addr + i) << (8 * i) #reads one byte starting from adress x and then left shift operator
        return result #|= this operator is bitwise or and assign merges the byte to construct a word 

#this fucntion extend a smaller signed no. to 32 bit signed no.
    def sign_extend(self, value, bits): #value->the no. we want to extend,bits->the original bit widht
        sign_bit = 1 << (bits - 1) #assign the sign bit , suppose 12 bits are there this means that 1<<11 means 100000000000
        return (value & (sign_bit - 1)) - (value & sign_bit) #value&(Sign_bit-1) -> extract the magnitude bit
#value&sign_bit extract the sign bit,if 1 then negative no. 

    def fetch(self): #simulates the fetch state of cpu,self.pc stores the adress of the next instruction
        return self.mem_read_word(self.pc) #return the instruction fetch from the adress at(self.pc) to cpu 

    def decode(self, instr):
        opcode = instr & 0x7F
        rd     = (instr >> 7)  & 0x1F
        funct3 = (instr >> 12) & 0x7
        rs1    = (instr >> 15) & 0x1F
        rs2    = (instr >> 20) & 0x1F
        funct7 = (instr >> 25) & 0x7F

        imm_i = self.sign_extend((instr >> 20) & 0xFFF, 12)
        imm_s = self.sign_extend(
                    ((instr >> 25) & 0x7F) << 5 |
                    ((instr >> 7)  & 0x1F), 12)
        imm_b = self.sign_extend(
                    ((instr >> 31) & 1) << 12 |
                    ((instr >> 7)  & 1) << 11 |
                    ((instr >> 25) & 0x3F) << 5 |
                    ((instr >> 8)  & 0xF)  << 1, 13)
        imm_u = (instr & 0xFFFFF000)
        imm_j = self.sign_extend(
                    ((instr >> 31) & 1)    << 20 |
                    ((instr >> 12) & 0xFF) << 12 |
                    ((instr >> 20) & 1)    << 11 |
                    ((instr >> 21) & 0x3FF) << 1, 21)

        return opcode, rd, funct3, rs1, rs2, funct7, \
               imm_i, imm_s, imm_b, imm_u, imm_j

    def execute(self, instr):
        opcode, rd, funct3, rs1, rs2, funct7, \
        imm_i, imm_s, imm_b, imm_u, imm_j = self.decode(instr)

        pc_next = self.pc + 4
        r1 = self.reg_read(rs1)
        r2 = self.reg_read(rs2)

        # ── R-TYPE ──────────────────────────────
        if opcode == 0x33:
            if   funct3==0x0 and funct7==0x00: self.reg_write(rd, r1 + r2)
            elif funct3==0x0 and funct7==0x20: self.reg_write(rd, r1 - r2)
            elif funct3==0x4:                  self.reg_write(rd, r1 ^ r2)
            elif funct3==0x6:                  self.reg_write(rd, r1 | r2)
            elif funct3==0x7:                  self.reg_write(rd, r1 & r2)
            elif funct3==0x1:                  self.reg_write(rd, r1 << (r2 & 0x1F))
            elif funct3==0x5 and funct7==0x00: self.reg_write(rd, r1 >> (r2 & 0x1F))
            elif funct3==0x5 and funct7==0x20:
                self.reg_write(rd, self.sign_extend(r1,32) >> (r2 & 0x1F))
            elif funct3==0x2:
                self.reg_write(rd, 1 if self.sign_extend(r1,32) < self.sign_extend(r2,32) else 0)
            elif funct3==0x3:
                self.reg_write(rd, 1 if r1 < r2 else 0)

        # ── I-TYPE ARITHMETIC ────────────────────
        elif opcode == 0x13:
            if   funct3==0x0: self.reg_write(rd, r1 + imm_i)
            elif funct3==0x4: self.reg_write(rd, r1 ^ imm_i)
            elif funct3==0x6: self.reg_write(rd, r1 | imm_i)
            elif funct3==0x7: self.reg_write(rd, r1 & imm_i)
            elif funct3==0x1: self.reg_write(rd, r1 << (imm_i & 0x1F))
            elif funct3==0x5 and funct7==0x00:
                self.reg_write(rd, r1 >> (imm_i & 0x1F))
            elif funct3==0x5 and funct7==0x20:
                self.reg_write(rd, self.sign_extend(r1,32) >> (imm_i & 0x1F))
            elif funct3==0x2:
                self.reg_write(rd, 1 if self.sign_extend(r1,32) < imm_i else 0)
            elif funct3==0x3:
                self.reg_write(rd, 1 if r1 < (imm_i & 0xFFFFFFFF) else 0)

        # ── LOADS ────────────────────────────────
        elif opcode == 0x03:
            addr = (r1 + imm_i) & 0xFFFFFFFF
            if   funct3==0x0:
                self.reg_write(rd, self.sign_extend(self.mem_read_byte(addr), 8))
            elif funct3==0x1:
                v = self.mem_read_byte(addr) | (self.mem_read_byte(addr+1) << 8)
                self.reg_write(rd, self.sign_extend(v, 16))
            elif funct3==0x2:
                self.reg_write(rd, self.mem_read_word(addr))
            elif funct3==0x4:
                self.reg_write(rd, self.mem_read_byte(addr))
            elif funct3==0x5:
                v = self.mem_read_byte(addr) | (self.mem_read_byte(addr+1) << 8)
                self.reg_write(rd, v)

        # ── STORES ───────────────────────────────
        elif opcode == 0x23:
            addr = (r1 + imm_s) & 0xFFFFFFFF
            if   funct3==0x0: self.mem_write_byte(addr, r2 & 0xFF)
            elif funct3==0x1:
                self.mem_write_byte(addr,   r2 & 0xFF)
                self.mem_write_byte(addr+1, (r2 >> 8) & 0xFF)
            elif funct3==0x2: self.mem_write_word(addr, r2)

        # ── BRANCHES ─────────────────────────────
        elif opcode == 0x63:
            taken = False
            s1 = self.sign_extend(r1, 32)
            s2 = self.sign_extend(r2, 32)
            if   funct3==0x0: taken = (r1 == r2)
            elif funct3==0x1: taken = (r1 != r2)
            elif funct3==0x4: taken = (s1 <  s2)
            elif funct3==0x5: taken = (s1 >= s2)
            elif funct3==0x6: taken = (r1 <  r2)
            elif funct3==0x7: taken = (r1 >= r2)
            if taken:
                pc_next = (self.pc + imm_b) & 0xFFFFFFFF

        # ── JAL ──────────────────────────────────
        elif opcode == 0x6F:
            self.reg_write(rd, self.pc + 4)
            pc_next = (self.pc + imm_j) & 0xFFFFFFFF

        # ── JALR ─────────────────────────────────
        elif opcode == 0x67:
            self.reg_write(rd, self.pc + 4)
            pc_next = (r1 + imm_i) & 0xFFFFFFFE

        # ── LUI ──────────────────────────────────
        elif opcode == 0x37:
            self.reg_write(rd, imm_u)

        # ── AUIPC ────────────────────────────────
        elif opcode == 0x17:
            self.reg_write(rd, (self.pc + imm_u) & 0xFFFFFFFF)

        # ── ECALL / EBREAK ───────────────────────
        elif opcode == 0x73:
            print(f"\n[ISS] ECALL — simulation complete")
            print(f"[ISS] Exit code (a0/x10) = {self.regs[10]}")
            self.running = False

        # ── FENCE (NOP) ──────────────────────────
        elif opcode == 0x0F:
            pass

        else:
            print(f"[ISS] Unknown opcode 0x{opcode:02X} at PC=0x{self.pc:08X}")
            self.running = False

        self.pc = pc_next

    def run(self):
        print(f"[ISS] Starting at PC=0x{self.pc:08X}")
        steps = 0
        while self.running:
            instr = self.fetch()
            if instr == 0:
                print(f"[ISS] Zero instruction at PC=0x{self.pc:08X} — halting")
                break
            self.execute(instr)
            steps += 1
            if steps > 1_000_000:
                print("[ISS] Step limit hit — possible infinite loop")
                break
        print(f"[ISS] Done — {steps} instructions executed")
        self.dump_regs()

    def dump_regs(self):
        names = ["zero","ra","sp","gp","tp","t0","t1","t2",
                 "s0","s1","a0","a1","a2","a3","a4","a5",
                 "a6","a7","s2","s3","s4","s5","s6","s7",
                 "s8","s9","s10","s11","t3","t4","t5","t6"]
        print("\n── Register Dump ──────────────────────────")
        for i in range(32):
            print(f"  x{i:<2} ({names[i]:<4}) = 0x{self.regs[i]:08X}  ({self.regs[i]})")
        print(f"  PC        = 0x{self.pc:08X}")
        print("───────────────────────────────────────────")


# ── Test: addi x1,x0,10 | addi x2,x0,20 | add x3,x1,x2 | ecall
if __name__ == "__main__":
    iss = RV32I_ISS()
    iss.mem_write_word(0,  0x00A00093)   # addi x1, x0, 10
    iss.mem_write_word(4,  0x01400113)   # addi x2, x0, 20
    iss.mem_write_word(8,  0x002081B3)   # add  x3, x1, x2
    iss.mem_write_word(12, 0x00000073)   # ecall
    iss.run()
