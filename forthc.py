#!/usr/bin/python3
from collections import namedtuple
import json
import re
import sys
import preamble
from isa import Opcode, write_code

class MemoryAddress():
    def __init__(self, start_obj: dict, offset: int):
        self._offset = offset; 
        self._start_obj = start_obj;
    
    def compute(self):
        return self._offset + self._start_obj["val"]
    
class MemorySection():
    def __init__(self):
        self._offset = 0

        #Ugly, but it must be passed by ref
        self._start = {"val": 0}
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
        word["offset"] = self.offset_addr()
        self.words.append(word)
        self._offset+=1
        return word["offset"]
    
    def push_range(self, words) -> MemoryAddress:
        old_offset = self.offset_addr()
        for word in words:
            word["offset"] = self.offset_addr()
            self.words.append(word)
            self._offset+=1
        return old_offset
    
    def offset_addr(self) -> MemoryAddress:
        return MemoryAddress(self._start, self._offset)

    def allocate(self):
        allocated = self.words.copy()
        for word in allocated:
            if(isinstance(word['offset'], MemoryAddress)):
                word['offset'] = word['offset'].compute()
            if 'operand' in word and isinstance(word['operand'], MemoryAddress):
                word['operand'] = word['operand'].compute()
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
    "/":    Opcode.DIV,
    "mod":  Opcode.MOD,
    "or":   Opcode.OR,
    "and":  Opcode.AND,

    "=":    Opcode.EQUAL
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

