# Stack Processor. Модель и Forth транслятор

* P3217, Хороших Дмитрий Максимович
* `forth | stack | neum | mc -> hw | tick -> instr | struct | stream | mem | pstr | prob1 | cache`

* Усложнённый вариант

## Язык программирования

``` ebnf

<program> ::= <program> <program>
        | <primitive expr>
        | <word>
        | <comment>

<comment> ::= "(" <any symbols except: ")" >")"

<print> ::= ".\"" <str literal>"\""
<str literal> ::= <any symbols except: "\"" >

<word> ::= ":" <word name> <expr> ";"

<loop> ::= <do-loop>|<begin-until>
<do-loop> ::= "do" [<leave expr>] "loop"
<begin-until> ::= "begin" [<leave expr>] "until"

<if-else-then> ::= "if" [<expr>] ["else" <expr>] "then"

<expr> ::= <expr> <expr>
        | <token> 
        | <loop> 
        | <if-else-then>
        | <word name> 

<leave expr> ::= [<expr>] "leave" 
        | [<expr>] <leave-if-else-then> [<expr>]
        | <expr>
<leave-if-else-then> ::= "if" [<leave expr>] ["else" <leave expr>] "then"  

<primitive expr> ::= <primitive expr> <primitive expr>
        | <token>
        | <variable>
        | <sallot>
        | <word name>
<sallot> ::= "sallot" <int literal>
<variable> ::= "variable" <word name>

token ::= "dup" 
        | "drop" | "swap" | "@" | "!" | "+" | "-" 
        | "*" | "/" | "mod" | "or" | "and" | "=" | "emit"
        | "key" | "<" | ">=" | "." | <int literal> | <print>

<word name> = <any symbols>

<int literal> ::= ['-']<natural num>
<natural num> ::= [<decimal digit>]<decimal digit> 
<decimal digit> ::= "0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"
```

В модели машины языка, как и в симулируемом процессоре, существуют 2 стэка: Data Stack (DS) с открытым прямым доступом программиста и Return Stack (DS) - вспомогательный стэк, используемый при вызове процедур и в do-loop цикле. На текущую ячейку памяти указывает DP - data pointer, значение которого резервируется за именем переменной при variable <имя>. DP cдвигается с помощью операции sallot.

Все операторы, кроме заключённых в объявления прцедур, интерпретируются последовательно.

Циклы и условные конструкции разрешены только в объявлениях процедур. Разрешены рекурсивные и вложенные вызовы процедур.

Объявление переменных и аллокация памяти разрешена только вне процедур.

Область видимости имён процедур и переменных - в любом месте после объявления. Аргументы процедур и возвращаемые значения передаются через DS.

Все операции осуществляются над 32-х-битными знаковыми числами.

Операции :

| Операция | (DS до -- DS после)       | Описание                  |
|:---------|:-------------|:--------------------------|
| "dup"    | (x -- x x)   |                           |
| "swap"   | (y x -- x y) |                           |
| "@" | (adr -- mem(adr)) | |
| "!" | (val adr -- ) | Записать val в память по адресу adr |
| "+" | (x y -- x+y) ||
| "-" | (x y -- x-y) ||
| "*" | (x y -- x*y) ||
| "/" | (x y -- x/y) ||
| "mod" | (x y -- x mod y) ||
| "or" | (x y -- x or y) ||
| "and" | (x y -- x and y) ||
| "=" | (x y -- x==y) | -1 если x==y, 0 - в противном случае |
| "<" | (x y -- x<y) | -1 если x<y, 0 - в противном случае |
| ">=" | (x y -- x>=y) | -1 если x>=y, 0 - в противном случае |
| "." | (x -- ) | Вывод вершины стека в виде числа в stdout  |
| "emit" | (x -- ) | Вывод вершины стека в виде ASCII-символа в stdout  |
| "key" | ( -- x ) | Ввод  ASCII-символа  из stdin  |

* : <слово> <выражение> ; - Объявление процедуры, операторы при интерпретировании не выполняются
* variable <слово> - Объявление переменной
* sallot <нат. число> - Сдвинуть текущее значение DP на <нат. число>
* <слово> - Если <слово> - имя переменной, то ( -- adr), иначе - вызывается процедура <слово>
* if <true-выражение> [else <false-выражение>] then - Вершина стека удаляется, если оно != 0, то выполняется <true-выражение> выражение, в противном слуае, при наличии else - выполняется <false-выражение>
* begin <выражение> until - При встрече оператора until вершина стека удаляется, если она != 0, то цикл заканчивается, в противном случае - цикл возобновляется
* do <выражение> loop - При встрече оператора do - (limit start -- ), <выражения> вызываются пока start != limit, в конце каждоый итерации: start++. В цикле можно использовать оператор i: ( -- cur_start)

