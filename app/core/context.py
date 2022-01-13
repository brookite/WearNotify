from .appconfig import APP_VERSION, APP_VERSION_NAME, API_VERSION
import os
import json
from . import cache
from .import_service import load_py_from
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
            self._app = app
            self._mnems = self._app.mnems
        else:
            self._extensions = None
            self._cfg = None
            self._runtimecache = None
            self._app = app
            self._mnems = None
        self._builded_ext = {}
        self._user_action = None
        self._logger = get_logger(f"{module.name}")
        self._custom_mnems = {}
        self._load_mnems()

    @property
    def current_user_action(self):
        return self._app._current_user_action

    @current_user_action.setter
    def current_user_action(self, value):
        if callable(value):
            self._user_action = value

    def _load_mnems(self):
        if not self._module.path:
            return
        fpath = os.path.join(self._module.path, "mnemonic.json")
        if os.path.exists(fpath):
            with open(fpath) as fobj:
                loaded = json.load(fobj)
                for mnemonic in loaded:
                    self._custom_mnems[mnemonic] = loaded[mnemonic]

    def get_mnemonic(self, mnem, onlycustom=False):
        if mnem in self._mnems and not onlycustom:
            return self._mnems[mnem]
        elif mnem in self._custom_mnems:
            return self._custom_mnems[mnem]
        else:
            return None

    def fork(self):
        return self._app

    def set_cleanable_cache(self, state=True):
        if not state:
            cache.put_allowed_cache(self._module.name)
        else:
            cache.remove_allowed_cache(self._module.name)

    @property
    def mnemonics(self):
        return self._mnems, self._custom_mnems

    def clear_mnemonics(self):
        self._custom_mnems.clear()

    @staticmethod
    def get_shared_cache():
        return cache.get_shared_cache()

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

    @property
    def api_version(self):
        return API_VERSION

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

    def logger(self):
        return self._logger

    def put_cache(self, filename, data):
        LOGGER.info("Adding new cache %s" % filename)
        if isinstance(data, str):
            data = data.encode("utf-8")
        return cache.put_module_cache(self._module.name, filename, data)

    def put_tempdata(self, name, data):
        self._runtimecache.put(name, data, module=self._module)

    def get_tempdata(self, name):
        return self._runtimecache.get(name, module=self._module)

    def is_cached_tempdata(self, name):
        return self._runtimecache.is_cached(name)

    def remove_tempdata(self, name):
        self._runtimecache.remove(name, module=self._module)

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

    def import_submodule_by_path(self, path):
        LOGGER.info("Importing submodule: %s" % path)
        prevcwd = os.getcwd()
        os.chdir(self._module.path)
        module = load_py_from(os.path.abspath(path))
        os.chdir(prevcwd)
        return module

    def absolute_cfg(self, name):
        return self._cfg.absolute_cfg(name, module=self._module)

    def relative_cfg(self, name):
        return self._cfg.relative_cfg(name, self._module)

    def put_config(self, name, value):
        return self._cfg.put(name, value, module=self._module)

    def chmnemmod(self, mode):
        if self._app:
            self._app.chmnemmod(pref=mode)

    def quit(self):
        self._app.input_context.null()

    def mnem_manipulator(self):
        if "mnemonic_server" in self._app.input_services:
            module = self._app.input_services["mnemonic_server"].native_module
            if hasattr(module, "manip"):
                if module.manip:
                    return module.manip


