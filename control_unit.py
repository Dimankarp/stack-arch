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

    SetZ = 6

    IRLatch = 7


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


mPCJump = namedtuple("mPCJump", ["adr", "uncond", "z"])


micro_program = [
    # Instruction fetch
    [ARLatch.PC, MemSignal.MemRD],
    [
        DPSignal.IRLatch,
        PCLatch.PLUS1,
    ],
    [mPCLatch.IR],
    # PUSH
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush, TOSLatch.IR],
    [mPCJump(0, True, False)],
    # POP
    [DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(0, True, False)],
    # DUP
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
    [mPCJump(0, True, False)],
    # SWAP
    [ALUOp(lambda dp: dp._TOS), RSPush.ALU, DPSignal.DSPop, TOSLatch.DS],
    [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), DPSignal.DSPush],
    [mPCJump(0, True, False)],
    # FETCH
    [ALUOp(lambda dp: dp._TOS), ARLatch.ALU, MemSignal.MemRD],
    [TOSLatch.MEM],
    [mPCJump(0, True, False)],
    # STORE
    [ALUOp(lambda dp: dp._TOS), ARLatch.ALU],
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data()), MemSignal.MemWR],
    [DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(0, True, False)],
    # ADD
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() + dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    # SUB
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() - dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    # MUL
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() * dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    # DIV
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() // dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    # MOD
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() % dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    # OR
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() | dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    # AND
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() & dp._TOS), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    # EQUAL
    [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() - dp._TOS), DPSignal.SetZ],
    [mPCJump(37, False, True)],
    [ALUOp(lambda dp: 0), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    [ALUOp(lambda dp: 1), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    # JMPZ
    [ALUOp(lambda dp: dp._TOS), DPSignal.SetZ, DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(42, False, False)],
    # JMP
    [PCLatch.IR],
    [mPCJump(0, True, False)],
    # STASH
    [ALUOp(lambda dp: dp._TOS), RSPush.ALU, DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(0, True, False)],
    # UNSTASH
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
    [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    # CPSTASH
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
    [DPSignal.RSPeek, ALUOp(lambda dp: dp._RS.data()), TOSLatch.ALU],
    [mPCJump(0, True, False)],
    # LOOP
    [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
    [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), TOSLatch.ALU],
    [DPSignal.RSPeek, ALUOp(lambda dp: dp._TOS - dp._RS.data()), DPSignal.SetZ],
    [mPCJump(57, False, False)],
    [DPSignal.RSPop, DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(0, True, False)],
    [ALUOp(lambda dp: dp._TOS + 1), RSPush.ALU, PCLatch.IR, DPSignal.DSPop, TOSLatch.DS],
    [mPCJump(0, True, False)],
    # CALL
    [RSPush.PC, PCLatch.IR],
    [mPCJump(0, True, False)],
    # RET
    [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), PCLatch.ALU],
    [mPCJump(0, True, False)],
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
            case DPSignal.SetZ:
                self._dp.set_z()
            case DPSignal.IRLatch:
                self._dp.ir_latch()

            case RSPush():
                self._dp.rs_push(signal)
            case TOSLatch():
                self._dp.tos_latch(signal)
            case PCLatch():
                self._dp.pc_latch(signal)

            case MemSignal.MemWR:
                self._mem.write(self._dp._ALU)
            case MemSignal.MemRD:
                self._mem.read()

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
            case mPCJump(adr, uncond, z):
                if uncond or self._dp._Z == z:
                    self._mPC = adr

    def simulate(self, tick_limit: int):
        try:
            while self._ticks < tick_limit:
                logging.debug(" %s \n%s\n%s\n------------", self, self._mem, self._dp)
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
        logging.info(" Output Buffer: %s", output)
        logging.info(" Output Buffer(ASCII codes): %s", ", ".join(map(str, self._mem._write_buffer)))
        logging.debug(" Memory Dump: %s", self._mem._mem)
        return (
            output,
            self._ticks,
        )

    def __repr__(self) -> str:
        return f"TCK: {self._ticks:3} mPC: {self._mPC:3}\n mPROG: {micro_program[self._mPC]}"
