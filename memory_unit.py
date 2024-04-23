from enum import Enum

from exceptions import EOFException


class ARLatch(Enum):
      PC = 0,
      ALU = 1

class MemoryUnit:
      def __init__(self, io_adr: int, mem_size: int, code, read_buffer: list):
            self._AR = 0 

            self._mem = [0] * mem_size
            for instr in code:
                 self._mem[instr['offset']] = instr

            self._data = 0
            self._IO_ADR = io_adr
            self._write_buffer = []
            print(list(map(ord, read_buffer)))
            self._read_buffer = read_buffer

      def __repr__(self) -> str:
            return f' AR: {self._AR:3} MEM_OUT: {self._data}'
      
      def read(self):
            if self._AR == self._IO_ADR:
                  if len(self._read_buffer) < 1:
                        raise EOFException(f"Buffer is empty")
                  self._data = ord(self._read_buffer.pop(0))
            else:
                  if isinstance(self._mem[self._AR], dict) and 'word' in self._mem[self._AR]:
                        self._data = self._mem[self._AR]['word']
                  else :
                        self._data = self._mem[self._AR]
      def write(self, item):
            if self._AR == self._IO_ADR:
                  self._write_buffer.append(item)
            else:
                  self._mem[self._AR] = item