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

    def __repr__(self) -> str:
        return "ALUop"


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
        self._N: bool = False
        self._Z: bool = True
        self._V: bool = False

        self._IR: map = {}  # Instructions are maps
        self._PC: int = start_adr

        self._Mem = memory

    def __repr__(self) -> str:
        data_state = f"{'TOS:': >6} {self._TOS:5} {'ALU:': >6} {self._ALU:5}"
        ds_stack = f"DS (LEN: {len(self._DS.stack)}): {self._DS.stack[:-(min(4, len(self._DS.stack))+1):-1]}..."
        rs_stack = f"RS (LEN: {len(self._RS.stack)}): {self._RS.stack[:-(min(4, len(self._RS.stack))+1):-1]}..."
        if "opcode" in self._IR:
            instr_token = (
                f"'{self._IR['token']['val']}'@{self._IR['token']['line']}:{self._IR['token']['num']}"
                if "token" in self._IR
                else ""
            )
            instr_operand = f" {self._IR['operand']:3}" if "operand" in self._IR else ""
            instr_state = (
                f"{'PC:': >6} {self._PC:5} {'IR:': >6} {self._IR['opcode'].name}{instr_operand}\t{instr_token}"
            )
        else:
            instr_state = f"{'PC:': >6} {self._PC:5} {'IR:': >6} {self._IR}"
        return f"{data_state}\n{ds_stack}\n{rs_stack}\n{instr_state}"

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
        fit_mask = 2**32 - 1

        result = op(self)

        # Here overflow is checked for with simple boundary compare
        # Obviously it's just a model simplification and in reality
        # bit checks are done
        if result > 2**31 - 1 or result < -(2**31):
            self._V = True
            # Extracting number that fits 32 bit int
            result = result & fit_mask
            b = result.to_bytes(4, signed=False)
            result = int.from_bytes(b, signed=True)
        else:
            self._V = False

        self._Z = result == 0
        self._N = result < 0

        self._ALU = result

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