* ( <комментарий>) - Комментарии не интерпретируются

Виды литералов:

* <32i> - ( -- <32i>) 32-х-битное знаковое число
* ." <строка>"  - Печать в stdout ASCII строки <строка>

## Организация памяти

Память команд и данных общая, адрес 26-битный.  Отдельно существуют 2 стэка: Data Stack (DS) с открытым прямым доступом программиста и Return Stack (DS) - вспомогательный стэк. В стэках и в памяти хранятся 32-х-битные машинные слова.

Для программиста память линейна, начинается с некоторого адреса и заканчивается Data Pointer'ом. DP можно двигать вперёд, аллоцируя тем самым память. Переменные именуют адреса в этой памяти. По памяти можно двигаться, изменяя адрес в стеке математическимим операциями. Обращение по адресам, меньшим начального или большим DP - неопределённое поведение.

При трансляции в памяти формируются 3 раздела: раздел инструкций, раздел процедур и раздел данных. Все инструкции вне процедур отображаются в раздел инструкций последовательно, аналогично в раздел процедур отображаются процедуры. В разделе данных хранятся строковые литералы и пустые, зарезервированные переменными или sallot, ячейки.

## Система команд

Инструкция может изменять состояния одного из 2-х стэков, осуществлять ввод-вывод с памятью, изменять поток управления (условные и безусловные переходы).

Ввод-вывод с внешними устройствами аналогичен записи/чтению памяти из особых установленных адресов (обычно около нулевые адреса памяти)

DS может напрямую передать значени в TOS - отдельно выделенный регистр, хранящий вершину DS. Оба стэка, DS и RS, могут быть использованые как операнды в АЛУ. Запись в DS и RS возможна из АЛУ.

Чтение из DS и RS доступна с (stack.pop()) и без (stack.peek()) удаления вершины.

### Обозначения

* DS - Data Stack
* RS - Return Stack
* TOS - Top of Data Stack register
* IR.lit - операнд инструкции в IR

### STACK & MEMORY OPERATIONS

1. PUSH (LIT)
    * DS.push(TOS) |  TOS <- IR.lit
1. POP
    * TOS <- DS.pop()
1. DUP
    * DS.push(TOS)
1. SWAP
    * RS.push(TOS) | TOS <- DS.pop()
    * DS.push(RS.pop())
1. FETCH
    * ADR <- TOS
    * TOS <- MEM.out(ADR)
1. STORE
    * ADR <- TOS
    * MEM.in <- DS.pop()
    * TOS <- DS.pop()

### ARITHMETIC OPERATIONS

1. ADD
    * TOS <- DS.pop() + TOS
1. SUB
    * TOS <- DS.pop() - TOS
1. MUL
    * TOS <- DS.pop() * TOS
1. DIV
    * TOS <- DS.pop() / TOS
1. MOD
    * TOS <- DS.pop() % TOS

### LOGIC OPERATION

1. OR
    * TOS <- TOS or DS.pop()
1. AND
    * TOS <- TOS and DS.pop()

### COMPARE OPERATION

1. EQUAL
    * Z <- TOS or DS.pop()
    * | IF(Z==1): TOS <- 1
      | ELSE: TOS <- 0
1. LESS
    * NV <- DS.pop() - TOS
    * | IF(N==1):
        *| IF(V==0): TOS <- 1
         | ELSE: TOS <- 0
      | ELSE:
        *| IF(V==1): TOS <- 1
         | ELSE: TOS <- 0
1. GREATEQ
    * NV <- DS.pop() - TOS
    * | IF(N==1):
        *| IF(V==1): TOS <- 1
         | ELSE: TOS <- 0
      | ELSE:
        *| IF(V==0): TOS <- 1
         | ELSE: TOS <- 0

### BRANCHING, LOOPING & RETURN STACK

1. JMPZ (ADDR)
    * Z <- TOS | TOS <- DS.pop()
    * | IF(Z==1): PC <- IR.lit  
1. JMP (ADDR)
    * PC <- IR.lit
1. STASH
    * RS.push(TOS) | TOS <- DS.pop()
1. UNSTASH
    * DS.push(TOS)
    * TOS <- RS.pop()
