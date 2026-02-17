from __future__ import annotations

import logging
import sys

DEBUG = False


def setup_logger(name: str) -> logging.Logger:
    """Setup and configure a logger with consistent formatting.

    Args:
        name: Logger name.
    Returns:
        Configured logger instance.
    """
    format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    stream = sys.stderr
    logger = logging.getLogger(name)

    logger.handlers.clear()

    handler = logging.StreamHandler(stream)
    level = logging.DEBUG if DEBUG else logging.WARNING
    handler.setLevel(level)
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.debug("Logger initiated")

    return logger
