import os
from datetime import datetime
from .appinfo import *


def format_filename():
    dt = datetime.now()
    return dt.strftime("log_%d%m%Y_%H%M%S.log")


def check_workdir():
    if __file__:
        parent = os.path.dirname(os.path.dirname(__file__))
        if not os.path.samefile(parent, os.getcwd()):
            os.chdir(parent)


check_workdir()

PIPELINE = {
    # DON'T DELETE ANY KEYS IN THIS DICT. ELSE PIPELINE WON'T BE CREATED
    "start": None,
    "stop": None,
    "step": -1,
    "max_packet_length": 126,
    "allow_part_number": False,  # it may cause errors in symbol limit type with very huge packets count
    "limit_type": "symbol",
    "clear_text": False,  # it's slows app
    "packets_count": 16,
    "packet_delay": 1250,
    "initial_delay": 800,
    "special_delay": 0,
    "after_limit": "user_action"
    # or finish or initial_delay or special_delay
}
DEFAULT_MODULE_CONFIG = {
    "NOCACHE": False,
    "ENTER_CONTEXT": False,
    "QUIT_COMMANDS": ["quit", "exit", "exit()", "quit()"]
}

APP_PATH = os.path.abspath("./")
DATA_PATH = os.path.abspath("../data")
DEFAULT_ENCODING = "utf-8"
DEFAULT_MNEMONIC_MODE = 0x1
ISOLATED_MODULE = False
MAX_REQUEST_CACHE_SIZE = 262144
DEFAULT_INPUT_SERVICE = "default"
RESET_PIPECONFIG = False
ONLY_STRING_IO_DATA = False
PIPELINE_ENGINE = "DANDELION"
LOG_FILE = os.path.join(DATA_PATH, "cache", "logs", format_filename())

LOGGER_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'std_format': {
            'format': '[{asctime}:{levelname}] <{module}:{funcName}:{lineno}> - {name}: {message}',
            'style': '{'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'WARNING',
            'formatter': 'std_format'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE,
            'level': 'DEBUG',
            'formatter': 'std_format',
            'encoding': 'utf-8',
            'maxBytes': MAX_REQUEST_CACHE_SIZE,
            'backupCount': 5
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
        }
    },
}

ALLOWED_FOR_CHANGE = [
    "DEFAULT_ENCODING",
    "MAX_REQUEST_CACHE_SIZE",
    "RESET_PIPECONFIG",
    "PIPELINE",
    "PIPELINE_ENGINE"
]
