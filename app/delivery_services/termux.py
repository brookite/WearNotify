import os
import time
import json
import subprocess as sub


ids = []
count = 1

textbuffer = ""
allow_speech = False
speech_params = {
    "pitch": 1.0,
    "rate": 1.0,
    "stream": "MUSIC"
}


def escape(string):
    return json.dumps(string, ensure_ascii=False)


def init():
    global ids
    ids = []
    os.system("termux-wake-lock")


def send(packet):
    global count, textbuffer, ids
    template = "termux-notification -t s --priority high -c {} -i {}".format(escape(packet), count)
    os.system(template)
    textbuffer += packet
    ids.append(count)
    count += 1


def finished(cnt):
    global ids, textbuffer
    time.sleep(1)
    if allow_speech:
        pitch = speech_params["pitch"]
        rate = speech_params["rate"]
        stream = speech_params["stream"]
        speech_template = f"termux-tts-speak -p {pitch} -r {rate} -s {stream} {textbuffer}"
        os.system(speech_template)
    for id in ids:
        os.system("termux-notification-remove {}".format(id))
    ids.clear()
    textbuffer = ""


def exit():
    os.system("termux-wake-unlock")
