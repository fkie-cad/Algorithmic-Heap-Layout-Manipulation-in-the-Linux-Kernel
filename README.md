# Algorithmic Heap Layout Manipulation in the Linux Kernel

This repository contains the code and auxilliary tools for the Paper "Algorithmic Heap Layout Manipulation in the Linux Kernel". For information on how to setup and run KEvoHeap, see [RUNNING_KEVOHEAP.md](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/blob/main/RUNNING_KEVOHEAP.md). More information about the exemplary vulnerable kernel module can be found in [EXAMPLE_VULN.md](https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/blob/main/EXAMPLE_VULN.md). The "ftrace" folder contains instructions and tools for debugging memory allocation using ftrace. The "visualisation" folder contains scripts to visualize candidate solutions in an animated fashion. The "exploit" folder contains an exemplary exploit for the given vulnerable kernel module (found in "vuln").

## Structure

- (https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/algorithms)[algorithms]: This folder contains the algorithms developed in our paper
- (https://github.com/fkie-cad/Algorithmic-Heap-Layout-Manipulation-in-the-Linux-Kernel/tree/main/exploit)[exploits]: This folder contains an exemplary exploit for the given vulnerable kernel module (found in "vuln").
- 

## Dependencies

- >= python3.6

For the visualisation:
- pyglet (pip install pyglet)
- numpy (pip3 install numpy)
- matplotlib (pip3 install matplotlib)