class ExtensionContext:
    def __init__(self, extension, module, app):
        LOGGER.debug("Creating extension context %s" % extension.name)
        self._extension = extension
        self._extensions = app.extensions
        self._app = app
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

    def set_cleanable_cache(self, state=True):
        if not state:
            cache.put_allowed_cache(self._extension.name)
        else:
            cache.remove_allowed_cache(self._extension.name)

    @property
    def app_version(self):
        return APP_VERSION_NAME

    @property
    def api_version(self):
        return API_VERSION

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

    def import_submodule_by_path(self, path):
        LOGGER.info("Importing submodule: %s" % path)
        prevcwd = os.getcwd()
        os.chdir(self._module.path)
        module = load_py_from(os.path.abspath(path))
        os.chdir(prevcwd)
        return module

    def import_submodule(self, module_name):
        LOGGER.info("Importing submodule: %s" % module_name)
        # module name without py
        module_name = module_name.replace(".py", "") + ".py"
        module = load_py_from(os.path.join(self._extension.path, module_name))
        return module

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
        self._runtimecache.set(name, data, module=self.module)

    def get_tempdata(self, name):
        return self._runtimecache.get(name, module=self.module)

    def is_cached_tempdata(self, name):
        return self._runtimecache.is_cached(name)

    def remove_tempdata(self, name):
        return self._runtimecache.remove(name, module=self.module)

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
        if self._module:
            if self._module.configs["ENTER_CONTEXT"]:
                self._module.exit()
        self.hook(self._registry, value, self._module, module)
        self._registry = value
        self._module = module

    def null(self):
        LOGGER.debug("Clearing context")
        if self._module:
            if self._module.configs["ENTER_CONTEXT"]:
                self._module.exit()
        self.hook(self._registry, None, self._module, None)
        self._registry = None
        self._module = None


class InputServiceContext:
    def __init__(self, inputservice, app):
        self._inputservice = inputservice
        self._nativemodule = inputservice.native_module
        self._runtimecache = app.runtime_cache
        self._extensions = app.extensions
        self._builded_ext = {}
        self._app = app
        self._mnems = self._app.mnems
        self._cfg = app.config
        self._custom_mnems = {}
        self._logger = get_logger(f"{self._nativemodule.__name__}")

    def set_cleanable_cache(self, state=True):
        if not state:
            cache.put_allowed_cache(self._inputservice.name)
        else:
            cache.remove_allowed_cache(self._inputservice.name)

    def fork(self):
        return self._app

    def extension(self, name):
        LOGGER.info("Using extension %s" % name)
        if name not in self._builded_ext:
            if name not in self._extensions:
                LOGGER.error(f"Extension {name} wasn't found")
                return None
            self._builded_ext[name] = self._extensions[name].build(self._inputservice)
        return self._builded_ext[name]

    def get_mnemonic(self, mnem, onlycustom=False):
        if mnem in self._mnems and not onlycustom:
            return self._mnems[mnem]
        elif mnem in self._custom_mnems:
            return self._custom_mnems[mnem]
        else:
            return None

    @staticmethod
    def get_shared_cache():
        return cache.get_shared_cache()

    @property
    def app_version(self):
        return APP_VERSION_NAME

    @property
    def api_version(self):
        return API_VERSION

    def pipe(self, name):
        return pipe.Pipe(name, self._app)

    def logger(self):
        return self._logger

    def put_cache(self, filename, data):
        LOGGER.info("Adding new cache %s" % filename)
        if isinstance(data, str):
            data = data.encode("utf-8")
        return cache.put_module_cache(self._nativemodule.__name__, filename, data)

    def put_tempdata(self, name, data):
        self._runtimecache.put(name, data, module=self._inputservice)

    def get_tempdata(self, name):
        return self._runtimecache.get(name, module=self._inputservice)

    def is_cached_tempdata(self, name):
        return self._runtimecache.is_cached(name)

    def remove_tempdata(self, name):
        self._runtimecache.remove(name, module=self._inputservice)

    def get_cached(self, filename):
        LOGGER.info("Getting cache %s" % filename)
        return cache.get_module_cached(self._nativemodule.__name__, filename)

    def get_cache_path(self, filename=None):
        pth = cache.module_path(self._nativemodule.__name__)
        if filename:
            return os.path.join(pth, filename)
        return pth

    def is_cached(self, filename):
        return cache.is_module_cached(self._nativemodule.__name__, filename)

    def remove_cache(self, filename):
        LOGGER.info("Removing module cache: %s" % filename)
        cache.remove_module_cache(self._nativemodule.__name__, filename)

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

    def enter_context(self, module):
        if module.name in self._app.registry:
            if "ENTER_CONTEXT" in module.configs:
                if module.configs["ENTER_CONTEXT"]:
                    self._app.input_context.set(self._app.registry[module.name], module)

    def exit_context(self):
        self._app.input_context.null()

    def import_submodule_by_path(self, path):
        LOGGER.info("Importing submodule: %s" % path)
        prevcwd = os.getcwd()
        os.chdir(self._inputservice.path)
        module = load_py_from(os.path.abspath(path))
        os.chdir(prevcwd)
        return module

    def internal_path(self, path=None):
        LOGGER.info("Resolving internal path: %s" % path)
        if path is None:
            return self._inputservice.path
        else:
            return os.path.join(self._inputservice.path, path)

    def import_submodule(self, module_name):
        LOGGER.info("Importing submodule %s" % module_name)
        # module name without py
        module_name = module_name.replace(".py", "") + ".py"
        module = load_py_from(os.path.join(self._inputservice.path, module_name))
        return module


