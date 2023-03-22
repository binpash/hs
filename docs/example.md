### Partial Program Order Structures

* **Committed:** contains cmds that we are done with them completely

* **Workset:** contains cmds that are executing in the current cycle. These cmds
can either be Executing or Waiting to be resolved.

* **Frontier:** contains the next cmd(s) execute according to the partial program order. Frontier cmd(s) will run and get traced without sandboxing.

* **Speculated:** contains the cmds that were successfully speculated in a previous cycle. This means that the command was ran in the sandbox, and no dependencies involving in were discovered.

* **Executing:** contains cmds that are currently being executed and traced. It is a subset of the workset.

* **Waiting:** contains cmds that have finished executing but can’t yet be checked for dependencies.

* **To_resolve:** a dict that for each node contains the set of nodes to check for deps
—

### Example script:
```
(0) cat in1 > out1
(1) cat out1 > out2
(2) cat out2 > out3
(3) cat in2 > out4
```



### 0. Preprocessed script
```
Partial Order Edges:  ['0 -> 1', '1 -> 2', '2 -> 3']
----------------------------------------------------
WORKSET:        [0, 1, 2, 3]
COMMITTED:      []
FRONTIER:       [0]
SPECULATED:     []
EXECUTING:      []
WAITING:        []
TO RESOLVE:     {0: [], 1: [0], 2: [0, 1], 3: [0, 1, 2]}
> RW Sets
DEBUG:ID:0 | R:None | W:None
DEBUG:ID:1 | R:None | W:None
DEBUG:ID:2 | R:None | W:None
DEBUG:ID:3 | R:None | W:None
```

### 1. We execute everything in the workset in parallel.

```
EXECUTING becomes: [0, 1, 2, 3, 4]
```

### 2. Whenever a node is done executing, we try to see if it can be checked for dependencies.

For this we use the `EXECUTING`, `WAITING` and `TO RESOLVE` structures.

```
DEBUG:WORKSET:        [0, 1, 2, 3]
DEBUG:COMMITTED:      []
DEBUG:FRONTIER:       [0]
DEBUG:SPECULATED:     []
DEBUG:EXECUTING:      [1, 2, 3] *
DEBUG:WAITING:        []
DEBUG:TO RESOLVE:     {0: [], 1: [0], 2: [0, 1], 3: [0, 1, 2]}
> RW Sets
DEBUG:ID:0 | R:[in1] | W:[out1] *
DEBUG:ID:1 | R:None | W:None
DEBUG:ID:2 | R:None | W:None
DEBUG:ID:3 | R:None | W:None
```

We want the executing set to not have any of the nodes found in to_resolve[cmd], if there are such cases, we place cmd in waiting set.
We do this check for the **cmd currently done executing** and **all other WAITING cmds**.

For each of the examined nodes the above condition is satisfied,
we can add the node in 



Initially, the structures are as follows


COMMITTED:    []
FRONTIER:        [0]
SPECULATED:   []
EXECUTING:      []
WAITING:           []
TO RESOLVE:    {}
