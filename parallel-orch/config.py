import os
import subprocess
import sys
import logging


## TODO: Figure out how logging here plays out together with the log() in PaSh

## Setup TRACE level for logging
level = logging.TRACE = logging.DEBUG - 5

def log_logger(self, message, *args, **kwargs):
    if self.isEnabledFor(level):
        self._log(level, message, args, **kwargs)
logging.getLoggerClass().trace = log_logger

def log_root(msg, *args, **kwargs):
    logging.log(level, msg, *args, **kwargs)
logging.addLevelName(level, "TRACE")
logging.trace = log_root

if 'LOG_DIR' in os.environ:
    LOG_DIR = os.environ['PASH_SPEC_TOP']
else:
    PASH_SPEC_TOP = sys.stdout

# Format logging
# ref: https://docs.python.org/3/library/logging.html#formatter-objects
logging.basicConfig(format="%(levelname)s|%(asctime)s|%(message)s", 
                    filename=f"{os.path.join(LOG_DIR, 'log.txt')}", 
                    filemode="w")

GIT_TOP_CMD = [ 'git', 'rev-parse', '--show-toplevel', '--show-superproject-working-tree']
if 'PASH_SPEC_TOP' in os.environ:
    PASH_SPEC_TOP = os.environ['PASH_SPEC_TOP']
else:
    PASH_SPEC_TOP = subprocess.run(GIT_TOP_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).stdout.rstrip()


## Ensure that PASH_TMP_PREFIX is set by pa.sh
assert(not os.getenv('PASH_SPEC_TMP_PREFIX') is None)
PASH_SPEC_TMP_PREFIX = os.getenv('PASH_SPEC_TMP_PREFIX')

SOCKET_BUF_SIZE = 8192

SCHEDULER_SOCKET = os.getenv("PASH_SPEC_SCHEDULER_SOCKET")
