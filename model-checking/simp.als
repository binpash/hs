sig T { 
    var s : seq Int 
}


pred init {
    #T.s.elems = 0
    1 in T.s'.elems
    3 in T.s'.elems
    // some T.s'.add[2]
}

run {init} for exactly 1 T,3 seq