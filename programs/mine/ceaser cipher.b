[
Ceaser cipher program. By Harry Min.
The first character is the key (We can only have a max key of 9, sorry :P)
The rest are input characters to be encoded.
This overflows. (I don't know how to do modulus yet :P)
Finishes on \0.
]
[
c0 <- key
c1 <- temp for key
c2 <- current char
]

,    Get key

Now subtract 48
>+++++ +    To c1; Add 6
[
    -<    Sub 1; To c0
    ----- ---    Sub 8
    >    To c1
]
Pointer at 1
>    To c2

,    Take input
While input is not \0:
[
    <<    To c0
    [
        -    Sub 1
        >+>+    Add 1 to c1 and c2
        <<    To 0
    ]

    Now reload 0
    >    To c1
    [-<+>]    Add c2 to c1

    >    To c2
    .    Output
    ,    Next input char
]
