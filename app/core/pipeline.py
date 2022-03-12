import time
from . import appconfig
from .logger import get_logger


LOGGER = get_logger("pipeline")


def delay(ms):
    LOGGER.debug(f"Delaying in {ms}")
    time.sleep(int(ms) / 1000)


class Pipeline:
    # In iterations may return $:USER_ACTION

    def __init__(self, cfg, **kwargs):
        LOGGER.debug("Creating pipeline object")
        self._cfg = cfg
        self.DEFAULTS = self._cfg.absolute_cfg("PIPELINE")
        for key in kwargs:
            assert key in self.DEFAULTS
        self._config = dict(kwargs or self.DEFAULTS)
        for key in self.DEFAULTS:
            if key not in self._config:
                self._config[key] = self.DEFAULTS[key]
        self._source = None
        self._c = 0
        self._maxc = 0
        self._packets = None
        self._limit_marker = False

    def config(self, **kwargs):
        LOGGER.info(f"Reconfiguring pipeline: {kwargs}")
        for key in kwargs:
            if key in self.DEFAULTS:
                self._config[key] = kwargs[key]

    @property
    def configuration(self):
        return self._config

    def reset(self):
        LOGGER.info("Reset pipeline")
        self._source = None
        self._packets = None
        self._c = 0
        self._maxc = 0
        if appconfig.RESET_PIPECONFIG:
            self.reset_config()

    @staticmethod
    def text_filter(text):
        allowed_chars = ["\n", "\r", "\t"]
        result = filter(lambda x: x.isprintable() or x in allowed_chars, text)
        return "".join(list(result)).replace("\\", "/")

    @property
    def packets_sent(self):
        return self._c
    
    @property
    def source(self):
        return self._source

    def reset_config(self):
        LOGGER.info("Reset configuration pipeline")
        self._config = dict(self.DEFAULTS)

    def is_rollable(self):
        if self.is_filled():
            return False
        else:
            return self._c < self._maxc

    def is_filled(self):
        return self._source is None or self._packets is None

    def put(self, data):
        LOGGER.info("Added new data to pipeline")
        if self._config["clear_text"]:
            data = self.text_filter(data)
        self._source = data

    def preprocess(self):
        if isinstance(self._source, str):
            return list(self.pregenerate(self._source))
        else:
            generated = []
            for item in self._source:
                if isinstance(item, str):
                    generated += list(self.pregenerate(item))
            return generated

    def pregenerate_symbol(self, source):
        LOGGER.info("Inititalizing symbol pregenerator engine")
        partscount = len(source) // self._config["max_packet_length"]
        partsmod = len(source) % self._config["max_packet_length"]
        begin, end = 0, 0
        i = 0
        for i in range(partscount):
            partnumber = f"{str(i + 1)}." if self._config["allow_part_number"] else ""
            end += self._config["max_packet_length"] - len(partnumber)
            partsmod += len(partnumber)  # fixme. it may cause bugs with huge packets count
            yield partnumber + source[begin:end]
            begin = end
        if partscount != 0:
            i += 1
        if partsmod != 0:
            partnumber = f"{str(i + 1)}." if self._config["allow_part_number"] else ""
            if partsmod + len(partnumber) <= self._config["max_packet_length"]:
                yield partnumber + source[end:end + partsmod]
            else:
                partsmod2 = partsmod - len(partnumber)
                yield partnumber + source[end:end + partsmod2]
                partnumber = f"{str(i + 2)}." if self._config["allow_part_number"] else ""
                yield partnumber + source[end + partsmod2:end + partsmod]

    def pregenerate_bytes(self, source, encoding=appconfig.DEFAULT_ENCODING):
        LOGGER.info("Inititalizing bytes pregenerator engine")
        ptr = 0
        i = 1
        while ptr < len(source):
            firstbuf = bytes()
            partnumber = f"{str(i)}." if self._config["allow_part_number"] else ""
            firstbuf += partnumber.encode("utf-8")
            while len(firstbuf) < self._config["max_packet_length"] and ptr < len(source):
                byte = source[ptr].encode(encoding)
                if len(byte) + len(firstbuf) <= self._config["max_packet_length"]:
                    firstbuf += byte
                    ptr += 1
                else:
                    break
            if len(firstbuf) > 0:
                i += 1
                yield firstbuf.decode("utf-8")

    def pregenerate(self, source):
        LOGGER.info("Accepted new pipeline string. Length: {}".format(len(source)))
        if self._config["limit_type"] == "bytes":
            return self.pregenerate_bytes(source)
        else:
            return self.pregenerate_symbol(source)

    def __next__(self):
        return self.iterate()

    def __iter__(self):
        return self

    def dandelion(self, pregenerator):
        LOGGER.info("Initializing Dandelion engine")
        start = self._config["start"]
        stop = self._config["stop"]
        step = self._config["step"]
        rolls = list(pregenerator)
        self._maxc = len(rolls)
        desc = self._config["step"] < 0
        step = abs(step)
        parts = []
        if all(map(lambda x: isinstance(x, str), rolls)):
            for i in range(0, len(rolls), self._config["packets_count"]):
                array = rolls[i: i + self._config["packets_count"]][start:stop:][::step]
                if desc:
                    array = array[::-1]
                parts.append(array)
        else:
            for tmp in rolls:
                for i in range(0, len(tmp), self._config["packets_count"]):
                    array = tmp[i: i + self._config["packets_count"]][start:stop:][::step]
                    if desc:
                        array = array[::-1]
                    parts.append(array)
        yield None  # initializing generator
        for array in parts:
            for item in array:
                yield item

    def rose(self, pregenerator):
        LOGGER.info("Initializing Rose engine")
        start = self._config["start"]
        stop = self._config["stop"]
        step = self._config["step"]
        rolls = list(pregenerator)
        if all(map(lambda x: isinstance(x, str), rolls)):
            rolls = rolls[start:stop:step]
        else:
            tmp = []
            for t in rolls:
                t = t[start:stop:step]
                for item in t:
                    tmp.append(item)
            rolls = tmp
        self._maxc = len(rolls)
        return iter(rolls)

    def iterate(self):
        version = self._cfg.absolute_cfg("PIPELINE_ENGINE", None) or "DANDELION"
        if self._packets is None:
            if version == "DANDELION":
                self._packets = self.dandelion(self.preprocess())
                next(self._packets)
            else:
                self._packets = self.rose(self.preprocess())
            self._c = 0
            delay(self._config["initial_delay"])
        if self._c > 0:
            delay(self._config["packet_delay"])
        if self._c >= self._maxc:
            LOGGER.debug(f"Interrupting iteration. Packets sent: {self._c}/{self._maxc}")
            raise StopIteration
        if self._c % self._config["packets_count"] == 0 and self._c != 0 and not self._limit_marker:
            LOGGER.debug("Set limit marker")
            self._limit_marker = True
            if self._config["after_limit"] == "special_delay":
                delay(self._config["special_delay"])
            elif self._config["after_limit"] == "initial_delay":
                delay(self._config["initial_delay"])
            elif self._config["after_limit"] == "finish":
                raise StopIteration
            elif self._config["after_limit"] == "user_action":
                LOGGER.info(f"User action callback, packets count={self._c}/{self._maxc}")
                return "$:USER_ACTION"
        else:
            LOGGER.debug("Disable limit marker")
            self._limit_marker = False
        self._c += 1
        result = next(self._packets)
        resultsize = len(result.encode(appconfig.DEFAULT_ENCODING))
        LOGGER.debug("Rolled packet with length {} and size {} bytes".format(len(result), resultsize))
        return result

    def is_specific_source(self):
        return not(isinstance(self.source, str) \
            or isinstance(self.source, list) \
            or isinstance(self.source, tuple) \
            or isinstance(self.source, dict))
