from collections import namedtuple
from enum import Enum

#DataPath
from datapath import ALUOp, Datapath, RSPush, TOSLatch, ALULatch, PCLatch
from isa import Opcode
from memory_unit import ARLatch  
# signals that are not used in DP methods themselves
class DPSignal(Enum):
   DSPush = 0
   DSPop = 1
   DSPeek = 2

   RSPop = 3
   RSPeek = 4

   ALUDoOp = 6
   SetZ = 7

   IRLatch = 8

#Memory
class MemSignal(Enum):
   MemWR = 1
   MemRD = 0
#Control Unit
class CUSignal(Enum):
   Halt = 0
class mPCLatch(Enum):
   IR = 1
   PLUS1 = 2
mPCJump = namedtuple("mPCJump", ['adr', 'uncond', 'z'])


mProgram = [
  #Instruction fetch
  [ARLatch.PC, MemSignal.MemRD],
  [DPSignal.IRLatch, PCLatch.PLUS1,],
  [mPCLatch.IR],
  #PUSH
  [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush, TOSLatch.IR]
  [mPCJump(0, True, False)],
  #POP
  [DPSignal.DSPop, TOSLatch.DS],
  [mPCJump(0, True, False)],
  #DUP
  [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
  [mPCJump(0, True, False)],
  #SWAP
  [ALUOp(lambda dp: dp._TOS), RSPush.ALU, DPSignal.DSPop, TOSLatch.DS],
  [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), DPSignal.DSPush]
  [mPCJump(0, True, False)],
  #FETCH
  [ALUOp(lambda dp: dp._TOS), ARLatch.ALU],
  [TOSLatch.MEM],
  [mPCJump(0, True, False)],
  #STORE
  [ALUOp(lambda dp: dp._TOS), ARLatch.ALU],
  [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data()), MemSignal.MemWR],
  [DPSignal.DSPop, TOSLatch.DS],
  [mPCJump(0, True, False)],
  #ADD
  [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() + dp._TOS), TOSLatch.ALU]
  [mPCJump(0, True, False)],
  #SUB
  [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() - dp._TOS), TOSLatch.ALU]
  [mPCJump(0, True, False)],
  #MUL
  [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() * dp._TOS), TOSLatch.ALU]
  [mPCJump(0, True, False)],
  #DIV
  [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() / dp._TOS), TOSLatch.ALU]
  [mPCJump(0, True, False)],
  #MOD
  [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() % dp._TOS), TOSLatch.ALU]
  [mPCJump(0, True, False)],
  #OR
  [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() | dp._TOS), TOSLatch.ALU]
  [mPCJump(0, True, False)],
  #AND
  [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() & dp._TOS), TOSLatch.ALU]
  [mPCJump(0, True, False)],
  #EQUAL
  [DPSignal.DSPop, ALUOp(lambda dp: dp._DS.data() | dp._TOS), DPSignal.SetZ],
  [mPCJump(37, False, True)],
  [ALUOp(lambda dp: 0), TOSLatch.ALU],
  [mPCJump(0, True, False)],
  [ALUOp(lambda dp: 1), TOSLatch.ALU],
  [mPCJump(0, True, False)],
  #JMPZ
  [ALUOp(lambda dp: dp._TOS), DPSignal.SetZ, DPSignal.DSPop, TOSLatch.DS],
  [mPCJump(42, False, False)]
  #JMP
  [PCLatch.IR]
  [mPCJump(0, True, False)],
  #STASH
  [ALUOp(lambda dp: dp._TOS), RSPush.ALU, DPSignal.DSPop, TOSLatch.DS]
  [mPCJump(0, True, False)],
  #UNSTASH
  [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
  [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), TOSLatch.ALU]
  [mPCJump(0, True, False)],
  #CPSTASH
  [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
  [DPSignal.RSPeek, ALUOp(lambda dp: dp._RS.data()), TOSLatch.ALU]
  [mPCJump(0, True, False)],
  #LOOP
  [ALUOp(lambda dp: dp._TOS), DPSignal.DSPush],
  [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), TOSLatch.ALU]
  [DPSignal.RSPeek, ALUOp(lambda dp: dp._TOS + 1 - dp._RS.data()), DPSignal.SetZ]
  [mPCJump(57, False, False)]
  [DPSignal.RSPop, PCLatch.IR, DPSignal.DSPop, TOSLatch.DS]
  [mPCJump(0, True, False)],
  [ALUOp(lambda dp: dp._TOS + 1), RSPush.ALU, DPSignal.DSPop, TOSLatch.DS]
  [mPCJump(0, True, False)],
  #CALL
  [RSPush.PC, PCLatch.IR]
  [mPCJump(0, True, False)],
  #RET
  [DPSignal.RSPop, ALUOp(lambda dp: dp._RS.data()), PCLatch.ALU]
  [mPCJump(0, True, False)],
  #HALT
  [CUSignal.Halt]
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
    def __init__(self, datapath: Datapath, memory):
      self._mPC = 0
      self._dp = datapath
      self._mem = memory
      self._ticks = 0

    def mpc_latch(self, mux: mPCLatch):
        assert False, "TO DO"
    def mpc_mir_latch(self, addr: int):
        assert False, "TO DO"

    def simulate(self, tick_limit: int):
       while self._ticks < tick_limit:
          
       