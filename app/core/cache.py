import os
import json
from .appconfig import DATA_PATH, MAX_REQUEST_CACHE_SIZE
from .storage import read_json, write_json

from .logger import get_logger

LOGGER = get_logger("cache")

PATH = os.path.join(DATA_PATH, "cache")
REQUEST_CACHE = os.path.join(PATH, "requests")


class RuntimeCache:
    """
    RuntimeCache for temporary data saving and opening during runtime
    """

    def __init__(self, app):
        LOGGER.debug("Creating runtime cache data")
        self._app = app
        self._storage = {
            "SHARED": None,
            "INTERRUPT": None
        }

    def cleanup_cache(self, module):
        if module:
            del self._storage[module.name]

    def set(self, name, data, module=None, interrupt_call=False):
        allowed_names = ["SHARED"]
        if name in self._storage:
            LOGGER.info(f"Wiping old data in runtime cache: {name}")
            del self._storage[name]
        if module:
            allowed_names.append(module.name)
        if interrupt_call:
            allowed_names.append("INTERRUPT")
        if name in allowed_names:
            self._storage[name] = data

    def get(self, name, module=None, interrupt_call=False):
        LOGGER.debug(f"Getting runtime cache by name {name}")
        allowed_names = ["SHARED"]
        if module:
            allowed_names.append(module.name)
        if interrupt_call:
            allowed_names.append("INTERRUPT")
        if name in self._storage and name in allowed_names:
            return self._storage[name]

    def clear(self):
        LOGGER.info("Clearing runtime cache")
        self._storage.clear()

    def is_cached(self, name):
        return name in self._storage

    def size(self):
        return len(self._storage)

    def remove(self, name, module=None):
        LOGGER.debug(f"Removing runtime cache by name {name}")
        denied_names = ["SHARED", "INTERRUPT"]
        allowed_names = []
        if not module:
            if name not in ["SHARED", "INTERRUPT"]:
                return self._storage.pop(name)
        else:
            if name == module.name:
                return self._storage.pop(name)


def put_request_cache(request, data):
    """
    Puts request to cache
    :param request: request string
    :param data: response data
    """
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    else:
        data = str(data)
    maxnumber = 0
    for number in os.listdir(REQUEST_CACHE):
        maxnumber = max(int(number), maxnumber)
    file = os.path.join(REQUEST_CACHE, str(maxnumber))
    if not os.path.exists(file):
        write_json(file, {})
    if os.path.getsize(file) > MAX_REQUEST_CACHE_SIZE:
        maxnumber += 1
        file = os.path.join(REQUEST_CACHE, str(maxnumber))
        LOGGER.debug(f"Filling new request cache file: {maxnumber}")
        write_json(file, {request: data})
    else:
        cache = read_json(file)
        cache[request] = data
        LOGGER.debug(f"Putting request cache file: {maxnumber}")
        write_json(file, cache)


def find_request(request):
    """
    Returns a filename where storea response by passed request
    """
    listdir = list(map(int, filter(lambda x: x.isdigit(), os.listdir(REQUEST_CACHE))))
    listdir.sort(reverse=True)
    for number in listdir:
        loaded = read_json(os.path.join(REQUEST_CACHE, f"{number}"))
        if request in loaded:
            LOGGER.debug(f"Request {request} has found in cache")
            return str(number)
    return None


def put_module_cache(module, filename, data: bytes):
    """
    Store module cache in specific file with byte data
    :param module: module string name
    :param filename: name for specific file
    :param data: response data in bytes
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    if not os.path.exists(os.path.join(PATH, module)):
        os.mkdir(os.path.join(PATH, module))
    module_cachefile = os.path.join(PATH, module, filename)
    with open(module_cachefile, "wb") as fobj:
        fobj.write(data)
    LOGGER.debug(f"Putting request cache file: {module}/{filename}")


def is_request_cached(request_addr):
    return find_request(request_addr) is not None


def is_module_cached(module, filename):
    path = os.path.join(PATH, module, filename)
    return os.path.exists(path) and os.path.isfile(path)


def get_module_cached(module, filename):
    if not os.path.exists(os.path.join(PATH, module)):
        os.mkdir(os.path.join(PATH, module))
    path = os.path.join(PATH, module, filename)
    if os.path.exists(path):
        with open(path, "rb") as fobj:
            data = fobj.read()
        return data
    else:
        LOGGER.error(f"{filename} isn't cached in {module}")


def get_request_cached(request_addr):
    path = os.path.join(REQUEST_CACHE, find_request(request_addr))
    data = read_json(path)
    return data[request_addr]


def request_path(request_addr):
    return os.path.join(REQUEST_CACHE, find_request(request_addr))


def module_path(name):
    return os.path.join(PATH, name)


def cleanup(force=False):
    """
    Cleanup cache excluding ALLOWED_CACHE directory names
    """
    for root, _, files in os.walk(PATH):
        for file in files:
            path = os.path.join(root, file)
            if (os.path.basename in ALLOWED_CACHE \
                    or (os.path.basename(os.path.dirname(path)) in ALLOWED_CACHE)) and not force:
                continue
            else:
                try:
                    os.remove(path)
                    LOGGER.debug(f"Cleaning {path}")
                except PermissionError:
                    LOGGER.info(f"Skipping {path} due to PermissionError")


def remove_module_cache(module, filename):
    pth = os.path.join(PATH, module, filename)
    LOGGER.debug(f"Pemoving request cache file: {pth}")
    return os.remove(pth)


def remove_request_cached(request_addr):
    path = os.path.join(REQUEST_CACHE, find_request(request_addr))
    with open(path, "rb") as fobj:
        data = json.load(fobj)
    data.pop(request_addr)
    with open(path, "wb") as fobj:
        json.dump(fobj, data)
    LOGGER.debug(f"Removing {request_addr}")


def get_shared_cache():
    return os.path.join(DATA_PATH, "cache", "shared")


def load_allowed_cache():
    pth = os.path.join(DATA_PATH, "allowed_cache.json")
    if os.path.exists(pth):
        return list(set(read_json(pth) + ["fdel", "mnemonic_server"]))
    else:
        return ["fdel", "mnemonic_server"]


def put_allowed_cache(modulename):
    pth = os.path.join(DATA_PATH, "allowed_cache.json")
    if modulename not in ALLOWED_CACHE:
        ALLOWED_CACHE.append(modulename)
        write_json(pth, ALLOWED_CACHE)

def remove_allowed_cache(modulename):
    pth = os.path.join(DATA_PATH, "allowed_cache.json")
    if modulename in ALLOWED_CACHE:
        ALLOWED_CACHE.remove(modulename)
        write_json(pth, ALLOWED_CACHE)


ALLOWED_CACHE = load_allowed_cache()