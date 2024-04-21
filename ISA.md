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

### LOGIC OPERATION
12. NOT
    - TOS <- ~TOS
13. OR
    - TOS <- TOS or DS.pop()
14. AND
    - TOS <- TOS and DS.pop()

### COMPARE OPERATION
15. EQUAL
    - Z <- TOS or DS.pop()
    - | IF(Z==1): TOS <- 1
      | ELSE: TOS <- 0

### BRANCHING, LOOPING & RETURN STACK

16. JMPZ (ADDR)
    - Z <- TOS | TOS <- DS.pop()
    - | IF(Z==1): PC <- IR.lit  
17. JMP (ADDR)
    - PC <- IR.lit
18. STASH
    - RS.push(TOS) | TOS <- DS.pop()
19. UNSTASH
    - DS.push(TOS)
    - TOS <- RS.pop()
20. CPSTASH //COPY STASH
    - DS.push(TOS)
    - TOS <- RS
21. LOOP (ADDR)
    - DS.push(TOS)
    - TOS <- RS.pop() 
    - Z <- (TOS + 1) - RS
    - | IF(Z==1): RS.pop() | PC <- IR.lit | TOS <- DS.pop()

      | ELSE: RS.push(TOS + 1) | TOS <- DS.pop()
### PROCEDURES
22. CALL (ADDR)
    - RS.push(PC) | PC <- IR.lit
23. RET
    - PC <- RS.pop()

### MISC

24. HALT
