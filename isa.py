
from enum import Enum
import json


class Opcode(str, Enum):
    """
    Enum values are defined but used mostly as commentary.
    In end json file symbolic name is used
    """
    PUSH = "push"
    POP = "pop"
    DUP = "duplicate"
    SWAP = "swap"
    FETCH = "fetch"
    STORE = "store"

    ADD = "add"
    SUB = "subtract"
    MUL = "multiply"
    DIV = "divide"
    MOD = "modulo"
    OR = "or"
    AND = "and"

    EQUAL = "equal"

    JMPZ = "jump on zero"
    JMP = "jump"
    STASH = "stash"
    UNSTASH = "unstash"
    CPSTASH = "copy stash"
    LOOP = "loop"

    CALL = "call"
    RET = "return"

    HALT = "halt"

def write_code(file, code):
    with open(file, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n ".join(buf) + "]")

def read_code(file):
    with open(file, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        if 'opcode'in instr:
            instr['opcode'] = Opcode(instr['opcode'])
    return code