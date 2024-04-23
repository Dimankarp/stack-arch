from enum import Enum


class ARLatch(Enum):
      PC = 0,
      ALU = 1

class MemoryUnit:
    def __init__(self, io_adr: int, code):
           self._AR = 0 
           self._mem = []
           self._data = 0
           self._IO_ADR = io_adr
    def read(self):
          self._data = self._mem[self._AR]
    def write(self, item):
          self._mem[self._AR] = item