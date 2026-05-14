import logging
import sys

# Structured format: Timestamp | Level | Module:Function:Line - Message
LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
)

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("execution.log"),  # Persists logs to a file
    ],
)


def get_logger(name):
    return logging.getLogger(name)
