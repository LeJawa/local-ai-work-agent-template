import sys
from loguru import logger

logger.remove()

def terminal_format(record):
    if record["level"].name == "INFO":
        return "{message}\n"
    elif record["level"].name == "SUCCESS":
        return "<lg>{message}</lg>\n"
    elif record["level"].name == "WARNING":
        return "<y>{message}</y>\n"
    elif record["level"].name == "ERROR" or record["level"].name == "CRITICAL":
        return "<r>{level} | {name}:{function}:{line} | {message}</r>\n{exception}"
    return "{level} | {message}\n"

logger.add(sys.stderr, level="INFO", format=terminal_format)

logger.add("logs/{time}.log", level="TRACE")
