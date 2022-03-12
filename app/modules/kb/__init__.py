import os
import re

SETTINGS = {
    "NOCACHE": True,
    "ENTER_CONTEXT": True
}

DIRECTORY = None
KB = None
INPUT = None

recent = []

pattern = re.compile(r"^sel\s+(\d+)$")


def init():
    global DIRECTORY, KB, INPUT
    ctx.set_cleanable_cache(False)
    DIRECTORY = ctx.get_cache_path("indexes")
    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)
    KB = ctx.import_submodule("kb").KnowledgeBase(DIRECTORY)
    INPUT = ctx.get_cache_path("input")
    if not os.path.exists(INPUT):
        os.mkdir(INPUT)
    else:
        KB.index_from_directory(INPUT)


def exit():
    KB.finish_search()


def swallow(string):
    global recent
    if m := re.match(pattern, string):
        num = int(m.group(1)) - 1
        for result in recent:
            if int(result["pos"]) == num:
                filename = result["title"]
                files = os.listdir(INPUT)
                for file in files:
                    if file.lower().startswith(filename.lower()):
                        with open(os.path.join(INPUT, file), "r", encoding=ctx.absolute_cfg("default_encoding")) as fobj:
                            s = fobj.read()
                        return s
        return "File not found"
    if string:
        results = KB.find(string, static_results=True)
        resultstring = "Найдено {} файлов с содержанием {}|".format(len(results), string)
        for result in results:
            resultstring += "{}.{}|[{}]|".format(result["pos"] + 1, result["title"], result["tags"])
        recent = results
        return resultstring
