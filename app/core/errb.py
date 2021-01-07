from .storage import lookup_errb
from . import models
from . import import_service
from .logger import get_logger


LOGGER = get_logger("errb")


def load_sockets():
    LOGGER.debug("Loading ERRB sockets...")
    imported = {}
    ext = lookup_errb()
    for name in ext:
        imported[name] = models.ERRBSocket(
            ext[name]["alias"],
            name,
            import_service.load_py_from(ext[name]["file"]),
        )
    return imported


def port_handler(port, ports, *args):
    if isinstance(port, str):
        if not port.isdigit():
            for p in ports:
                if ports[p]["alias"] == port:
                    port = p
                    break
            if not port.isdigit():
                LOGGER.error("Alias wasn't found")
                return None, None
    port = int(port)
    if port in ports:
        if ports[port].is_available():
            return ports[port].make_pair(*args)
        else:
            LOGGER.error("Unavailable port")
            return None, None
    else:
        LOGGER.error("Unavailable port, port wasn't found")
        return None, None


def post_sender(sender, data: bytes):
    if sender:
        LOGGER.info(f"Posting to sender")
        return sender.send(data)


def recieve(reciever):
    if reciever:
        LOGGER.info(f"Recieving from reciever")
        return reciever.recieve()