1. CPSTASH //COPY STASH
    * DS.push(TOS)
    * TOS <- RS
1. LOOP (ADDR)
    * DS.push(TOS)
    * TOS <- RS.pop()
    * Z <- (TOS + 1) - RS
    * | IF(Z==1): RS.pop() | TOS <- DS.pop()

      | ELSE: RS.push(TOS + 1) | TOS <- DS.pop() | PC <- IR.lit

### PROCEDURES

1. CALL (ADDR)
    * RS.push(PC) | PC <- IR.lit
1. RET
    * PC <- RS.pop()

### MISC

1. HALT

## Транслятор

Интерфейс командной строки транслятора forthc:

```bash
forthc.py [-s START_ADR] [-d IO_ADR] SOURCE TARGET

Позиционные аргументы:
  SOURCE                файл с исходным кодом
  TARGET                имя файла для записи транслированного кода

Опции:
  -s START_ADR, --start-adr START_ADR
                        адрес начала выполнения инструкций процессора (начальное значение PC)
  -d IO_ADR, --device-adr IO_ADR
                        адрес внешнего устройства
```

### Этапы транслирования

1. Этап - выделение и удаление из исходного кода строковых литералов

2. Этап - выделение токенов

3. Этап - последовательная трансляция токенов и групп токенов из очереди в инструкции. На этом вместов адресов (инструкций и в значенихя операндах) присваиваются "затычки" - определяющие относительные смещения в разделах (инструкций, слов и данных)

4. Этап - вычисление и присвоение реальных адресов.

## Модель процессора

### Datapath

```text
                 ┌───────────────────────────────────────────────┐                                 
                 │                             mux_tos           │                                 
                 │                             ------►┌────┐     │                                 
                 │          mux_stck                ┌─┘DS  ◄─────┘                                 
┌──────────┐     │    ┌───┐◄--------                │   /  │                                       
│          ├─────┴────►DS └┐           ┌───────┐    │  MEM ◄──────────┐                            
│          │          │ /  ├─────┐     │  TOS  ◄────┤   /  │          │                            
│  DATA    │       ┌──►RS ┌┘     │     └───┬───┘    │  IR  ◄───┐      │              ┌────────────┐
│  STACK   │       │  └───┘      │         │        │   /  │   │      │              │            │
│          │       │       alu_l │         │ alu_r  └─┐ALU ◄─┐ │IR.lit│              │ MEMORY     │
│          ◄───────┼────┐  ----► │         │ ◄----    └────┘ │ │[26:0]│    MOUT[31:0]│ UNIT &     │
└──────────┘       │    │        │         │                 │ │      ├──────────────┤ CACHE      │
                   │    │     ┌──▼──┐   ┌──▼──┐        ┌─────┘ │      │         mrd  │            │
┌──────────┐       │    │     │     └───┘     │  CTRL  │       │      │         ---► │            │
│          ├───────┘    │     │               │  UNIT  │      ┌┴──────▼┐        mwr  │            │
│          │            │     └┐     ALU     ┌┘    ▲   │      │   IR   ├─┐      ---► │            │
│  RETURN  │            │      └┐           ┌┘     │   │      └────────┘ │           │            │
│  STACK   │   ┌───┐    │  ----►└─────┬──┬──┘    ┌─┴─┐ │                 │  MIN[31:0]│            │
│          │  ┌┘ALU◄────┤  alu_op     │  │    ┌─►│NZV│ ├─────────────────┼───────────►            │
│          ◄──┤  / │    │             │  └────┘  └───┘ │                 │           │            │
└──────────┘  └┐PC ◄──┐ │             │                │ ┌───┐           │           │            │
         -----►└───┘  │ └─────────────┴─┬──────────────┴─►ALU└┐  ┌────┐  │  ADR[26:0]│            │
         mux_rs       │                 │                │ /  ├──► AR ├──┼───────────►            │
                      └────────────┬────┼────────────────►PC ┌┘  └────┘  │           │            │
                                   │    │                └───┘◄------    │           │            │
   IR   ┌────────────┐             │    └───────────┐          mux_ar    │           │            │
   ─────►            │             │   mux_pc       │                    │           └────────────┘
   NZV  │            │             │   -----►┌────┐ │                    │                         
   ─────► CONTROL    │             │       ┌─┘    ◄─┘                    │IR.lit                   
        │ UNIT       │             │       │ ALU  │                      │[26:0]                   
   ◄----│            │         ┌───┴──┐    │  /   │                      │                         
 signals│            │         │  PC  ├────┤ IR   ◄──────────────────────┤                         
        └────────────┘         └───┬──┘    │  /   │                      │                         
                                   │       │ +1   │                      ▼                         
                                   │       └─┐    ◄────┐               CTRL                        
                                   │         └────┘    │               UNIT                        
                                   │                 ┌─┴┐                                          
                                   └─────────────────►+1│                                          
                                                     └──┘                                          
```

