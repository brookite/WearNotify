from .configs import APP_VERSION, APP_VERSION_NAME
import os
import json
from . import cache
from .import_service import load_py_from
from . import errb
from . import pipe
from .logger import get_logger

LOGGER = get_logger("ctx")


class ModuleContext:
    def __init__(self, module, app):
        LOGGER.debug("Created context for module: %s" % module.name)
        self._module = module
        if app:
            self._extensions = app.extensions
            self._cfg = app.config
            self._runtimecache = app.runtime_cache
            self._errb = app.errb
            self._app = app
            self._mnems = self._app.mnems
        else:
            self._extensions = None
            self._cfg = None
            self._runtimecache = None
            self._errb = None
            self._app = app
            self._mnems = None
        self._builded_ext = {}
        self._logger = get_logger(f"{module.name}")
        self._custom_mnems = {}
        self._load_mnems()

    def _load_mnems(self):
        if not self._module.path:
            return
        fpath = os.path.join(self._module.path, "mnemonic.json")
        if os.path.exists(fpath):
            with open(fpath) as fobj:
                loaded = json.load(fobj)
                for mnemonic in loaded:
                    self._custom_mnems[mnemonic] = loaded[mnemonic]

    def get_mnenmoic(self, mnem, onlycustom=False):
        if mnem in self._mnems and not onlycustom:
            return self._mnems[mnem]
        elif mnem in self._custom_mnems:
            return self._custom_mnems[mnem]
        else:
            return None

    def fork(self):
        return self._app

    @property
    def mnemonics(self):
        return self._mnems, self._custom_mnems

    def clear_mnemonics(self):
        self._custom_mnems.clear()

    def is_mnemonic(self, mnem):
        return mnem in self._mnems or mnem in self._mnems

    def set_mnemonic(self, mnem: int, value):
        assert isinstance(mnem, int)
        self._custom_mnems[mnem] = value

    @property
    def app_version(self):
        return APP_VERSION_NAME

    def pipe(self, name):
        return pipe.Pipe(name, self._app)

    @property
    def version_array(self):
        return APP_VERSION

    def internal_path(self, path=None):
        LOGGER.info("Resolving internal path: %s" % path)
        if path is None:
            return self._module.path
        else:
            return os.path.join(self._module.path, path)

    def import_submodule(self, module_name):
        LOGGER.info("Importing submodule %s" % module_name)
        # module name without py
        module_name = module_name.replace(".py", "") + ".py"
        module = load_py_from(os.path.join(self._module.path, module_name))
        return module

    def extension(self, name):
        LOGGER.info("Using extension %s" % name)
        if name not in self._builded_ext:
            if name not in self._extensions:
                LOGGER.error(f"Extension {name} wasn't found")
                return None
            self._builded_ext[name] = self._extensions[name].build(self._module)
        return self._builded_ext[name]

    def send_errb(self, port, data: bytes):
        LOGGER.info("Sending to ERRB port %s" % port)
        sender, _ = errb.port_handler(port, self._errb)
        if sender:
            errb.post_sender(sender, data)

    def logger(self):
        return self._logger

    def recieve_errb(self, port):
        LOGGER.info("Recieveing from ERRB port %s" % port)
        _, reciever = errb.port_handler(port, self._errb)
        if reciever:
            return errb.recieve(reciever)

    def put_cache(self, filename, data):
        LOGGER.info("Adding new cache %s" % filename)
        if isinstance(data, str):
            data = data.encode("utf-8")
        return cache.put_module_cache(self._module.name, filename, data)

    def put_tempdata(self, name, data):
        self._runtimecache.put(name, data)

    def get_tempdata(self, name):
        return self._runtimecache.get(name)

    def is_cached_tempdata(self, name):
        return self._runtimecache.is_cached(name)

    def remove_tempdata(self, name):
        self._runtimecache.remove(name)

    def get_cached(self, filename):
        LOGGER.info("Getting cache %s" % filename)
        return cache.get_module_cached(self._module.name, filename)

    def get_cache_path(self, filename=None):
        pth = cache.module_path(self._module.name)
        if filename:
            return os.path.join(pth, filename)
        return pth

    def is_cached(self, filename):
        return cache.is_module_cached(self._module.name, filename)

    def remove_cache(self, filename):
        LOGGER.info("Removing module cache: %s" % filename)
        cache.remove_module_cache(self._module.name, filename)

    def import_submodule_by_path(self, path, change_cwd=False):
        LOGGER.info("Importing submodule: %s" % path)
        prevcwd = None
        if change_cwd:
            prevcwd = os.getcwd()
            os.chdir(self._module.path)
        module = load_py_from(os.path.abspath(path))
        if change_cwd:
            os.chdir(prevcwd)
        return module

    def check_errb(self, port):
        LOGGER.info("Checking port availability: %s" % port)
        s, r = errb.port_handler(port, self._errb)
        return s is not None or r is not None

    def absolute_cfg(self, name):
        return self._cfg.absolute_cfg(name, module=self._module)

    def relative_cfg(self, name):
        return self._cfg.relative_cfg(name, self._module)

    def put_config(self, name, value):
        return self._cfg.put(name, value, module=self._module)


