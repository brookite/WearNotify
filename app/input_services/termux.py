import subprocess as sub
import json

def raw_input(ctx):
    try:
        s = sub.run("termux-dialog", stdout=sub.PIPE)
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
