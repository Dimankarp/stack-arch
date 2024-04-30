variable num
: input_num 0 num !
    begin
        key dup 13 = if
        ( pass )
        else
           dup 48 - num @ 10 * + num !
        then
    13 = until
    num @
;
: guess_num
    begin 
        dup input_num ." Your choice is: " dup .
        = if
            ." \n You are right!\n"
            1
        else
            ." \n You are wrong\n"
            0
        then
    until
;
12 guess_num