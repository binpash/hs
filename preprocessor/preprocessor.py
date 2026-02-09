"""
PaSh Preprocessor Entry Point

This module handles preprocessing of shell scripts by:
1. Parsing the shell script to ASTs
2. Replacing candidate dataflow regions with calls to PaSh runtime
3. Unparsing the transformed ASTs back to shell syntax
"""

import sys
import os
import argparse
import logging
import socket
from datetime import datetime

import transformation
import ast_transform
from parse import parse_shell_to_asts, from_ast_objects_to_shell
from util import log, logging_prefix, print_time_delta


LOGGING_PREFIX = "PaSh Preprocessor: "

## Increase the recursion limit (it seems that the parser/unparser needs it for bigger scripts)
sys.setrecursionlimit(10000)


def config_from_args(pash_args):
    """Configure logging based on command-line arguments."""
    if pash_args.log_file == "":
        logging.basicConfig(format="%(message)s")
    else:
        logging.basicConfig(
            format="%(message)s",
            filename=f"{os.path.abspath(pash_args.log_file)}",
            filemode="w",
        )

    if pash_args.debug == 0:
        logging.getLogger().setLevel(logging.ERROR)
    elif pash_args.debug == 1:
        logging.getLogger().setLevel(logging.WARNING)
    elif pash_args.debug == 2:
        logging.getLogger().setLevel(logging.INFO)
    elif pash_args.debug >= 3:
        logging.getLogger().setLevel(logging.DEBUG)


class Parser(argparse.ArgumentParser):
    """Command-line argument parser for the preprocessor."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_argument(
            "-d",
            "--debug",
            type=int,
            help="configure debug level; defaults to 0",
            default=1,
        )
        self.add_argument(
            "--log_file",
            help="configure where to write the log; defaults to stderr.",
            default="",
        )
        self.add_argument(
            "input",
            help="the script file to be preprocessed",
        )
        self.add_argument(
            "--output",
            help="path where the preprocessed script will be saved",
            required=True,
        )
        self.add_argument(
            "--bash",
            help="(experimental) interpret the input as a bash script file",
            action="store_true",
        )


@logging_prefix(LOGGING_PREFIX)
def main():
    """Main entry point for the preprocessor."""
    args = parse_args()
    input_script_path = args.input

    preprocessed_shell_script = preprocess(input_script_path, args)

    # Write the preprocessed script to the output file
    fname = args.output
    log("Preprocessed script stored in:", fname)
    with open(fname, "wb") as new_shell_file:
        preprocessed_shell_script = preprocessed_shell_script.encode(
            "utf-8", errors="replace"
        )
        new_shell_file.write(preprocessed_shell_script)

    log("-" * 40)  # log end marker


def preprocess(input_script_path, args):
    """
    Preprocess a shell script.

    This function:
    1. Parses the shell script to ASTs
    2. Preprocesses ASTs by replacing candidate dataflow regions
    3. Unparses the ASTs back to shell syntax
    """
    # 1. Parse shell to AST
    preprocessing_parsing_start_time = datetime.now()
    ast_objects = parse_shell_to_asts(input_script_path, bash_mode=args.bash)
    preprocessing_parsing_end_time = datetime.now()
    print_time_delta(
        "Preprocessing -- Parsing",
        preprocessing_parsing_start_time,
        preprocessing_parsing_end_time,
    )

    # 2. Preprocess ASTs by replacing candidates with calls to PaSh runtime
    preprocessing_pash_start_time = datetime.now()
    preprocessed_asts = preprocess_asts(ast_objects, args)
    preprocessing_pash_end_time = datetime.now()
    print_time_delta(
        "Preprocessing -- PaSh",
        preprocessing_pash_start_time,
        preprocessing_pash_end_time,
    )

    # 3. Unparse the ASTs back to shell syntax
    preprocessing_unparsing_start_time = datetime.now()
    preprocessed_shell_script = from_ast_objects_to_shell(preprocessed_asts)
    preprocessing_unparsing_end_time = datetime.now()
    print_time_delta(
        "Preprocessing -- Unparsing",
        preprocessing_unparsing_start_time,
        preprocessing_unparsing_end_time,
    )

    return preprocessed_shell_script


def preprocess_asts(ast_objects, args):
    """Preprocess AST objects using speculative transformation."""
    trans_options = transformation.TransformationState(
        po_file=args.partial_order_file
    )
    transformation.initialize(trans_options)

    # Preprocess ASTs by replacing regions with calls to PaSh runtime
    preprocessed_asts = ast_transform.replace_ast_regions(ast_objects, trans_options)

    # Finalize the partial order file
    transformation.serialize_partial_order(trans_options)

    # Inform the scheduler that the partial order file is ready
    unix_socket_file = os.getenv("PASH_SPEC_SCHEDULER_SOCKET")
    msg = transformation.scheduler_server_init_po_msg(
        trans_options.get_partial_order_file()
    )
    _unix_socket_send_and_forget(unix_socket_file, msg)

    return preprocessed_asts


def _unix_socket_send_and_forget(socket_file, msg):
    """Send a message to a Unix socket without waiting for a response."""
    if socket_file is None:
        return
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(socket_file)
        msg_with_newline = msg + '\n'
        sock.sendall(msg_with_newline.encode('utf-8'))
        sock.close()
    except Exception as e:
        log(f"Warning: Failed to send message to scheduler socket: {e}")


def parse_args():
    """Parse command-line arguments."""
    prog_name = sys.argv[0]
    if "PASH_FROM_SH" in os.environ:
        prog_name = os.environ["PASH_FROM_SH"]
    parser = Parser(prog_name)
    args = parser.parse_args()
    config_from_args(args)

    # Set up partial order file path
    args.__dict__["partial_order_file"] = transformation.partial_order_file_path()
    log("Partial order file:", args.partial_order_file)

    # Log all arguments
    log("Arguments:")
    for arg_name, arg_val in vars(args).items():
        log(arg_name, arg_val)
    log("-" * 40)

    return args


if __name__ == "__main__":
    main()
