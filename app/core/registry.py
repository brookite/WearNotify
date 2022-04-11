from .appconfig import DATA_PATH, AUTO_INITIALIZING_STDMODULES
from .storage import read_json
from .stdmodules import load_std_registry, \
    is_std_registry, get_stdmodule, init_stdmodules
import os
from .logger import get_logger


LOGGER = get_logger("registry")


SPECIAL_SYMBOLS = [':', ' ', '=']


def split(request, registries):
    '''
    Split into registry and request for further request handling in target module
    '''
    special = list(filter(lambda x: len(x) > 3 or x.isalpha(), registries.keys()))
    if len(request) >= 3 and request.startswith("0"):
        reg = request[:3]
        req = request[4:]
        return reg, req
    elif request.startswith(' '):
        return "default", request[1:]
    elif len(special) > 0:
        for symbol in SPECIAL_SYMBOLS:
            for specreg in special:
                if request.startswith(specreg + symbol):
                    reg = request[:len(specreg + symbol) - 1]
                    req = request[len(specreg + symbol):]
                    return reg, req
        if request in special:
            return request, ""
        else:
            return "default", request
    else:
        return "default", request


def load_predefined_registries(app):
    '''
    Loads registries as module name and initializes stdmodules if required
    '''
    for name in app.modules:
        if name not in app.registries:
            app.registries[name] = name
    if AUTO_INITIALIZING_STDMODULES:
        init_stdmodules(app)
    

def get_registry():
    """
    Loads registries to app
    """
    LOGGER.debug("Getting registries")
    registry = os.path.join(DATA_PATH, "registry.json")
    registry = read_json(registry)
    if "default" not in registry:
        registry["default"] = "000"
    load_std_registry(registry)
    return registry


def route(registry, modules, registries, app):
    '''
    Routing to module by registry
    '''
    LOGGER.debug("Rounting registry...")
    if is_std_registry(registry):
        return get_stdmodule(registry, app)
    if registry.lower() == "default":
        registry = registries["default"]
        if registry not in registries:
            LOGGER.error("Default registry wasn't found")
            return None
    if registries[registry] in modules:
        return modules[registries[registry]]
    elif registries[registry].replace(".py", "") in modules:
        return modules[registries[registry].replace(".py", "")]
    elif is_std_registry(registries[registry]):
        return get_stdmodule(registries[registry])
    else:
        LOGGER.error(f"Registry {registry} wasn't found in modules")
        return None
