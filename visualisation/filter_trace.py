#!/usr/bin/env python3
import argparse
import re

def filter_trace(trace, process):
    found_beginning = False
    alloced_addresses = []
    for line in trace:
        if process in line:
            found_beginning = True
        if found_beginning:
            if "kmalloc_node" in line and "bytes_alloc=256" in line:
                ptr = re.search(r"ptr=([a-f0-9]+)", line).group(1)
                alloced_addresses.append(ptr)
                process = line.split()[0]
                call_site = re.search(r"call_site=(\w+)", line).group(1)
                print(f"{process}: kmalloc_node call_site={call_site} ptr={ptr}")
            elif "kmalloc" in line and "bytes_alloc=256" in line:
                ptr = re.search(r"ptr=([a-f0-9]+)", line).group(1)
                alloced_addresses.append(ptr)
                process = line.split()[0]
                call_site = re.search(r"call_site=(\w+)", line).group(1)
                print(f"{process}: kmalloc call_site={call_site} ptr={ptr}")
            elif "kfree" in line:
                ptr = re.search(r"ptr=([a-f0-9]+)", line).group(1)
                process = line.split()[0]
                call_site = re.search(r"call_site=(\w+)", line).group(1)
                if ptr in alloced_addresses:
                    alloced_addresses.remove(ptr)
                    print(f"{process}: kfree call_site={call_site} ptr={ptr}")


def main():
    parser = argparse.ArgumentParser(description="Filter relevant allocations. Remember: If you want actual addresses, you have to change the format string in include/trace/events/kmem.h from 'ptr=%p' to 'ptr=%lx'")
    parser.add_argument("trace", type=str, nargs=1, help="The log file")
    parser.add_argument("-p", metavar="process name", default="demo_exploit", required=False, type=str)
    args = parser.parse_args()
    with open(args.trace[0]) as f:
        trace = f.readlines()
    filter_trace(trace, args.p)

if __name__ == "__main__":
    main()
