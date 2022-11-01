## Dynamic Parallelizer

A dynamic parallelizer that optimistically/speculatively executes everything in a script in parallel and ensures that it executes correctly by tracing it and reexecuting the parts that were erroneous.


### TODO Items

#### Backward dependencies

How do we resolve backward dependencies? For example: 
```sh
grep foo in1 > out1
grep bar in0 > in1 ## Its write might affect the first command exec.
```

One solution would be to run the non-frontier (non-root) commands in an isolated environment and only at the end of their execution commit their results. This might have significant overhead, except if we can just write to temporary files and then move them? Or let them work in a temporary directory? 

Another way would be to dynamically track writes of non-frontier commands and stop them when they try to write to something that might be a read dependency of the first, but there are timing issues here that I don't see how to resolve.

#### Commands that change current directory

Can we actually trace that and not run these commands? Is that simply a change of an environment variable? They will run in a forked version anyway, but we want to see their results.

#### Extending to arbitrary control flow

Is it safe to use the above technique when we have control flow? If then else/loops? Do we have to stop before these constructs or is there an optimization that would allow us to even optimistically run commands in multiple branches etc.

#### Tracking non-command dependencies

When we receive an original script, we will create a dependency graph of all commands and trace/speculate with them. This requires that we are somehow able to inteleave real script execution with our commands (maybe use PaSh-JIT) to actually get a full script to run.
