import os
import json
from .appconfig import APP_PATH, DATA_PATH, DEFAULT_ENCODING
from .logger import get_logger
from .import_service import pip_install


LOGGER = get_logger("storage")


def init():
    paths = [
        os.path.join(DATA_PATH),
        os.path.join(DATA_PATH, "errb"),
        os.path.join(DATA_PATH, "extensions"),
        os.path.join(DATA_PATH, "input_services"),
        os.path.join(DATA_PATH, "delivery_services"),
        os.path.join(DATA_PATH, "modules"),
        os.path.join(DATA_PATH, "errb", "sockets"),
        os.path.join(DATA_PATH, "cache"),
        os.path.join(DATA_PATH, "cache", "requests"),
        os.path.join(DATA_PATH, "cache", "shared")
    ]
    files = {
        os.path.join(DATA_PATH, "errb", "alias.json"): '{}',
        os.path.join(DATA_PATH, "errb", "port.json"): '{}',
        os.path.join(DATA_PATH, "registry.json"): '{}',
    }
    for directory in paths:
        if not os.path.exists(directory):
            os.mkdir(directory)
    for file in files:
        if not os.path.exists(file):
            with open(file, "w", encoding=DEFAULT_ENCODING) as f:
                f.write(files[file])


def get_included(path):
    include = os.path.join(path, "include.txt")
    if os.path.exists(include):
        with open(include, "r") as fobj:
            included = fobj.read().split("\n")
        return included
    else:
        return []


def lookup_services_path(service_name):
    paths = []
    app_services = os.path.join(APP_PATH, service_name)
    data_services = os.path.join(DATA_PATH, service_name)
    data_paths = list(map(lambda x: os.path.join(data_services, x), os.listdir(data_services)))
    app_paths = list(map(lambda x: os.path.join(app_services, x), os.listdir(app_services)))
    app_ignored = get_included(app_services)
    data_ignored = get_included(data_services)
    if len(data_ignored) > 0:
        data_paths = list(filter(lambda x: x in data_ignored, data_paths))
    if len(app_ignored) > 0:
        app_paths = list(filter(lambda x: x in app_ignored, app_paths))
    for element in data_paths + app_paths:
        if os.path.isfile(element) and element.endswith(".py"):
            paths.append(element)
    return paths


def lookup_modules():
    return lookup_plugins("modules")


def lookup_extensions():
    return lookup_plugins("extensions")


def lookup_plugins(plugin_type):
    result = {}
    data_modules = os.path.join(DATA_PATH, plugin_type)
    app_modules = os.path.join(APP_PATH, plugin_type)
    for modules in [app_modules, data_modules]:
        if os.path.exists(modules):
            for path in os.listdir(modules):
                pth = os.path.join(modules, path)
                if os.path.isdir(pth):
                    initfile = os.path.join(pth, "__init__.py")
                    if os.path.exists(initfile):
                        result[os.path.basename(pth)] = os.path.abspath(pth)
    return result


def read_json(file):
    with open(file, "r", encoding=DEFAULT_ENCODING) as f:
        LOGGER.debug(f"Reading JSON: {file}")
        return json.load(f)


def write_json(file, data):
    LOGGER.debug(f"Writing JSON: {file}")
    with open(file, "w", encoding=DEFAULT_ENCODING) as f:
        return json.dump(data, f, ensure_ascii=False)


def get_requirements(file):
    if os.path.exists(file):
        with open(file, encoding=DEFAULT_ENCODING) as f:
            req = f.read().strip().split("\n")
        return req
    else:
        return []


def get_ooc_commands():
    path = os.path.join(DATA_PATH, "commands.json")
    if os.path.exists(path):
        return read_json(path)
    else:
        return {}


def satisfact_requirements(requirements):
    reqmarker = os.path.join(DATA_PATH, "markers.json")
    if not os.path.exists(reqmarker):
        with open(reqmarker, "w", encoding=DEFAULT_ENCODING) as f:
            f.write("{}")
        marker = {}
    else:
        with open(reqmarker, "r", encoding=DEFAULT_ENCODING) as f:
            marker = json.load(f)
    if "pip" in marker:
        if any(map(lambda x: x not in marker["pip"], requirements)):
            print(pip_install(requirements).stdout)
            for requirement in requirements:
                if requirement not in marker["pip"]:
                    marker["pip"].append(requirement)
    else:
        marker["pip"] = []
    with open(reqmarker, "w", encoding=DEFAULT_ENCODING) as f:
        json.dump(marker, f, ensure_ascii=False)


init()
