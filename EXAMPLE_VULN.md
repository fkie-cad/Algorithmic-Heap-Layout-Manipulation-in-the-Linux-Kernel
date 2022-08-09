# Example Vulnerability
The folder `vuln` contains an examplary kernel module that contains a heap buffer overflow vulnerability. Its behaviour is quite simple: It can be queried to allocate a buffer and to write/print data to/from said buffer. Before and after the buffer gets allocated noise allocations will be made to make exploitation non-trivial. In addition, to aid exploitation, it can also be used to simulate the allocation of a target object that contains a function pointer. The invocation of said function pointer can be triggered. To use the module, follow the steps described in `RUNNING_KEVOHEAP.md` to setup a suitable virtual machine with QEMU and load the module with `insmod`. Example exploits can be found under `./exploit`. 

The demo exploit `./exploit/demo_exploit_with_noise.c` performs heap layout manipulation to shape the heap into an exploitable state. It uses the `shmget/shmctl` system calls to allocate objects in the kmalloc-256 cache. These calls trigger (de)allocations of `struct shmid_kernel` objects, which are of appropriate size. A suiting series of allocations and deallocations can be found with KEvoHeap. To do this, follow the steps under "Run KEvoHeap+QEMU+BPFTrace" in `./RUNNING_KEVOHEAP.md`. KEvoHeap will generate candidates consisting of calls to the kernel module and `shmget/shmctl`, which will then be inserted into a general corpus programm which takes care of setup and teardown (`./hlm.template`). The generated candidates are then build and executed in the QEMU VM. The distance of the target objects gets extracted via `bpftrace` and fed back to KEvoHeap. When a correct sequence has been found, it can be used in an exploit to perform the neccessary allocations to place both target objects next to each other. For testing, you can use one of the demo exploits and replace the existing allocation directives with the sequence found by KEvoHeap.