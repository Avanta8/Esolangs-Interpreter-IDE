[multiply numbers without seeing how to do it
0 -> input 1
1 -> input 2
2 -> temp for 1
3 -> output]

,>,    Take input

[-<    Decrease 1; back to 0
    Increase 2 and 3 by 0
    [->>+>+    Increase 2 and 3
     <<<    Back to 0
    ]
    
    Reload 0 with 2
    >>    To 2
    [-<<+>>]    Reload 0

    <    To 1
]

>>    To 3
.


[-]    Short Version:
[
    ,>,[-<[->>+>+<<<]>>[-<<+>>]<]>>.
]
