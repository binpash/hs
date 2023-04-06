
// open scheduler as sch
// open util/ordering[Command] as lin

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
