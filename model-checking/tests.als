
open scheduler as sch
open util/ordering[Command] as lin

// // should be SAT
// // run  {
// //     scheduler_e2e 
// //     some dependency
// //     no preprocessor_next  
// //     } for exactly 4 State , 3 Command, 6 File

// // should be UNSAT 
// // Why should this be unsat?
// // run {
// //     scheduler_e2e 
// //     some dependency
// //     some c1 ,c2 : Command {
// //          (c1->c2) in preprocessor_next
// //          (c1->c2) in ~dependency
         
// //         eventually( not (c1->c2 in preprocessor_next))
// //     }
// // }  for exactly 4 State , 3 Command, 2 File


//     // Tests for dependency 
//         run {(some a : Command, b : Command | not independent[a,b])}
//         run {dependencies_valid and (some dependency)} 


//         // Misc / Testing

// ---------------------------------------------
// pred all_sideffects_and_deps {

//     all c : Command | has_operation_on_filesystems[c]
//     some dependency
// }

// check  {(scheduler_e2e and all_sideffects_and_deps) implies (eventually final) } for exactly 4 State, exactly 2 Command, 6 File
// ----------------------------------------------
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

run {
    scheduler_e2e
    eventually(some action_order)
}for exactly 6 State, 6 Command, 6 File

run { 
    scheduler_e2e
    eventually(
        some f : File | #(f.action_order.elems)  =4 
    )
} for exactly 6 State, 4 Command, 6 File , 4 seq
run { 
    scheduler_e2e
    eventually(
        some f : File | #(f.action_order.elems)  =4 
    )
} for exactly 6 State, 4 Command, 6 File , 4 seq
run { 
    scheduler_e2e
    eventually (
        some f1,f2 : File | {
            #(f1.action_order.elems) = 6
            #(f2.action_order.elems) = 3
        }
    )
}for exactly 6 State, 6 Command, 6 File,6 seq
