GSM Instruction Set:
* DS - Data Stack
* RS - Return Stack
* TOS - Top of Data Stack register 

### STACK & MEMORY OPERATIONS

1. PUSH (LIT)
    - DS.push(TOS) |  TOS <- IR.lit
2. POP
    - TOS <- DS.pop()
3. DUP
    - DS.push(TOS)
4. SWAP
    - RS.push(TOS) | TOS <- DS.pop()
    - DS.push(RS.pop())
5. FETCH
    - ADR <- TOS
    - TOS <- MEM.out(ADR)
6. STORE
    - ADR <- TOS
    - MEM.in <- DS.pop()
    - TOS <- DS.pop()

### ARITHMETIC OPERATIONS

7. ADD
    - TOS <- TOS + DS.pop()
8. SUB
    - TOS <- TOS - DS.pop()
9. MUL
    - TOS <- TOS * DS.pop()
10. DIV
    - TOS <- TOS / DS.pop()
11. MOD
    - TOS <- TOS % DS.pop()

### BRANCHING, LOOPING & RETURN STACK

12. JMPNZ (ADDR)
    - Z <- TOS | TOS <- DS.pop()
    - | IF(Z==0): PC <- IR.lit  
13. JMP (ADDR)
    - PC <- IR.lit
14. STASH
    - RS.push(TOS) | TOS <- DS.pop()
15. UNSTASH
    - DS.push(TOS)
    - TOS <- RS.pop()
16. CPSTASH //COPY STASH
    - DS.push(TOS)
    - TOS <- RS
17. LOOP (ADDR)
    - DS.push(TOS)
    - TOS <- RS.pop() 
    - Z <- (TOS + 1) - RS
    - | IF(Z==1): RS.pop() | PC <- IR.lit | TOS <- DS.pop()

      | ELSE: RS.push(TOS + 1) | TOS <- DS.pop()
### PROCEDURES
18. CALL (ADDR)
    - RS.push(PC) | PC <- IR.lit
19. RET
    - PC <- RS.pop()
