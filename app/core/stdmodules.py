from .utils import ChapteredText
from .models import Module
from .cache import get_module_cached, is_module_cached
from .appconfig import DEFAULT_MNEMONIC_MODE, DEFAULT_ENCODING
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
        self.text = None
        self.mnemonic_toggle = False
        self._chapter_ptr = 0

    def init(self):
        pass

    def _toggle_mnemonic(self):
        if self.mnemonic_toggle:
            self.mnemonic_toggle = False
        else:
            self.mnemonic_toggle = True

    @staticmethod
    def filter(text):
        text = re.sub(r"[\n\t\r]+", "|", text)
        return text

    def swallow(self, value):
        value = value.strip()
        if self.mnemonic_toggle and value.isdigit():
            if value == "4":
                self._chapter_ptr -= 1
                return self.filter(self.text.get(self._chapter_ptr))
            elif value == "5":
                self._chapter_ptr = (self._chapter_ptr + 1) % len(self.text.chapters())
                return self.filter(self.text.get(self._chapter_ptr))
            elif value == "1":
                return ";".join(map(lambda x: x.strip(), self.text.chapters()))[1:]
            elif value == "0":
                self._toggle_mnemonic()
                return 

        if is_module_cached("fdel", value):
            if value.lower().endswith(".chp"):
                self.text = ChapteredText(get_module_cached("fdel", value).decode(DEFAULT_ENCODING))
                self._toggle_mnemonic()
                return self.filter(self.text.get(self._chapter_ptr))
            else:   
                self.text = self.filter(
                    get_module_cached("fdel", value).decode(DEFAULT_ENCODING)
                )
                self._toggle_mnemonic()
                return self.text
        else:
            return "File not found"

    @property
    def configs(self):
        return self.standard_params(
            {"NOCACHE": True, 
             "ENTER_CONTEXT": self.mnemonic_toggle, 
             "PREF_MNEMMOD": 0x0 if self.mnemonic_toggle else 0x1})


class Help(Module):
    def __init__(self, app):
        super().__init__("fdel", None, None, app)

    def init(self):
        pass

    def swallow(self, value):
        values = value.split(" ")
        if len(values) == 0:
            return "Help for this application wasn't written. Use external documentation files"
        else:
            module = values[0]
            obj = None
            if module in self._app.modules:
                obj = self._app.modules[module]
            elif module in self._app.input_services:
                obj = self._app.input_services[module]
            elif module in self._app.delivery_services:
                obj = self._app.delivery_services[module]
            obj.help(*values[1:])

    @property
    def configs(self):
        return self.standard_params({"NOCACHE": True})


REGISTRIES = {
    "idel": Idel,
    "fdel": Fdel,
    "help": Help
}


def load_std_registry(registries):
    for i in REGISTRIES:
        registries[i] = i


def is_std_registry(registry):
    return registry in REGISTRIES


def get_stdmodule(registry, app=None):
    if isinstance(REGISTRIES[registry], type):
        REGISTRIES[registry] = REGISTRIES[registry](app)
    return REGISTRIES[registry]
