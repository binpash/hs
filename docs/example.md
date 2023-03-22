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
Let's analyze the following example script
```
(0) cat in1 > out1
(1) cat out1 > out2
(2) cat out2 > out3
(3) cat in2 > out4
```

### 0. Preprocessed script
After the preprocessing of the script, we are in the state below:
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
ID:0 | R:None | W:None
ID:1 | R:None | W:None
ID:2 | R:None | W:None
ID:3 | R:None | W:None
```

### 1. We execute everything in the workset in parallel.

```
EXECUTING becomes: [0, 1, 2, 3, 4]
```

### 2. Whenever a node is done executing, we try to see if it can be checked for dependencies.

For this we use the `EXECUTING`, `WAITING` and `TO RESOLVE` structures.



We want the executing set to not have any of the nodes found in to_resolve[cmd], if there are such cases, we place cmd in waiting set.
We do this check for the **cmd currently done executing** and **all other WAITING cmds**.

For each of the examined nodes the above condition is satisfied,
we can add the node in the set of nodes to resolve.


Let's say `node 0` is done executing first. `to_resolve[0]` has no nodes inside, so it is good to be checked for dependencies. Structures would change as follows:
```
WORKSET:        [0, 1, 2, 3]
COMMITTED:      []
FRONTIER:       [0]
SPECULATED:     []
EXECUTING:      [1, 2, 3] *
WAITING:        []
TO RESOLVE:     {0: [], 1: [0], 2: [0, 1], 3: [0, 1, 2]}
> RW Sets
ID:0 | R:[in1] | W:[out1] *
ID:1 | R:None  | W:None
ID:2 | R:None  | W:None
ID:3 | R:None  | W:None
```
We can now start resolving dependencies for nodes: `[0]`

Let's say `node 1` is done executing first instead. `to_resolve[1]` has `node 0` inside, that is currently still executing, so it gets placed in the waiting set. Structures would change as follows:
```
WORKSET:        [0, 1, 2, 3]
COMMITTED:      []
FRONTIER:       [0]
SPECULATED:     []
EXECUTING:      [0, 2, 3] *
WAITING:        [1] *
TO RESOLVE:     {0: [], 1: [0], 2: [0, 1], 3: [0, 1, 2]}
> RW Sets
ID:0 | R:None  | W:None
ID:1 | R:[in1] | W:[out1] *
ID:2 | R:None  | W:None
ID:3 | R:None  | W:None
```

If `node 2` is node executing afterwards, we check `to_resolve[2]` and spot that `node 0` is inside and currently executing, therefore we cannot check it. We put it to the waiting set. In this iteration we recheck `node 1`, which still cannot be resolved and therefore remains waiting. Structures change as follows:
```
WORKSET:        [0, 1, 2, 3]
COMMITTED:      []
FRONTIER:       [0]
SPECULATED:     []
EXECUTING:      [0, 3] *
WAITING:        [1, 2] *
TO RESOLVE:     {0: [], 1: [0], 2: [0, 1], 3: [0, 1, 2]}
> RW Sets
ID:0 | R:None    | W:None
ID:1 | R:[out1]  | W:[out2]
ID:2 | R:[out2]  | W:[out3] *
ID:3 | R:None    | W:None
```

`node 3` finishes next, it enters waiting state because of 0 currently executing. We recheck `node 1` and `node 2`, without success. Structures change as follows:

```
WORKSET:        [0, 1, 2, 3]
COMMITTED:      []
FRONTIER:       [0]
SPECULATED:     []
EXECUTING:      [0] *
WAITING:        [1, 2, 3] *
TO RESOLVE:     {0: [], 1: [0], 2: [0, 1], 3: [0, 1, 2]}
> RW Sets
ID:0 | R:None   | W:None
ID:1 | R:[out1] | W:[out2]
ID:2 | R:[out2] | W:[out3]
ID:2 | R:[in2]  | W:[out4] *
```

`node 0` finishes next, it can be ckecked for dependencies. Other waiting nodes are getting rechecked. They can also be checked for dependencies as `node 0` in not executing anymore.
```
WORKSET:        [0, 1, 2, 3]
COMMITTED:      []
FRONTIER:       [0]
SPECULATED:     []
EXECUTING:      [] *
WAITING:        [] *
TO RESOLVE:     {0: [], 1: [0], 2: [0, 1], 3: [0, 1, 2]}
> RW Sets
ID:0 | R:[in1]  | W:[out1] *
ID:1 | R:[out1] | W:[out2]
ID:2 | R:[out2] | W:[out3]
ID:2 | R:[in2]  | W:[out4]
```
We can now start resolving dependencies for nodes: `[0, 1, 2, 3]`

### 3. We resolve the dependencies of the nodes that we were able to check this round.

