# Current Architecture
- Client written in pure C, which reads file(s) with instructions, executes them SEQUENCIALLY (can't be parallel because of side effects) and writes results for each in another file 
- Algorithm produces a file with instructions after reading population and fitness (mostly irrelevant for random search) from files
- Algo and Client are called in a loop from a shell script. We probably can not call the client directly from the algorithm unless we code it in pure c to avoid any sideeffects to the kernel heap by the python vm, the go scheduler etc...

# Possible optimizations
- In addition to the allocations array we could create a "free-list" which keeps track of free indexes in the array. Currently we just search them with linear runtime. Depends how the runtime of the algorithm turns out. -> Not relevant anymore, client has to give ID and take care that he doesnt reuse them
