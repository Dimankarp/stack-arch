variable buffer sallot 255

: get_name 
  1 begin
    dup key dup 13 = if
      drop 1 -  buffer ! drop 256 ( 256 is here instead of leave)
    else
      swap buffer + ! 1 +
    then
    dup 256 = until
  drop
;

." Please, enter your name and press ENTER:"

get_name

." Hello, "

( 1 + is used since start is 1, hence -  everything is up by 1)
: print_name 
  buffer @ dup 0 = if
    else
      1 do 
        buffer i + @ emit
      loop
    then
;

print_name