Особенности:

* NZV - флаги результата выставляются после каждой операции в АЛУ
* На схеме ради читаемости опущены сигналы замыкания регистров *_latch
* Сиганл alu_op - комплексный, выбирает операцию
* Memory Unit состоит из Cache и Memory

### Stack

```text
                                           STCK.peek():             
                                                                    
         ┌────────────┐                        mux_stck_adr = -1    
stck_rd  │            │STCKOUT[31:0]                                
-------► │ SRAM       ├─────►                  mux_sp = X           
         │ UNIT       │                                             
stck_wr  │            │                        sp_latch = 0         
-------► │ 128x32     │                                             
         │            │                    STCK.push(Y):            
         │            │STCKIN[31:0]                                 
         │            ◄──────                  mux_stck_adr = SP    
         │            │                                             
         └────▲───────┘                        mux_sp = +1          
              │ADR[6:0]                                             
              │                                sp_latch = 1         
            ┌─┴──┐                                                  
           ┌┘    └┐  mux_stck_adr          STCK.pop():              
           │-1/ SP│ ◄------------                                   
           └─▲──▲─┘                            mux_stck_adr = -1    
             │  │                                                   
             ├──┼──────────────────┐           mux_sp = -1          
             │  │                  │                                
           ┌─┴┐ │      ┌──┐        │           sp_latch = 1         
           │-1│ ├──────►+1├────┐   │                                
           └─▲┘ │      └──┘    │   │                                
             │  │            ┌─▼───▼─┐  mux_sp                      
             │  │            │+1 / -1│ ◄------                      
             │  │            └┐     ┌┘                              
             │  │             └──┬──┘                               
           ┌─┴──┴─┐              │                                  
           │  SP  ◄──────────────┘                                  
           └──────┘                                                 
```

### Control Unit

```text
          ┌─────────────────────────────┐            
          │        mux_mpc              │mIR.adr     
          │  ┌───┐◄-------              │            
          └──►mIR└┐                ┌────┴─────┐      
             │ /  │     ┌─────┐    │          │      
    ┌────────► IR ├─────► mPC ├─┬──► mPROGRAM │      
    │        │ /  │     └─────┘ │  │          │      
    │     ┌──► +1┌┘             │  └──────────┘      
    │     │  └───┘              │    ▲      |        
    │     │                     │    │      |        
    │     │                     │    │ NZV  | signals
    │     │        ┌──┐         │    │      |        
    │     └────────┤+1├─────────┘    │      |        
┌───┴───┐          └──┘              │      ▼        
│IR->mPC│                                            
└───▲───┘                          ┌──────────┐      
    │                              │          │      
    │            IR.opcode[31:27]  │          │      
    └──────────────────────────────┤ DATAPATH │      
                                   │          │      
                                   │          │      
                                   └──────────┘      
  mPROGRAM                                           
 ┌─────────────────────────────────────────────┐     
 │                                             │     
 │                   ▲                         │     
 │                   |                         │     
 │                   | signals                 │     
 │                   |                         │     
 │               ┌───────┐                     │     
 │           --► │signals│                     │     
 │           |   └───▲───┘                     │     
 │           |       │            ┌──────────┐ │     
 │           |   ┌───┴───┐ M.out  │mPROGRAM  │ │     
 │  mIR.type ----│  mIR  ├───◄────┤MEMORY    │ │     
 │           |   └───────┘        │          │ │     
 │           |       |            │          │ │     
 │           |  mIR.z|            └─────▲────┘ │     
 │           |       |                  │mAddr │     
 │    mJMP   ▼       ▼                  │      │     
 │    ◄------AND ◄--EQ◄--( Z/0 )    mPC │      │     
 │                        ▲   ▲         │      │     
 │                        |   |                │     
 │  Z can be one of NZV  Z|   |0               │     
 │  depending on mInstr   |   |                │     
 │                                             │     
 └─────────────────────────────────────────────┘     
```

## Тестирование

Тестирование выполняется при помощи golden test-ов.

Запуск golden-тестов: [golden_test.py](./golden_test.py)

