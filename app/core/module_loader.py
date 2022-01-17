from .storage import lookup_modules, \
    get_requirements, satisfact_requirements
from . import import_service
from .models import Module
from .logger import get_logger
import os


LOGGER = get_logger("module_loader")


def load_modules(app):
    imported = {}
    modules = lookup_modules()
    LOGGER.info("Loading modules")
    for name in modules:
        path = os.path.join(modules[name], "__init__.py")
        req = os.path.join(modules[name], "requirements.txt")
        reqs = get_requirements(req)
        satisfact_requirements(reqs)
        module = Module(
            name,
            import_service.load_py_from(path),
            modules[name],
            app
        )
        for dep in module.configs["DEPENDENCIES"]:
            if dep not in app.extensions:
                LOGGER.error(f"Missing {dep} in extensions. Module {module.name} wasn't loaded")
                continue
        imported[name] = module
    return imported
