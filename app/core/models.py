from . import import_service
from . import context as ctx
import os
from .logger import get_logger
from .appconfig import DEFAULT_MODULE_CONFIG


LOGGER = get_logger("objects")


def _module_attr(module, attr):
    LOGGER.debug(f"Module attribute getting with name {attr}")
    try:
        if hasattr(module, attr):
            return module.__getattribute__(attr)
        else:
            return None
    except Exception:
        LOGGER.exception("Unknown attribute getting error: ")
        return None


def _set_in_module(module, attr, value):
    module.__setattr__(attr, value)


def _module_call(module, attr, *args, **kwargs):
    LOGGER.debug(f"Module with name calling. Method: {attr}")
    try:
        if hasattr(module, attr):
            return module.__getattribute__(attr)(*args, **kwargs)
        else:
            return None
    except Exception:
        LOGGER.exception("Unknown attribute getting error: ")
        return None


class Module:
    def __init__(self, name, native_module, path,
                 app):
        LOGGER.debug("Creating new module object %s in path: %s" % (name, path))
        self._name = name
        self._native_module = native_module
        self._path = path
        self._app = app
        self._ctx = ctx.ModuleContext(self, app)
        if self._native_module:
            _set_in_module(self._native_module, "ctx", self._ctx)
        self.init()

    @property
    def name(self):
        return self._name

    @property
    def native_module(self):
        return self._native_module

    @property
    def context(self):
        return self._ctx

    def __repr__(self):
        return f"Module <name={self.name};path={self.path}>"

    @property
    def path(self):
        return self._path

    def getattr(self, attribute):
        return self._native_module.__getattr__(attribute)

    def swallow(self, value):
        LOGGER.debug(f"{self._name} swallows: {value}")
        return _module_call(self._native_module, "swallow", value)

    def interrupt_call(self, value):
        LOGGER.debug(f"{self._name} interrupts by: {value}")
        return _module_call(self._native_module, "interrupt_call", value)

    def init(self):
        LOGGER.debug(f"{self._name} is initializing")
        _module_call(self._native_module, "init")

    def exit(self):
        _module_call(self._native_module, "exit")

    def help(self, *args, **kwargs):
        return _module_call(self._native_module, "help", *args, **kwargs)

    @staticmethod
    def standard_params(dct):
        defaults = DEFAULT_MODULE_CONFIG
        for key in defaults:
            if key not in dct:
                dct[key] = defaults[key]
        return dct

    @property
    def configs(self):
        result = _module_attr(self._native_module, "SETTINGS") \
            or _module_attr(self._native_module, "CONFIGS") \
            or _module_attr(self._native_module, "MANIFEST")
        if result is None:
            result = {}
        if "NOCACHE" not in result:
            result["NOCACHE"] = True
        if "ENTER_CONTEXT" not in result:
            result["ENTER_CONTEXT"] = False
        if "QUIT_COMMANDS" not in result:
            result["QUIT_COMMANDS"] = ["quit", "exit", "exit()", "quit()"]
        return result


class DeliveryService:
    def __init__(self, name, native_module, path, app):
        LOGGER.debug(f"Creating delivery service with name {name}")
        self._name = name
        self._native_module = native_module
        self._path = path
        self._ctx = ctx.DeliveryServiceContext(self, native_module, app)
        if self._native_module:
            _set_in_module(self._native_module, "ctx", self._ctx)
        self.init()

    @property
    def configs(self):
        result = _module_attr(self._native_module, "SETTINGS") \
                 or _module_attr(self._native_module, "CONFIGS") \
                 or _module_attr(self._native_module, "MANIFEST")
        if result is None:
            result = {}
        return result

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    def exit(self):
        return _module_call(self._native_module, "exit")

    def init(self):
        return _module_call(self._native_module, "init")

    def help(self, *args):
        LOGGER.debug(f"Returning help message")
        _module_call(self._native_module, "help", *args)

    def begin(self):
        _module_call(self._native_module, "begin")

    def finished(self, count):
        _module_call(self._native_module, "finished", count)

    def send(self, packet):
        try:
            if hasattr(self._native_module, "send"):
                self._native_module.__getattribute__("send")(packet)
            else:
                LOGGER.error(f"Failed to send packet: send method wasn't found. Name: {self._name}")
        except Exception:
            LOGGER.exception(f"Delivery service with name {self._name} exception: ")

    @property
    def native_module(self):
        return self._native_module


class InputService:
    def __init__(self, name, native_module, app, path):
        LOGGER.debug(f"Creating input service with name {name}")
        self._name = name
        self._native_module = native_module
        self._app = app
        self._path = os.path.dirname(path)
        self._ctx = ctx.InputServiceContext(self, app)
        if self._native_module:
            _set_in_module(self._native_module, "ctx", self._ctx)
        self.init()

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def native_module(self):
        return self._native_module

    @property
    def configs(self):
        result = _module_attr(self._native_module, "SETTINGS") \
                 or _module_attr(self._native_module, "CONFIGS") \
                 or _module_attr(self._native_module, "MANIFEST")
        if result is None:
            result = {}
        return result

    def help(self, *args):
        LOGGER.debug(f"Returning help message")
        _module_call(self._native_module, "help", *args)

    def exit(self):
        return _module_call(self._native_module, "exit")

    def init(self):
        return _module_call(self._native_module, "init")

    def raw_input(self, *args):
        return _module_call(self._native_module, "raw_input", *args)

    def user_action(self, *args):
        return _module_call(self._native_module, "user_action", *args)


class ExtensionInfo:
    def __init__(self, name, path, app):
        LOGGER.debug(f"Creating extension info with name {name}")
        self._name = name
        self._path = path
        self._app = app

    def __repr__(self):
        return f"ExtensionInfo <name={self._name};path={self._path}>"

    def build(self, module):
        path = os.path.join(self._path, "__init__.py")
        native_module = import_service.load_py_from(path)
        return Extension(self._name, module, native_module, self._path,
                         self._app)


class Extension:
    def __init__(self, name, module_src,
                 native_module, path, app):
        if module_src:
            LOGGER.debug(f"Creating extension with name {name} for {module_src.name}")
        else:
            LOGGER.debug(f"Creating extension with name {name} without paired module")
        self._name = name
        self._native_module = native_module
        self._path = path
        self._app = app
        self._ctx = ctx.ExtensionContext(self, module_src, app)
        if self._native_module:
            if hasattr(self._native_module, "put_ctx"):
                self.put_ctx(self._ctx)
            else:
                self._native_module.ctx = self._ctx

    @property
    def native_module(self):
        return self._native_module

    @property
    def name(self):
        return self._name

    @property
    def context(self):
        return self._ctx

    @property
    def path(self):
        return self._path

    def __repr__(self):
        return f"Extension <name={self.name};path={self.path}>"

    @property
    def configs(self):
        result = _module_attr(self._native_module, "SETTINGS") \
                 or _module_attr(self._native_module, "CONFIGS") \
                 or _module_attr(self._native_module, "MANIFEST")
        if result is None:
            result = {}
        return result

    def __getattr__(self, attr):
        if attr in dir(super().__getattribute__("_native_module")):
            return super().__getattribute__("_native_module").__getattribute__(attr)
        else:
            LOGGER.warning(f"Extension attribute '{attr}' wasn't found")
