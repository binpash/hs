import os
import subprocess

##
## Contains global configuration information and later arguments and other global
## things should be moved here.
##

GIT_TOP_CMD = [ 'git', 'rev-parse', '--show-toplevel', '--show-superproject-working-tree']
if 'PASH_SPEC_TOP' in os.environ:
    PASH_SPEC_TOP = os.environ['PASH_SPEC_TOP']
else:
    PASH_SPEC_TOP = subprocess.run(GIT_TOP_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).stdout.rstrip()


## Ensure that PASH_TMP_PREFIX is set by pa.sh
assert(not os.getenv('PASH_SPEC_TMP_PREFIX') is None)
PASH_SPEC_TMP_PREFIX = os.getenv('PASH_SPEC_TMP_PREFIX')

SOCKET_BUF_SIZE = 8192
