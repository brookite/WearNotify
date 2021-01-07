import importlib
import importlib.util
import os
import subprocess
import sys

from .logger import get_logger

LOGGER = get_logger("import_service")


def load_py_from(path, execute=True):
    name = os.path.basename(path).replace(".py", "")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if execute:
        spec.loader.exec_module(module)
    return module


def pip_install(package):
    print("Satisfacting requirement ({})...".format(package))
    LOGGER.info("Satisfacting requirement ({})...".format(package))
    return subprocess.run(
        [sys.executable, '-m', 'pip', 'install', package],
        stdout=subprocess.PIPE, encoding='utf-8'
    )
