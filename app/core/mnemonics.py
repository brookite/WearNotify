import json
import os.path
from . import configs


def load_global_mnemonics():
    loaded = {}
    fpath = os.path.join(configs.DATA_PATH, "mnemonic.json")
    if os.path.exists(fpath):
        with open(fpath) as fobj:
            loaded = json.load(fobj)
    return loaded
