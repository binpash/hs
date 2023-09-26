import config
import logging
import os
import socket
import subprocess
import tempfile
import time
import re
import psutil
import signal

def ptempfile():
    fd, name = tempfile.mkstemp(dir=config.PASH_SPEC_TMP_PREFIX)
    ## TODO: Get a name without opening the fd too if possible
    os.close(fd)
    return name

def init_unix_socket(socket_file: str) -> socket.socket:
    server_address = socket_file

    # Make sure the socket does not already exist
    ## TODO: Is this necessary?
    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise
    logging.debug("SocketManager: Made sure that socket does not exist")

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    logging.debug("SocketManager: Created socket")

    sock.bind(server_address)
    logging.debug("SocketManager: Successfully bound to socket")    

    ## TODO: Check if we need to configure the backlog
    sock.listen()    
    logging.debug("SocketManager: Listenting on socket")    

    return sock

def socket_get_next_cmd(sock: socket.socket) -> "tuple[socket.socket, str]" :
    connection, client_address = sock.accept()
    data = connection.recv(config.SOCKET_BUF_SIZE)

    ## TODO: This could be avoided for efficiency
    str_data = data.decode('utf-8')
    logging.debug(f'Received data: {str_data}')
    ## TODO: Lift this requirement if needed
    ##
    ## We need to ensure that we read a command at once or the command was empty (only relevant in the first invocation)
    assert(str_data.endswith("\n") or str_data == "")
    
    return (connection, str_data)

def socket_respond(connection: socket.socket, message: str):
    bytes_message = message.encode('utf-8')
    connection.sendall(bytes_message)
    connection.close()

def parse_env_string_to_dict(content):
    # Parse scalar string vars
    scalar_vars_string = re.findall(r'declare (?:-x|--)? (\w+)="([^"]*)"', content, re.DOTALL)

    # Parse scalar integer vars
    scalar_vars_int = re.findall(r'declare -i (\w+)="(\d+)"', content)

    # Parse array declarations
    array_vars = re.findall(r'declare -a (\w+)=(\([^)]+\))', content)

    # Merge all parsed variables
    result = {key: value for key, value in scalar_vars_string}
    result.update({key: int(value) for key, value in scalar_vars_int})
    result.update({key: value for key, value in array_vars})
    
    return result

def compare_dicts(dict1, dict2):
    only_in_first = {}
    only_in_second = {}
    different_in_both = {}
    # Check for keys in dict1 but not in dict2 and for different values
    for key, value in dict1.items():
        if key not in dict2:
            only_in_first[key] = value
        elif dict1[key] != dict2[key]:
            different_in_both[key] = (dict1[key], dict2[key])
    # Check for keys in dict2 but not in dict1
    for key, value in dict2.items():
        if key not in dict1:
            only_in_second[key] = value
    return only_in_first, only_in_second, different_in_both

def compare_env_strings(file1_content, file2_content):
    dict1 = parse_env_string_to_dict(file1_content)
    dict2 = parse_env_string_to_dict(file2_content)
    return compare_dicts(dict1, dict2)

def log_time_delta_from_start(module: str, action: str, node=None):
    logging.info(f">|{module}|{action}{',' + str(node) if node is not None else ''}|Time From start:{to_milliseconds_str(time.time() - config.START_TIME)}")

def set_named_timestamp(action: str, node=None, key=None):
    if key is None:
        key = f"{action}{',' + str(node) if node is not None else ''}"
    config.NAMED_TIMESTAMPS[key] = time.time()
    
def invalidate_named_timestamp(action: str, node=None, key=None):
    if key is None:
        key = f"{action}{',' + str(node) if node is not None else ''}"
    del config.NAMED_TIMESTAMPS[key]
    
def log_time_delta_from_start_and_set_named_timestamp(module: str, action: str, node=None, key=None):
    try:
        set_named_timestamp(action, node, key)
        logging.info(f">|{module}|{action}{',' + str(node) if node is not None else ''}|Time from start:{to_milliseconds_str(time.time() - config.START_TIME)}")
    except KeyError:
        logging.error(f"Named timestamp {key} already exists")
    
def log_time_delta_from_named_timestamp(module: str, action: str, node=None, key=None, invalidate=True):
    try:
        if key is None:
            key = f"{action}{',' + str(node) if node is not None else ''}"
        logging.info(f">|{module}|{action}{',' + str(node) if node is not None else ''}|Time from start:{to_milliseconds_str(time.time() - config.START_TIME)}|Step time:{to_milliseconds_str(time.time() - config.NAMED_TIMESTAMPS[key])}")
        if invalidate:
            invalidate_named_timestamp(action, node, key)
    except KeyError:
        logging.error(f"Named timestamp {key} does not exist")

def to_milliseconds_str(seconds: float) -> str:
    return f"{seconds * 1000:.3f}ms"



def get_all_child_processes(pid):
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return []
    
    children = parent.children(recursive=True)
    parent_of_parent = parent.parent()
    logging.critical("PARENT_PROCESS: " + str(parent_of_parent))
    logging.critical("MAIN_PROCESS: " + str(parent))
    all_processes = [parent] + children
    for process in all_processes:
        logging.critical("PROCESS: " + str(process))
    return all_processes


def kill_process_tree(pid, sig=signal.SIGTERM):
    processes = get_all_child_processes(pid)
    for proc in processes:
        try:
            os.kill(proc.pid, sig)
        except (psutil.NoSuchProcess):
            pass
        except (PermissionError):
            logging.critical("NO PERMISSION")
        except (ProcessLookupError):
            logging.critical("PROCESS LOOKUP ERROR")

    # Check if processes are still alive
    alive_processes = []
    for proc in processes:
        try:
            if proc.is_running():
                alive_processes.append(f"{proc}-({proc.status()})")
        except:
            pass
    return alive_processes
