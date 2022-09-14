#!/bin/bash
# This script sets up a full environment for qemu
# This means it installs qemu, downloads the latest linux kernel from git, adjusts the configuration for debugging and builds it
# It also creates a image using the "create_image" script from the syzkaller repository, which has been adjusted for our setting

ENABLE_eBPF_SUPPORT=false
BUILDING_HEADERS=false

if [[ $# -gt 0 ]]; then
	printf "\n"
	while [[ $# -gt 0 ]]; do
		key="$1"
		case $key in
			-e|--ebpf)
				ENABLE_eBPF_SUPPORT=true
				shift
				;;
                        -bkh|--build-kernel-headers)
                                BUILDING_HEADERS=true
                                shift
                                ;;

			*)
				shift
				printf "unknown option! Skipping this\n"
				;;
		esac
	done
fi

# get the version of the running debian version if its no debian based system it will be null
DEBIAN_VERSION=$($(which lsb_release) 2>/dev/null -r | awk '{print $NF}')
# if $DEBIAN_VERSION is null set it to 10.04
DEBIAN_FINAL_VERSION=${DEBIAN_VERSION:="10.04"}

version_greater_equal()
{
    printf '%s\n%s\n' "$2" "$1" | sort --check=quiet --version-sort
}
BINUTILS_VERSION=$(as --version | head -n 1 | awk '{print $NF}')

echo "Installing dependencies"
if command -v apt-get &> /dev/null
then
    sudo apt-get -y  update && sudo apt-get upgrade -y && sudo apt-get -y install git fakeroot build-essential ncurses-dev xz-utils libssl-dev bc flex libelf-dev bison qemu-system-x86 debootstrap dwarves netcat
elif command -v pacman &> /dev/null
then
    sudo pacman -Sy --needed git fakeroot base-devel ncurses xz bc flex libelf bison qemu-headless debootstrap pahole gnu-netcat
else
    echo "Neither apt or pacman was found, exitting"
    exit
fi
pip3 install deap


KERNEL="./kernel_src"
echo "Downloading kernel source..."
mkdir -p $KERNEL
#git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git $KERNEL
#wget -c https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.9.7.tar.xz -O - | tar -xJ --strip-components 1 -C $KERNEL
wget -c https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.14.11.tar.xz -O - | tar -xJ --strip-components 1 -C $KERNEL
#wget -c https://cdn.kernel.org/pub/linux/kernel/v4.x/linux-4.9.tar.xz -O - | tar -xJ --strip-components 1 -C $KERNEL
echo "Creating configuration"
cd $KERNEL
make defconfig
#make kvmconfig
make kvm_guest.config
./scripts/config --enable CONFIG_DEBUG_INFO
./scripts/config --enable CONFIG_CONFIGFS_FS
./scripts/config --enable CONFIG_SECURITYFS
./scripts/config --enable CONFIG_KCOV
#./scripts/config --enable CONFIG_KASAN
#./scripts/config --enable CONFIG_KASAN_INLINE
./scripts/config --enable CONFIG_GDB_SCRIPTS
./scripts/config --disable CONFIG_RANDOMIZE_BASE

if [[ $ENABLE_eBPF_SUPPORT == true ]]; then
	./scripts/config --enable CONFIG_BPF
	./scripts/config --enable CONFIG_BPF_EVENTS
	./scripts/config --enable CONFIG_BPF_JIT
	./scripts/config --enable CONFIG_BPF_SYSCALL
	./scripts/config --enable CONFIG_FTRACE_SYSCALLS
	./scripts/config --enable CONFIG_HAVE_EBPF_JIT
	./scripts/config --enable CONFIG_FUNCTION_TRACER
	./scripts/config --enable CONFIG_HAVE_DYNAMIC_FTRACE
	./scripts/config --enable CONFIG_DYNAMIC_FTRACE
	./scripts/config --enable CONFIG_HAVE_KPROBES
	./scripts/config --enable CONFIG_KPROBES
	./scripts/config --enable CONFIG_KPROBE_EVENTS
	./scripts/config --enable CONFIG_ARCH_SUPPORTS_UPROBES
	./scripts/config --enable CONFIG_UPROBES
	./scripts/config --enable CONFIG_UPROBE_EVENTS
	./scripts/config --enable CONFIG_DEBUG_FS
        ./scripts/config --enable CONFIG_DEBUG_INFO_BTF
        ./scripts/config --enable CONFIG_IKHEADERS
        ./scripts/config --enable CONFIG_BPF_KPROBE_OVERRIDE
        ./scripts/config --enable CONFIG_DEBUG_INFO_BTF_MODULES
        ./scripts/config --enable CONFIG_PAHOLE_HAS_SPLIT_BTF
fi
make olddefconfig
if version_greater_equal ${BINUTILS_VERSION} 2.36; then
    wget -c https://github.com/torvalds/linux/commit/1d489151e9f9d1647110277ff77282fe4d96d09b.patch
    patch -p1 < 1d489151e9f9d1647110277ff77282fe4d96d09b.patch
fi
echo "Starting kernel build (this might take a while...)"
make -j$(nproc)
if [[ ${BUILDING_HEADERS} == true ]]; then
	echo "Creating kernel headers"
	if version_greater_equal $DEBIAN_FINAL_VERSION 20.04; then
                make -j $(nproc) bindeb-pkg
	else
                fakeroot make-kpkg --initrd -j`nproc` kernel_headers
	fi
fi

cd ..
echo "Creating image"
./create-image.sh -d bullseye
sudo rm -rf ./chroot
qemu-img convert -f raw -O qcow2 bullseye.img bullseye.qcow2