class DeliveryServiceContext:
    def __init__(self, delservice, nativemodule, app):
        self._nativemodule = nativemodule
        self._delservice = delservice
        self._extensions = app.extensions
        self._builded_ext = {}
        self._app = app
        self._runtimecache = app.runtime_cache
        self._cfg = app.config

    @property
    def app_version(self):
        return APP_VERSION_NAME

    @property
    def api_version(self):
        return API_VERSION

    def set_cleanable_cache(self, state=True):
        if not state:
            cache.put_allowed_cache(self._delservice.name)
        else:
            cache.remove_allowed_cache(self._delservice.name)

    def extension(self, name):
        LOGGER.info("Using extension %s" % name)
        if name not in self._builded_ext:
            if name not in self._extensions:
                LOGGER.error(f"Extension {name} wasn't found")
                return None
            self._builded_ext[name] = self._extensions[name].build(self._delservice)
        return self._builded_ext[name]

    def internal_path(self, path=None):
        LOGGER.info("Resolving internal path: %s" % path)
        if path is None:
            return self._delservice.path
        else:
            return os.path.join(self._delservice.path, path)

    def absolute_cfg(self, name):
        return self._cfg.absolute_cfg(name, module=self._nativemodule)

    def relative_cfg(self, name):
        return self._cfg.relative_cfg(name, self._nativemodule)

    def put_config(self, name, value):
        return self._cfg.put(name, value, module=self._nativemodule)

    @property
    def version_array(self):
        return APP_VERSION

    def put_cache(self, filename, data):
        LOGGER.info("Adding new cache %s" % filename)
        if isinstance(data, str):
            data = data.encode("utf-8")
        return cache.put_module_cache(self._nativemodule.__name__, filename, data)

    def put_tempdata(self, name, data):
        self._runtimecache.put(name, data, module=self._delservice)

    def get_tempdata(self, name):
        return self._runtimecache.get(name, module=self._delservice)

    def is_cached_tempdata(self, name):
        return self._runtimecache.is_cached(name)

    def remove_tempdata(self, name):
        self._runtimecache.remove(name, module=self._delservice)

    @staticmethod
    def get_shared_cache():
        return cache.get_shared_cache()

    def get_cached(self, filename):
        LOGGER.info("Getting cache %s" % filename)
        return cache.get_module_cached(self._nativemodule.__name__, filename)

    def get_cache_path(self, filename=None):
        pth = cache.module_path(self._nativemodule.__name__)
        if filename:
            return os.path.join(pth, filename)
        return pth

    def is_cached(self, filename):
        return cache.is_module_cached(self._nativemodule.__name__, filename)

    def remove_cache(self, filename):
        LOGGER.info("Removing module cache: %s" % filename)
        cache.remove_module_cache(self._nativemodule.__name__, filename)




