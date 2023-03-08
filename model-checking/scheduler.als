
// Assumption: Real dependencies ALSO form a partial order (no dependecy cycles)
// Assumption: the predicted dependecies are a subset of real dependecies (enforced in wellFormed. This may very likely be too strong)

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
    dependency: set Command
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
    pred preprocWellFormed{
        //This enforces the wellformedness of the preproc relation.
        // We don't want preproc to arbitarily change it should only change if and only if 
        // the trace executor finds a dependency. However a dependency may be discovered by another 
        // command as well. Say for example C1 is not in the trace executor state but C2 is and discovers 
        // a dependency on C1
        
        //  For all commands . The preproc relation affects the command C if and only if 
        // either the trace executor finds a dependency for that command or some other 
        // command finds a dependency on C. Any such new dependency must be a true dependency.

        // NOTE: We want this here and not in trace_executor_found_dependency because otherwise
        // trace_executor would be recursive.


        // Remove edges from preprocessor_next if and only if it violates the partial order
        // some command in the transitive closure must be being traced

        all c1,c2 : Command {
            (c1->c2) in (preprocessor_next - preprocessor_next') iff {
                not(partialOrder[preprocessor_next' + (c1->c2)])
                not (c1->c2) in ~dependency
                some c3 : Command | {
                    run_trace_executor[c3]
                    (c3 in (c1 + c2)) or 
                    ((c3 in c1.^preprocessor_next) and not(c3 in c2.^preprocessor_next)) 
                    not (c2 in (c3.^preprocessor_next'))
                }
            }
        }
        // Add edges from preprocessor_next if and only if it is a true dependency
        // and some command in the transitive closure must be being traced


        all c1,c2 : Command {
            (c1->c2) in (preprocessor_next' - preprocessor_next)  iff {
                (c1->c2) in ~dependency
                some c3 : Command {
                    run_trace_executor[c3]
                    (c3 in (c1 + c2)) or 
                    ((c3 in c1.^preprocessor_next) and not(c3 in c2.^preprocessor_next)) 
                    (c2 in (c3.^preprocessor_next'))
                }
            }
        }

    }

    pred wellFormed {
        // partialOrder[preprocessor_next] This is now true only of init and becomes a property to check
        partialOrder[~dependency]
        preprocWellFormed

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
    
    // Command does not develop new preprocs
    pred preprocSame[c : Command] {
        c.preprocessor_next' = c.preprocessor_next
        preprocessor_next'.c = preprocessor_next.c
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
        // Only the initial state should be partial order everything else is enforced through transitions
        partialOrder[preprocessor_next] 
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

// Verification properties

    //If a command has been committed, then all of its dependencies have also been committed.
pred dependency_preservation {
    all x : Command | committed[x] => always ((no x.^dependency) or committed[x.^dependency])
}

check { always (scheduler_e2e implies dependency_preservation)} for exactly 4 State, 3 Command
    
// Once terminated, nothing is scheduled.
check {final implies (always final)  } for exactly 4 State , 3 Command
// This shows that the scheduler terminates, with all Commands committed.
check  {scheduler_e2e implies (eventually final) } for exactly 4 State ,3 Command

// We always have a partial order if we start off with one
check { always (scheduler_e2e implies always(partialOrder[preprocessor_next]))} for exactly 4 State, 3 Command


// Sanity checks

// This is failing!!!
run{
   scheduler_e2e
    some dependency
    no preprocessor_next
    } for exactly 4 State,  3 Command

run{
    scheduler_e2e
    } for exactly 4 State,  6 Command
