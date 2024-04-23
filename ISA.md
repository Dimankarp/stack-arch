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
    - TOS <- DS.pop() + TOS 
8. SUB
    - TOS <- DS.pop() - TOS 
9. MUL
    - TOS <- DS.pop() * TOS
10. DIV
    - TOS <- DS.pop() / TOS
11. MOD
    - TOS <- DS.pop() % TOS

### LOGIC OPERATION
12. OR
    - TOS <- TOS or DS.pop()
13. AND
    - TOS <- TOS and DS.pop()

### COMPARE OPERATION
14. EQUAL
    - Z <- TOS or DS.pop()
    - | IF(Z==1): TOS <- 1
      | ELSE: TOS <- 0

### BRANCHING, LOOPING & RETURN STACK

15. JMPZ (ADDR)
    - Z <- TOS | TOS <- DS.pop()
    - | IF(Z==1): PC <- IR.lit  
16. JMP (ADDR)
    - PC <- IR.lit
17. STASH
    - RS.push(TOS) | TOS <- DS.pop()
18. UNSTASH
    - DS.push(TOS)
    - TOS <- RS.pop()
19. CPSTASH //COPY STASH
    - DS.push(TOS)
    - TOS <- RS
20. LOOP (ADDR)
    - DS.push(TOS)
    - TOS <- RS.pop() 
    - Z <- (TOS + 1) - RS
    - | IF(Z==1): RS.pop() | TOS <- DS.pop()

      | ELSE: RS.push(TOS + 1) | TOS <- DS.pop() | PC <- IR.lit 
### PROCEDURES
21. CALL (ADDR)
    - RS.push(PC) | PC <- IR.lit
22. RET
    - PC <- RS.pop()

### MISC

23. HALT
