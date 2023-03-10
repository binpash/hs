## Dynamic Parallelizer

A dynamic parallelizer that optimistically/speculatively executes everything in a script in parallel and ensures that it executes correctly by tracing it and reexecuting the parts that were erroneous.

## Installing

```sh
./scripts/install_deps_ubuntu20.sh
```

## Tests

To run the tests:
```sh
cd test
./test_orch.sh
```

### TODO Items

#### Complete control flow and complex script support

Extend the architecture to support complete scripts and not just partial order graphs of commands.

A potential solution is shown below:

![Architecture Diagram](/docs/handdrawn_architecture.jpeg)

This solution includes a preprocessor that creates two executable artifacts: 
- the preprocessed/instrumented script (similar to what the PaSh-JIT preprocessor produces)
- the partial program order graph (a graph of commands that will be speculated and executed with tracing from the orchestrator)

The graph might contain unexpanded commands, so the orchestrator should support unexpanded strings.
On these commands, the orchestrator can speculate for the value of these strings and then when they become the frontier (the preprocessed script has reached them), we actually know their values and could confirm/abort the speculation.

The two executors communicate with each other and progress through the script execution in tandem. The JIT executor (left) also needs to trace execution to inform the orchestrator about changes in the environment.

#### Orchestator: Partial Program Order Graph

The orchestrator needs to support arbitrary partial program order graphs (instead of just sequences of instructions), to figure out the precise real program order dependencies.

An instance of a graph is shown below:

![Example Partial Program Order Graph](/docs/handdrawn_partial_program_order.jpeg)

One important characteristic of the graph (and the speculative execution algorithm) is that there is a committed prefix-closed part that has already executed and cannot be affected.
The rest of the graph is uncommited and therefore might or might not have completed execution. The uncommited frontier, the part of the graph adjacent to the prefix is guaranteed to execute and complete without speculation (since we have both the environment and the variables resolved) and this is part of the argument for the termination of the algorithm. Every step that the orchestration takes, it can always commit the uncommited frontier, and therefore the commited prefix grows until it reaches the whole graph.

#### Orchestrator: Backward dependencies and Execution Isolation/Aborting/Reverting

How do we resolve backward dependencies? For example: 
```sh
grep foo in1 > out1
grep bar in0 > in1 ## Its write might affect the first command exec.
```

One solution would be to run the non-frontier (non-root) commands in an isolated environment and only at the end of their execution commit their results. This might have significant overhead, except if we can just write to temporary files and then move them? Or let them work in a temporary directory? 

Another way would be to dynamically track writes of non-frontier commands and stop them when they try to write to something that might be a read dependency of the first, but there are timing issues here that I don't see how to resolve.

#### Commands that change current directory

Can we actually trace that and not run these commands? Is that simply a change of an environment variable? They will run in a forked version anyway, but we want to see their results.
