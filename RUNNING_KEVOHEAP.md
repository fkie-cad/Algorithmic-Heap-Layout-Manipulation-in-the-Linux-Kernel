# Running KEvoHeap
Setting up an environment to effectively run KEvoHeap+QEMU is a little bit convoluted, so here are some instructions

## Run KEvoHeap+QEMU+KernelSieve (Custom-Cache Method)
This is probably the method you want to use if you want to recreate the results from the paper, as it offers the best performance, so it is best for running experiments multiple times in a row.

A large part of setting up QEMU has been automated, but some manual steps still have to be performed.

1. Run the `setup.sh` script. This script will perform the following steps:
    - Install dependencies (should work on Debian-based distros as well as Arch-based distros)
    - Download kernel source code (currently v5.14.11) into a folder called "kernel_src"
    - configure and build the kernel
    - create a debian image for qemu, using "create-image.sh" script, which is a slightly modified version of the script syzkaller uses to create images
    - convert the image to qcow2 (needed for savevm)
2. In both `kernel_sieve/client/kernel_sieve.c` and `kernel_sieve/kernel_module/slab_api.c`, comment out or remove the line `#define USE_REAL`. 
3. Build the KernelSieve client and kernel module
```bash
$ cd kernel_sieve/client/
$ gcc kernel_sieve.c -static -o kernel_sieve
$ cd ../kernel_module
$ make
```
4. Start qemu using `qemu_startup_qcow2_no_load.sh`
5. Copy the following files to qemu
```bash
$ ./scp_to_qemu.sh kernel_sieve/client/kernel_sieve
$ ./scp_to_qemu.sh kernel_sieve/kernel_module/slab_api.ko
$ ./scp_to_qemu.sh algorithms/evoheap.py
$ ./scp_to_qemu.sh algorithms/randomsearch.py
$ ./scp_to_qemu.sh ./evo_statistics.sh
$ ./scp_to_qemu.sh ./random_statistics.sh
```
6. Login to qemu, load the kernel module and create the folders ins, res, raw and exec
```bash
$ ./ssh.sh #(Or login with user "root")
...
root@syzkaller:~# insmod slab_api.ko
root@syzkaller:~# mkdir ins res raw exec
```
7. Now you are ready to run kevoheap via `./evo_statistics.sh` and randomsearch via `./random_statistics.sh` (both from INSIDE the VM). Per default, both scripts will run the respective algorithm for 3 noise 100 times and write the number of generations it needed to find a solution to a file called `tries.log`. To change the number of times the algrithm should be run, change the variable `GLOBAL_RUNS` in the script. To change the level of noise, change the variable `NOISE`. The default allocation order is "natural". If you want to change it to reverse, you need to change the target distance to a positive value _both_ in the runner scripts and in evoheap.py (at the place where `EvoHeapWithNoise` is created, in the function `use_slabapi_allocs`)

## Run KEvoHeap+QEMU+KernelSieve (Fast-Reset Method)
1. Run the `setup.sh` script.
2. Build the KernelSieve client and kernel module
```bash
$ cd kernel_sieve/client/
$ gcc kernel_sieve.c -static -o kernel_sieve
$ cd ../kernel_module
$ make
```
3. Start qemu using `qemu_startup_qcow2_no_load.sh`
4. Copy the client, the kernel module, and the netcat server to qemu
```bash
$ ./scp_to_qemu.sh kernel_sieve/client/kernel_sieve
$ ./scp_to_qemu.sh kernel_sieve/kernel_module/slab_api.ko
$ ./scp_to_qemu.sh ./netcat_from_buster
$ ./scp_to_qemu.sh ./ncserver.sh
```
5. Login to qemu, load the kernel module and start the server
```bash
$ ./ssh.sh #(Or login with user "root")
root@syzkaller:~# insmod slab_api.ko
root@syzkaller:~# chmod +x ncserver.sh
root@syzkaller:~# ./ncserver.sh &
```

6. create folders `ins`, `res` , `raw` and `exec` both in the VM as well as on the host
```bash
$ mkdir ins res raw exec
```
7. Create the savestate that we will use for Fast-Reset. To do this, access qemu monitor in another tab/window. One way to do this is to connect to it via netcat on port 55555
```bash
#On the host
$ nc localhost 55555
$ savevm savestate
```

Now you should quit (just enter `quit`) this qemu session or you can just press `CTRL+C`. QEMU will start automatically by the scripts to generate the statistics in the final step.

8. To now run EvoHeap with fast reset, quit qemu and run `fast_reset_evo_statistics.sh` (The script starts a new qemu instance, thats why we quit qemu first). To modify the number of noise allocations, edit the `fast_reset_evo_statistics.sh` script and change the `-n` parameter in the line `python3 algorithms/evoheap.py -a ksieve -n 3`.


## Run KEvoHeap+QEMU+BPFTrace
This section describes how to setup everything to use KEvoHeap on the `vuln` kernel module, an examplary vulnerable kernel module, with the help of bpftrace. More information about the `vuln` module can be found in `EXAMPLE_VULN.md`.

