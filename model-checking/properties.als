
open scheduler as sch
open util/ordering[Command] as lin

// Safety:


    //If a command has been committed, then all of its dependencies have also been committed.
    pred dependency_preservation {
        all c1,c2 : Command | {
            c2 in c1.^commit_order implies not(c1 in c2.^syntactic_order)
        }
    }
    pred commit_order_contained {
        some c : Command { 
            some (commit_order.c ) iff committed[c]
        }
    }

    pred rw_preservation{ 
        some c1,c2 : Command | {
            c2 in c1.^commit_order implies not hasDependency[c2,c1] 
        }
    }
    check { always (scheduler_e2e implies dependency_preservation)} for exactly 6 State, 6 Command, 6 File
    
    check { always (scheduler_e2e implies rw_preservation)} for exactly 6 State, 6 Command, 6 File

// Termination

    // Once terminated, nothing is scheduled.
    check {final implies (always final)  } for exactly 6 State, 6 Command, 6 File
    // This shows that the scheduler terminates, with all Commands committed.
    check  {scheduler_e2e implies (eventually final) } for exactly 6 State, 6 Command, 6 File

    check {scheduler_e2e implies commit_order_contained} for exactly 6 State, 6 Command, 6 File

    // Only 1 command should be executing outside the sandbox at a time
    // Currently failing - there are fixes but not implemented as afaik the code doesn't handle this yet
    check {scheduler_e2e implies always(lone c : Command | Daction[c])}  for exactly 6 State, 6 Command, 6 File

    

run { 
    init 
    traces
} for exactly 6 State, exactly 6 Command, 6 File

run {
    scheduler_e2e 
    eventually(some c : Command | some c.side_effect)
    }  for exactly 6 State, 2 Command, 6 File


run { 
    scheduler_e2e
    no syntactic_order
    
} for exactly 6 State, exactly 6 Command, 6 File

run {
    scheduler_e2e
    eventually (some read_set)
    eventually (some write_set)
} for exactly 6 State, exactly 6 Command, 6 File

run {
    scheduler_e2e
    some f : File , c : Command {
        eventually(f in c.write_set until f not in c.write_set)
    }
} for exactly 6 State, exactly 6 Command, 6 File

run { 
    scheduler_e2e
    eventually(some c1,c2 : Command {
        committed[c1]
        !committed[c2]
        c1 in c2.^syntactic_order
        hasDependency[c2,c1]
    })
} for exactly 6 State, exactly 6 Command, 6 File
run {
    scheduler_e2e
    some c1,c2 : Command | {
        staySpec[c1]
        c1 in c2.^syntactic_order
        stayNE[c2]        
    }
} for exactly 6 State, 6 Command, 6 File