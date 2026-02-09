import argparse
import runpy
from pathlib import Path

from python_hs import logging_


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Input file to speculate", type=Path)
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main():
    args = parse_args()
    logging_.DEBUG = args.debug

    from python_hs.constants import PASH_SPEC_TMP_PREFIX
    from python_hs.preprocessor import preprocess_file
    from python_hs.runtime import init_scheduler

    assert PASH_SPEC_TMP_PREFIX is not None

    preprocessed_file = preprocess_file(PASH_SPEC_TMP_PREFIX, args.file)
    init_scheduler()
    runpy.run_path(str(preprocessed_file))


if __name__ == "__main__":
    main()
