: word 1 * ;

variable buffer 256 word allot 

: get_name 1 begin
  key dup 13 = if
    drop 1 -  buffer ! leave
  else
    swap buffer + ! 1 +
  then
  dup 256 = until
drop ;

." Please, enter your name and press ENTER:"

get_name

." Hello, "

: print_name buffer @ 1 do
  buffer i + @ emit
  loop ;

print_name