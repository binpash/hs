
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
    pred action_order_violation { 
        some  f : File  | {
            some c1,c2 : Command  | { 
                (c1 + c2) in f.action_order.elems
                f.action_order.idxOf[c1] < f.action_order.idxOf[c2]
                hasDependency[c1,c2]
                c1 in c2.^syntactic_order
            }
        }
    }

    check {  always(scheduler_e2e implies not action_order_violation)} for exactly 6 State, 6 Command, 6 File,6 seq
    check { always (scheduler_e2e implies dependency_preservation)} for exactly 6 State, 6 Command, 6 File
    
    check { always (scheduler_e2e implies rw_preservation)} for exactly 6 State, 6 Command, 6 File,6 seq

// Termination

    // Once terminated, nothing is scheduled.
    check {final implies (always final)  } for exactly 6 State, 6 Command, 6 File , 6 seq 
    // This shows that the scheduler terminates, with all Commands committed.
    check  {scheduler_e2e implies (eventually final) } for exactly 6 State, 6 Command, 6 File, 6 seq 

    check {scheduler_e2e implies commit_order_contained} for exactly 6 State, 3 Command, 6 File, 6 seq 

    // Only 1 command should be executing outside the sandbox at a time
    // Currently failing - there are fixes but not implemented as afaik the code doesn't handle this yet
    check {scheduler_e2e implies always(lone c : Command | Daction[c])}  for exactly 6 State, 6 Command, 6 File, 6 seq 

    // TODO : Dependency between commands on the frontier


