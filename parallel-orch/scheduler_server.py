
import argparse
import logging
import os
import signal

from util import *
from partial_program_order import parse_partial_program_order_from_file

##
## A scheduler server
##

## TODO: Figure out how logging here plays out together with the log() in PaSh
logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(message)s")


def handler(signum, frame):
    logging.debug(f'Signal: {signum} caught')
    shutdown()

signal.signal(signal.SIGTERM, handler)

def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    ## TODO: Import the arguments so that they are not duplicated here and in orch
    parser.add_argument("-d", "--debug-level", 
                        type=int, 
                        default=0,
                        help="Set debugging level")
    args, unknown_args = parser.parse_known_args()

    if args.debug_level == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif args.debug_level >= 2:
        logging.getLogger().setLevel(logging.DEBUG)


    return args


def init():
    args = parse_args()
    # config.set_config_globals_from_pash_args(args)

    return args

def success_response(string):
    return f'OK: {string}\n'


def error_response(string):
    return f'ERROR: {string}\n'


class Scheduler:
    """ Schedules a partial order of commands to run out-of-order
    Flow:
        input cmd -> 
                    |   Daemon Start -> Receive whens tarting
                    |   Init -> Read the partial order from a file
                    |   CommandExecComplete -> A command completed its execution
                    |   Wait -> The JIT component waits for the results of a specific command
                    |   Done -> We are done
    """

    def __init__(self, socket_file):
        ## TODO: Add all the orchestrator state here (it should just be the partial order)
        self.done = False
        self.socket = init_unix_socket(socket_file)
        ## A map containing connections for node_ids that are waiting for a response
        self.waiting_for_response = {}
        self.partial_program_order = None

    def handle_init(self, input_cmd: str):
        assert(input_cmd.startswith("Init"))
        partial_order_file = input_cmd.split(":")[1].rstrip()
        logging.debug(f'Scheduler: Received partial_order_file: {partial_order_file}')
        self.partial_program_order = parse_partial_program_order_from_file(partial_order_file)
        logging.debug(f'Parsed partial program order:')
        self.partial_program_order.log_partial_program_order_info()

    def handle_wait(self, input_cmd: str, connection):
        assert(input_cmd.startswith("Wait"))
        ## We have received this message by the JIT, which waits for a node_id to
        ## finish execution.
        node_id = int(input_cmd.split(":")[1].rstrip())
        logging.debug(f'Scheduler: Received wait for node_id: {node_id}')
        
        ## TODO: If the node_id is already committed, just return its exit code
        ##       Else, add this wait to self.waiting_for_response

        exit_code = "0"
        socket_respond(connection, success_response(exit_code))

        ## TODO: Normally we don't always want to close the connection
        connection.close()

    def process_next_cmd(self):
        connection, input_cmd = socket_get_next_cmd(self.socket)

        if(input_cmd.startswith("Init")):
            connection.close()
            self.handle_init(input_cmd)
            ## TODO: Read the partial order from the given file  
        elif (input_cmd.startswith("Daemon Start") or input_cmd == ""):
            connection.close()
            ## This happens when pa.sh first connects to daemon to see if it is on
            logging.debug(f'PaSh made first contact with scheduler server.')
        elif (input_cmd.startswith("CommandExecComplete:")):
            ## We have received this message from an a runner (tracer +isolation)
            ## The runner should have already parsed RWsets and serialized them to
            ## a file.
            connection.close()
            ## TODO: Read the node id from the command argument and the RWSets from file and 
            ## TODO: Progress the graph as much as possible,
            ##       i.e., resolve dependencies and see if we can move commands from frontier to committed etc
            ## TODO: If there is a connection waiting for this node_id, respond to it
        elif (input_cmd.startswith("Wait")):
            self.handle_wait(input_cmd, connection)
        elif (input_cmd.startswith("Done")):
            ## TODO: Make sure everything is done here too (assert that the graph is fully committed)
            ##
            ## We send output to the top level pash process
            ## to signify that we are done.
            logging.debug(f'Scheduler server received shutdown message.')
            socket_respond(connection, success_response("All finished!"))
            self.done = True
        else:
            logging.error(error_response(f'Error: Unsupported command: {input_cmd}'))
            raise Exception(f'Error: Unsupported command: {input_cmd}')


    ## This function schedules commands for execution until our capacity is reached
    ##
    ## It should add some work (if possible), and then return immediately.
    ## It is called once per loop iteration, making sure that there is always work happening
    def schedule_work(self):
        ## TODO: Use the partial order object to pick a few commands (for start let's do all)
        ##       and run them using the scheduler.
        ##
        ## TODO: When scheduling commands, run them with subprocess.run and make sure that at the end
        ##       they will try to connect to our scheduler socket $PASH_SPEC_SCHEDULER_SOCKET to let us
        ##       know that they are done.
        pass

    def run(self):
        ## The first command should be the daemon start
        self.process_next_cmd()
        
        ## The second command should be the partial order init
        self.process_next_cmd()
        

        while not self.done:
            ## Scheduler some work (if we are already at capacity this will return immediately)
            self.schedule_work()

            ## Process a single request
            self.process_next_cmd()

        
        self.socket.close()
        shutdown()




def shutdown():
    ## There may be races since this is called through the signal handling
    logging.debug("PaSh-Spec scheduler is shutting down...")
    logging.debug("PaSh-Spec scheduler shut down successfully...")

def main():
    args = init()

    unix_socket_file = os.getenv("PASH_SPEC_SCHEDULER_SOCKET")

    # print(unix_socket_file)
    scheduler = Scheduler(unix_socket_file)
    scheduler.run()
   

if __name__ == "__main__":
    main()
