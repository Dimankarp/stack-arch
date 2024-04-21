variable buffer sallot 255

: get_name 1 begin
  dup key dup 13 = if
    drop 1 -  buffer ! drop 256
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