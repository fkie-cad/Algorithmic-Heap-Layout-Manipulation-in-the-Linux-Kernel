# Visualisation

The content of this README:
- [Visualisation](#visualisation)
  * [Animating results from algorithm](#animating-results-from-algorithm)
  * [Requirements animatesolution.py](#requirements-animatesolutionpy)
  * [Preprocessing tries.log](#preprocessing-trieslog)
  * [Plotting](#plotting)
  * [Requirements Plotting](#requirements-plotting)

## Visualize the results from our algorithmic solutions

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

## Animating results from algorithm

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

## Requirements animatesolution.py 

- >= python3.6 
- pyglet (`pip install pyglet`)

## Preprocessing tries.log

When running kevoheap via `./evo_statistics.sh` and randomsearch via `./random_statistics.sh` (both from INSIDE the VM) a solution file called `tries.log` is created. This file contains the number of generations it needed to find a solution. By default both scripts will run the respective algorithm for 3 noise 100 times for the allocation order "natural". In the following we see an example output from  `tries.log`  after running  `./evo_statistics.sh` configured for 3 noise 100 times for the allocation order "natural":
```bash
$ cat tries.log
Number of generations:
4
11
4
6
5
8
6
11
4
10
9
5
5
6
2
2
2
5
11
2
2
11
5
2
2
5
9
11
2
7
8
4
11
5
17
5
8
5
2
7
4
3
7
8
2
2
17
2
6
8
9
8
8
6
8
5
6
5
7
3
4
7
2
11
5
5
8
4
10
3
13
4
10
10
6
2
5
9
3
13
11
4
5
2
12
11
10
10
7
12
7
10
2
3
3
8
2
5
3
11
```

Now we can calculate the average generations easily utilizing `awk`:
```bash
$ awk 'BEGIN {print "Calculating average generations:"} NR > 1 { sum += $1; n++ } END { if (n > 0) print sum / n; }' tries.log
Calculating average generations:
6.42
```
In order to plot these results we have to remember that each generation consist of 400 candidate solutions (cf. (KEvoHeap)[https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/blob/25b4b3f671ad414f03e35486129c54eff981fa92/algorithms/evoheap.py#L442]). For KEvoHeap we have to keep that into account when we want to get the average tries it took to get a solution:
```bash
$ awk 'BEGIN {print "Calculating candidates (num of tries):"} NR > 1 {sum =$1*400 + sum; n++} END { if (n > 0) printf("%.0f\n", sum / n);; }' tries.log
Calculating candidates (num of tries):
400
```
Instead when wan to calculate the overall number of tries it took to get a solution from pseudo-random search we don't have to take that into account because its `tries.log`-file already contains the final number of tries:
```bash
$ awk 'BEGIN {print "Calculating candidates (num of tries):"} NR > 1 {sum =$1 + sum; n++} END { if (n > 0)  printf("%.0f\n", sum / n); }' tries.log
Calculating candidates (num of tries):
3
```
To indicate if we are dealing with the total number of candidates or if we only have the number of generations we have to analyze the first line of `tries.log`:
```bash
Number of tries: 		--> total number of candidates
Number of generations:	--> number of generations
```

Furthermore, if we want to plot something we take the average candidate solutions for the respective noise level. So for instance to plot a bar chart showing the average generations needed in both algorithms with respect to the level of noise, we have to generate for each noise level a `tries.log`-file for each algorithm. Instead of doing this manually we provided `preprocessing.py` to do the parsing. It expects a folder containing the different `tries.log`- files which have the following structure:
```
<noise_level>_noise_<algorithm>.log --> natural allocation order
<noise_level>_noise_rev_<algorithm>.log --> reverse allocation order
```
In our example to illustrate the steps to be taken we will have the following two folders:
```bash
$ ls natural
0_noise_kevo.log  1_noise_kevo.log  2_noise_kevo.log  3_noise_kevo.log  4_noise_kevo.log  5_noise_kevo.log  6_noise_kevo.log
0_noise_prs.log   1_noise_prs.log   2_noise_prs.log   3_noise_prs.log   4_noise_prs.log   5_noise_prs.log
$ ls reverse
0_noise_rev_kevo.log  1_noise_rev_kevo.log  2_noise_rev_kevo.log  3_noise_rev_kevo.log  4_noise_rev_kevo.log  5_noise_rev_kevo.log  6_noise_rev_kevo.log
0_noise_rev_prs.log   1_noise_rev_prs.log   2_noise_rev_prs.log   3_noise_rev_prs.log   4_noise_rev_prs.log   5_noise_rev_prs.log
```

We can use our `preprocessing.py`-script in order to get a list of average candidate solutions for the respective noise level. If we redirect the output to a file, we can later use that file for plotting:
```bash
$ ./preprocessing.py reverse > natural_allocation_challenge.log
$ cat natural_allocation_challenge.log
400 kevo
400 kevo
496 kevo
1220 kevo
1900 kevo
2548 kevo
3280 kevo
9 prs
61 prs
376 prs
2796 prs
28408 prs
42752 prs
```

Keep in mind when we want to do a box plot we need instead n-times a `tries.log`-file for the same noise level, the same algorithm and the same allocation order. Its struture should than look like the following:
```
<noise_level>_noise_<algorithm>_<iterator>.log --> natural allocation order
<noise_level>_noise_rev_<algorithm>_<iterator>.log --> reverse allocation order
```
and the example directory of  n-times the `tries.log`-file looks like the following:
```bash
$ ls noise0_reverse_challenge_100_runs/
0_noise_rev_kevo_10.log  0_noise_rev_kevo_14.log  0_noise_rev_kevo_4.log  0_noise_rev_kevo_8.log  0_noise_rev_prs_12.log  0_noise_rev_prs_4.log  0_noise_rev_prs_8.log
0_noise_rev_kevo_11.log  0_noise_rev_kevo_1.log   0_noise_rev_kevo_5.log  0_noise_rev_kevo_9.log  0_noise_rev_prs_1.log   0_noise_rev_prs_5.log  0_noise_rev_prs_9.log
0_noise_rev_kevo_12.log  0_noise_rev_kevo_2.log   0_noise_rev_kevo_6.log  0_noise_rev_prs_10.log  0_noise_rev_prs_2.log   0_noise_rev_prs_6.log  0_noise_rev_prs_7.log
...
```

Because of the diffrent structure of these files we need to provide the parameter `-f box` to tell the `preprocessing.py`-script that its structure changed:
```bash
$ ./preprocessing.py -f box noise0_reverse_challenge_100_runs > box_blot_data_noise0_reverse_challenge_100_runs.log
$ cat box_blot_data_noise0_reverse_challenge_100_runs.log
400 kevo
2748 kevo
4648 kevo
9140 kevo
17300 kevo
400 kevo
400 kevo
496 kevo
1220 kevo
1900 kevo
...
```

Now we know how to preprocess the `tries.log`-files to plot the log data.

## Plotting

The scripts `box_plots.py` and `bar_charts.py` can be used to plot the results from the `tries.log`-file after we preprocessed them. In order to check if these scripts working on your system try at first to generate the plots with the provided `.log`-files. These log files contain the data used in our paper.

`./bar_charts.py` gets as an paramter a file which contains the candidates and should looks like this:
```bash
400 kevo
436 kevo
..
3 prs
...
```
The first column indicates the number of candidates and the second column the used algorithm (cf. above). Further the order indicates the noise level.

With a given candidate file we can generate the bar charts:
```bash
./bar_charts.py reverse_challenge.log
./bar_charts.py natural_challenge.log
```

With a given candidate file we can also generate box plots:
```bash
./box_plots.py reverse_challenge_100_runs.log
```


## Requirements Plotting
- >= python3.6
- numpy (`pip3 install numpy`)
- matplotlib (`pip3 install matplotlib`)

