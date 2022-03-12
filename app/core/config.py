import json

from . import appconfig
import os.path
from .logger import get_logger


LOGGER = get_logger("config")


class Config:
    """
    App configuration object
    """
    def __init__(self):
        LOGGER.info("Creating config object")
        self._dyn = {}  # dynamic, changeable configs
        self._static = {}  # static configs, constant config

    def _put(self, name, value, module="globals", dest="dyn"):
        LOGGER.debug(f"Internal method call: adding {name}={value} to module {module} in {dest}")
        name = name.lower()
        module = module.lower()
        dest = self._static if dest == "static" else self._dyn
        if module not in dest:
            dest[module] = {}
        dest[module][name] = value

    @staticmethod
    def _convert(value):
        try:
            value = json.loads(value)
            return value
        except json.decoder.JSONDecodeError:
            LOGGER.debug(f"Internal method call: failed to parse JSON: {value}")
            pass
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
        return str(value)

    def load_configfile(self):
        LOGGER.info("Loading configs from configuration file")
        path = os.path.join(appconfig.DATA_PATH, "config.txt")
        if not os.path.exists(path):
            LOGGER.info("config.txt wasn't found")
            return
        with open(path, "r") as fobj:
            lines = fobj.read().strip().split("\n")
        for line in lines:
            config = line.split("=")
            if len(config) > 1:
                name = config[0].strip()
                value = config[1].strip()
                self.put(name, self._convert(value), None)

    def load(self, app):
        """
        Load configuration from application units
        """
        modules, extensions, inputservices = app.modules, app.extensions, app.input_services
        LOGGER.info("Loading configs...")
        self._dyn.clear()
        self._static.clear()
        for name in appconfig.ALLOWED_FOR_CHANGE:
            self._put(name, appconfig.__getattribute__(name))
        for name in dir(appconfig):
            if name not in appconfig.ALLOWED_FOR_CHANGE and not name.startswith("_"):
                self._put(name, appconfig.__getattribute__(name), "globals", "static")
        for name in modules:
            module = modules[name]
            cfg = module.configs
            allowed = cfg.get("ALLOWED_FOR_CHANGE")
            for param_name in cfg:
                dest = "dyn"
                if allowed is not None:
                    if param_name not in allowed:
                        dest = "static"
                self._put(param_name, cfg[param_name], name, dest)
        for name in extensions:
            ext = extensions[name].build(None)
            cfg = ext.configs
            allowed = cfg.get("ALLOWED_FOR_CHANGE")
            for param_name in cfg:
                dest = "dyn"
                if allowed is not None:
                    if param_name not in allowed:
                        dest = "static"
                self._put(param_name, cfg[param_name], name, dest)
        for name in inputservices:
            inputservice = inputservices[name]
            cfg = inputservice.configs
            allowed = cfg.get("ALLOWED_FOR_CHANGE")
            for param_name in cfg:
                dest = "dyn"
                if allowed is not None:
                    if param_name not in allowed:
                        dest = "static"
                self._put(param_name, cfg[param_name], name, dest)
        self.load_configfile()

    def route(self, abscfg):
        """
        Find absolute config without access restrictions
        """
        LOGGER.info(f"Rounting configuration: {abscfg}")
        path = self.sep_namespace(abscfg)
        tmp = self._static
        for ns in path:
            if tmp is None:
                break
            else:
                tmp = tmp.get(ns)
        if tmp is not None:
            return tmp
        else:
            LOGGER.debug("Configuration wasn't found in static config")
            tmp = self._dyn
            for ns in path:
                if tmp is None:
                    break
                else:
                    tmp = tmp.get(ns)
            return tmp

    def sep_namespace(self, name):
        name = name.lower().split(".")
        if len(name) == 1:
            return "globals", *name
        else:
            if name[0] in self._dyn or name[0] in self._static:
                return name[0], *name[1:]
            else:
                return "globals", *name

    def absolute_cfg(self, name, module=None):
        LOGGER.info(f"Getting absolute configuration {name} for module={module}")
        if name not in dir(appconfig):
            if name in list(self._dyn.keys()) and name in list(self._static.keys()):
                temp = dict(self._dyn[name])
                temp.update(self._static[name])
                return temp
            elif name in list(self._dyn.keys()):
                return dict(self._dyn[name])
            elif name in list(self._static.keys()):
                dict(self._dyn[name])
        path = self.sep_namespace(name)
        result = self.route(name)
        if isinstance(result, dict):
            result = result.copy()
        if module is not None:
            if path[0] == "globals" or path[0] == module.name.lower():
                return result
        else:
            return result

    def put(self, name, value, module=None):
        LOGGER.info(f"Put new configuration: {name}={value} with module={module}")
        path = self.sep_namespace(name)
        tmp = self._dyn
        if path[0] not in self._dyn:
            tmp = tmp.get("globals")
        else:
            tmp = tmp.get(path[0])
        for item in path[1:-1]:
            if tmp.get(item) is None:
                tmp[item] = {}
            tmp = tmp.get(item)
        if module is not None:
            if path[0] != "globals" and path[0] != module.name.lower():
                return
        tmp[path[-1]] = value

    def relative_cfg(self, name, module):
        LOGGER.info(f"Getting relative configuration for module={module}, name={name}")
        if name.strip() == '':
            return dict(self._dyn[module.name.lower()])
        else:
            modulecfg = ".".join([module.name.lower(), name.lower()])
            globalcfg = ".".join(["globals", name.lower()])
            return self.absolute_cfg(modulecfg) or self.absolute_cfg(globalcfg)

