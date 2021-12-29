import json
import os.path
from . import appconfig


def load_global_mnemonics():
    loaded = {}
    fpath = os.path.join(appconfig.DATA_PATH, "mnemonic.json")
    if os.path.exists(fpath):
        with open(fpath) as fobj:
            loaded = json.load(fobj)
    return loaded
