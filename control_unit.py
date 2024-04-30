import logging
from collections import namedtuple
from enum import Enum

# DataPath
from datapath import ALUOp, Datapath, PCLatch, RSPush, TOSLatch
from exceptions import BufferEmptyError, HaltError, MicrocodeJumpFailError
from isa import Opcode
from memory_unit import ARLatch, MemoryUnit


# signals that are not used in DP methods themselves
class DPSignal(Enum):
    DSPush = 0
    DSPop = 1
    DSPeek = 2

    RSPop = 3
    RSPeek = 4

    IRLatch = 6


# Memory
class MemSignal(Enum):
    MemWR = 1
    MemRD = 0


# Control Unit
class CUSignal(Enum):
    Halt = 0


class mPCLatch(Enum):  # noqa: N801 - m... stands for micro here
    IR = 1
    PLUS1 = 2


class ResStatus(Enum):
    N = "n"
    Z = "z"
    V = "v"


class mPCJump(namedtuple("mPCJump", ["adr", "uncond", "status", "status_val"])):  # noqa: N801 - m... stands for micro here
    def __repr__(self) -> str:
        if self.uncond:
            return f"mJMP {self.adr}"
        return f"mJMPZ({self.status.value}=={1 if self.status_val else 0}) {self.adr}"


micro_program = [
    # Instruction fetch
    [ARLatch.PC, MemSignal.MemRD],
    [DPSignal.IRLatch, PCLatch.PLUS1],
    [mPCLatch.IR],
    # PUSH
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush, TOSLatch.IR],
    [mPCJump(0, True, ResStatus.Z, False)],
    # POP
    [DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(0, True, ResStatus.Z, False)],
    # DUP
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
    [mPCJump(0, True, ResStatus.Z, False)],
    # SWAP
    [ALUOp(lambda dp: dp._TOS), RSPush.ALU, DPSignal.DSPop, TOSLatch.DS],
    [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), DPSignal.DSPush],
    [mPCJump(0, True, ResStatus.Z, False)],
    # FETCH
    [ALUOp(lambda dp: dp._TOS), ARLatch.ALU, MemSignal.MemRD],
    [TOSLatch.MEM],
    [mPCJump(0, True, ResStatus.Z, False)],
    # STORE
    [ALUOp(lambda dp: dp._TOS), ARLatch.ALU],
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data()), MemSignal.MemWR],
    [DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(0, True, ResStatus.Z, False)],
    # ADD
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() + dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # SUB
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() - dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # MUL
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() * dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # DIV
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() // dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # MOD
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() % dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # OR
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() | dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # AND
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() & dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # EQUAL
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() - dp._TOS)],
    [mPCJump(37, False, ResStatus.Z, True)],
    [ALUOp(lambda dp: 0), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    [ALUOp(lambda dp: 1), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # JMPZ
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(42, False, ResStatus.Z, False)],
    # JMP
    [PCLatch.IR],
    [mPCJump(0, True, ResStatus.Z, False)],
    # STASH
    [ALUOp(lambda dp: dp._TOS), RSPush.ALU, DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(0, True, ResStatus.Z, False)],
    # UNSTASH
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
    [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # CPSTASH
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
    [DPSignal.RSPeek, ALUOp(lambda dp: dp._RS.data()), TOSLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # LOOP
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
    [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), TOSLatch.ALU],
    [DPSignal.RSPeek, ALUOp(lambda dp: dp._TOS - dp._RS.data())],
    [mPCJump(57, False, ResStatus.Z, False)],
    [DPSignal.RSPop, DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(0, True, ResStatus.Z, False)],
    [ALUOp(lambda dp: dp._TOS + 1), RSPush.ALU, PCLatch.IR, DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(0, True, ResStatus.Z, False)],
    # CALL
    [RSPush.PC, PCLatch.IR],
    [mPCJump(0, True, ResStatus.Z, False)],
    # RET
    [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), PCLatch.ALU],
    [mPCJump(0, True, ResStatus.Z, False)],
    # HALT
    [CUSignal.Halt],
]