class ExtensionContext:
    def __init__(self, extension, module, app):
        LOGGER.debug("Creating extension context %s" % extension.name)
        self._extension = extension
        self._extensions = app.extensions
        self._app = app
        self._errb = app.errb
        self._cfg = app.config
        self._runtimecache = app.runtime_cache
        self._builded_ext = {}
        self._module = module
        if module:
            self._logger = get_logger(f"{extension.name}:{module.name}")
        else:
            self._logger = get_logger(f"{extension.name}")

    @property
    def module(self):
        return self._module

    def pipe(self, name):
        return pipe.Pipe(name, self._app)

    @property
    def app_version(self):
        return APP_VERSION_NAME

    @property
    def version_array(self):
        return APP_VERSION

    def extension(self, name):
        LOGGER.info("Using extension %s" % name)
        if name not in self._builded_ext:
            if name not in self._extensions:
                LOGGER.error(f"Extension {name} wasn't found")
                return None
            self._builded_ext[name] = self._extensions[name].build(None)
        return self._builded_ext[name]

    def logger(self):
        return self._logger

    def internal_path(self, path=None):
        LOGGER.info("Resolving internal path: %s" % path)
        if path is None:
            return self._extension.path
        else:
            return os.path.join(self._extension.path, path)

    def module_path(self, path=None):
        LOGGER.info("Resolving module path: %s" % path)
        if path is None:
            return self._extension.path
        else:
            return os.path.join(self._extension.path, path)

    def import_submodule_by_path(self, path, change_cwd=False):
        LOGGER.info("Importing submodule: %s" % path)
        prevcwd = None
        if change_cwd:
            prevcwd = os.getcwd()
            os.chdir(self._module.path)
        module = load_py_from(os.path.abspath(path))
        if change_cwd:
            os.chdir(prevcwd)
        return module

    def import_submodule(self, module_name):
        LOGGER.info("Importing submodule: %s" % module_name)
        # module name without py
        module_name = module_name.replace(".py", "") + ".py"
        module = load_py_from(os.path.join(self._extension.path, module_name))
        return module

    def send_errb(self, port, data: bytes):
        LOGGER.info("Sending ERRB port %s" % port)
        sender, _ = errb.port_handler(port, self._errb)
        if sender:
            errb.post_sender(sender, data)

    def recieve_errb(self, port):
        LOGGER.info("Recieveing from ERRB port %s" % port)
        _, reciever = errb.port_handler(port, self._errb)
        if reciever:
            return errb.recieve(reciever)

    def check_errb(self, port):
        LOGGER.info("Checking port availability: %s" % port)
        s, r = errb.port_handler(port, self._errb)
        return s is not None or r is not None

    def put_cache(self, filename, data):
        LOGGER.info("Adding new cache %s" % filename)
        if isinstance(data, str):
            data = data.encode("utf-8")
        return cache.put_module_cache(self._extension.name, filename, data)

    def get_cached(self, filename):
        LOGGER.info("Getting cache %s" % filename)
        return cache.get_module_cached(self._extension.name, filename)

    def get_cache_path(self, filename=None):
        pth = cache.module_path(self._extension.name)
        if filename:
            return os.path.join(pth, filename)
        return pth

    def is_cached(self, filename):
        return cache.is_module_cached(self._extension.name, filename)

    def remove_cache(self, filename):
        LOGGER.info("Removing module cache: %s" % filename)
        cache.remove_module_cache(self._extension.name, filename)

    def put_tempdata(self, name, data):
        self._runtimecache.put(name, data)

    def get_tempdata(self, name):
        return self._runtimecache.get(name)

    def is_cached_tempdata(self, name):
        return self._runtimecache.is_cached(name)

    def remove_tempdata(self, name):
        return self._runtimecache.remove(name)

    def absolute_cfg(self, name):
        return self._cfg.absolute_cfg(name, module=self._extension)

    def relative_cfg(self, name):
        return self._cfg.relative_cfg(name, self._extension)

    def put_config(self, name, value):
        return self._cfg.put(name, value, module=self._extension)


