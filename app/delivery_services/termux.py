import os
import time

ids = None
count = 1


def init(ctx):
    global ids
    ids = []


def send(ctx, packet):
    global count
    global ids
    template = "termux-notification -t s --priority high -c {} -i {}".format(repr(packet), count)
    os.system(template)
    ids.append(count)
    count += 1


def finished(ctx, cnt):
    global ids
    time.sleep(1)
    for id in ids:
        os.system("termux-notification-remove {}".format(id))
    ids.clear()
