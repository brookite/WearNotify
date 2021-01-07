from common import App
from time import sleep
from core.configs import APP_VERSION_NAME, BUILD_INFO, APP_BRANCH, MAINTAINER, APP_NAME, BUILD_STATUS
from core.logger import get_logger
import sys

CREDITS = """
{}
{}
{} {} {}

Powerful, speedly, lifehacking system for
delivery information to wear devices
by {}
2021

Licensed under MIT License (read LICENSE file)
""".format(APP_NAME, APP_VERSION_NAME, BUILD_STATUS, BUILD_INFO, APP_BRANCH, MAINTAINER)

inputservice = "default"
bundle = None


def cleanup(bundle):
    bundle.clear_cache()


def termux(bundle):
    global inputservice
    inputservice = "termux"


def about(bundle):
    msg = "{} {} by {}".format(APP_NAME, APP_VERSION_NAME, MAINTAINER)
    bundle.send_message(msg, user_action)


def chmnemmod(bundle):
    bundle.chmnemmod()


QUIT = ["quit()", "quit", "exit", "exit()"]
END_USER_ACTION = '00'
COMMANDS = {
    "cleanup": cleanup,
    "termux": termux,
    "chmnem": chmnemmod,
    "about": about
}


def user_action():
    try:
        result = input("TYPE ANYTHING FOR CONTINUE; FOR BREAK - (Ctrl+C or 00) >>")
        return not result.startswith(END_USER_ACTION)
    except KeyboardInterrupt:
        print()
        return False


def main():
    global inputservice, bundle
    logger = get_logger()
    bundle = App()
    print(CREDITS)
    sleep(0.1)
    while True:
        try:
            context = '' if not bundle.input_context.get() else \
                f"({bundle.input_context.get()}) "
            print(context, end='')
            req = bundle.collect_input(inputservice)
            if inputservice != "default":
                inputservice = "default"
            if not req:
                print(f"[{APP_NAME}]: Empty request")
                logger.debug("Got a empty request")
                continue
            elif req.lower() in QUIT and not bundle.is_context_entered():
                break
            elif req.lower() in COMMANDS:
                COMMANDS[req.lower()](bundle)
                continue
            registry, request, additional = bundle.handle_input(req)
            response, module = bundle.delegate(registry, request, additional)
            if not response:
                continue
            bundle.pack(request, response, module)
            bundle.post(user_action)
            sleep(0.2)
        except KeyboardInterrupt:
            logger.info("Exiting by CTRL+C...")
            break
        except Exception:
            logger.exception(f"{APP_NAME} prompt exception:")
    logger.info("App is closing...")


if __name__ == '__main__':
    main()
    sys.exit()