class InputContext:
    def __init__(self, hook=None):
        LOGGER.debug("Created input context")
        self._registry = None
        self._module = None
        if callable(hook):
            self._hook = hook
        else:
            self._hook = None

    def sethook(self, hook):
        if callable(hook):
            self._hook = hook

    def hook(self, prev, new, prevmod, newmod):
        if self._hook:
            self._hook(prev, new, prevmod, newmod)

    def get(self):
        LOGGER.debug("Getting context, context is %s" % self._registry)
        return self._registry

    @property
    def module(self):
        return self._module

    def set(self, value, module):
        LOGGER.debug("Setting context, new context is %s" % value)
        self.hook(self._registry, value, self._module, module)
        self._registry = value
        self._module = module

    def null(self):
        LOGGER.debug("Clearing context")
        self._registry = None
        self._module = None


class InputServiceContext:
    def __init__(self, nativemodule, app):
        self._nativemodule = nativemodule
        self._app = app
        self._mnems = self._app.mnems
        self._cfg = app.config
        self._custom_mnems = {}
        self._logger = get_logger(f"{nativemodule.__name__}")

    def fork(self):
        return self._app

    def get_mnenmoic(self, mnem, onlycustom=False):
        if mnem in self._mnems and not onlycustom:
            return self._mnems[mnem]
        elif mnem in self._custom_mnems:
            return self._custom_mnems[mnem]
        else:
            return None

    @property
    def app_version(self):
        return APP_VERSION_NAME

    def pipe(self, name):
        return pipe.Pipe(name, self._app)

    def logger(self):
        return self._logger

    @property
    def version_array(self):
        return APP_VERSION

    def is_mnemonic(self, mnem):
        return mnem in self._mnems or mnem in self._mnems

    def set_mnemonic(self, mnem: int, value):
        assert isinstance(mnem, int)
        self._custom_mnems[mnem] = value

    @property
    def mnemonics(self):
        return self._mnems, self._custom_mnems

    def clear_mnemonics(self):
        self._custom_mnems.clear()

    def absolute_cfg(self, name):
        return self._cfg.absolute_cfg(name, module=self._nativemodule)

    def relative_cfg(self, name):
        return self._cfg.relative_cfg(name, self._nativemodule)

    def put_config(self, name, value):
        return self._cfg.put(name, value, module=self._nativemodule)


class DeliveryServiceContext:
    def __init__(self, nativemodule):
        self._nativemodule = nativemodule
