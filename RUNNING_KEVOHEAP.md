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
$ gcc kernel_sieve.c -static -o kernel_sieve
$ cd ../kernel_module
$ make
```
3. Start qemu using `qemu_startup_qcow2_no_load.sh`
4. Copy the client and the kernel module to qemu
```bash
$ ./scp_to_qemu.sh kernel_sieve/client/kernel_sieve
$ ./scp_to_qemu.sh kernel_sieve/kernel_module/slab_api.ko
$ ./scp_to_qemu.sh ./netcat_from_buster
$ ./scp_to_qemu.sh ./ncserver.sh
```
5. Login to qemu, load the kernel module and start the server
```bash
$ ./ssh.sh #(Or login with user "root")
$ insmod slab_api.ko
$ chmod +x ncserver.sh
$ ./ncserver.sh &
```

6. create folders `ins`, `res` and `raw` both in the VM as well as on the host

7. Create the savestate that we will use for Fast-Reset. To do this, access qemu monitor. One way to do this is to connect to it via netcat on port 55555
```bash
#On the host
$ nc localhost 55555
$ savevm savestate
```
8. To now run EvoHeap with fast reset, quit qemu and run `fast_reset_evo_statistics.sh` (The script starts a new qemu instance, thats why we quit qemu first). To modify the number of noise allocations, edit the `fast_reset_evo_statistics.sh` script and change the `-n` parameter in the line `python3 algorithms/evoheap.py -a ksieve -n 3`.


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
$ ./scp_to_qemu.sh ./ncserver.sh
$ ./scp_to_qemu.sh ./kmem.bt
```
6. create folders `ins`, `res` and `raw` both in the VM as well as on the host
7. Shut qemu down and restart it
8. Load the modules, start the server and bpftrace
```bash
$ insmod slab_api.ko
$ insmod vuln.ko
$ chmod +x ncserver.sh
$ ./ncserver.sh &
$ chmod +x kmem.bt
$ ./kmem.bt > /tmp/dist
```
9. Create the savestate that we will use for Fast-Reset. To do this, access qemu monitor. One way to do this is to connect to it via netcat on port 55555
```bash
#On the host
$ nc localhost 55555
$ savevm savestate
```
10. Run evoheap via `./bpf_evo_runner.sh` after modifying `./algorithms/evoheap.py` accordingly to your needs. If you want to modify the number of noise allocations performed, you need to modify the `vuln` kernel module and rebuild it

## Troubleshooting
### Errors in res/
If you notice many errors in the `res` directory, this could mean that qemu does not reboot fast enough .Try increasing the time the respective runner script sleeps after rebooting qemu.

### Large Numbers in res
If you encounter mostly very large numbers in the files in `res/`, you have to recreate the savestate of the vm by booting it with the `./qemu_startup_qcow2_no_load.sh`, loading the module, starting the server etc. and then creating a snapshot. It might be neccessary to repeat this multiple times until you get a "good" savestate
