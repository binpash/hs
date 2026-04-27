from __future__ import annotations

from .bash_command import *
import ctypes
import os

from typing import Any

# current location + ../../bash-5.2/bash.so
BASH_FILE_PATH = os.path.join(os.path.dirname(__file__), "bash-5.2", "bash.so")


def _setup_bash() -> ctypes.CDLL:
    if not os.path.isfile(BASH_FILE_PATH):
        # run configure and make clean all
        # this will compile the bash source code into a shared object file
        # that can be called from python using ctypes
        result = os.system(
            "cd "
            + os.path.dirname(BASH_FILE_PATH)
            + " && ./configure && make clean all"
        )
        if result != 0:
            raise Exception("Bash compilation failed")

    if not os.path.isfile(BASH_FILE_PATH):
        raise Exception("Bash file not found at path: " + BASH_FILE_PATH)

    try:
        bash = ctypes.CDLL(BASH_FILE_PATH)
    except OSError:
        raise Exception("Bash shared object file not found at path: " + BASH_FILE_PATH)

    # tell python arg types and return type of the initialize_shell_libbash
    bash.initialize_shell_libbash.argtypes = []
    bash.initialize_shell_libbash.restype = ctypes.c_int

    # call the function
    init_result: ctypes.c_int = bash.initialize_shell_libbash()
    if init_result != 0:
        raise Exception("Bash initialization failed")

    return bash


def ast_to_bash(ast: list[Command], write_to: str):
    """
    Converts the AST of a bash script back into the bash source code.
    :param ast: The AST of the bash script
    will be called before parsing the bash file. By default this is set to false, but
    if the bash source hasn't been compiled yet, this flag will be ignored.
    :return: The bash source code
    """
    bash = _setup_bash()

    # specify arg types and return type of make_command_string function
    bash.make_command_string.argtypes = [ctypes.POINTER(c_bash.command)]
    bash.make_command_string.restype = ctypes.c_char_p

    bash_str = bytes()

    for comm in ast:
        command_string = bash.make_command_string(comm._to_ctypes())
        bash_str += command_string
        bash_str += "\n".encode("utf-8")

    with open(write_to, "wb") as f:
        # don't decode the bytes, just write them to the file
        f.write(bash_str)


def ast_to_json(ast: list[Command]) -> list[dict[str, Any]]:
    """
    Converts the AST to a JSON style object.
    :param ast: The AST, a list of Command objects.
    :return: A JSON style object, a list of dicts from str to JSON style object.
    """
    return [command._to_json() for command in ast]


def bash_to_ast(
    bash_file: str, with_linno_info: bool = False
) -> list[Command] | list[tuple[Command, bytes, int, int]]:
    """
    Extracts the AST from the bash source code.
    Uses ctypes to call an injected bash function that returns the AST.

    :param bash_file: The path to the bash file to parse
    will be called before parsing the bash file. By default this is set to false, but
    if the bash source hasn't been compiled yet, this flag will be ignored.
    :param with_linno_info: If true, the line numbers of the commands will be returned
    :return: The AST of the bash script
    """
    bash = _setup_bash()

    # tell python arg types and return type of the set_bash_file function
    bash.set_bash_file.argtypes = [ctypes.c_char_p]
    bash.set_bash_file.restype = ctypes.c_int

    # call the function
    set_result: int = bash.set_bash_file(bash_file.encode("utf-8"))
    if set_result < 0:
        raise IOError("Setting bash file failed")

    # tell python arg types and return type of the read_command_safe function
    bash.read_command_safe.argtypes = []
    bash.read_command_safe.restype = ctypes.c_int

    # this function closes the file, the function is written by bash, not us
    bash.unset_bash_input.argtypes = [ctypes.c_int]

    command_list = []

    with open(bash_file, "rb") as f:
        lines = f.readlines()

    while True:
        # call the function
        linno_before: int = ctypes.c_int.in_dll(bash, "line_number").value
        read_result: ctypes.c_int = bash.read_command_safe()
        linno_after: int = ctypes.c_int.in_dll(bash, "line_number").value
        if read_result != 0:
            bash.unset_bash_input(0)
            raise RuntimeError("Bash read command failed, shell script may be invalid")

        # read the global_command variable
        global_command: ctypes._Pointer[c_bash.command] = ctypes.POINTER(
            c_bash.command
        ).in_dll(bash, "global_command")

        # global_command is null
        if not global_command:
            eof_reached: ctypes.c_int = ctypes.c_int.in_dll(bash, "EOF_Reached")
            if eof_reached:
                bash.unset_bash_input(0)
                break
            else:
                # newline probably
                continue

        # read the command
        command = Command(global_command.contents)

        # add the command to the list
        if with_linno_info:
            command_string = b"".join(lines[linno_before:linno_after])
            command_list.append((command, command_string, linno_before, linno_after))
        else:
            command_list.append(command)

    return command_list
