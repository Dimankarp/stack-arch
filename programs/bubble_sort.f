variable buffer sallot 255
: get_data 
    1 begin
        dup key dup 13 = if
            drop 1 - buffer ! leave
        else
            swap buffer + ! 1 +
        then
    dup 256 = until
drop
;

get_data

: bubble_sort
        begin
            1 
            buffer @ 1 - 1 do
                buffer i + @
                buffer i + 1 + @ < 
                buffer i + @
                buffer i + 1 + @ =
                or if ( pass )
                else
                    drop 0
                    buffer i + 1 + @
                    buffer i + @
                    buffer i + 1 + !
                    buffer i + !
                then
            loop
        until
;

bubble_sort

: print_data
    buffer @ 1 do
        buffer i + @ emit
    loop
;

print_data