1. Run the `setup.sh` script with the `-e` flag to enable bpf support:
```bash
$ ./setup.sh -e
```
2. Build the `slab_api` kernel module
```bash
$ cd kernel_sieve/kernel_module
$ make
```
3. Build the `vuln` kernel module
```bash
$ cd vuln
$ make
```
4. Start qemu using `qemu_startup_qcow2_no_load.sh`
5. Copy the following files to qemu:
```bash
$ ./scp_to_qemu.sh kernel_sieve/kernel_module/slab_api.ko
$ ./scp_to_qemu.sh vuln/vuln.ko
$ ./scp_to_qemu.sh ./netcat_from_buster
$ ./scp_to_qemu.sh ./ncserver.sh
$ ./scp_to_qemu.sh ./kmem.bt
```
6. create folders `ins`, `res`, `raw`, and `exec` both in the VM as well as on the host.
Host (in the same path as `./bpf_evo_runner.sh`; we expect it to be root folder of our repo):
```bash
$ mkdir ins res raw exec
```
```bash
$ ./ssh.sh
Linux syzkaller 5.14.11 #1 SMP Mon Sep 19 12:10:32 CEST 2022 x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
A valid context for root could not be obtained.
Last login: Tue Sep 20 05:36:12 2022 from 10.0.2.10
root@syzkaller:~# mkdir ins res raw exec
```
7. Shut qemu down and restart it (e.g. run `reboot`)
8. Load the modules, start the server and bpftrace
```bash
$ ./ssh.sh
...
root@syzkaller:~# mkdir ins res raw exec
root@syzkaller:~# insmod slab_api.ko
root@syzkaller:~# insmod vuln.ko
root@syzkaller:~# chmod +x ncserver.sh
root@syzkaller:~# ./ncserver.sh &
root@syzkaller:~# chmod +x kmem.bt
root@syzkaller:~# ./kmem.bt > /tmp/dist
```
9. Create the savestate that we will use for Fast-Reset. To do this, access qemu monitor in another tab/window. One way to do this is to connect to it via netcat on port 55555
```bash
#On the host
$ nc localhost 55555
$ savevm savestate
```
                                                                                          
Now you should quit (just enter `quit`) this qemu session or you can just press `CTRL+C`. QEMU will start automatically by the runner script in the final step.

10. Run evoheap via `./bpf_evo_runner.sh` after modifying `./algorithms/evoheap.py` accordingly to your needs. If you want to modify the number of noise allocations performed, you need to modify the `vuln` kernel module and rebuild it. The default is 2.

```bash
$./bpf_evo_runner.sh
[*] Starting try number 1
...
Ping...
Ping...
Ping...
Ping...
...
Ping...
Ping...
Ping...
Ping...
Going into next gen after 72 tries
[!] Found solution!
int fengshui318 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
int fengshui573 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
int fengshui956 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
int fengshui628 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
int fengshui230 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
int fengshui1249 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
int fengshui569 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
int fengshui1518 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
int fengshui984 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
shmctl(fengshui956, IPC_RMID, NULL);
shmctl(fengshui984, IPC_RMID, NULL);
shmctl(fengshui569, IPC_RMID, NULL);
shmctl(fengshui230, IPC_RMID, NULL);
sleep(1);
int fengshui370 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
shmctl(fengshui318, IPC_RMID, NULL);
shmctl(fengshui1249, IPC_RMID, NULL);
sleep(1);
int fengshui1608 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
shmctl(fengshui628, IPC_RMID, NULL);
sleep(1);
int fengshui1319 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
shmctl(fengshui1518, IPC_RMID, NULL);
sleep(1);
int fengshui189 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
shmctl(fengshui573, IPC_RMID, NULL);
shmctl(fengshui1608, IPC_RMID, NULL);
sleep(1);
int fengshui625 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
shmctl(fengshui1319, IPC_RMID, NULL);
shmctl(fengshui189, IPC_RMID, NULL);
sleep(1);
int fengshui1253 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
int fengshui934 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
shmctl(fengshui625, IPC_RMID, NULL);
shmctl(fengshui370, IPC_RMID, NULL);
shmctl(fengshui934, IPC_RMID, NULL);
shmctl(fengshui1253, IPC_RMID, NULL);
sleep(1);
int fengshui61 = shmget(IPC_PRIVATE, 1024, IPC_CREAT);
ioctl(fd, VULN_ALLOC_OVERFLOW);
ioctl(fd, VULN_ALLOC_TARGET);

Fitness: 256
```

Now after some time KEvoHeap will print the solution for the heap layout manipulation. This solution can now be used in `exploit/demo_exploit_with_noise.c` for the function `do_heap_layout_manipulation(int fd)`. Moreover the hard coded adresss of `commit_creds` and `prepare_kernel_cred` needs to be updated as written in the function `escalate_privs(void)`. Normally these addresses should be resolved dynamically but in this case we want to focus on the heap layout manipulation.

## Troubleshooting
### Errors in res/
If you notice many errors in the `res` directory, this could mean that qemu does not reboot fast enough .Try increasing the time the respective runner script sleeps after rebooting qemu.

### Large Numbers in res
If you encounter mostly very large numbers in the files in `res/`, you have to recreate the savestate of the vm by booting it with the `./qemu_startup_qcow2_no_load.sh`, loading the module, starting the server etc. and then creating a snapshot. It might be neccessary to repeat this multiple times until you get a "good" savestate
