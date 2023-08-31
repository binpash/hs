import argparse
import copy
import logging
import signal
from util import *
import config
import sys
from partial_program_order import parse_partial_program_order_from_file, LoopStack, NodeId, parse_node_id

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
    parser.add_argument("-f", "--log_file", 
                        type=str,
                        default=None,
                        help="Set logging output file. Default: stdout")
    args, unknown_args = parser.parse_known_args()
    return args

def init():
    args = parse_args()
    # config.set_config_globals_from_pash_args(args)
    return args

def success_response(string):
    return f'OK: {string}\n'

def unsafe_response(string):
    return f'UNSAFE: {string}\n'

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

    def __parse_wait(self, input_cmd: str) -> "tuple[NodeId, str]":
        try:
            node_id_component, loop_iter_counter_component, pash_runtime_vars_file_component = input_cmd.rstrip().split("|")
            raw_node_id_int = int(node_id_component.split(":")[1].rstrip())
            loop_counters_str = loop_iter_counter_component.split(":")[1].rstrip()
            pash_runtime_vars_file_str = pash_runtime_vars_file_component.split(":")[1].rstrip()
            if loop_counters_str == "None":
                node_id = NodeId(raw_node_id_int), pash_runtime_vars_file_str
            else:
                loop_counters = [int(cnt) for cnt in loop_counters_str.split("-")]
                node_id = NodeId(raw_node_id_int, LoopStack(loop_counters)), pash_runtime_vars_file_str           
            return node_id
        except:
            raise Exception(f'Parsing failure for line: {input_cmd}')

    def handle_wait(self, input_cmd: str, connection):
        assert(input_cmd.startswith("Wait"))
        ## We have received this message by the JIT, which waits for a node_id to
        ## finish execution.
        node_id, pash_runtime_vars_file_str = self.__parse_wait(input_cmd)        
        logging.debug(f'Scheduler: Received wait for node_id: {node_id}|New env file: {pash_runtime_vars_file_str}')

        ## Set the new env file for the node
        self.partial_program_order.set_new_env_file_for_node(node_id, pash_runtime_vars_file_str)

        
        ## Attempt to resolve environment differences on waiting partial order nodes
        self.partial_program_order.maybe_resolve_most_recent_envs_and_continue_resolution(node_id)
        
        ## Inform the partial order that we received a wait for a node so that it can push loops
        ## forward and so on.
        self.partial_program_order.wait_received(node_id)

        ## If the node_id is already committed, just return its exit code
        if node_id in self.partial_program_order.get_committed():
            # TODO: Env check and if no conflicts, commit
            logging.debug(f'Node: {node_id} found in committed, responding immediately!')
            self.waiting_for_response[node_id] = connection
            self.respond_to_pending_wait(node_id)
        elif node_id in self.partial_program_order.get_unsafe():
            logging.debug(f'Node: {node_id} found in unsafe, it must be executed in the original shell!')
            self.waiting_for_response[node_id] = connection
            self.respond_unsafe_to_pending_wait(node_id)
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
            trace_file = components[3].split(":")[1]
            return command_id, exit_code, sandbox_dir, trace_file
        except:
            raise Exception(f'Parsing failure for line: {input_cmd}')

    def respond_unsafe_to_pending_wait(self, node_id: int):
        assert(node_id in self.partial_program_order.get_unsafe())

        ## First remove node_id from unsafe and stopped and add to committed
        ##  since it will be executed immediately in the original shell
        self.partial_program_order.remove_from_unsafe(node_id)
        self.partial_program_order.commit_node(node_id)

        response = unsafe_response("")

        ## Send the response
        self.respond_to_frontend_core(node_id, response)


    ## TODO: send riker env here
    def respond_to_pending_wait(self, node_id: int):
        logging.debug(f'Responding to pending wait for node: {node_id}')
        ## Get the completed node info
        node = self.partial_program_order.get_node(node_id)
        completed_node_info = node.get_completed_node_info()
        msg = f'{completed_node_info.get_exit_code()} {completed_node_info.get_post_exec_env()} {completed_node_info.get_stdout_file()}'
        response = success_response(msg)
        ## Send the response
        self.respond_to_frontend_core(node_id, response)


    def respond_to_frontend_core(self, node_id: NodeId, response: str):
        assert(node_id in self.waiting_for_response)
        ## Get the connection that we need to respond to
        connection = self.waiting_for_response.pop(node_id)
        socket_respond(connection, response)
        connection.close()

    def handle_command_exec_complete(self, input_cmd: str):
        assert(input_cmd.startswith("CommandExecComplete:"))
        ## Read the node id from the command argument
        cmd_id, exit_code, sandbox_dir, trace_file = self.__parse_command_exec_complete(input_cmd)
        if trace_file in self.partial_program_order.banned_files:
            logging.debug(f'CommandExecComplete: {cmd_id} ignored')
            return
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
            logging.debug(f'The partial order was successfully completed.')
            if not self.partial_program_order.is_completed():
                logging.debug(" |- some nodes were skipped completed.")
            socket_respond(connection, success_response("All finished!"))
            self.partial_program_order.log_executions()
            self.done = True
        else:
            logging.error(error_response(f'Error: Unsupported command: {input_cmd}'))
            raise Exception(f'Error: Unsupported command: {input_cmd}')

    def check_unsafe_and_waiting(self):
        ## If a command is waiting and also deemed to be unsafe, we need to respond
        waiting_for_response = set(self.waiting_for_response.keys())
        unsafe = set(self.partial_program_order.get_unsafe())
        unsafe_and_waiting = unsafe.intersection(waiting_for_response)
        if len(unsafe_and_waiting) > 0:
            assert(len(unsafe_and_waiting) == 1)
            logging.debug(f'Unsafe and waiting for response nodes: {unsafe_and_waiting}')
            logging.debug(f'Sending responses to them: {unsafe_and_waiting}')
            unsafe_and_waiting_id = list(unsafe_and_waiting)[0]
            self.respond_unsafe_to_pending_wait(unsafe_and_waiting_id)

    ## This function schedules commands for execution until our capacity is reached
    ##
    ## It should add some work (if possible), and then return immediately.
    ## It is called once per loop iteration, making sure that there is always work happening
    def schedule_work(self):
        self.partial_program_order.schedule_work()

        ## Respond to any waiting nodes that have been deemed to be unsafe
        self.check_unsafe_and_waiting()

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
        self.shutdown()

    def shutdown(self):
        ## There may be races since this is called through the signal handling
        logging.debug("PaSh-Spec scheduler is shutting down...")
        logging.debug("PaSh-Spec scheduler shut down successfully...")
        self.terminate_pending_commands()
        
    def terminate_pending_commands(self):
        for _node_id, cmd_info in self.partial_program_order.commands_currently_executing.items():
            proc, _trace_file, _stdout, _stderr, _variable_file = cmd_info
            proc.terminate()


def main():
    args = init()

    # Format logging
    # ref: https://docs.python.org/3/library/logging.html#formatter-objects
    if args.log_file is None:
        logging.basicConfig(format="%(levelname)s|%(asctime)s|%(message)s")
    else:
        logging.basicConfig(format="%(levelname)s|%(asctime)s|%(message)s", 
                            filename=f"{os.path.abspath(args.log_file)}", 
                            filemode="w")

    # Set debug level
    if args.debug_level == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif args.debug_level >= 2:
        logging.getLogger().setLevel(logging.DEBUG)
    # elif args.debug_level >= 3:
    #     logging.getLogger().setLevel(logging.TRACE)

    scheduler = Scheduler(config.SCHEDULER_SOCKET)
    scheduler.run()
   

if __name__ == "__main__":
    main()
