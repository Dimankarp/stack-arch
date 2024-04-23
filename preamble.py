from forthc import MemorySection
from isa import Opcode
"""
PREDEFINED WORDS AKA Preamble
"""

def add_print_word(word: MemorySection, word_starts: dict, io_mem_addr:int):
     #PREDEFINED WORDS AKA Preambule
    print_start =  word.push_range([
        {"opcode": Opcode.DUP},
        {"opcode": Opcode.FETCH},
        {"opcode": Opcode.STASH},
        {"opcode": Opcode.PUSH, "operand": 1},
        {"opcode": Opcode.STASH}])
    cycle_start = word.push({"opcode": Opcode.DUP})
    word.push_range([
        {"opcode": Opcode.CPSTASH},
        {"opcode": Opcode.ADD},
        {"opcode": Opcode.FETCH},
        {"opcode": Opcode.PUSH, "operand": io_mem_addr},
        {"opcode": Opcode.STORE},
        {"opcode": Opcode.LOOP, "operand": cycle_start},
        {"opcode": Opcode.POP},
        {"opcode": Opcode.RET},
            ])
    word_starts[".\""] = print_start