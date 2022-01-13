import subprocess as sub
import json


def raw_input(speech=False):
    try:
        executable = "text" if not speech else "speech"
        s = sub.run("termux-dialog " + executable, stdout=sub.PIPE)
        if s.stdout:
            result = json.loads(s.stdout.decode("utf-8"))
            if result["text"]:
                return result["text"]
            else:
                return None
        else:
            return None
    except Exception as e:
        print(str(e))
        return None
