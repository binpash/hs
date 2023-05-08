import argparse
import copy
import logging
import signal
from util import *
import config
import sys
from partial_program_order import parse_partial_program_order_from_file, NodeId, parse_node_id

##
## A scheduler server
##

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
    parser.add_argument("-f", "--debug-file", 
                        type=str,
                        default=None,
                        help="Set debugging output file. Default: stdout")
    args, unknown_args = parser.parse_known_args()
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
        self.partial_program_order.init_partial_order()

    def __parse_wait(self, input_cmd: str):
        try:
            node_id_component, loop_iter_counter_component = input_cmd.rstrip().split("|")
            node_id = NodeId(int(node_id_component.split(":")[1].rstrip()))
            loop_counters_str = loop_iter_counter_component.split(":")[1].rstrip()
            if loop_counters_str == "None":
                loop_counters = []
            else:
                loop_counters = [int(cnt) for cnt in loop_counters_str.split("-")]
            return node_id, loop_counters
        except:
            raise Exception(f'Parsing failure for line: {input_cmd}')

    def handle_wait(self, input_cmd: str, connection):
        assert(input_cmd.startswith("Wait"))
        ## We have received this message by the JIT, which waits for a node_id to
        ## finish execution.
        raw_node_id, loop_counters = self.__parse_wait(input_cmd)        
        logging.debug(f'Scheduler: Received wait for node_id: {raw_node_id} with loop counters: {loop_counters}')
                    
        if self.partial_program_order.is_loop_node(raw_node_id):  
            node_id = NodeId(raw_node_id.id, loop_counters)
            if not self.partial_program_order.is_node_id(node_id):
                ## TODO: This unrolling can also happen and be moved to speculation.
                ##       For now we are being conservative and that is why it only happens here
                ## TODO: Move this to the scheduler.schedule_work() (if we have a loop node waiting for response and we are not unrolled, unroll to create work)
                self.partial_program_order.unroll_loop_node(raw_node_id)
        else:
            ## If we are not in a loop, then the node id corresponds to the concrete node
            node_id = raw_node_id

        ## Inform the partial order that we received a wait for a node so that it can push loops
        ## forward and so on.
        self.partial_program_order.wait_received(node_id)

        ## If the node_id is already committed, just return its exit code
        if node_id in self.partial_program_order.get_committed():
            logging.debug(f'Node: {node_id} found in committed, responding immediately!')
            self.waiting_for_response[node_id] = connection
            self.respond_to_pending_wait(node_id)
            
        else:
            ## Command has not executed yet, so we need to wait for it
            logging.debug(f'Node: {node_id} has not finished execution, waiting for response...')
            self.waiting_for_response[node_id] = connection


    def __parse_command_exec_complete(self, input_cmd: str) -> "tuple[int, int]":
        try:
            components = input_cmd.rstrip().split("|")
            command_id = parse_node_id(components[0].split(":")[1])
            exit_code = int(components[1].split(":")[1])
            sandbox_dir = components[2].split(":")[1]
            return command_id, exit_code, sandbox_dir
        except:
            raise Exception(f'Parsing failure for line: {input_cmd}')

    def respond_to_pending_wait(self, node_id: int):
        assert(node_id in self.waiting_for_response)
        ## Get the connection that we need to respond to
        connection = self.waiting_for_response.pop(node_id)

        ## Get the completed node info
        node = self.partial_program_order.get_node(node_id)
        completed_node_info = node.get_completed_node_info()
        response = f'{completed_node_info.get_exit_code()} {completed_node_info.get_variable_file()} {completed_node_info.get_stdout_file()}'
        socket_respond(connection, success_response(response))
        connection.close()

    def handle_command_exec_complete(self, input_cmd: str):
        assert(input_cmd.startswith("CommandExecComplete:"))
        ## Read the node id from the command argument
        cmd_id, exit_code, sandbox_dir = self.__parse_command_exec_complete(input_cmd)
        logging.debug(input_cmd)

        ## Gather RWset, resolve dependencies, and progress graph
        self.partial_program_order.command_execution_completed(cmd_id, exit_code, sandbox_dir)

        ## If there is a connection waiting for this node_id, respond to it
        if cmd_id in self.waiting_for_response and cmd_id in self.partial_program_order.get_committed():
            self.respond_to_pending_wait(cmd_id)

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
            self.handle_command_exec_complete(input_cmd)
        elif (input_cmd.startswith("Wait")):
            self.handle_wait(input_cmd, connection)
        elif (input_cmd.startswith("Done")):
            
            logging.debug(f'Scheduler server received shutdown message.')
            assert self.partial_program_order.is_completed(), 'The partial program order was not completed!'
            logging.debug(f'The partial order was successfully completed.')
            socket_respond(connection, success_response("All finished!"))
            self.partial_program_order.log_committed_cmd_state()
            self.done = True
        else:
            logging.error(error_response(f'Error: Unsupported command: {input_cmd}'))
            raise Exception(f'Error: Unsupported command: {input_cmd}')


    ## This function schedules commands for execution until our capacity is reached
    ##
    ## It should add some work (if possible), and then return immediately.
    ## It is called once per loop iteration, making sure that there is always work happening
    def schedule_work(self):
        self.partial_program_order.schedule_work()

    def run(self):
        ## The first command should be the daemon start
        self.process_next_cmd()
        
        ## The second command should be the partial order init
        self.process_next_cmd()
        

        while not self.done:
            ## Schedule some work (if we are already at capacity this will return immediately)
            self.schedule_work()
            ## Process a single request
            self.process_next_cmd()
            # If workset is empty we should end.
            # TODO: ec checks fail for now
        self.socket.close()
        shutdown()


def shutdown():
    ## There may be races since this is called through the signal handling
    logging.debug("PaSh-Spec scheduler is shutting down...")
    logging.debug("PaSh-Spec scheduler shut down successfully...")

def main():
    args = init()

    # Format logging
    # ref: https://docs.python.org/3/library/logging.html#formatter-objects
    if args.debug_file is None:
        logging.basicConfig(format="%(levelname)s|%(asctime)s|%(message)s")
    else:
        print(os.path.abspath(args.debug_file))
        logging.basicConfig(format="%(levelname)s|%(asctime)s|%(message)s", 
                            filename=f"{os.path.abspath(args.debug_file)}", 
                            filemode="w")

    # Set debug level
    if args.debug_level == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif args.debug_level == 2:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.debug_level >= 3:
        logging.getLogger().setLevel(logging.TRACE)

    scheduler = Scheduler(config.SCHEDULER_SOCKET)
    scheduler.run()
   

if __name__ == "__main__":
    main()
