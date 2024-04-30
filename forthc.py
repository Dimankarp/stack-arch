#!/usr/bin/python3
import argparse
import logging
import re
import sys

import preamble
from forthc_exceptions import (
    BareBeginUntilError,
    BareConditionalError,
    BareDoLooplError,
    BareLeaveError,
    BeginUntilTreeError,
    DoLoopTreeError,
    ExpectedStringLiteralError,
    IfElseTreeError,
    InvalidIntLiteralError,
    LoopVarError,
    MissingPreambuleWordError,
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
    "<": Opcode.LESS,
    ">=": Opcode.GREATEQ,
}


# TOKEN PROCESSING FUNCTIONS
def parse_int_lit(token_val: str) -> int:
    parsed = int(token_val)
    if parsed < -(2**31) or parsed > 2**31 - 1:
        raise InvalidIntLiteralError(parsed)
    return parsed


def add_print(token: Token, t: Translator):
    lit = t.str_literals.pop(0).replace("\\n", "\n")
    # Pascal String
    data_off = t.data.push({"word": len(lit)})
    for char in lit:
        t.data.push({"word": ord(char)})
    t.section.push_range(
        [
            {"opcode": Opcode.PUSH, "operand": data_off, "token": vars(token)},
            {"opcode": Opcode.CALL, "operand": t.word_start['."'], "token": vars(token)},
        ]
    )


def process_print(token: Token, t: Translator):
    if len(t.str_literals) > 0:
        if '."' not in t.word_start:
            raise MissingPreambuleWordError('."')
        add_print(token, t)
    else:
        raise ExpectedStringLiteralError(token)
    return t.section

    # ------------------------------
    # IO
    # ------------------------------


def process_emit(token: Token, t: Translator):
    t.section.push_range(
        [
            {"opcode": Opcode.PUSH, "operand": t.io_adr, "token": vars(token)},
            {"opcode": Opcode.STORE, "token": vars(token)},
        ]
    )


def process_dot(token: Token, t: Translator):
    if "." not in t.word_start:
        raise MissingPreambuleWordError(".")
    t.section.push({"opcode": Opcode.CALL, "operand": t.word_start["."], "token": vars(token)})


def process_key(token: Token, t: Translator):
    t.section.push_range(
        [
            {"opcode": Opcode.PUSH, "operand": t.io_adr, "token": vars(token)},
            {"opcode": Opcode.FETCH, "token": vars(token)},
        ]
    )

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
    except InvalidIntLiteralError | Exception as e:
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
    t.section.push({"opcode": Opcode.RET, "token": vars(token)})

    t.token_stack.pop()
    # NOTE!: Chaning current section
    t.section = t.instructions


# ------------------------------
# If-else-then
# ------------------------------
def process_if(token: Token, t: Translator):
    if ":" not in map(lambda x: x["token"], t.token_stack):
        raise BareConditionalError(token)
    jz_instr = {"opcode": Opcode.JMPZ, "token": vars(token)}
    t.section.push(jz_instr)
    t.token_stack.append({"token": "if", "instr_obj": jz_instr})


def process_else(token: Token, t: Translator):
    if len(t.token_stack) == 0 or t.token_stack[-1]["token"] != "if":
        raise IfElseTreeError(token)
    end_jmp_instr = {"opcode": Opcode.JMP, "token": vars(token)}
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
# Cycle leave
# ------------------------------
def process_leave(token: Token, t: Translator):
    headers = list(filter(lambda item: item["token"] in ["begin", "do"], reversed(t.token_stack)))
    if len(headers) == 0:
        raise BareLeaveError(token)
    if headers[0]["token"] == "do":
        t.section.push_range(
            [
                {"opcode": Opcode.UNSTASH, "token": vars(token)},
                {"opcode": Opcode.POP, "token": vars(token)},
                {"opcode": Opcode.UNSTASH, "token": vars(token)},
                {"opcode": Opcode.POP, "token": vars(token)},
            ]
        )
    header = headers[0]
    jmp_inst = {"opcode": Opcode.JMP, "token": vars(token)}
    t.section.push(jmp_inst)
    header["leave_jmps"] = [*header.get("leave_jmps", []), jmp_inst]


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
    begin_header = t.token_stack.pop()
    t.section.push({"opcode": Opcode.JMPZ, "operand": begin_header["addr"], "token": vars(token)})
    for leave_jmp in begin_header.get("leave_jmps", []):
        leave_jmp["operand"] = t.section.offset_addr()


