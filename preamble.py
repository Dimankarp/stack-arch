from forthc import MemorySection
from isa import Opcode

"""
PREDEFINED WORDS AKA Preamble
"""


def add_print_word(word: MemorySection, word_starts: dict, io_mem_addr: int):
    print_start = word.push_range(
        [
            {"opcode": Opcode.DUP},
            {"opcode": Opcode.FETCH},
            {"opcode": Opcode.STASH},
            {"opcode": Opcode.PUSH, "operand": 1},
            {"opcode": Opcode.STASH},
        ]
    )
    cycle_start = word.push({"opcode": Opcode.DUP})
    word.push_range(
        [
            {"opcode": Opcode.CPSTASH},
            {"opcode": Opcode.ADD},
            {"opcode": Opcode.FETCH},
            {"opcode": Opcode.PUSH, "operand": io_mem_addr},
            {"opcode": Opcode.STORE},
            {"opcode": Opcode.LOOP, "operand": cycle_start},
            {"opcode": Opcode.POP},
            {"opcode": Opcode.RET},
        ]
    )
    word_starts['."'] = print_start


def add_print_num(word: MemorySection, word_starts: dict, data: MemorySection, io_mem_addr: int):
    var_adr = data.offset_addr()
    data.set_offset(data.offset() + 1)

    jmpz_instr = {
        "opcode": Opcode.JMPZ,
    }
    print_start = word.push_range(
        [
            {"opcode": Opcode.DUP},
            {"opcode": Opcode.PUSH, "operand": -2147483648},
            {"opcode": Opcode.AND},
            jmpz_instr,
            {"opcode": Opcode.PUSH, "operand": 45},
            {"opcode": Opcode.PUSH, "operand": io_mem_addr},
            {"opcode": Opcode.STORE},
            {"opcode": Opcode.PUSH, "operand": -1},
            {"opcode": Opcode.MUL},
        ]
    )
    jmp_adr = word.push_range(
        [
            {"opcode": Opcode.PUSH, "operand": 0},
            {"opcode": Opcode.PUSH, "operand": var_adr},
            {"opcode": Opcode.STORE},
        ]
    )
    jmpz_instr["operand"] = jmp_adr
    jmp_adr = word.push_range(
        [
            {"opcode": Opcode.PUSH, "operand": var_adr},
            {"opcode": Opcode.FETCH},
            {"opcode": Opcode.PUSH, "operand": 1},
            {"opcode": Opcode.ADD},
            {"opcode": Opcode.PUSH, "operand": var_adr},
            {"opcode": Opcode.STORE},
            {"opcode": Opcode.DUP},
            {"opcode": Opcode.PUSH, "operand": 10},
            {"opcode": Opcode.MOD},
            {"opcode": Opcode.PUSH, "operand": 48},
            {"opcode": Opcode.ADD},
            {"opcode": Opcode.SWAP},
            {"opcode": Opcode.PUSH, "operand": 10},
            {"opcode": Opcode.DIV},
            {"opcode": Opcode.DUP},
            {"opcode": Opcode.PUSH, "operand": 0},
            {"opcode": Opcode.EQUAL},
        ]
    )
    word.push_range(
        [
            {"opcode": Opcode.JMPZ, "operand": jmp_adr},
            {"opcode": Opcode.POP},
            {"opcode": Opcode.PUSH, "operand": var_adr},
            {"opcode": Opcode.FETCH},
            {"opcode": Opcode.PUSH, "operand": 1},
            {"opcode": Opcode.SWAP},
            {"opcode": Opcode.STASH},
            {"opcode": Opcode.STASH},
        ]
    )
    jmp_adr = word.push({"opcode": Opcode.PUSH, "operand": io_mem_addr})
    word.push_range([{"opcode": Opcode.STORE}, {"opcode": Opcode.LOOP, "operand": jmp_adr}, {"opcode": Opcode.RET}])

    word_starts["."] = print_start
