import dataclasses
import functools
import os
import random
import socket
import string
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal, TypeAlias

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
    stdout: str | bytes | None


def get_vars(spec_dir: Path) -> str | None:
    bash_vars = str(spec_dir / f"variables_{random_str()}")
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


communicate_with_scheduler = (
    functools.partial(
        communicate_socket, "PaSh-Spec-scheduler", PASH_SPEC_SCHEDULER_SOCKET
    )
    if PASH_SPEC_SCHEDULER_SOCKET is not None
    else None
)


def create_partial_order(spec_dir: Path) -> Path:
    path = spec_dir / "partial_order_file"
    path.touch()
    return path


def init_scheduler() -> None:
    if PASH_SPEC_TMP_PREFIX is None or communicate_with_scheduler is None:
        raise RuntimeError("Pash is not initialized!")
    partial_order_file = create_partial_order(PASH_SPEC_TMP_PREFIX)
    communicate_with_scheduler(f"Init:{partial_order_file}")


IO: TypeAlias = Any


def hs_run(
    cmd_id: int,
    loop_id: int | None,
    dest: Literal["output", "capture"] | IO,
    check: bool,
    text: bool,
):
    # allowing it be None is conceptually clearer when preprocesing
    # code not in a loop but equivalent to the first iter of a loop
    # if loop_id is None:
    #     loop_id = 0

    # we unroll all loops currently
    assert PASH_SPEC_TMP_PREFIX is not None and communicate_with_scheduler is not None
    loop_id = 0
    msg = f"Wait:{cmd_id}|Loop iters:{loop_id}|Variables file:{get_vars(PASH_SPEC_TMP_PREFIX)}"
    res = communicate_with_scheduler(msg)

    type_, _ = res.split(":", maxsplit=1)
    if type_ == "UNSAFE":
        return subprocess.run(
            ["bash", PASH_SPEC_TMP_PREFIX / "partial_order" / str(cmd_id)], check=check
        )
    elif type_ == "OK":
        _, err_code, _, outfiles = res[:-1].split(" ")

        mode = "r" if text else "rb"

        # TODO: stderr
        with open(os.path.join(outfiles, "1"), mode) as stdout_file:
            stdout = stdout_file.read()

        match dest:
            case "output":
                sys.stdout.write(stdout)
                stdout = None
            case "capture":
                pass
            case file:
                # inefficient
                file.write(stdout)
                stdout = None

        if check and err_code != 0:
            # TODO: Better error messages.
            # The last argument is supposed to be the command The last argument is supposed to be the command.
            raise subprocess.CalledProcessError(err_code, "hs_run")

        return CompletedProcess(int(err_code), stdout)
    else:
        raise NotImplementedError()