opcode_to_mprog = {
    Opcode.PUSH: 3,
    Opcode.POP: 5,
    Opcode.DUP: 7,
    Opcode.SWAP: 9,
    Opcode.FETCH: 12,
    Opcode.STORE: 15,
    Opcode.ADD: 19,
    Opcode.SUB: 21,
    Opcode.MUL: 23,
    Opcode.DIV: 25,
    Opcode.MOD: 27,
    Opcode.OR: 29,
    Opcode.AND: 31,
    Opcode.EQUAL: 33,
    Opcode.JMPZ: 39,
    Opcode.JMP: 41,
    Opcode.STASH: 43,
    Opcode.UNSTASH: 45,
    Opcode.CPSTASH: 48,
    Opcode.LOOP: 51,
    Opcode.CALL: 59,
    Opcode.RET: 61,
    Opcode.HALT: 63,
}


class ControlUnit:
    def __init__(self, datapath: Datapath, memory: MemoryUnit):
        self._mPC = 0
        self._dp = datapath
        self._mem = memory
        self._ticks = 0

    def apply_signal(self, signal):
        match signal:
            case DPSignal.DSPush:
                self._dp.ds_push()
            case DPSignal.DSPop:
                self._dp.ds_pop()
            case DPSignal.DSPeek:
                self._dp.ds_peek()
            case DPSignal.RSPop:
                self._dp.rs_pop()
            case DPSignal.RSPeek:
                self._dp.rs_peek()
            case ALUOp():
                self._dp.alu_do_opeation(signal.op)
            case DPSignal.IRLatch:
                self._dp.ir_latch()
            case RSPush():
                self._dp.rs_push(signal)
            case TOSLatch():
                self._dp.tos_latch(signal)
            case PCLatch():
                self._dp.pc_latch(signal)

            case MemSignal.MemWR:
                self._ticks += self._mem.write(self._dp._ALU, self._ticks)
            case MemSignal.MemRD:
                self._ticks += self._mem.read(self._ticks)

            case ARLatch.PC:
                self._mem._AR = self._dp._PC
            case ARLatch.ALU:
                self._mem._AR = self._dp._ALU

            case CUSignal.Halt:
                raise HaltError()
            case mPCLatch.IR:
                if "opcode" in self._dp._IR:
                    self._mPC = opcode_to_mprog[self._dp._IR["opcode"]]
                else:
                    raise MicrocodeJumpFailError()
            case mPCJump(adr, uncond, status, status_val):
                if uncond:
                    self._mPC = adr
                else:
                    cond = False
                    match status:
                        case ResStatus.N:
                            cond = self._dp._N == status_val
                        case ResStatus.Z:
                            cond = self._dp._Z == status_val
                        case ResStatus.V:
                            cond = self._dp._V == status_val
                    if cond:
                        self._mPC = adr

    def simulate(self, tick_limit: int):
        try:
            while self._ticks < tick_limit:
                # Separating journal entry into lines for readability
                lines = str(self).split("\n")
                for line in lines[:-1]:
                    logging.debug("%s", line)
                logging.debug("%s\n", lines[-1])
                self._ticks += 1
                micro_instructions = micro_program[self._mPC]
                # Will be rewritten on mjump
                self._mPC += 1

                for instr in micro_instructions:
                    self.apply_signal(instr)
        except HaltError:
            logging.warning("Halt!")
        except BufferEmptyError:
            logging.warning("Input buffer was empty on fetch!")
        if self._ticks >= tick_limit:
            logging.warning("Tick limit exceeded")
        output = "".join(map(chr, self._mem._write_buffer))
        miss_rate = (self._mem._cache._requests - self._mem._cache._hits) / self._mem._cache._requests

        logging.debug("Output Buffer: %s", output)
        logging.debug("Output Buffer(ASCII codes): %s", ", ".join(map(str, self._mem._write_buffer)))
        logging.debug("Memory Dump: %s", self._mem._mem)
        logging.debug("Cache Dump: \n%s", "\n".join([f"{j.line}" for i in self._mem._cache._sets for j in i.entries]))
        return (output, self._ticks, miss_rate)

    def __repr__(self) -> str:
        m_prog = ", ".join(
            [
                f"{type(instr).__name__}.{instr.name}" if isinstance(instr, Enum) else f"{instr}"
                for instr in micro_program[self._mPC]
            ]
        )
        return (
            f"{'TCK:': >6} {self._ticks:5} {self._dp}\n{self._mem}\n{'mPC:': >6} {self._mPC:5} {'mPROG:': >6} {m_prog}"
        )
