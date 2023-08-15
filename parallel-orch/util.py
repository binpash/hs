import config
import logging
import os
import socket
import tempfile
import time

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

# Check if the process with the given PID is alive.
def is_process_alive(self, pid) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

# Get all child process PIDs of a process
def get_child_processes(self, parent_pid) -> int:
    try:
        output = subprocess.check_output(['pgrep', '-P', str(parent_pid)])
        return [int(pid) for pid in output.decode('utf-8').split()]
    except subprocess.CalledProcessError:
        # No child processes were found
        return []

# Kills the process with the provided PID.
# Returns True if the process was successfully killed, False otherwise.
def kill_process(self, pid: int) -> bool:
    kill_attempts = 0
    while is_process_alive(pid) and kill_attempts < MAX_KILL_ATTEMPTS:
        try:
            # Send SIGKILL signal for a forceful kill
            subprocess.check_call(['kill', '-9', str(pid)])
            time.sleep(0.01)  # Sleep for 10 milliseconds before checking again
        except subprocess.CalledProcessError:
            logging.debug(f"Failed to kill PID {pid}.")
        kill_attempts += 1
    
    if kill_attempts >= MAX_KILL_ATTEMPTS:
        logging.warning(f"Gave up killing PID {pid} after {MAX_KILL_ATTEMPTS} attempts.")
        return False
    
    return True