Тесты:

* [tests/hello.yml](tests/hello.yml) - Печатает "Hello World!" в stdout
* [test/hello_user_name.yml](tests/hello_user_name.yml) - Запрашивает имя пользовается и приветствует его
* [test/cat.yml](tests/cat.yml) - Выводит символы, переданные в stdin, до истощения буфера
* [test/prob1.yml](tests/prob1.yml) - Euler problem 1
* [test/bubble_sort.yml](tests/bubble_sort.yml) - Сортировка пузырьком для проверки Cache'а
* [test/factorial.yml](tests/factorial.yml) - Подсчёт факториала, проверяющий рекурсию процедур

CI полностью взять из референсной работы.

Запуск тестов: `poetry run pytest . -v`

Обновление:  `poetry run pytest . -v --update-goldens`

CI при помощи Github Action:

``` yaml
name: Python CI

on:
  push:
    branches:
      - master
    paths:
      - ./*.py
      - ./*.lock
      - ./pyproject.toml
      - ./tests/*
      - .github/workflows/python.yaml
  pull_request:
    branches:
      - master
    paths:
      - ./*.py
      - ./*.lock
      - ./pyproject.toml
      - ./tests/*
      - .github/workflows/python.yaml
defaults:
  run:
    working-directory: ./

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .

      - name: Run Ruff linters
        run: poetry run ruff check .
```

Пример использования и журнал работы процессора на примере `cat`:

``` shell
$ cat ./programs/cat.f
: cat
        begin
                key dup dup if
                        emit  
                then
        0 = until
;
cat
$ python forthc.py -d 0 -s 10 ./programs/cat.f target.out
Translated successfully. Source LoC: 8  Machine Instructions: 13
$ cat target.out
[{"opcode": "call", "operand": 12, "token": {"val": "cat", "line": 8, "num": 1}, "offset": 10},
 {"opcode": "halt", "offset": 11},
 {"opcode": "push", "operand": 0, "token": {"val": "key", "line": 3, "num": 1}, "offset": 12},
 {"opcode": "fetch", "token": {"val": "key", "line": 3, "num": 1}, "offset": 13},
 {"opcode": "duplicate", "token": {"val": "dup", "line": 3, "num": 2}, "offset": 14},
 {"opcode": "duplicate", "token": {"val": "dup", "line": 3, "num": 3}, "offset": 15},
 {"opcode": "jump on zero", "operand": 19, "token": {"val": "if", "line": 3, "num": 4}, "offset": 16},
 {"opcode": "push", "operand": 0, "token": {"val": "emit", "line": 4, "num": 1}, "offset": 17},
 {"opcode": "store", "token": {"val": "emit", "line": 4, "num": 1}, "offset": 18},
 {"opcode": "push", "operand": 0, "token": {"val": "0", "line": 6, "num": 1}, "offset": 19},
 {"opcode": "equal", "token": {"val": "=", "line": 6, "num": 2}, "offset": 20},
 {"opcode": "jump on zero", "operand": 12, "token": {"val": "until", "line": 6, "num": 3}, "offset": 21},
 {"opcode": "return", "token": {"val": ";", "line": 7, "num": 1}, "offset": 22}]
$ python machine.py -j -d 0 -s 10 -m 1024 -c 32 target.out -i "St"
[JRNL]   TCK:     0   TOS:     0   ALU:     0
[JRNL] DS (LEN: 0): []...
[JRNL] RS (LEN: 0): []...
[JRNL]    PC:    10    IR: {}
[JRNL]   ADR:     0   MEM: 0
[JRNL]   mPC:     0 mPROG: ARLatch.PC, MemSignal.MemRD

[JRNL] Prefetch finishing: 0 extra ticks
[JRNL] Cache read 10 miss for 0 extra ticks
[JRNL] Cache insert 10
[JRNL] Memory store/fetch: 10 extra ticks

[JRNL] Started PARALLEL FETCHING of 14:
[JRNL] Cache miss on lookup 14
[JRNL] Cache insert 14
[JRNL] planned finish on 22 tick:

[JRNL] In total CPU waited for 10 extra ticks

[JRNL]   TCK:    11   TOS:     0   ALU:     0
[JRNL] DS (LEN: 0): []...
[JRNL] RS (LEN: 0): []...
[JRNL]    PC:    10    IR: {}
[JRNL]   ADR:    10   MEM: CALL  12 'cat'@8:1
[JRNL]   mPC:     1 mPROG: DPSignal.IRLatch, PCLatch.PLUS1

[JRNL]   TCK:    12   TOS:     0   ALU:     0
[JRNL] DS (LEN: 0): []...
[JRNL] RS (LEN: 0): []...
[JRNL]    PC:    11    IR: CALL  12 'cat'@8:1
[JRNL]   ADR:    10   MEM: CALL  12 'cat'@8:1
[JRNL]   mPC:     2 mPROG: mPCLatch.IR

...

[JRNL]   TCK:   193   TOS:     0   ALU:     0
[JRNL] DS (LEN: 1): [0]...
[JRNL] RS (LEN: 1): [11]...
[JRNL]    PC:    13    IR: PUSH   0 'key'@3:1
[JRNL]   ADR:    12   MEM: PUSH   0 'key'@3:1
[JRNL]   mPC:     0 mPROG: ARLatch.PC, MemSignal.MemRD

[JRNL] Prefetch finishing: 0 extra ticks
[JRNL] Cache read 13 hit for 0 extra ticks
[JRNL] In total CPU waited for 0 extra ticks

[JRNL]   TCK:   194   TOS:     0   ALU:     0
[JRNL] DS (LEN: 1): [0]...
[JRNL] RS (LEN: 1): [11]...
[JRNL]    PC:    13    IR: PUSH   0 'key'@3:1
[JRNL]   ADR:    13   MEM: FETCH 'key'@3:1
[JRNL]   mPC:     1 mPROG: DPSignal.IRLatch, PCLatch.PLUS1

[JRNL]   TCK:   195   TOS:     0   ALU:     0
[JRNL] DS (LEN: 1): [0]...
[JRNL] RS (LEN: 1): [11]...
[JRNL]    PC:    14    IR: FETCH 'key'@3:1
[JRNL]   ADR:    13   MEM: FETCH 'key'@3:1
[JRNL]   mPC:     2 mPROG: mPCLatch.IR

[JRNL]   TCK:   196   TOS:     0   ALU:     0
[JRNL] DS (LEN: 1): [0]...
[JRNL] RS (LEN: 1): [11]...
[JRNL]    PC:    14    IR: FETCH 'key'@3:1
[JRNL]   ADR:    13   MEM: FETCH 'key'@3:1
[JRNL]   mPC:    12 mPROG: ALUop, ARLatch.ALU, MemSignal.MemRD

[JRNL] Prefetch finishing: 0 extra ticks
[WARN] Input buffer was empty on fetch!
[INFO] Cache miss rate: 8.696%
[INFO] Ticks: 197
St
[JRNL] Output Buffer: St
[JRNL] Output Buffer(ASCII codes): 83, 116
[WARN] Input buffer was empty on fetch!
[INFO] Cache miss rate: 8.696%
[INFO] Ticks: 197
St
Cache miss rate: 8.696% Ticks: 197
```

