from .storage import lookup_services_path
from .models import InputService
import os
from . import import_service
from . import registry
from .logger import get_logger


LOGGER = get_logger("input")


def load_services(app):
    LOGGER.info("Loading input services")
    imported = {}
    paths = lookup_services_path("input_services")
    for path in paths:
        name = os.path.basename(path).replace(".py", "")
        imported[name] = InputService(name, import_service.load_py_from(path), app)
    return imported


def input_handler(request, registries, input_ctx, modules, handle_ctx=True):
    # if returns null then actions not required
    if input_ctx.get() is not None and handle_ctx:
        LOGGER.debug("Handling request in context")
        reg = input_ctx.get()
        module = registry.route(reg, modules, registries)
        if request not in module.configs.get("QUIT_COMMANDS"):
            return reg, request, {}
        else:
            LOGGER.debug("Nulling context")
            input_ctx.null()
            return None, None, {}
    else:
        LOGGER.debug("Handling request out of context")
        reg, request = registry.split(request, registries)
        module = registry.route(reg, modules, registries)
        if module:
            if module.configs.get("ENTER_CONTEXT"):
                LOGGER.debug("Handling request out of context")
                input_ctx.set(reg, module)
        return reg, request, {}
