
open scheduler as sch
open util/ordering[Command] as lin

// Safety:

    //If a command has been committed, then all of its dependencies have also been committed.
    pred dependency_preservation {
        all c1,c2 : Command | {
            c2 in c1.^commit_order implies not(c1 in c2.^syntactic_order)
        }
    }

    check { always (scheduler_e2e implies dependency_preservation)} for exactly 5 State, 6 Command, 6 File
        
// Termination

    // Once terminated, nothing is scheduled.
    check {final implies (always final)  } for exactly 5 State, 6 Command, 6 File
    // This shows that the scheduler terminates, with all Commands committed.
    check  {scheduler_e2e implies (eventually final) } for exactly 5 State, 6 Command, 6 File


run { 
    init 
    traces
    
} for exactly 5 State, exactly 2 Command, 6 File