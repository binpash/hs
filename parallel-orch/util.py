import config
import logging
import os
import socket
import tempfile


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
