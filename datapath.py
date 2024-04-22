from enum import Enum


class Stack:
    def __init__(self, size: int):
        assert size > 0, "Stack size must be positive"
        self.stack = []
        self._size = size
        self._data = 0

    def data(self):
        return self._data
    
    def peek(self):
        if len(self.stack) < 1:
            raise Exception(f"Stack underflow")
        self._data = self.stack[-1]
    def push(self, item):
        if len(self.stack) >= self._size:
            raise Exception("Stack overflow")  
        self.stack.append(item)
    def pop(self):
        if len(self.stack) < 1:
            raise Exception("Stack underflow")  
        self._data = self.stack.pop()   

#I think writing all the methods & stuff
# would violate the simplicity dogma
class ALU:
    def __init__(self):
        self.left = 0
        self.right = 0
        self.data = 0

#Enums required in datapath functions
#(functional enum syntax is avoided since
# export to control_uint.py is required)
class RSPush(Enum):
    ALU = 0
    PC = 1
class TOSLatch(Enum):
    DS = 0,
    MEM = 1,
    IR = 2,
    ALU = 3
class ALULatch(Enum):
    RS = 0,
    DS = 1,
class PCLatch(Enum):
    ALU = 0,
    IR = 1,
    PLUS1 = 2

class Datapath:
    def __init__(self, start_adr: int, memory):
        self._DS: Stack = Stack(128)
        self._RS: Stack = Stack(128)

        self._TOS: int = 0
        self._ALU: ALU = ALU()
        self._Z: bool = True

        self._IR: map = {} #Instructions are maps
        self._PC: int = start_adr

        self._Mem = memory
    
    def ds_push(self):
        self._DS.push(self._ALU.data)
    def ds_pop(self):
        self._DS.pop()
    def ds_peek(self):
        self._DS.peek()

    def rs_push(self, mux: RSPush):
        self._RS.push(self._ALU.data if mux == RSPush.ALU else self._PC )
    def rs_pop(self):
        self._RS.pop()
    def rs_peek(self):
        self._RS.pop()
    
    def tos_latch(self, mux: TOSLatch):
        match mux:
            case TOSLatch.DS:
                self._TOS = self._DS.data()
            case TOSLatch.MEM:
                assert False, "TO DO"
            case TOSLatch.IR:
                val = self._IR["operand"] if "operand" in self._IR else self._IR["data"]
                self._TOS = val
            case TOSLatch.ALU:
                self._TOS = self._ALU.data
    
    def alu_left_latch(self, mux: ALULatch):
        self._ALU.left = self._DS.data() if mux == ALULatch.DS else self._RS.data()
    def alu_right_latch(self):
        self._ALU.right = self._TOS
    def alu_do_opeation(self, op):
        self._ALU.data = op(self._ALU.left, self._ALU.right)

    def set_z(self):
        self._Z = self._ALU.data == 0
    
    def ir_latch(self):
        assert False, "TO DO"
    def pc_latch(self, mux: PCLatch):
        match mux:
            case PCLatch.ALU:
                self._PC = self._ALU.data
            case PCLatch.IR:
                self._PC = self._IR["operand"] if "operand" in self._IR else self._IR["data"]
            case PCLatch.PLUS1:
                self._PC = self._PC + 1
    