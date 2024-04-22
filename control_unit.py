from enum import Enum

#DataPath
from datapath import Datapath, RSPush, TOSLatch, ALULatch, PCLatch  
# signals that are not used in DP methods themselves
class DPSignal(Enum):
   DSPush = 0
   DSPop = 1
   DSPeek = 2

   RSPop = 3
   RSPeek = 4

   ALURightLatch = 5
   ALUDoOp = 6
   SetZ = 7

   IRLatch = 8

class mPCLatch(Enum):
   IR = 1
   PLUS1 = 2

class ControlUnit:
    def __init__(self, datapath: Datapath, memory):
      self._mPC = 0
      self._dp = datapath
      self._mem = memory

    def mpc_latch(self, mux: mPCLatch):
        assert False, "TO DO"
    def mpc_mir_latch(self, addr: int):
        assert False, "TO DO"