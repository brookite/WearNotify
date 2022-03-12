from .models import ExtensionInfo
from .storage import lookup_extensions, \
    get_requirements, satisfact_requirements
from .logger import get_logger
import os


LOGGER = get_logger("ext_loader")


def load_extensions(app):
    LOGGER.info("Loading extensions")
    imported = {}
    ext = lookup_extensions()
    for name in ext:
        req = os.path.join(ext[name], "requirements.txt")
        reqs = get_requirements(req)
        satisfact_requirements(reqs)
        imported[name] = ExtensionInfo(
            name,
            ext[name],
            app
        )
    return imported
