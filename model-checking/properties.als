
open scheduler as sch
open util/ordering[Command] as lin

// Safety:

    //If a command has been committed, then all of its dependencies have also been committed.
    pred dependency_preservation {
        all x : Command | committed[x] => always ((no x.^dependency) or committed[x.^dependency])
    }

    check { always (scheduler_e2e implies dependency_preservation)} for exactly 4 State, exactly 2 Command, 6 File
        
// Termination

    // Once terminated, nothing is scheduled.
    check {final implies (always final)  } for exactly 4 State, exactly 2 Command, 6 File
    // This shows that the scheduler terminates, with all Commands committed.
    check  {scheduler_e2e implies (eventually final) }for exactly 4 State, exactly 2 Command, 6 File
