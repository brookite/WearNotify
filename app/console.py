from common import App
from time import sleep
from core.configs import WELCOME_MSG, ABOUT_MSG, APP_NAME
from core.logger import get_logger
import sys
import os

inputservice = "default"
bundle = None


def cleanup(bundle):
    bundle.clear_cache()


def termux(bundle):
    global inputservice
    inputservice = "termux"


def about(bundle):
    bundle.send_message(ABOUT_MSG, user_action)


def chmnemmod(bundle):
    bundle.chmnemmod()


QUIT = ["quit()", "quit", "exit", "exit(), logout()", "logout"]
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
    print(WELCOME_MSG)
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
            response, module = bundle.delegate(registry, request, additional, user_action)
            if not response:
                continue
            bundle.pack(request, response, module)
            bundle.post(user_action)
            sleep(0.2)
        except KeyboardInterrupt:
            logger.info("Exiting by CTRL+C...")
            req = ''
            break
        except Exception:
            logger.exception(f"{APP_NAME} prompt exception:")
    logger.info("App is closing...")
    bundle.quit()
    if req.lower() in QUIT and req.lower().startswith("logout") and os.name != "nt":
        os.system("logout")


if __name__ == '__main__':
    main()
    sys.exit()
