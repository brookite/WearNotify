from common import App
from time import sleep
from core.appconfig import WELCOME_MSG, ABOUT_MSG, APP_NAME
from core.logger import get_logger
import sys


bundle = None


def termux():
    bundle.current_inputservice = "termux"


def speak():
    bundle.collect_input("termux", speech=True)


def about():
    bundle.send_message(ABOUT_MSG, user_action)


QUIT = ["quit()", "quit", "exit", "exit()", "logout"]
END_USER_ACTION = '00'


def user_action():
    try:
        result = input("TYPE ANYTHING FOR CONTINUE; FOR BREAK - (Ctrl+C or 00) >>")
        return not result.startswith(END_USER_ACTION)
    except KeyboardInterrupt:
        print()
        return False


def main():
    global bundle
    logger = get_logger()
    bundle = App()
    bundle.define_ooc_command("termux", termux)
    bundle.define_ooc_command("speak", speak)
    bundle.define_ooc_command("about", about)
    print(WELCOME_MSG)
    sleep(0.1)
    while True:
        try:
            context = '' if not bundle.input_context.get() else \
                f"({bundle.input_context.get()}) "
            print(context, end='')
            req = bundle.collect_input(bundle.current_inputservice)
            if bundle.current_inputservice != "default":
                bundle.current_inputservice = "default"
            if not req:
                print(f"[{APP_NAME}]: Empty request")
                logger.debug("Got a empty request")
                continue
            elif req.lower() in QUIT and not bundle.is_context_entered():
                break
            elif bundle.check_ooc(req):
                req = bundle.handle_ooc(req)
                if not req:
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
            logger.exception(f"{APP_NAME} console exception:")
    logger.info("App is closing...")
    bundle.quit()


if __name__ == '__main__':
    main()
    sys.exit()
