from enum import Enum

from exceptions import DataAsInstructionError, InstructionAsDataError, StackOverflowError, StackUnderflowError
from memory_unit import MemoryUnit


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
            raise StackUnderflowError()
        self._data = self.stack[-1]

    def push(self, item):
        if len(self.stack) >= self._size:
            raise StackOverflowError()
        self.stack.append(item)
        self._data = self.stack[-1]

    def pop(self):
        if len(self.stack) < 1:
            raise StackUnderflowError()
        self._data = self.stack.pop()


# I think writing all the methods & stuff
# would violate the simplicity dogma
class ALUOp:
    def __init__(self, op):
        self.op = op


# Enums required in datapath functions
# (functional enum syntax is avoided since
# export to control_uint.py is required)
class RSPush(Enum):
    ALU = 0
    PC = 1


class TOSLatch(Enum):
    DS = 0
    MEM = 1
    IR = 2
    ALU = 3


class PCLatch(Enum):
    ALU = 0
    IR = 1
    PLUS1 = 2


class Datapath:
    def __init__(self, start_adr: int, memory: MemoryUnit):
        self._DS: Stack = Stack(128)
        self._RS: Stack = Stack(128)

        self._TOS: int = 0
        self._ALU: int = 0
        self._Z: bool = True

        self._IR: map = {}  # Instructions are maps
        self._PC: int = start_adr

        self._Mem = memory

    def __repr__(self) -> str:
        datapath_state = f"TOS: {self._TOS:3} PC: {self._PC:3} ALU: {self._ALU:3}"
        ds_stack = f"DS (LEN: {len(self._DS.stack)}): {self._DS.stack[:-(min(4, len(self._DS.stack))+1):-1]}..."
        rs_stack = f"RS (LEN: {len(self._RS.stack)}): {self._RS.stack[:-(min(4, len(self._RS.stack))+1):-1]}..."
        if "opcode" in self._IR:
            instr = f"Instruction: {self._IR['opcode'].name} {self._IR['operand'] if 'operand' in self._IR else ''}"
        else:
            instr = f"Instruction: {self._IR}"

        return f"{datapath_state}\n{ds_stack}\n{rs_stack}\n{instr}"

    def ds_push(self):
        self._DS.push(self._ALU)

    def ds_pop(self):
        self._DS.pop()

    def ds_peek(self):
        self._DS.peek()

    def rs_push(self, mux: RSPush):
        self._RS.push(self._ALU if mux == RSPush.ALU else self._PC)

    def rs_pop(self):
        self._RS.pop()

    def rs_peek(self):
        self._RS.peek()

    def tos_latch(self, mux: TOSLatch):
        match mux:
            case TOSLatch.DS:
                self._TOS = self._DS.data()
            case TOSLatch.MEM:
                self._TOS = self._Mem._data
            case TOSLatch.IR:
                val = self._IR["operand"] if "operand" in self._IR else self._IR["data"]
                self._TOS = val
            case TOSLatch.ALU:
                self._TOS = self._ALU
        if not isinstance(self._TOS, int):
            raise InstructionAsDataError("TOS", self._TOS)

    def alu_do_opeation(self, op):
        self._ALU = op(self)

    def set_z(self):
        self._Z = self._ALU == 0

    def ir_latch(self):
        self._IR = self._Mem._data
        if not isinstance(self._IR, dict):
            raise DataAsInstructionError("IR", self._IR)

    def pc_latch(self, mux: PCLatch):
        match mux:
            case PCLatch.ALU:
                self._PC = self._ALU
            case PCLatch.IR:
                self._PC = self._IR["operand"] if "operand" in self._IR else self._IR["data"]
            case PCLatch.PLUS1:
                self._PC = self._PC + 1
