# Algorithmic Heap Layout Manipulation in the Linux Kernel

This repository contains the code and auxilliary tools for the Paper "Algorithmic Heap Layout Manipulation in the Linux Kernel". For information on how to setup and run KEvoHeap, see [RUNNING_KEVOHEAP.md](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/blob/main/RUNNING_KEVOHEAP.md). More information about the exemplary vulnerable kernel module can be found in [EXAMPLE_VULN.md](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/blob/main/EXAMPLE_VULN.md). The "ftrace" folder contains instructions and tools for debugging memory allocation using ftrace. The "visualisation" folder contains scripts to visualize candidate solutions in an animated fashion. The "exploit" folder contains an exemplary exploit for the given vulnerable kernel module (found in "vuln").

## Getting started

Just follow the instruction at [RUNNING_KEVOHEAP.md](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/blob/main/RUNNING_KEVOHEAP.md).

## Structure

- [algorithms](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/algorithms): This folder contains the algorithms developed in our paper
- [exploits](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/exploit): This folder contains an exemplary exploit for the given vulnerable kernel module (found in [vuln](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/vuln)).
- [ftrace](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/ftrace): This folder contains a script to enable the logging allocations via ftrace.
- [kernel sieve](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/kernel_sieve): This folder contains kernel sieve our framework for evaluating heap layout manipulation algorithms that target the SLAB/SLUB allocator in the Linux kernel.
- [krobe](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/kprobe): This folder conatins a kretprobe which observes all allocations in the target cache and creations of new slabs. This was our first approach in order to observe this kind of allocations. Later we switched to eBPF to the same.
- [netcat from Debian Buster](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/netcat_from_buster): This folder contains the netcat version from Debian Buster used in our framework.
- [visualisation](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/visualisation): This folder contains scripts for visualisation. This might be either an animation of the algorithmic solutions or the plotting of the results as bar charts/box plots.
- [vuln](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/vuln): This folder contains an exemplary vulnerable kernel module.

## Dependencies

- >= python3.6
- deap (`pip3 install deap`)

For the visualisation:
- pyglet (`pip3 install pyglet`)
- numpy (`pip3 install numpy`)
- matplotlib (`pip3 install matplotlib`)
