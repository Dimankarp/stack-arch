
from enum import Enum


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
    NOT = "inversion"
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

