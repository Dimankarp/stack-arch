# Stack Processor

```text
forth - Forth, procedures required
stack
neum - Von Neumann
mc - Microcoded
tick - Tick level
struct - Commands as Data Structure
stream - IO as token stream
mem - Memory Mapped
pstr - Pascal String
prob1  - Multiples of 3 or 5  | cache
```

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

GSM Instruction Set:

* DS - Data Stack
* RS - Return Stack
* TOS - Top of Data Stack register

## STACK & MEMORY OPERATIONS

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
