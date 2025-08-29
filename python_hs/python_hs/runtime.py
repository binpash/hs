import dataclasses
import functools
import os
import random
import socket
import string
import subprocess
import sys
from pathlib import Path
from typing import Literal, assert_never

from python_hs.constants import (
    PASH_SPEC_SCHEDULER_SOCKET,
    PASH_SPEC_TMP_PREFIX,
    RUNTIME_DIR,
)
from python_hs.logging_ import setup_logger

logger = setup_logger(__name__)

alphabet = string.ascii_lowercase + string.digits


def random_str(n: int = 8) -> str:
    return "".join(random.choices(alphabet, k=n))


@dataclasses.dataclass
class CompletedProcess:
    returncode: int
    stdout: str | None


def get_vars() -> str:
    bash_vars = str(PASH_SPEC_TMP_PREFIX / f"variables_{random_str()}")
    subprocess.run([f"{RUNTIME_DIR}/pash_declare_vars.sh", bash_vars], check=True)
    logger.info(f"Bash variables saved in {bash_vars!r}")
    return bash_vars


def communicate_socket(server_name: str, socket_path: str | Path, msg: str) -> str:
    socket_path = str(socket_path)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    logger.info(f"{server_name}: connecting to {socket_path!r}")
    sock.connect(socket_path)
    logger.info(f"{server_name}: sending {msg!r}")
    sock.sendall(msg.encode() + b"\n")
    response = sock.recv(1024).decode()
    sock.close()
    logger.info(f"{server_name}: received {response!r}")
    return response


communicate_with_scheduler = functools.partial(
    communicate_socket, "PaSh-Spec-scheduler", PASH_SPEC_SCHEDULER_SOCKET
)


def create_partial_order() -> Path:
    path = PASH_SPEC_TMP_PREFIX / "partial_order_file"
    path.touch()
    return path


def init_scheduler():
    partial_order_file = create_partial_order()
    communicate_with_scheduler(f"Init:{partial_order_file}")


def hs_run(cmd_id: int, loop_id: int | None, dest: Literal["output", "capture"]):
    # allowing it be None is conceptually clearer when preprocesing
    # code not in a loop but equivalent to the first iter of a loop
    # if loop_id is None:
    #     loop_id = 0

    # we unroll all loops currently
    loop_id = 0
    msg = f"Wait:{cmd_id}|Loop iters:{loop_id}|Variables file:{get_vars()}"
    res = communicate_with_scheduler(msg)
    _, err_code, _, outfiles = res[:-1].split(" ")

    # TODO: stderr
    with open(os.path.join(outfiles, "1")) as stdout_file:
        stdout = stdout_file.read()

    match dest:
        case "output":
            sys.stdout.write(stdout)
            stdout = None
        case "capture":
            pass
        case _:
            assert_never(dest)

    return CompletedProcess(int(err_code), stdout)
