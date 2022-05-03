from .utils import ChapteredText
from .models import Module
from .cache import get_module_cached, is_module_cached, module_path
from .appconfig import DEFAULT_ENCODING
import re
import os



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
        path = module_path("fdel")
        if os.path.exists(path):
            files = []
            for file in os.listdir(path):
                if os.path.isfile(os.path.join(path, file)):
                    files.append(file)
            self._ctx.extend_gsuggestions(files)

    @staticmethod
    def filter(text):
        text = re.sub(r"[\n\t\r]+", "|", text)
        return text

    def chapter_filter(self, text):
        new_text = ''
        text = text.split("\n")
        for line in text:
            line = line.strip()
            if line:
                new_text += re.sub(r"[\n\t\r]+", "|", line) + "|"
        if new_text:
            new_text = new_text[::-1]
        return new_text

    def swallow(self, value):
        value = value.strip()
        if self.mnemonic_toggle and value.isdigit():
            if value == "4":
                self._chapter_ptr = (self._chapter_ptr - 1) % len(self.text.chapters())
            elif value == "5":
                self._chapter_ptr = (self._chapter_ptr + 1) % len(self.text.chapters())
            elif value == "1":
                return self.chapter_filter(self.text.get(self._chapter_ptr))
            elif value == "0":
                self._mnemonic_toggle = False
                return
            elif value == "7":
                self._chapter_ptr = 0
            elif value == "6":
                self._chapter_ptr = len(self.text.chapters()) - 1
            elif value == "10" or value == "8":
                infostr = ""
                for i, chapter in enumerate(map(lambda x: x.strip(), self.text.chapters())):
                    infostr += f"{i + 1}.{chapter}|" if i != self._chapter_ptr else f"{i + 1}>{chapter}|"
                return infostr[:-1]
            return "{}>{}".format(self._chapter_ptr + 1, self.text.chapters()[self._chapter_ptr])
        elif self.mnemonic_toggle and value.startswith("cmd"):
            value = value.replace("cmd", "").lstrip()
            if value.isdigit():
                self._chapter_ptr = (int(value)-1) % len(self.text.chapters())
                return self.filter(self.text.get(self._chapter_ptr))
            elif value.startswith("find"):
                value = value.replace("find", "").lstrip()
                chapters = self.text.chapters()
                found = None
                for i in range(len(chapters)):
                    if value.lower() in chapters[i].lower():
                        found = i
                        break
                    elif value.lower() in self.text.get(i).lower():
                        found = i
                        break
                if found is not None:
                    self._chapter_ptr = found
                    return "{}>{}".format(self._chapter_ptr + 1, self.text.chapters()[self._chapter_ptr])
                return

        if is_module_cached("fdel", value):
            if value.lower().endswith(".chp"):
                self.text = ChapteredText(get_module_cached("fdel", value).decode(DEFAULT_ENCODING))
                self.mnemonic_toggle = True
                return
            else:   
                self.text = self.filter(
                    get_module_cached("fdel", value).decode(DEFAULT_ENCODING)
                )
                self.mnemonic_toggle = False
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


def init_stdmodules(app):
    for registry in REGISTRIES:
        if isinstance(REGISTRIES[registry], type):
            REGISTRIES[registry] = REGISTRIES[registry](app)


def get_stdmodule(registry, app=None):
    if isinstance(REGISTRIES[registry], type):
        REGISTRIES[registry] = REGISTRIES[registry](app)
        REGISTRIES[registry].init()
    return REGISTRIES[registry]
