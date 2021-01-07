import os
import json
from .configs import DATA_PATH, MAX_REQUEST_CACHE_SIZE
from .storage import read_json, write_json

from .logger import get_logger


LOGGER = get_logger("cache")

PATH = os.path.join(DATA_PATH, "cache")
REQUEST_CACHE = os.path.join(PATH, "requests")


class RuntimeCache:
    def __init__(self):
        LOGGER.debug("Creating runtime cache data")
        self._byte_storage = {}
        self._str_storage = {}

    def put(self, name, data):
        if name in self._str_storage:
            LOGGER.info(f"Wiping old string data in runtime cache: {name}")
            del self._str_storage[name]
        elif name in self._byte_storage:
            LOGGER.info(f"Wiping old data in runtime cache: {name}")
            del self._byte_storage[name]
        if isinstance(data, str):
            self._str_storage[name] = data.encode("utf-8")
        else:
            self._byte_storage[name] = bytes(data)

    def get(self, name):
        LOGGER.debug(f"Getting runtime cache by name {name}")
        if name in self._str_storage:
            return self._str_storage[name]
        elif name in self._byte_storage:
            return self._byte_storage[name]

    def clear(self):
        LOGGER.info("Clearing runtime cache")
        self._byte_storage.clear()
        self._str_storage.clear()

    def is_cached(self, name):
        return name in self._str_storage or name in self._byte_storage

    def size(self):
        c = 0
        for key in self._byte_storage:
            c += len(self._byte_storage[key])
        for key in self._str_storage:
            c += len(self._str_storage[key])
        return c

    def remove(self, name):
        LOGGER.debug(f"Removing runtime cache by name {name}")
        if name in self._str_storage:
            return self._str_storage.pop(name)
        if name in self._byte_storage:
            return self._byte_storage.pop(name)


def put_request_cache(request, data):
    if isinstance(data, bytes):
        data = data.decode("utf-8")
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
    # Returns a filename
    listdir = list(map(int, filter(lambda x: x.isdigit(), os.listdir(REQUEST_CACHE))))
    listdir.sort(reverse=True)
    for number in listdir:
        loaded = read_json(os.path.join(REQUEST_CACHE, f"{number}"))
        if request in loaded:
            LOGGER.debug(f"Request {request} has found in cache")
            return str(number)
    return None


def put_module_cache(module, filename, data: bytes):
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
    return os.path.exists(os.path.join(PATH, module, filename))


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


def cleanup():
    for root, _, files in os.walk(PATH):
        for file in files:
            path = os.path.join(root, file)
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
