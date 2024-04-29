variable a 
sallot 400
variable b

: destroy_hit_rate
    400 1 do
    i 2 mod if
        1 a i + !
    else
        0 b i - !
    then
    loop
;

destroy_hit_rate