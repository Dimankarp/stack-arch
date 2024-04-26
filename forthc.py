#!/usr/bin/python3
import re
import sys

import preamble
from forthc_exceptions import (
    BareBeginUntilError,
    BareConditionalError,
    BareDoLooplError,
    BeginUntilTreeError,
    DoLoopTreeError,
    ExpectedStringLiteralError,
    IfElseTreeError,
    InvalidIntLiteralError,
    LoopVarError,
    NestedWordError,
    SallotQueryError,
    UnclosedWordsError,
    UnknownWordError,
    WordEndError,
)
from isa import Opcode, write_code


class MemoryAddress:
    def __init__(self, start_obj: dict, offset: int):
        self._offset = offset
        self._start_obj = start_obj

    def compute(self):
        return self._offset + self._start_obj["val"]


class MemorySection:
    def __init__(self):
        self._offset = 0

        # Ugly, but it must be passed by ref
        self._start = {"val": 0}
        self.words = []

    def set_offset(self, offset: int):
        self._offset = offset

    def offset(self):
        return self._offset

    def set_start(self, start: int):
        self._start["val"] = start

    def get_start(self) -> int:
        return self._start["val"]

    def push(self, word) -> MemoryAddress:
        word["offset"] = self.offset_addr()
        self.words.append(word)
        self._offset += 1
        return word["offset"]

    def push_range(self, words) -> MemoryAddress:
        old_offset = self.offset_addr()
        for word in words:
            word["offset"] = self.offset_addr()
            self.words.append(word)
            self._offset += 1
        return old_offset

    def offset_addr(self) -> MemoryAddress:
        return MemoryAddress(self._start, self._offset)

    def allocate(self):
        allocated = self.words.copy()
        for word in allocated:
            if isinstance(word["offset"], MemoryAddress):
                word["offset"] = word["offset"].compute()
            if "operand" in word and isinstance(word["operand"], MemoryAddress):
                word["operand"] = word["operand"].compute()
        return allocated


class Token:
    def __init__(self, val: str, line_n: int, word_n: int):
        self.val = val
        self.line = line_n
        self.num = word_n


class Translator:
    def __init__(
        self,
        instructions: MemorySection,
        word: MemorySection,
        data: MemorySection,
        token_queue: list,
        string_literals: list,
        io_adr: int,
    ):
        self.instructions = instructions
        self.word = word
        self.data = data
        self.io_adr = io_adr
        self.token_queue = token_queue
        # List of string literals found in ." ..."
        self.str_literals = string_literals

        # Additional dictionary to keep track of variables
        self.variables = {}

        # Additional dictionary to keep track of words and their addresses
        self.word_start = {}

        self.token_stack = []
        self.section = instructions


STRLIT_RE = re.compile(r'(\." )(.*?)(")', flags=re.MULTILINE)
PRIMITIVE_WORDS = {
    "dup": Opcode.DUP,
    "drop": Opcode.POP,
    "swap": Opcode.SWAP,
    "@": Opcode.FETCH,
    "!": Opcode.STORE,
    "+": Opcode.ADD,
    "-": Opcode.SUB,
    "*": Opcode.MUL,
    "/": Opcode.DIV,
    "mod": Opcode.MOD,
    "or": Opcode.OR,
    "and": Opcode.AND,
    "=": Opcode.EQUAL,
}


# TOKEN PROCESSING FUNCTIONS
def parse_int_lit(token_val: str) -> int:
    parsed = int(token_val)
    if parsed < -(2**31) or parsed > 2**31 - 1:
        raise InvalidIntLiteralError(parsed)
    return parsed


def add_print(t: Translator):
    lit = t.str_literals.pop(0)
    # Pascal String
    data_off = t.data.push({"word": len(lit)})
    for char in lit:
        t.data.push({"word": ord(char)})
    t.instructions.push_range(
        [{"opcode": Opcode.PUSH, "operand": data_off}, {"opcode": Opcode.CALL, "operand": t.word_start['."']}]
    )


def process_print(token: Token, t: Translator):
    if len(t.str_literals) > 0:
        if '."' not in t.word_start:
            preamble.add_print_word(t.word, t.word_start, t.io_adr)
        add_print(t)
    else:
        raise ExpectedStringLiteralError(token)
    return t.section

    # ------------------------------
    # IO
    # ------------------------------


