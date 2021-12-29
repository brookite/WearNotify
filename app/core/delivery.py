from .storage import lookup_services_path
from .models import DeliveryService
from . import import_service
import os
from .logger import get_logger


LOGGER = get_logger("delivery")


def load_services(app):
    LOGGER.debug("Loading delivery services...")
    imported = []
    paths = lookup_services_path("delivery_services")
    for path in paths:
        name = os.path.basename(path).replace(".py", "")
        imported.append(DeliveryService(name, import_service.load_py_from(path), path, app))
    return imported


def put_on_pipeline(pipeline, request, response, module, config):
    """
    Puts response on pipeline or 
    """
    LOGGER.debug("Put new response on pipeline")
    pipeline.reset()
    pipeline.put(handle_response(response, pipeline, module, config))


def handle_response(obj, pipeline, module, config):
    """
    Handles various object representation
    """
    LOGGER.debug("Handling output response...")
    if isinstance(obj, str):
        if "PIPELINE_MANIP" in module.configs:
            LOGGER.debug("Configuring pipeline...")
            pipeline.config(**module.configs["PIPELINE_MAINP"])
        return obj
    elif isinstance(obj, dict):
        if "status" in obj:
            if not obj["status"]:
                LOGGER.warning("Something bad, status=false")
        if "log_messages" in obj:
            for logmsg in obj["log_messages"]:
                LOGGER.info(logmsg)
        if "warnings" in obj:
            for logmsg in obj["warnings"]:
                LOGGER.warning(logmsg)
        if "pipeline_manip" in obj:
            LOGGER.debug("Configuring pipeline...")
            pipeline.config(**obj["pipeline_manip"])
        if "message" in obj:
            return obj["message"]
        else:
            LOGGER.error("Empty response...")
            return "empty"
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return obj
    else:
        if config.absolute_cfg("only_string_io_data"):
            return str(obj)
        else:
            return obj


def sendto(packet, services):
    for service in services:
        service.send(packet)


def begin(services):
    for service in services:
        service.begin()


def finished(services, cnt):
    for service in services:
        service.finished(cnt)


def roll_pipeline(pipeline, services, user_action=None):
    LOGGER.info("Rolling pipeline...")
    if pipeline.is_specific_source():
        sendto(pipeline.source, services)
    else:
        debug_packet_count = 0
        debug_packet_length = 0
        if pipeline.is_filled():
            LOGGER.debug("Pipeline is filled.")
            for service in services:
                service.begin()
            for packet in pipeline:
                if packet != "$:USER_ACTION":
                    debug_packet_length += len(packet)
                    debug_packet_count += 1
                    sendto(packet, services)
                else:
                    if user_action:
                        LOGGER.debug("Calling user action")
                        for service in services:
                            service.finished(pipeline.packets_sent)
                            service.begin()
                        if not user_action():
                            break
            for service in services:
                service.finished(pipeline.packets_sent)
    LOGGER.info("Packet delivery finished. Sent {} packets with length {}".format(debug_packet_count, debug_packet_length))
    pipeline.reset()
