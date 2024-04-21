
from enum import Enum


class Opcode(Enum):
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

    JMPNZ = "jump on no zero"
    JMP = "jump"
    STASH = "stash"
    UNSTASH = "unstash"
    CPSTASH = "copy stash"
    LOOP = "loop"

    CALL = "call"
    RET = "return"

    HALT = "halt"
