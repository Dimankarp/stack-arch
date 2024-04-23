( this method is used as . word aka 'print number' | stores on stack)
variable counter
: emit_num
    dup -2147483648 ( 31st bit 1, sign checker)
    and if ( enter if when number is negative)
        45 emit ( hyphen -) -1 *
    then
    0 counter !
    begin
        counter @ 1 + counter !
        dup
        10 mod 48 + ( ascii-izing digit) swap
        10 /
    dup 0 = until
    drop

    counter @ 1 do
        emit
    loop
;

-1561445 emit_num