# ------------------------------
# Do-Loop
# ------------------------------
def process_do(token: Token, t: Translator):
    if ":" not in map(lambda x: x["token"], t.token_stack):
        raise BareDoLooplError(token)
    t.section.push_range(
        [
            # Since first on DS is start, and it should be last on RS
            {"opcode": Opcode.SWAP, "token": vars(token)},
            {"opcode": Opcode.STASH, "token": vars(token)},
            {"opcode": Opcode.STASH, "token": vars(token)},
        ]
    )
    t.token_stack.append({"token": "do", "addr": t.section.offset_addr()})


def process_i(token: Token, t: Translator):
    if "do" not in map(lambda x: x["token"], t.token_stack):
        raise LoopVarError(token)
    t.section.push({"opcode": Opcode.CPSTASH, "token": vars(token)})


def process_loop(token: Token, t: Translator):
    if len(t.token_stack) == 0 or t.token_stack[-1]["token"] != "do":
        raise DoLoopTreeError(token)
    do_header = t.token_stack.pop()
    t.section.push({"opcode": Opcode.LOOP, "operand": do_header["addr"], "token": vars(token)})
    for leave_jmp in do_header.get("leave_jmps", []):
        leave_jmp["operand"] = t.section.offset_addr()


def process_lit_and_custom(token: Token, t: Translator):
    # Variable
    if token.val in t.variables:
        t.section.push({"opcode": Opcode.PUSH, "operand": t.variables[token.val], "token": vars(token)})
    # Custom word
    elif token.val in t.word_start:
        t.section.push({"opcode": Opcode.CALL, "operand": t.word_start[token.val], "token": vars(token)})
    else:
        # Integer literal
        try:
            parsed = parse_int_lit(token.val)
            t.section.push({"opcode": Opcode.PUSH, "operand": parsed, "token": vars(token)})
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
    "leave": process_leave,
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

    # Adding preambule (can't add it during token parsng, since word open/close shenanigans will ruin everytihng)
    if "." in map(lambda token: token.val, token_queue):
        preamble.add_print_num(translator.word, translator.word_start, translator.data, translator.io_adr)
    if '."' in map(lambda token: token.val, token_queue):
        preamble.add_print_word(translator.word, translator.word_start, translator.io_adr)

    while len(translator.token_queue) > 0:
        token = translator.token_queue.pop(0)
        # Primitive words
        if token.val in PRIMITIVE_WORDS:
            translator.section.push({"opcode": PRIMITIVE_WORDS[token.val], "token": vars(token)})
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


def translate(src: str, io_adr: int, start_adr: int) -> list:
    # Instruction Section
    instructions = MemorySection()

    # Data Section
    data = MemorySection()

    # Procedure Section
    word = MemorySection()

    main_cycle(src, instructions, data, word, io_adr)

    instructions_start = start_adr
    instructions.set_start(instructions_start)

    word_start = instructions_start + instructions.offset()
    word.set_start(word_start)

    data_start = word_start + word.offset()
    data.set_start(data_start)
    return instructions.allocate() + word.allocate() + data.allocate()


def main(args):
    with open(args.source, encoding="utf-8") as file:
        src = file.read()

    code = translate(src, args.io_adr, args.start_adr)

    write_code(args.target, code)
    logging.info("Translated successfully. Wrote to %s", args.target)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simple forth-like language translator",
        epilog="It's sallot and not allot here! What allot even stands for?!",
    )
    parser.add_argument("source", metavar="SOURCE", help="a source file with forth code to translate")
    parser.add_argument("target", metavar="TARGET", help="a target file to write translated json to")
    parser.add_argument(
        "-s",
        "--start-adr",
        dest="start_adr",
        type=int,
        metavar="START_ADR",
        required=False,
        default=10,
        help="an address from which the program exectuion starts (first in PC)",
    )
    parser.add_argument(
        "-d",
        "--device-adr",
        dest="io_adr",
        type=int,
        metavar="IO_ADR",
        required=False,
        default=0,
        help="an address mapped to the IO device",
    )
    args = parser.parse_args()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)

    main(args)