def main_cycle(src: str, instructions: MemorySection, data: MemorySection, word: MemorySection):
    #Additional dictionary to keep track of variables
    variables = {}

    #Additional dictionary to keep track of words and their addresses
    word_starts = {}


    #Extracting string literals (." <text" -> ." )
    str_literals = [match[1] for match in re.findall(STRLIT_RE, src)]
    src = re.sub(STRLIT_RE, '.\"', src)

    #Breaking into lines for debug-log purposes
    token_lines = src.splitlines()

    # Tokenizing is as simple as getting all the
    # words separated by whitespaces.
    Token = namedtuple("Token", ["val", 'line', "num"])
    token_queue = [Token(token, line_n+1, token_n+1) for line_n, line in enumerate(token_lines) for token_n, token in enumerate(line.split())]

    token_stack = []
    section = instructions
    

    while len(token_queue) > 0:
        token, line_n, token_n = token_queue.pop(0)

        if token in PRIMITIVE_WORDS:
            section.push({"opcode": PRIMITIVE_WORDS[token]})
            continue

        #Comments
        if token == '(':
            while len(token_queue) > 0 and token_queue.pop(0).val[-1] != ')':
                pass
            continue

        match token:
            #------------------------------  
            # IO
            #------------------------------  
            case '.\"':
                if len(str_literals) > 0:
                    if '.\"' not in word_starts:
                        preamble.add_print_word(word, word_starts, IO_MEM_ADRESS)
                    add_print(section, data, word_starts, str_literals.pop(0))
                else:
                    raise SyntaxError(f"No literal provided for : {token} | (ln:{line_n}, wrd num:{token_n})") 
            case 'emit':
                section.push_range([
                    {'opcode': Opcode.PUSH, 'operand': IO_MEM_ADRESS},
                    {'opcode': Opcode.STORE}
                ])
            case '.':
                if '.' not in word_starts:
                    preamble.add_print_num(word, word_starts, data, IO_MEM_ADRESS)
                section.push({'opcode': Opcode.CALL, 'operand': word_starts['.']})     
            case 'key':
                section.push_range([
                    {'opcode': Opcode.PUSH, 'operand': IO_MEM_ADRESS},
                    {'opcode': Opcode.FETCH}
                ])
            #------------------------------  
            #Variable
            #------------------------------  
            case 'variable':
                word_name = token_queue.pop(0).val

                var_adr = data.push({"word": 0})
                variables[word_name] = var_adr

            #------------------------------  
            #Static Allocation
            #------------------------------  
            case 'sallot':
                query = token_queue.pop(0)
                try:
                    parsed = parse_int_lit(query.val)
                    data.set_offset(data.offset() + parsed)
                except Exception  as e:
                    raise ValueError(f"Coudn't parse sallot query: {query.val} | (ln:{query.line}, wrd num:{query.num})")
            #------------------------------  
            #Word Definition:
            #------------------------------  
            case ':':
                for token_entry in token_stack:
                    if token_entry['token'] == ':':
                        raise SyntaxError(f"Nested word definition is forbidden: nested word definition | (ln:{line_n}, wrd num:{token_n})")

                #NOTE!: Chaning current section
                section = word

                word_name = token_queue.pop(0).val
                word_starts[word_name] = section.offset_addr()

                token_stack.append({'token': ':'})
            
            case ';':
                if len(token_stack) == 0 or token_stack[-1]['token'] != ':':
                    raise SyntaxError(f"Failed to end word definition at (ln:{line_n}, wrd num:{token_n})| Check for opened \":\", conditionals and loops")
                section.push({"opcode": Opcode.RET})
                #NOTE!: Chaning current section
                section = instructions
                token_stack.pop()
            #------------------------------    
            #If-else-then
            #------------------------------  
            case 'if':
                if ':' not in map(lambda x: x['token'], token_stack):
                  raise SyntaxError(f"Conditionals are only allowed in word definitions | (ln:{line_n}, wrd num:{token_n})")
                jz_instr = {'opcode': Opcode.JMPZ}
                section.push(jz_instr)
                token_stack.append({'token' : 'if', 'instr_obj': jz_instr})
            case 'else':
                 if len(token_stack) == 0 or token_stack[-1]['token'] != 'if':
                    raise SyntaxError(f"Failed to complete if-else-then tree at (ln:{line_n}, wrd num:{token_n})| Check for opened \"if\"")
                 end_jmp_instr = {"opcode": Opcode.JMP}
                 section.push(end_jmp_instr)
                 token_stack[-1]['instr_obj']['operand'] = section.offset_addr()
                 token_stack.append({'token' : 'else', 'instr_obj': end_jmp_instr})
            case 'then':
                if len(token_stack) == 0 or token_stack[-1]['token'] != 'if' and token_stack[-1]['token'] != 'else':
                    raise SyntaxError(f"Failed to complete if-else-then tree at (ln:{line_n}, wrd num:{token_n})| Check for opened \"if\"")
                token_stack[-1]['instr_obj']['operand'] = section.offset_addr()
                if token_stack[-1]['token'] == 'else':
                    token_stack.pop()
                token_stack.pop()
            #------------------------------      
            #Begin-until
            #------------------------------  
            case 'begin':
                if ':' not in map(lambda x: x['token'], token_stack):
                    raise SyntaxError(f"Begin-until is only allowed in word definitions | (ln:{line_n}, wrd num:{token_n})")
                token_stack.append({'token' : 'begin', 'addr': section.offset_addr()})
            case 'until':
                if len(token_stack) == 0 or token_stack[-1]['token'] != 'begin':
                    raise SyntaxError(f"Failed to complete Begin-until  tree at (ln:{line_n}, wrd num:{token_n})| Check for opened \"begin\"")
                begin_addr = token_stack.pop()
                section.push({"opcode": Opcode.JMPZ, 'operand': begin_addr['addr']})
            #------------------------------  
            #Do-Loop
            #------------------------------  
            case 'do':
                if ':' not in map(lambda x: x['token'], token_stack):
                    raise SyntaxError(f'Do-loop is only allowed in word definitions | (ln:{line_n}, wrd num:{token_n})')
                section.push_range([
                    #Since first on DS is start, and it should be last on RS
                    {"opcode": Opcode.SWAP},
                    {"opcode": Opcode.STASH},
                    {"opcode": Opcode.STASH}])
                token_stack.append({'token' : 'do', 'addr': section.offset_addr()})
            case 'i':
                if 'do' not in map(lambda x: x['token'], token_stack):
                    raise SyntaxError(f"Failed to insert iterating var at (ln:{line_n}, wrd num:{token_n})| Check for opened \"do\"")
                section.push({"opcode": Opcode.CPSTASH})
            case 'loop':
                if len(token_stack) == 0 or token_stack[-1]['token'] != 'do':
                    raise SyntaxError(f"Failed to complete Do-loop  tree at (ln:{line_n}, wrd num:{token_n})| Check for opened \"do\"")
                begin_addr = token_stack.pop()
                section.push({"opcode": Opcode.LOOP, 'operand': begin_addr['addr']})
            #------------------------------  
            case _:
                #Integer literal
                try:
                    parsed = parse_int_lit(token)
                    section.push({"opcode": Opcode.PUSH, "operand": parsed})
                    continue
                except Exception:
                    pass

                #Variable
                if token in variables:
                    section.push({"opcode": Opcode.PUSH, "operand": variables[token]})
                    continue
                #Custom word
                if token in word_starts:
                    section.push({"opcode": Opcode.CALL, "operand": word_starts[token]})
                    continue

                #Unrecognized word
                raise SyntaxError(f"Unrecognized word: {token} | (ln:{line_n}, wrd num:{token_n})")
    if len(token_stack) != 0:
        raise SyntaxError(f"Some tokens weren't closed: {token_stack[-1]['token']}")
    instructions.push({'opcode' : Opcode.HALT})


def transpilate(src: str) -> list:
    
    #Instruction Section
    instructions = MemorySection()

    #Data Section
    data = MemorySection()

    #Procedure Section
    word = MemorySection()

    main_cycle(src, instructions, data, word)


    instructions_start = IO_MEM_ADRESS + 10
    instructions.set_start(instructions_start)

    word_start = instructions_start + instructions.offset()
    word.set_start(word_start)
    
    data_start = word_start + word.offset()
    data.set_start(data_start)
    return instructions.allocate()+ word.allocate() + data.allocate()


    


def main(src, target):
    with open(src, 'r', encoding='utf-8') as file:
        src = file.read()
    
    code = transpilate(src)
    
    write_code(target, code)
    print("Forthc - Transpiled successfully")

if __name__ == "__main__":
    assert len(sys.argv) == 3, f"Invalid number of arguments: {len(sys.argv)}. Correct use: forthc.py <input_file> <target_file>"

    _, src, target = sys.argv
    main(src, target)