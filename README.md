```
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

```
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
│  STACK   │   ┌───┐    │  ----►└─────┬──┬──┘     ┌┴┐  │                 │  MIN[31:0]│            │
│          │  ┌┘ALU◄────┤  alu_op     │  │      ┌─►Z│  ├─────────────────┼───────────►            │
│          ◄──┤  / │    │             │  └──────┘ └─┘  │                 │           │            │
└──────────┘  └┐PC ◄──┐ │             │                │   ┌──────┐      │  ADR[26:0]│            │
         -----►└───┘  │ └─────────────┴──────────┬─────┴───►  AR  ├──────┼───────────►            │
         mux_rs       │                          │         └──────┘      │           │            │
                      └────────────────────┐     └────────┐              │           │            │
                                           │ mux_pc       │              │           │            │
                  IR   ┌────────────┐      │ -----►┌────┐ │              │           │            │
                  ─────►            │      │     ┌─┘    ◄─┘              │IR.lit     └────────────┘
                  Z    │            │      │     │ ALU  │                │[26:0]                   
                  ─────► CONTROL    │  ┌───┴──┐  │  /   │                │                         
                       │ UNIT       │  │  PC  ◄──┤ IR   ◄────────────────┤                         
                  ◄----│            │  └───┬──┘  │  /   │                │                         
                signals│            │      │     │ +1   │                ▼                         
                       └────────────┘      │     └─┐    ◄────┐         CTRL                        
                                           │       └────┘    │         UNIT                        
                                           │               ┌─┴┐                                    
                                           └───────────────►+1│                                    
                                                           └──┘                                    
```

```
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
```
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
    │     │                     │    │ Z    | signals                                                                  
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
  ┌────────────────────────────────────────────┐                                                                       
  │                                            │                                                                       
  │                  ▲                         │                                                                       
  │                  |                         │                                                                       
  │                  | signals                 │                                                                       
  │                  |                         │                                                                       
  │              ┌───────┐                     │                                                                       
  │          --► │signals│                     │                                                                       
  │          |   └───▲───┘                     │                                                                       
  │  mIR.type|       │            ┌──────────┐ │                                                                       
  │          |   ┌───┴───┐ M.out  │mPROGRAM  │ │                                                                       
  │          ----│  mIR  ├───◄────┤MEMORY    │ │                                                                       
  │          |   └───────┘        │          │ │                                                                       
  │          |       |            │          │ │                                                                       
  │          |  mIR.z|            └─────▲────┘ │                                                                       
  │          |       |                  │mAddr │                                                                       
  │   mJMP   ▼       ▼                  │      │                                                                       
  │   ◄------AND ◄--EQ◄--( Z/0 )    mPC │      │                                                                       
  │                       ▲   ▲         │      │                                                                       
  │                       |   |                │                                                                       
  │                      Z|   |0               │                                                                       
  │                       |   |                │                                                                       
  └────────────────────────────────────────────┘                                                                       
                                                                                                                    
```