def process_emit(token: Token, t: Translator):
    t.section.push_range([{"opcode": Opcode.PUSH, "operand": t.io_adr}, {"opcode": Opcode.STORE}])


def process_dot(token: Token, t: Translator):
    if "." not in t.word_start:
        preamble.add_print_num(t.word, t.word_start, t.data, t.io_adr)
    t.section.push({"opcode": Opcode.CALL, "operand": t.word_start["."]})


def process_key(token: Token, t: Translator):
    t.section.push_range([{"opcode": Opcode.PUSH, "operand": t.io_adr}, {"opcode": Opcode.FETCH}])

    # ------------------------------
    # Variable
    # ------------------------------


def process_variable(token: Token, t: Translator):
    word_name = t.token_queue.pop(0).val

    var_adr = t.data.push({"word": 0})
    t.variables[word_name] = var_adr

    # ------------------------------
    # Static Allocation
    # ------------------------------


def process_sallot(token: Token, t: Translator):
    query = t.token_queue.pop(0)
    try:
        parsed = parse_int_lit(query.val)
        t.data.set_offset(t.data.offset() + parsed)
    except InvalidIntLiteralError as e:
        raise SallotQueryError(query) from e
    # ------------------------------


# Word Definition:
# ------------------------------
def process_colon(token: Token, t: Translator):
    for token_entry in t.token_stack:
        if token_entry["token"] == ":":
            raise NestedWordError(token)

    word_name = t.token_queue.pop(0).val
    t.word_start[word_name] = t.word.offset_addr()

    t.token_stack.append({"token": ":"})
    # NOTE!: Chaning current section
    t.section = t.word


def process_semicolon(token: Token, t: Translator):
    if len(t.token_stack) == 0 or t.token_stack[-1]["token"] != ":":
        raise WordEndError(token)
    t.section.push({"opcode": Opcode.RET})

    t.token_stack.pop()
    # NOTE!: Chaning current section
    t.section = t.instructions


# ------------------------------
# If-else-then
# ------------------------------
def process_if(token: Token, t: Translator):
    if ":" not in map(lambda x: x["token"], t.token_stack):
        raise BareConditionalError(token)
    jz_instr = {"opcode": Opcode.JMPZ}
    t.section.push(jz_instr)
    t.token_stack.append({"token": "if", "instr_obj": jz_instr})


def process_else(token: Token, t: Translator):
    if len(t.token_stack) == 0 or t.token_stack[-1]["token"] != "if":
        raise IfElseTreeError(token)
    end_jmp_instr = {"opcode": Opcode.JMP}
    t.section.push(end_jmp_instr)
    t.token_stack[-1]["instr_obj"]["operand"] = t.section.offset_addr()
    t.token_stack.append({"token": "else", "instr_obj": end_jmp_instr})


def process_then(token: Token, t: Translator):
    if len(t.token_stack) == 0 or t.token_stack[-1]["token"] != "if" and t.token_stack[-1]["token"] != "else":
        raise IfElseTreeError(token)
    t.token_stack[-1]["instr_obj"]["operand"] = t.section.offset_addr()
    if t.token_stack[-1]["token"] == "else":
        t.token_stack.pop()
    t.token_stack.pop()


# ------------------------------
# Begin-until
# ------------------------------
def process_begin(token: Token, t: Translator):
    if ":" not in map(lambda x: x["token"], t.token_stack):
        raise BareBeginUntilError(token)
    t.token_stack.append({"token": "begin", "addr": t.section.offset_addr()})


def process_until(token: Token, t: Translator):
    if len(t.token_stack) == 0 or t.token_stack[-1]["token"] != "begin":
        raise BeginUntilTreeError(token)
    begin_addr = t.token_stack.pop()
    t.section.push({"opcode": Opcode.JMPZ, "operand": begin_addr["addr"]})


# ------------------------------
# Do-Loop
# ------------------------------
def process_do(token: Token, t: Translator):
    if ":" not in map(lambda x: x["token"], t.token_stack):
        raise BareDoLooplError(token)
    t.section.push_range(
        [
            # Since first on DS is start, and it should be last on RS
            {"opcode": Opcode.SWAP},
            {"opcode": Opcode.STASH},
            {"opcode": Opcode.STASH},
        ]
    )
    t.token_stack.append({"token": "do", "addr": t.section.offset_addr()})