Пример проверки исходного кода:

``` shell
$ poetry run pytest . -v
====================================================================================== test session starts ======================================================================================                                 
platform win32 -- Python 3.11.5, pytest-7.4.4, pluggy-1.5.0 -- C:\Users\marin\AppData\Local\pypoetry\Cache\virtualenvs\stack-processor-ibGfME1p-py3.11\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\marin\OneDrive\Documents\ITMOStudies\Computer Architecture\stack_processor
configfile: pyproject.toml
plugins: golden-0.2.2
collected 6 items

golden_test.py::test_forthc_and_machine[tests/bubble_sort.yml] PASSED                                                                                                                [ 16%]
golden_test.py::test_forthc_and_machine[tests/cat.yml] PASSED                                                                                                                        [ 33%]
golden_test.py::test_forthc_and_machine[tests/factorial.yml] PASSED                                                                                                                  [ 50%]
golden_test.py::test_forthc_and_machine[tests/hello.yml] PASSED                                                                                                                      [ 66%]
golden_test.py::test_forthc_and_machine[tests/hello_user_name.yml] PASSED                                                                                                            [ 83%]
golden_test.py::test_forthc_and_machine[tests/prob1.yml] PASSED                                                                                                                      [100%]

============================================================================== 6 passed in 145.76s (0:02:25) ============================================================================== 


$ poetry run ruff check .
$ poetry run ruff format .
10 files left unchanged
```

```text
| ФИО                            | алг   | LoC | code байт | code инстр. | инстр. | такт. | вариант |
| Хороших Дмитрий Максимович | cat   | 1   | -         | 6           | 15     | 28    | ...     |
```
