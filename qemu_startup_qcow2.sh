qemu-system-x86_64 \
  -kernel ./kernel_src/arch/x86_64/boot/bzImage \
  -append "console=ttyS0 root=/dev/sda earlyprintk=serial nokaslr"\
  -hda ./bullseye.qcow2 \
  -net user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10021-:22,hostfwd=tcp:127.0.0.1:44444-:44444 \
  -net nic,model=e1000 \
  -enable-kvm \
  -nographic \
  -m 8G \
  -s \
  -smp 4 \
  -pidfile vm.pid \
  -monitor telnet:127.0.0.1:55555,server,nowait \
  -loadvm savestate \
  2>&1 | tee vm.log
