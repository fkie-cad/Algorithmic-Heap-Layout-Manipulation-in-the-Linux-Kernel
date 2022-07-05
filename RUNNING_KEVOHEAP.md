# Running KEvoHeap
Setting up an environment to effectively run KEvoHeap+QEMU is a little bit convoluted, so here are some instructions

## Run KEvoHeap+QEMU+KernelSieve (Fast-Reset Method)
A large part of setting up QEMU has been automated, but some manual steps still have to be performed.

1. Run the `setup.sh` script. This script will perform the following steps:
    - Install dependencies (should work on Debian-based distros as well as Arch-based distros)
    - Download kernel source code (currently v5.14.11) into a folder called "kernel_src"
    - configure and build the kernel
    - create a debian image for qemu, using "create-image.sh" script, which is a slightly modified version of the script syzkaller uses to create images
    - convert the image to qcow2 (needed for savevm)
2. Build the KernelSieve client and kernel module
```bash
$ cd kernel_sieve/client/
$ gcc kernel_sieve.c -o kernel_sieve
$ cd ../kernel_module
$ make
```
3. Start qemu using `qemu_startup_qcow2_no_load.sh`
4. Copy the client and the kernel module to qemu
```bash
$ ./scp_to_qemu.sh kernel_sieve/client/kernel_sieve
$ ./scp_to_qemu.sh kernel_sieve/kernel_module/slab_api.ko
```
5. Login to qemu and load the kernel module
```bash
$ ./ssh.sh
$ insmod slab_api.ko
```
6. Still inside qemu, create folders `ins`, `res` and `raw`

7. Create the savestate that we will use for Fast-Reset. To do this, access qemu monitor. One way to do this is to connect to it via netcat on port 55555
```bash
#On the host
$ nc localhost 55555
$ savevm savestate
```
8. To now run EvoHeap with fast reset, quit qemu and run `fast_reset_evo_statistics.sh` (The scriptstarts a new qemu instance, thats why we quit qemu first)


## Run KEvoHeap+QEMU+BPFTrace
This section describes how to setup everything to use KEvoHeap on the `vuln` kernel module, an examplary vulnerable kernel module, with the help of bpftrace. More information about the `vuln` module can be found in `EXAMPLE_VULN.md`.

1. Run the `setup.sh` script.
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
$ ./scp_to_qemu.sh ./kmem.bt
```
6. inside qemu (Login with user 'root'), create folders `ins`, `res` and `raw`
7. Shut qemu down and restart it
8. Load the modules, start the server and bpftrace
```bash
$ insmod slab_api.ko
$ insmod vuln.ko
$ ./ncserver.sh &
$ ./kmem.bt > /tmp/dist
```
9. Create the savestate that we will use for Fast-Reset. To do this, access qemu monitor. One way to do this is to connect to it via netcat on port 55555
```bash
#On the host
$ nc localhost 55555
$ savevm savestate
```
10. Run evoheap via `./bpf_evo_runner.sh` after modifying `./algorithms/evoheap.py` accordingly to your needs
