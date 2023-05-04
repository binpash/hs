echo hi
for i in 1 2 3 4 5; do
    ## Can't do nested loops yet
    # for j in 1 2; do
        ## Until we figure out variables the only way to determine that this run twice is by measuring the executed time
        sleep 1
        ## TODO: Manage to do multiple commands in a single loop
        echo hi
    # done
done
