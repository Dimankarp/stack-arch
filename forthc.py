#!/usr/bin/python3
from collections import namedtuple
import re
import sys
from isa import Opcode

class MemoryAddress():
    def __init__(self, start_obj: dict, offset: int):
        self._offset = offset; 
        self._start_obj = start_obj["val"];
    
    def compute(self):
        return self._offset + self._start_obj["val"]
class MemorySection():
    def __init__(self):
        self._offset = 0

        #Ugly, but it must be passed by ref
        self._start = {"val", 0}
        self.words = []

    def set_offset(self, offset: int):
        self._offset = offset

    def offset(self):
        return self._offset
    
    def set_start(self, start:int):
        self._start["val"] = start
    
    def get_start(self) -> int:
        return self._start["val"]
    
    def push(self, word) -> MemoryAddress:
        word["offset"] = self._offset
        old_offset = self._offset
        self.words.append(word)
        self._offset+=1
        return MemoryAddress(self._start, old_offset)
    
    def push_range(self, words) -> MemoryAddress:
        old_offset = self._offset
        for word in words:
            word["offset"] = self._offset
            self.words.append(word)
            self._offset+=1
        return MemoryAddress(self._start, old_offset)
    
    def allocate(self):
        allocated = self.words.copy()
        for word in allocated:
            word["offset"]+=self._start
        return allocated


STRLIT_RE = re.compile(f"(\.\" )(.*?)(\")", flags=re.MULTILINE)
PRIMITIVE_WORDS ={
    "dup" : Opcode.DUP,
    "drop": Opcode.POP,
    "swap": Opcode.SWAP,
    "@":    Opcode.FETCH,
    "!":    Opcode.STORE,
    
    "+":    Opcode.ADD,
    "-":    Opcode.SUB,
    "*":    Opcode.MUL,
    "%":    Opcode.MOD,
}

IO_MEM_ADRESS = 0

def parse_int_lit(token: str) -> int:
    parsed = int(token)
    if parsed < -2**31 or parsed > 2**31-1:
        raise ValueError("Provided literal doesn't fit into 32bit signed integer")
    return parsed

def add_print(instr_section: MemorySection, data_section: MemorySection, words:dict, lit: str):
    #Pascal String
    data_off = data_section.push({"word": len(lit)})
    for char in lit:
        data_section.push({"word": ord(char)})
    instr_section.push_range([
        {"opcode": Opcode.PUSH, "operand": data_off},
        {"opcode": Opcode.CALL, "operand": words['.\"']}
    ])
def transpilate(src: str) -> str:
    
    #Instruction Section
    instructions = MemorySection()

    #Data Section
    data = MemorySection()

    #Additional dictionary to keep track of variables

    variables = {}

    #Procedure Section
    word = MemorySection()

    #Additional dictionary to keep track of words and their addresses
    word_starts = {}


    #PREDEFINED WORDS
    print_start =  word.push_range([
        {"opcode": Opcode.DUP},
        {"opcode": Opcode.FETCH},
        {"opcode": Opcode.PUSH, "operand": 1},
        {"opcode": Opcode.STASH},
        {"opcode": Opcode.STASH}])
    cycle_start = word.push({"opcode": Opcode.DUP})
    word.push_range([
        {"opcode": Opcode.CPSTASH},
        {"opcode": Opcode.ADD},
        {"opcode": Opcode.FETCH},
        {"opcode": Opcode.STORE, "operand": IO_MEM_ADRESS},
        {"opcode": Opcode.LOOP, "operand": cycle_start},
        {"opcode": Opcode.POP},
        {"opcode": Opcode.RET},
            ])
    word_starts[".\""] = print_start


    #Extracting string literals (." <text" -> ." )
    str_literals = [match[1] for match in re.findall(STRLIT_RE, src)]
    src = re.sub(STRLIT_RE, '.\"', src)

    #Breaking into lines for debug-log purposes
    token_lines = src.splitlines()

    token_stack = []
    
    # Tokenizing is as simple as getting all the
    # words separated by whitespaces.
    Token = namedtuple("Token", ["val", 'line', "num"])
    token_queue = [Token(token, line_n+1, token_n+1) for line_n, line in enumerate(token_lines) for token_n, token in enumerate(line.split())]

    while token_queue.count > 0:
        token, line_n, token_n = token_queue.pop(0)

        if token in PRIMITIVE_WORDS:
            instructions.push({"opcode": PRIMITIVE_WORDS[token].name})
            continue
        
        match token:
            #Print literal string
            case '.\"':
                if str_literals.count > 0:
                    add_print(instructions, data, word_starts, str_literals.pop(0))
                else:
                    raise SyntaxError(f"No literal provided for : {token} | (ln:{line_n}, wrd num:{token_n})") 
            case 'variable':
                word_name = token_queue.pop(0).val

                var_adr = data.push({"word": 0})
                variables[word_name] = var_adr  
            #Static Allocation
            case 'sallot':
                query = token_queue.pop(0)
                try:
                    parsed = parse_int_lit(query.val)
                    data.set_offset(data.offset() + parsed)
                except ValueError | TypeError as e:
                    raise ValueError(f"Coudn't parse sallot query: {query.val} | | (ln:{query.line}, wrd num:{query.num})")
            case _:
            
                #Integer literal
                try:
                    parsed = parse_int_lit(token)
                    instructions.push({"opcode": Opcode.PUSH.name, "operand": {parsed}})
                    continue
                except ValueError | TypeError:
                    pass

                #Variable
                if token in variables:
                    instructions.push({"opcode": Opcode.PUSH, "operand": variables[token]})
                    continue
                #Custom word
                if token in word_starts:
                    instructions.push({"opcode": Opcode.CALL, "operand": word_starts[token]})
                    continue

                #Unrecognized word
                raise SyntaxError(f"Unrecognized word: {token} | (ln:{line_n}, wrd num:{token_n})")









def main(src, target):
    with open(src, 'r', encoding='utf-8') as file:
        src = file.read()
    
    code = transpilate(src)
    print(code)

if __name__ == "__main__":
    assert len(sys.argv) == 3, f"Invalid number of arguments: {len(sys.argv)}. Correct use: forthc.py <input_file> <target_file>"

    _, src, target = sys.argv
    main(src, target)