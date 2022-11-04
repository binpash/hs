import subprocess

def run_and_trace_workset(workset, trace_file):
    write_cmds_to_rikerfile(workset)
    ## Call Riker to execute the remaining commands all in parallel
    subprocess.run(["rkr", "--show"], stdout=subprocess.DEVNULL)
    ## Call Riker to get the trace
    ## TODO: Normally we would like to plug in Riker and get the actual Trace data structure
    subprocess.run(["rkr", "trace", "-o", trace_file])
    trace = read_rkr_trace(trace_file)
    return trace

## Write a Rikerfile with these commands to execute them
def write_cmds_to_rikerfile(cmds_to_run):
    with open("Rikerfile", "w") as f:
        for cmd in cmds_to_run:
            f.write(cmd + " & \n")

## Read trace and capture each command
def read_rkr_trace(trace_file):
    with open(trace_file) as f:
        return f.readlines()
