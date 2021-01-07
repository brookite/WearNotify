from . import import_service
from . import context as ctx
import os
from .logger import get_logger
from .configs import DEFAULT_MODULE_CONFIG


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
        _module_call(self._native_module, "init", self._ctx)

    @property
    def name(self):
        return self._name

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
        return _module_call(self._native_module, "swallow", self._ctx, value)

    def init(self):
        LOGGER.debug(f"{self._name} is initializing")
        _module_call(self._native_module, "init", self._ctx)

    def standard_params(self, dct):
        defaults = DEFAULT_MODULE_CONFIG
        for key in defaults:
            if key not in dct:
                dct[key] = defaults[key]
        return dct

    @property
    def configs(self):
        result = _module_attr(self._native_module, "SETTINGS") \
            or _module_attr(self._native_module, "CONFIGS")
        if result is None:
            result = {}
        if "NOCACHE" not in result:
            result["NOCACHE"] = False
        if "ENTER_CONTEXT" not in result:
            result["ENTER_CONTEXT"] = False
        if "QUIT_COMMANDS" not in result:
            result["QUIT_COMMANDS"] = ["quit", "exit", "exit()", "quit()"]
        return result


class DeliveryService:
    def __init__(self, name, native_module):
        LOGGER.debug(f"Creating delivery service with name {name}")
        self._name = name
        self._native_module = native_module
        self._ctx = ctx.DeliveryServiceContext(native_module)
        _module_call(self._native_module, "init", self._ctx)

    @property
    def name(self):
        return self._name

    def begin(self):
        _module_call(self._native_module, "begin", self._ctx)

    def finished(self, count):
        _module_call(self._native_module, "finished", self._ctx, count)

    def send(self, packet):
        try:
            if hasattr(self._native_module, "send"):
                self._native_module.__getattribute__("send")(self._ctx, packet)
            else:
                LOGGER.error(f"Failed to send packet: send method wasn't found. Name: {self._name}")
        except Exception:
            LOGGER.exception(f"Delivery service with name {self._name} exception: ")


class InputService:
    def __init__(self, name, native_module, app):
        LOGGER.debug(f"Creating input service with name {name}")
        self._name = name
        self._native_module = native_module
        self._app = app
        self._ctx = ctx.InputServiceContext(native_module, app)
        self.init()

    @property
    def name(self):
        return self._name

    @property
    def configs(self):
        result = _module_attr(self._native_module, "SETTINGS") \
            or _module_attr(self._native_module, "CONFIGS")
        if result is None:
            result = {}
        return result

    def init(self):
        return _module_call(self._native_module, "init", self._ctx)

    def raw_input(self, *args):
        return _module_call(self._native_module, "raw_input", self._ctx, *args)

    def user_action(self, *args):
        return _module_call(self._native_module, "user_action", self._ctx, *args)


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
        if hasattr(self._native_module, "put_ctx"):
            self.put_ctx(self._ctx)
        else:
            self._native_module.ctx = self._ctx

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
            or _module_attr(self._native_module, "CONFIGS")
        if result is None:
            result = {}
        return result

    def __getattr__(self, attr):
        if attr in dir(super().__getattribute__("_native_module")):
            return super().__getattribute__("_native_module").__getattribute__(attr)
        else:
            LOGGER.warning(f"Extension attribute '{attr}' wasn't found")


class ERRBSocket:
    def __init__(self, alias, port, native_module):
        LOGGER.info(f"Created ERRB socket with alias={alias} and port={port}")
        self._alias = alias
        self._native_module = native_module
        self._port = port

    def __repr__(self):
        return f"ERRBSocket(alias={self._alias}, port={self._port})"

    @property
    def alias(self):
        return self._alias

    @property
    def port(self):
        return self._port

    def make_pair(self, *args):
        s, r = _module_call(self._native_module, "make_pair", *args)
        return ERRBSender(s), ERRBReciever(r)

    def is_available(self):
        return _module_call(self._native_module, "is_available")


class ERRBReciever:
    def __init__(self, native_module):
        self._native_module = native_module

    def recieve(self, buf=None):
        return _module_call(self._native_module, "recieve", buf=None)

    def flush(self):
        return _module_call(self._native_module, "flush")

    @property
    def port_no(self):
        return _module_attr(self._native_module, "port_no")

    @property
    def source(self):
        return _module_attr(self._native_module, "source")


class ERRBSender:
    def __init__(self, native_module):
        self._native_module = native_module

    def send(self, data: bytes):
        if isinstance(data, str):
            data = data.encode("utf-8")
        return _module_call(self._native_module, "send", data)

    def flush(self):
        return _module_call(self._native_module, "flush")

    @property
    def port_no(self):
        return _module_attr(self._native_module, "port_no")

    @property
    def source(self):
        return _module_attr(self._native_module, "source")
