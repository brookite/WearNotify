import os
import time
import json


ids = []
count = 1


def escape(string):
    return json.dumps(string, ensure_ascii=False)


def init():
    global ids
    ids = []
    os.system("termux-wake-lock")


def send(packet):
    global count
    global ids
    template = "termux-notification -t s --priority high -c {} -i {}".format(escape(packet), count)
    os.system(template)
    ids.append(count)
    count += 1


def finished(cnt):
    global ids
    time.sleep(1)
    for id in ids:
        os.system("termux-notification-remove {}".format(id))
    ids.clear()


def exit():
    os.system("termux-wake-unlock")
