# KProbe

This our old approach to observes all allocations in the target cache and creations of new slabs. This is just for reference. 

To build it:

```bash
$ make
$ cd ..
$ ./scp_to_qemu.sh kprobe/infoleakprobe.ko
```

Next we connect to the running QEMU-VM via SSH and than load it:
```bash
$ ./ssh.sh
root@syzkaller:~# insmod infoleakprobe.ko
```