def process_i(token: Token, t: Translator):
    if "do" not in map(lambda x: x["token"], t.token_stack):
        raise LoopVarError(token)
    t.section.push({"opcode": Opcode.CPSTASH})


def process_loop(token: Token, t: Translator):
    if len(t.token_stack) == 0 or t.token_stack[-1]["token"] != "do":
        raise DoLoopTreeError(token)
    begin_addr = t.token_stack.pop()
    t.section.push({"opcode": Opcode.LOOP, "operand": begin_addr["addr"]})


def process_lit_and_custom(token: Token, t: Translator):
    # Variable
    if token.val in t.variables:
        t.section.push({"opcode": Opcode.PUSH, "operand": t.variables[token.val]})
    # Custom word
    elif token.val in t.word_start:
        t.section.push({"opcode": Opcode.CALL, "operand": t.word_start[token.val]})
    else:
        # Integer literal
        try:
            parsed = parse_int_lit(token.val)
            t.section.push({"opcode": Opcode.PUSH, "operand": parsed})
        except Exception:
            raise UnknownWordError(token)  # noqa TRY200 - it's basically another token parsing branch and not lit-error-handling


WORD_TO_PROCESSOR = {
    '."': process_print,
    "emit": process_emit,
    ".": process_dot,
    "key": process_key,
    "variable": process_variable,
    "sallot": process_sallot,
    ":": process_colon,
    ";": process_semicolon,
    "if": process_if,
    "else": process_else,
    "then": process_then,
    "begin": process_begin,
    "until": process_until,
    "do": process_do,
    "i": process_i,
    "loop": process_loop,
}


def main_cycle(src: str, instructions: MemorySection, data: MemorySection, word: MemorySection, io_adr: int):
    str_literals = [match[1] for match in re.findall(STRLIT_RE, src)]
    src = re.sub(STRLIT_RE, '."', src)

    # Breaking into lines for debug-log purposes
    token_lines = src.splitlines()

    # Tokenizing is as simple as getting all the
    # words separated by whitespaces.
    token_queue = [
        Token(token, line_n + 1, token_n + 1)
        for line_n, line in enumerate(token_lines)
        for token_n, token in enumerate(line.split())
    ]

    # An object holding current translation state
    translator = Translator(instructions, word, data, token_queue, str_literals, io_adr)

    while len(translator.token_queue) > 0:
        token = translator.token_queue.pop(0)
        # Primitive words
        if token.val in PRIMITIVE_WORDS:
            translator.section.push({"opcode": PRIMITIVE_WORDS[token.val]})
            continue

        # Complex words
        if token.val in WORD_TO_PROCESSOR:
            WORD_TO_PROCESSOR[token.val](token, translator)
            continue

        # Comments
        if token.val == "(":
            while len(token_queue) > 0 and token_queue.pop(0).val[-1] != ")":
                pass
            continue

        # Literal or custom words
        process_lit_and_custom(token, translator)

    if len(translator.token_stack) != 0:
        raise UnclosedWordsError(translator.token_stack[-1]["token"])
    instructions.push({"opcode": Opcode.HALT})


def translate(src: str, io_adr: int) -> list:
    # Instruction Section
    instructions = MemorySection()

    # Data Section
    data = MemorySection()

    # Procedure Section
    word = MemorySection()

    main_cycle(src, instructions, data, word, io_adr)

    instructions_start = io_adr + 10
    instructions.set_start(instructions_start)

    word_start = instructions_start + instructions.offset()
    word.set_start(word_start)

    data_start = word_start + word.offset()
    data.set_start(data_start)
    return instructions.allocate() + word.allocate() + data.allocate()


def main(src, target):
    with open(src, encoding="utf-8") as file:
        src = file.read()

    code = translate(src, 0)

    write_code(target, code)
    print("Forthc - Transpiled successfully")


if __name__ == "__main__":
    assert (
        len(sys.argv) == 3
    ), f"Invalid number of arguments: {len(sys.argv)}. Correct use: forthc.py <input_file> <target_file>"

    _, src, target = sys.argv
    main(src, target)
