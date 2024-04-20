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
                                           STCK.peek():             
                                                                    
         +------------+                        mux_stck_adr = -1    
stck_rd  |            |STCKOUT[31:0]                                
-------> | SRAM       +----->                  mux_sp = X           
         | UNIT       |                                             
stck_wr  |            |                        sp_latch = 0         
-------> | 128x32     |                                             
         |            |                    STCK.push(Y):            
         |            |STCKIN[31:0]                                 
         |            <------                  mux_stck_adr = SP    
         |            |                                             
         +----^-------+                        mux_sp = +1          
              |ADR[6:0]                                             
              |                                sp_latch = 1         
            +-+--+                                                  
           ++    ++  mux_stck_adr          STCK.pop():              
           |-1/ SP| <------------                                   
           +-^--^-+                            mux_stck_adr = -1    
             |  |                                                   
             +--+------------------+           mux_sp = -1          
             |  |                  |                                
           +-++ |      +--+        |           sp_latch = 1         
           |-1| +------>+1+----+   |                                
           +-^+ |      +--+    |   |                                
             |  |            +-v---v-+  mux_sp                      
             |  |            |+1 / -1| <------                      
             |  |            ++     ++                              
             |  |             +--+--+                               
           +-+--+-+              |                                  
           |  SP  <--------------+                                  
           +------+                                                 
```