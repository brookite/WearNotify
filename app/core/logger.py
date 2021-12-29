import logging
import logging.config
import os
from .appconfig import LOGGER_CONFIG, DATA_PATH


LOG_PATH = os.path.join(DATA_PATH, "cache", "logs")
os.makedirs(LOG_PATH, exist_ok=True)
logging.config.dictConfig(LOGGER_CONFIG)


def get_logger(name=None):
    return logging.getLogger(name)
