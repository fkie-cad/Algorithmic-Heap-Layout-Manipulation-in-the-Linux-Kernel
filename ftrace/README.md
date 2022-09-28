# Logging allocations via ftrace
To identify issues with solutions or the algorithm, it can be very helpful to have a look at all allocations performed by the kernel in the targetted cache. By this you can notice if candidates actually perform the expected allocations. On way to do this is via ftrace. For detailed explanations refer to [the official Documentation](https://www.kernel.org/doc/html/latest/trace/ftrace.html) or [this talk](https://events.linuxfoundation.org/mentorship-session-tracefs-the-building-blocks-of-linux-kernel-tracing-by-ftrace/), here i will only show how to use it for our usecase.
## Preperations
Whenever the kernel outputs kernel addresses they are hashed per default. We have to change this to get meaningful output. To do this, got to `include/trace/events/kmem.h` and in the format strings change `ptr=%p` to `ptr=%lx`. Then go ahead and rebuild the kernel.
## Tracing
To start tracing, use the `enable_tracing.sh` script. This will enable tracing for the events `kmalloc`, `kmalloc_node` and `kfree`. After you ran the candidate or whatever you want to analyse, use `get_trace.sh` to retrieve the trace.
## Tracing all candidates during a KEvoHeap
`trace_real_fast_reset_evo_statistics.sh` is an alternative runner script that is identical to `real_fast_reset_evo_statistics.sh` but retrieves traces of each candidate and stores them under `./trace`. Just remember to enable tracing before creating the inital save.
## Filering traces
`./visualisation/filter_trace.py` is a small utility script that cleans up logfiles a bit. Use the `-p` flag to pass it the processes name with the pid. To get this, take a look at the log first. For example, if the candidate is named "137", the process name will be something like "137-252", where 252 is an example pid. The script will then filter all allocations performed previous to the execution of the candidate and remove some informational overhead.
