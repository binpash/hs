import config
import os
import tempfile

def ptempfile():
    fd, name = tempfile.mkstemp(dir=config.PASH_SPEC_TMP_PREFIX)
    ## TODO: Get a name without opening the fd too if possible
    os.close(fd)
    return name
