: factorial
     dup 1 = if
        ( pass )
    else
        dup
        1 - factorial
        *
    then
;

10 factorial .