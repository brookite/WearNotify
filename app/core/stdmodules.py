from .models import Module
from .cache import get_module_cached, is_module_cached
import re


class Idel(Module):
    def __init__(self, app):
        super().__init__("idel", None, None, app)

    def init(self):
        pass

    def swallow(self, value):
        if value != '':
            return value
        else:
            return None

    @property
    def configs(self):
        return self.standard_params({"ENTER_CONTEXT": True, "NOCACHE": True})


class Fdel(Module):
    def __init__(self, app):
        super().__init__("fdel", None, None, app)

    def init(self):
        pass

    def filter(self, text):
        text = re.sub(r"[\n\t\r]+", " ", text)
        return text

    def swallow(self, value):
        value = value.strip()
        if is_module_cached("fdel", value):
            return self.filter(
                get_module_cached("fdel", value).decode("utf-8")
            )
        else:
            return "File not found"

    @property
    def configs(self):
        return self.standard_params({"NOCACHE": True})


REGISTRIES = {
    "idel": Idel,
    "fdel": Fdel
}


def load_std_registry(registry):
    for i in REGISTRIES:
        registry[i] = i


def is_std_registry(registry):
    if registry in REGISTRIES:
        if isinstance(REGISTRIES[registry], type):
            return REGISTRIES[registry](None)
        else:
            return REGISTRIES[registry]


def get_stdmodule(registry):
    if isinstance(REGISTRIES[registry], type):
        return REGISTRIES[registry](None)
    else:
        return REGISTRIES[registry]
