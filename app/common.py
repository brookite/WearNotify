import time

from core.registry import get_registry, route, load_predefined_registries
from core.module_loader import load_modules
from core.extension_loader import load_extensions
from core.errb import load_sockets
from core import delivery
from core import input_manager
from core.pipeline import Pipeline
from core.logger import get_logger
from core.cache import is_request_cached, get_request_cached, \
    put_request_cache, cleanup, RuntimeCache
from core.context import InputContext
from core.config import Config
from core.mnemonics import load_global_mnemonics

from threading import RLock


class App:
    def __init__(self):
        self.logger = get_logger("app")
        self.runtime_cache = RuntimeCache()
        self.mnems = load_global_mnemonics()
        self.config = Config()
        self.logger.debug("Initializing app")
        self.registries = get_registry()
        self.errb = load_sockets()
        self.extensions = load_extensions(self)
        self.modules = load_modules(self)
        load_predefined_registries(self.registries, self.modules)
        self.input_services = input_manager.load_services(self)
        self.config.load(self)
        self.pipeline = Pipeline(self.config)
        self.delivery_services = delivery.load_services()
        self.input_context = InputContext()
        self._request_lock = RLock()
        self._mnemmode = self.config.absolute_cfg("default_mnemonic_mode")
        self._mnemmem = self.config.absolute_cfg("default_mnemonic_mode")
        self.input_context.sethook(self.hookmnemmod)
        self._current_user_action = None

    @property
    def request_lock(self):
        return self._request_lock

    def is_context_entered(self):
        return self.input_context.get() is not None

    def hookmnemmod(self, prev, new, prev_module, new_module):
        if new_module:
            if "PREF_MNEMMOD" in new_module.configs:
                self._mnemmem = self._mnemmode
                self.chmnemmod(new_module.configs["PREF_MNEMMOD"])
            else:
                self.chmnemmod(self._mnemmem)
                self._mnemmem = self.config.absolute_cfg("default_mnemonic_mode")
        else:
            self.chmnemmod(self._mnemmem)
            self._mnemmem = self.config.absolute_cfg("default_mnemonic_mode")

    def chmnemmod(self, pref=None):
        if "mnemonic_server" in self.input_services:
            self._mnemmode = int(self.config.absolute_cfg("mnemonic_server.mode"))
            if pref:
                self._mnemmode = int(pref)
            elif self._mnemmode == 0x1:
                self._mnemmode = 0x0
            else:
                self._mnemmode = 0x1
            self.config.put("mnemonic_server.mode", self._mnemmode)

    def collect_input(self, service=None, *args):
        if service is None:
            self.logger.debug(f"Collecting input from all services")
            for service in self.input_services:
                self.logger.debug(f"Collecting input from {service}")
                return self.input_services[service].raw_input(*args)
        else:
            self.logger.debug(f"Collecting input from service {service}")
            if service in self.input_services:
                self.logger.debug(f"Input service {service} has found")
                return self.input_services[service].raw_input(*args)
            else:
                self.logger.error(f"Input service ({service}) wasn't found")
                return None

    def handle_input(self, request, handle_ctx=True):
        self.logger.debug(f"Collected input {request}")
        return input_manager.input_handler(request,
                                           self.registries,
                                           self.input_context,
                                           self.modules,
                                           handle_ctx
                                           )

    def clear_cache(self):
        self.logger.debug("Clearing all cache...")
        cleanup()

    def delegate(self, reg, request, additional, user_action, deny_cache=False):
        self.logger.debug(f"Delegating request (registry={reg}, request={request})")
        self._current_user_action = user_action
        if reg is None or request is None:
            self.logger.info("Invalid registry")
            return None, None
        else:
            module = route(reg, self.modules, self.registries)
            full_request = request
            if self.input_context.get() is not None:
                full_request = str(self.input_context.get()) + " " + request
            if not module:
                self.logger.debug("Module is None")
                return None, None
            if not is_request_cached(full_request) or deny_cache:
                self.logger.debug(f"Request {request} is not cached")
                response = module.swallow(request)
                self.logger.info("Got response from module")
                if not module.configs["NOCACHE"] and response and full_request:
                    put_request_cache(full_request, response)
                return response, module
            else:
                self.logger.debug(f"Request {request} is cached")
                return get_request_cached(full_request), module

    def pack(self, request, response, module):
        self.lock_requests()
        self.logger.debug(f"Packing response (response={response}, request={request})")
        delivery.put_on_pipeline(self.pipeline, request, response, module)
        return self.pipeline.is_filled()

    def post(self, user_action):
        self.logger.debug("Posting. Rolling pipeline")
        delivery.roll_pipeline(self.pipeline, self.delivery_services, user_action)
        self.unlock_requests()

    def mapmnem(self, request):
        if self.input_context.get():
            reg = self.input_context.get()
            module = route(reg, self.modules, self.registries)
        else:
            module = None
        if module:
            if "DENY_MNEMONIC" in module.configs:
                if module.configs["DENY_MNEMONIC"]:
                    return None
            if request in module.context.mnemonics[0]:
                return module.context.mnemonics[0][request]
            elif request in module.context.mnemonics[1]:
                return module.context.mnemonics[1][request]
            elif request in self.mnems:
                return self.mnems[request]
        else:
            if request in self.mnems:
                return self.mnems[request]
        return None

    def lock_requests(self):
        self.logger.debug("Acquiring request lock")
        self._request_lock.acquire()

    def unlock_requests(self):
        self._request_lock.release()
        self.logger.debug("Released request lock")

    def direct_message(self, text: str, timeout=0):
        """
        Sends message directly without pipeline (without packet splitting)
        """
        self.logger.info("Sending direct message")
        delivery.begin(self.delivery_services)
        delivery.sendto(text, self.delivery_services)
        time.sleep(timeout)
        delivery.finished(self.delivery_services, 1)

    def send_message(self, text: str, user_action):
        """
        Sends message through pipeline
        """
        self.lock_requests()
        self.logger.info("Sending direct message through pipeline")
        self.pipeline.reset()
        self.pipeline.put(text)
        delivery.roll_pipeline(self.pipeline, self.delivery_services, user_action)
        self.pipeline.reset()
        self.unlock_requests()

    def process(self, input_data, user_action,
                mnemonic_handle=False, deny_cache=False, handle_ctx=True):
        self.lock_requests()
        if mnemonic_handle:
            tmp = self.mapmnem(input_data)
            if tmp:
                input_data = tmp
        registry, request, additional = self.handle_input(input_data, handle_ctx)
        response, module = self.delegate(registry, request, additional, user_action, deny_cache)
        if not response:
            self.unlock_requests()
            return False
        self.pack(request, response, module)
        self.post(user_action)
        self.unlock_requests()
        return True

    def quit(self):
        self.input_context.null()
        for inputservice in self.input_services:
            self.input_services[inputservice].exit()
        for delservice in self.delivery_services:
            delservice.exit()
