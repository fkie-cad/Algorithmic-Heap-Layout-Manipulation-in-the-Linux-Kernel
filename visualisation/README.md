# Visualisation

The script `animatesolution.py` can be used to visualize the results from our algorithmic solutions.

In order to run the script at least a candidate solution needes to be provided:
```bash
$ ./animatesolution.py <candidate>
```
To ensure that the script is working on your system try at first our provided example candidate:
```bash
$ ./animatesolution.py beispiel.txt 
[*] kmalloc at 0
[*] kmalloc at 1
[*] kmalloc at 2
[*] kmalloc at 3
[*] kmalloc at 4
[*] kmalloc at 5
[*] kmalloc at 6
[*] kmalloc at 7
[*] kmalloc at 8
[*] kfree at 2
[*] kfree at 8
[*] kfree at 6
[*] kfree at 4
[*] kmalloc at 4
[*] kfree at 0
[*] kfree at 5
[*] kmalloc at 5
[*] kfree at 3
[*] kmalloc at 3
[*] kfree at 7
[*] kmalloc at 7
[*] kfree at 1
[*] kfree at 5
[*] kmalloc at 5
[*] kfree at 3
[*] kfree at 7
[*] kmalloc at 7
[*] kmalloc at 3
[*] kfree at 5
[*] kfree at 4
[*] kfree at 3
[*] kfree at 7
[*] kmalloc at 7
[*] kmalloc at 3
[*] kmalloc at 4
[*] fst at 5
[*] kmalloc at 1
[*] kmalloc at 0
[*] snd at 6
```
While this script is running you should see the animated allocations and deallocations.

By default our animation is visualizing for a real scenario which means that instead of kmalloc and kfree some system calls are used which are under the control of the exploit developer. Currently we hardcoded only the system calls which are used in our example exploit inside `animatesolution.py` but this can easisly be changed.

## Animating results from algorithmus

In order to use the animation script while working with Kernel-SIEVE or to be more precise to work with the results from the algorithm we have to tell our script that we are running in Kernel-SIEVE mode. When we run for instance KEvoHeap we will receive the following three directories:
```bash
$ ls
ins  raw  res
```

Inside ins we will see the different candiates with its allocations and deallocations:
```bash
$ ls ins/
0    109  12   130  141  152  163  174  185  196  206  217  228  239  25   260  271  282  293  303  314  325  336  347  358  369  38   390  41  52  63  74  85  96
1    11   120  131  142  153  164  175  186  197  207  218  229  24   250  261  272  283  294  304  315  326  337  348  359  37   380  391  42  53  64  75  86  97
10   110  121  132  143  154  165  176  187  198  208  219  23   240  251  262  273  284  295  305  316  327  338  349  36   370  381  392  43  54  65  76  87  98
100  111  122  133  144  155  166  177  188  199  209  22   230  241  252  263  274  285  296  306  317  328  339  35   360  371  382  393  44  55  66  77  88  99
101  112  123  134  145  156  167  178  189  2    21   220  231  242  253  264  275  286  297  307  318  329  34   350  361  372  383  394  45  56  67  78  89
102  113  124  135  146  157  168  179  19   20   210  221  232  243  254  265  276  287  298  308  319  33   340  351  362  373  384  395  46  57  68  79  9
103  114  125  136  147  158  169  18   190  200  211  222  233  244  255  266  277  288  299  309  32   330  341  352  363  374  385  396  47  58  69  8   90
104  115  126  137  148  159  17   180  191  201  212  223  234  245  256  267  278  289  3    31   320  331  342  353  364  375  386  397  48  59  7   80  91
105  116  127  138  149  16   170  181  192  202  213  224  235  246  257  268  279  29   30   310  321  332  343  354  365  376  387  398  49  6   70  81  92
106  117  128  139  15   160  171  182  193  203  214  225  236  247  258  269  28   290  300  311  322  333  344  355  366  377  388  399  5   60  71  82  93
107  118  129  14   150  161  172  183  194  204  215  226  237  248  259  27   280  291  301  312  323  334  345  356  367  378  389  4    50  61  72  83  94
108  119  13   140  151  162  173  184  195  205  216  227  238  249  26   270  281  292  302  313  324  335  346  357  368  379  39   40   51  62  73  84  95
```

Now when we want to see how a candiate is working we just have to invoke `animatesolution.py` like this:
```bash
./animatesolution.py -f ksieve ins/101
[*] kmalloc at 0
[*] kmalloc at 1
[*] kmalloc at 2
[*] kmalloc at 3
[*] kmalloc at 4
[*] kmalloc at 5
[*] kmalloc at 6
[*] kmalloc at 7
[*] kmalloc at 8
[*] kmalloc at 9
[*] kfree at 3
[*] kfree at 5
[*] kfree at 7
[*] kfree at 9
[*] kmalloc at 9
[*] kmalloc at 7
[*] kmalloc at 5
[*] fst at 3
[*] kmalloc at 10
[*] kmalloc at 11
[*] kmalloc at 12
[*] kfree at 4
[*] snd at 4
```

This way we can easily understand how this allocations/deallocations are working and manipulate the heap layout.

## Requirements

- >= python3.6
- pyglet (`pip install pyglet`)
