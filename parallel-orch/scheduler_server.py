import argparse
import logging
import signal
import util
import config
from partial_program_order import NodeId
from node import LoopStack

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
    parser.add_argument("--sandbox-killing",
                        action="store_true",
                        default=False,
                    help="Kill any running overlay instances before commiting to the lower layer")
    parser.add_argument("--speculate-immediately",
                    action="store_true",
                    default=False,
                    help="Speculate immediately instead of waiting for the first Wait message.")

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
    window: int  # Integer representing the window
    latest_env: str # This variable should be initialized by the first wait, and always have a value since

    def __init__(self, socket_file):
        self.window = 0
        self.done = False
        self.socket = util.init_unix_socket(socket_file)
        ## A map containing connections for node_ids that are waiting for a response
        self.waiting_for_response = {}
        self.partial_program_order = None

    def handle_init(self, input_cmd: str):
        assert(input_cmd.startswith("Init"))
        partial_order_file = input_cmd.split(":")[1].rstrip()
        logging.debug(f'Scheduler: Received partial_order_file: {partial_order_file}')
        self.partial_program_order = util.parse_partial_program_order_from_file(partial_order_file)
        self.partial_program_order.init_partial_order()

    def handle_wait(self, input_cmd: str, connection):
        node_id, env_file = self.__parse_wait(input_cmd)
        self.waiting_for_response[node_id] = connection
        logging.info(f'Scheduler: Received wait message - {node_id}.')
        self.latest_env = env_file
        
        self.partial_program_order.maybe_unroll_loop_node(node_id)
        
        self.partial_program_order.handle_wait(node_id, env_file)
        if self.partial_program_order.get_node(node_id).is_committed():
            self.respond_to_pending_wait(node_id)

    def process_next_cmd(self):
        connection, input_cmd = util.socket_get_next_cmd(self.socket)

        if(input_cmd.startswith("Init")):
            connection.close()
            self.handle_init(input_cmd)
        elif (input_cmd.startswith("Daemon Start") or input_cmd == ""):
            logging.info(f'Scheduler: Received daemon start message.')
            connection.close()
        elif (input_cmd.startswith("CommandExecComplete:")):
            node_id, exec_id, exit_code, sandbox_dir, trace_file = self.__parse_command_exec_x(input_cmd)
            if self.partial_program_order.get_node(node_id).exec_id == exec_id:
                logging.info(f'Scheduler: Received command exec complete message - {node_id}.')
                self.partial_program_order.handle_complete(node_id, node_id in self.waiting_for_response, self.latest_env)
                
                if self.partial_program_order.get_node(node_id).is_committed():
                    self.respond_to_pending_wait(node_id)
            else:
                logging.info(f'Scheduler: Received command exec complete message for a killed instance, ignoring - {node_id}.')
        elif (input_cmd.startswith("Wait")):
            self.handle_wait(input_cmd, connection)
        elif (input_cmd.startswith("Done")):
            util.socket_respond(connection, success_response("All finished!"))
            self.partial_program_order.log_info()
            self.done = True
        elif input_cmd.startswith("CommandExecStart:"):
            node_id, exec_id, sandbox_dir, trace_file = self.__parse_command_exec_x(input_cmd)
            logging.info(f'Scheduler: Received command exec start message - {input_cmd}.')
            # self.handle_command_exec_start(input_cmd)
        else:
            logging.error(error_response(f'Error: Unsupported command: {input_cmd}'))
            raise Exception(f'Error: Unsupported command: {input_cmd}')

    def respond_to_frontend_core(self, node_id: NodeId, response: str):
        assert(node_id in self.waiting_for_response)
        ## Get the connection that we need to respond to
        connection = self.waiting_for_response.pop(node_id)
        util.socket_respond(connection, response)
        connection.close()

    def respond_to_pending_wait(self, node_id: int):
        logging.debug(f'Responding to pending wait for node: {node_id}')
        ## Get the completed node info
        node = self.partial_program_order.get_node(node_id)
        msg = '{} {} {}'.format(*node.execution_outcome())
        response = success_response(msg)
        
        ## Send the response
        self.respond_to_frontend_core(node_id, response)

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
        
    def __parse_command_exec_x(self, input_cmd: str) -> "tuple[int, int]":
        try:
            components = input_cmd.rstrip().split("|")
            command_id = NodeId.parse_node_id(components[0].split(":")[1])
            exec_id = int(components[1].split(":")[1])
            exit_code = int(components[2].split(":")[1])
            sandbox_dir = components[3].split(":")[1]
            trace_file = components[4].split(":")[1]
            return command_id, exec_id, exit_code, sandbox_dir, trace_file
        except:
            raise Exception(f'Parsing failure for line: {input_cmd}')


    def schedule_work(self):
        nodes = self.partial_program_order.get_schedulable_nodes()
        for n in nodes[:2]:
            self.partial_program_order.schedule_spec_work(n, self.latest_env)
        
    def run(self):
        ## The first command should be the daemon start
        self.process_next_cmd()
        
        ## The second command should be the partial order init
        self.process_next_cmd()

        self.partial_program_order.log_state()
        while not self.done:
            self.process_next_cmd()
            self.partial_program_order.log_state()
            self.schedule_work()
            self.partial_program_order.log_state()
            self.partial_program_order.eager_fs_killing()
            self.partial_program_order.log_state()
        self.socket.close()
        self.shutdown()

    def shutdown(self):
        ## There may be races since this is called through the signal handling
        logging.debug("PaSh-Spec scheduler is shutting down...")
        logging.debug("PaSh-Spec scheduler shut down successfully...")
        self.terminate_pending_commands()
        
    def terminate_pending_commands(self):
        for node in self.partial_program_order.get_executing_normal_and_spec_nodes():
            proc, _trace_file, _stdout, _stderr, _variable_file, _ = node.get_main_sandbox()
            logging.debug(f'Killing: {proc}')
            # proc.terminate()

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

    # Set optimization options
    config.SANDBOX_KILLING = args.sandbox_killing
    config.SPECULATE_IMMEDIATELY = args.speculate_immediately
    scheduler = Scheduler(config.SCHEDULER_SOCKET)
    scheduler.run()
   

if __name__ == "__main__":
    main()
