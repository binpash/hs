module scheduler 

---------- Filesystem ----------------
    sig File {
        var content: one Int
    }

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
one sig CN extends State {}


sig Command {
    var command_state: one State,

    -- These are the dependencies predicted by the preprocessor.
    var preprocessor_next : set Command,    
    -- These are the real dependencies, that will only be found by the trace executor.
    dependency: set Command,

    // Details the operation_on_filesystems of each command from File to File for each possible state.
    // A read is of the form of an identity transformation for a File (ie content is unchanged)
    // while a write involves changing the content of a file!

    operation_on_filesystem: File->File 
}
----------------------------------------------------------------------------------------------------


// Dependency in terms of Filesystem

        pred independent[a : Command, b : Command] {
                let a_then_b = (operation_on_filesystem[a]).(operation_on_filesystem[b]),
                    b_then_a = (operation_on_filesystem[b]).(operation_on_filesystem[a])
                    | a_then_b = b_then_a
            
        }

        pred has_operation_on_filesystems [c : Command] {
            some f : File | c.operation_on_filesystem[f] != f
        }

        pred dependencies_valid {
            // Encoding dependency in terms of the filesystem.
            all a, b : Command| (a->b in dependency) => (not independent[a,b])
        }

// Well Formedness

    pred partialOrder[r: set (Command -> Command)] {
        no r & iden // Anti-reflexivity
        all x: Command, y: Command, z: Command |
        {
            (x->y in r and y->z in r) implies x->z in r // Transitivity
        }
        no (r & ~r) // anti-symmetric
    }

    pred preprocWellFormed {
        all c1,c2 : Command | {
            
            // Only remove edges which have been there since the beginning [preproc prediciton]
            // and would violate the partial Order
            (c1->c2) in (preprocessor_next - preprocessor_next') iff {
                historically (c1->c2 in preprocessor_next) 
                not partialOrder[preprocessor_next' + (c1->c2)]
            }

            // Adding an edge implies :
            (c1->c2 in preprocessor_next' - preprocessor_next) implies {
                (c1->c2) in ~dependency //should be a real dependency
                some c3 : Command | {
                    run_trace_executor[c3]
                    // should be added by c2 (backward dependency) or due to transitivity
                    (c3=c2) or 
                    {
                        c3 in c1.^preprocessor_next 
                        c2 in c3.^preprocessor_next
                    }
                }
            }

            // if you run the trace executor with some non committed dependencies then you should add some edges
            run_trace_executor[c1] and some (nonCommittedDependencies[c1,dependency]) implies {
                some (preprocessor_next' - preprocessor_next)
            }

        }
        
    }

    pred wellFormed {
        partialOrder[preprocessor_next]
        partialOrder[~dependency]

        //The preprocessor does not have false negs
        preprocWellFormed

        // Filesystem chages only if there is some c that is comitted
        (files != files') implies { some c : Command | commit_frontier[c]    }
    }

------------------------------------------------------------------------------------------------------

// Helpers

    fun firstNE[R: set (Command -> Command)] : set Command {
        {x: Command | 
            {
                x.command_state = NE
                all y: Command | y in x.^(~R) implies {y.command_state != NE}
                
            }
        }
    }

    pred committed[c: Command] {
        (c.command_state) = C or (c.command_state = CN)

        {(c.command_state) = C} implies always (c.command_state = C)
        {(c.command_state) = CN} implies always (c.command_state = CN)
    }

    fun nonCommittedDependencies[c : Command, previous : set (Command -> Command)] : set Command
    {
        {x : Command | (x in c.^previous) and !committed[x] }
    }

---------------------------------------------------------------------------------------------------------
//State transition rules

// NE -> NE
    pred speculate_dep_exists[c : Command] {
        c.command_state = NE
        after (c.command_state = NE)

        (some nonCommittedDependencies[c, (~preprocessor_next)])
    }

    // NE -> S
    pred speculate_no_dep[c : Command] {
        c.command_state = NE
        after (c.command_state = S)

        (no nonCommittedDependencies[c, (~preprocessor_next)])
    }

    // S -> NE
    pred trace_executor_found_dependency[c : Command] {
        c.command_state = S
        after (c.command_state = NE)

        (some nonCommittedDependencies[c, dependency])
    }

    // S -> C
    pred commit_frontier[c : Command] {
        c.command_state = S
         after (c.command_state = C )

        (no nonCommittedDependencies[c, dependency])

        // Apply the command's operation_on_filesystems to the system.
        // This operation of the filesystem could be a read or a write.
        // By virtue of the type signatures of File and operation_on_filesystem,
        // Alloy models 
        files' = c.operation_on_filesystem[files]
    }

    // S -> NE
    pred speculated_not_executed[c : Command] {
        c.command_state = S
         after (c.command_state = CN )
        (no nonCommittedDependencies[c, dependency])
    }

------------------------------------------------------------------------------------------------
// Actions
    pred awaiting_predecessors [c : Command] {
        c.command_state = NE
        after (c.command_state = NE)
        c not in firstNE[preprocessor_next]
    }

    pred speculatively_execute[c : Command] {
        c in firstNE[preprocessor_next]
        speculate_dep_exists[c] or speculate_no_dep[c]
    }

    pred run_trace_executor[c : Command] {
        trace_executor_found_dependency[c] or commit_frontier[c] or speculated_not_executed[c]
    }

    pred validAction[c : Command] {
       awaiting_predecessors[c] or speculatively_execute[c] or run_trace_executor[c] or committed[c]
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
        all c : Command | c.command_state = NE

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
