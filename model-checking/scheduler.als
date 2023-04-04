module scheduler 

---------- Filesystem ----------------
    sig File {}

    one sig Filesystem {
        files: seq File,
    }
    {
        File in files.elems
    }
---------------------------------------

abstract sig State {}
one sig NE extends State {}
one sig S extends State {}
one sig C extends State {}
one sig W extends State {}
one sig E extends State{}

// Just check that commit order respects actual partial Order


sig Command {
   
     var command_state: one State,
   
    -- This is the syntactic order predicted by the preprocessor. 
    syntactic_order : set Command,    


    // Details the operation_on_filesystems of each command from File to File for each possible state.
    // A read is of the form of an identity transformation for a File (ie content is unchanged)
    // while a write involves changing the content of a file!

    // Files Command reads from 
    var read_set : set File ,

    // Files Command writes from 
    var write_set : set File  ,

    var commit_order : lone Command ,

}
----------------------------------------------------------------------------------------------------
// Well Formedness

    pred partialOrder[r: set (Command -> Command)] {
        no r & iden // Anti-reflexivity
        all x: Command, y: Command, z: Command |
        {
            (x->y in r and y->z in r) implies x->z in r // Transitivity
        }
        no (r & ~r) // anti-symmetric
    }

    pred wellFormed {
        partialOrder[syntactic_order]

        (commit_order  in commit_order')

        no (commit_order & iden)
        some (command_state.C) implies {
            one c  : Command | c.*^commit_order = command_state.C 
        }
      
    }

------------------------------------------------------------------------------------------------------

// Helpers

    fun command_pred[c : Command] : set Command{
        {x : Command | 
            c in x.^syntactic_order
        }
    }
    fun Frontier_set [ordr : Command -> Command] : set Command {

        {x : Command | 
            {
                all y : Command | x in y.^ordr implies {committed[y]}
            }
        }
    }



    pred hasDependency [c1 : Command , c2 : Command ] { 
        // Forward Dependency C1 writes , C2 reads
        some (c1.write_set & c2.read_set) or 
        // Backward Dependency C1 reads,  C2 writes
        some (c1.read_set & c2.write_set) or 
        // Write dependency C1 writes, C2 writes
        some (c1.write_set & c2.write_set)
    }

    pred maintainRW[c : Command] {
        c.read_set' = c.read_set 
        c.write_set' = c.write_set
    }

    fun nonCommittedDependencies[c : Command] : set Command
    {
        {x : Command | (c in x.^syntactic_order) and !committed[x] and hasDependency[x,c] }
    }

---------------------------------------------------------------------------------------------------------
//State transition rules


    // NE -> NE 
    pred stayNE[c : Command] { 
        c.command_state = NE
        after (c.command_state = NE)
        
        c not in Frontier_set[syntactic_order]
        eventually (c.command_state != NE) //TODO : prob should remove
    }

    // NE -> E 
    pred execute_command[c : Command] {
        c.command_state = NE
        after (c.command_state = E)
    }

    // E -> E
    pred stayE [c : Command] { 
        c.command_state = E 
        after(c.command_state = E)
        eventually(c.command_state != E)
    }
    // E -> W
    pred command_exec_finished [c : Command] { 
        c.command_state = E
        after(c.command_state = W)
       
    }
    // W -> W 
    pred command_waiting [c : Command] {
        c.command_state = W
        after(c.command_state = W)
        
        some c2 : Command | {
            c in c2.^syntactic_order
            (c2.command_state = NE or c2.command_state = E)
        }

    }
    // W -> NE 
    pred trace_executor_found_dependency[c : Command] {
        c.command_state = W
        after (c.command_state = NE)
        all c2 : Command | {
            c in c2.^syntactic_order
            (c2.command_state != NE or c2.command_state != E)
        }
        some nonCommittedDependencies[c]
    }
    // W -> S
    pred mark_speculated[c : Command] {
        c.command_state = W
        after (c.command_state = S)
        
        no nonCommittedDependencies[c]

    }

    // S -> C
    pred commit_node[c : Command] {
        c.command_state = S
        after (c.command_state = C )

        c in Frontier_set[syntactic_order]
       
    }

    // S -> S
    pred staySpec[c : Command] {
        c.command_state = S
        after (c.command_state = S )

        c not in Frontier_set[syntactic_order]

    }
    // S -> NE
    pred speculated_dep_found[c : Command] {
        c.command_state = S
        after (c.command_state = NE )
        some c2 : Command | {
            c2.command_state = W 
            c in c2.^syntactic_order
            hasDependency[c2,c]
        }
    }
    pred NEaction[c : Command]  {
        stayNE[c] or execute_command[c]
    }
    pred Eaction [c : Command] { 
        stayE[c] or command_exec_finished[c]
    }
    pred Waction [c : Command] {
        command_waiting[c] 
        or trace_executor_found_dependency[c] 
        or mark_speculated[c]
    } 
    pred Saction [c : Command] {
        commit_node[c] 
        or speculated_dep_found[c] 
        or staySpec[c]
    }

    pred committed[c: Command] {
        (c.command_state) = C 
        {(c.command_state) = C} implies always (c.command_state = C)  
    }

    pred validAction[c : Command] {
       NEaction[c]   or Eaction[c] or Waction[c]  or Saction[c]   or committed[c]
       not maintainRW[c] implies Eaction[c]
       some c.commit_order implies committed[c]
    }
------------------------------------------------------------------------------------------------

// Scheduler Behavior
    pred traces {
        always wellFormed
        all c : Command | {
             always validAction[c]
        }
    }

    // Initial state
    pred init {
        all c : Command | {
            c.command_state = NE
            no c.read_set 
            no c.write_set
            no c.commit_order
        }
    }

    // Scheduler behavior
    pred scheduler_e2e {
        init
        traces
    }

    // All commands have been committed at the end
    pred final {
        all c : Command | committed[c]
    }
