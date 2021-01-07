import http.server
import socketserver
from threading import Thread, Event
import urllib.parse


PORT = 6904
app = None
REQ = "<html><head><title>SEZ Mnemonic</title></head><body>Done! It's working</body>"
event = Event()
uact = False

manip = None
context = None

SETTINGS = {"MODE": 0x1}


class Manipulator:
    def __init__(self, ctx):
        self._ctx = ctx
        self._app = ctx.fork()
        self._buffer = ""
        self._tmp = ""
        self._cursor = self.numberroll()
        self._map = {}
        self._mods = [self.numberroll,
                      self.reverse_numberroll,
                      self.previous_roll]
        self._selectedmod = 0
        self._event = Event()
        self.history = [0]
        self._user_action = False
        self._extra_flush_flag = False
        self.pair(4, self.flush)
        self.pair(5, self.push)
        self.pair(1, self.input)

    def numberroll(self):
        nums = list(map(str, range(1, 10))) + ["0", " ", "null"]
        cursor = 0
        while True:
            if cursor == len(nums):
                cursor = 0
            yield nums[cursor]
            cursor += 1

    def reverse_numberroll(self):
        nums = ["null", " ", "0"] + list(map(str, range(10, 1, -1)))
        cursor = 0
        while True:
            if cursor == len(nums):
                cursor = 0
            yield nums[cursor]
            cursor += 1

    def previous_roll(self):
        cursor = 0
        while True:
            if cursor == len(self.history):
                cursor = 0
            yield self.history[cursor]
            cursor += 1

    def flush(self):
        if self._user_action:
            self.user_action(True)
            return
        if self._buffer:
            if not self._extra_flush_flag:
                self._extra_flush_flag = True
                self.msg("What are you want? Tap input for change input mod or tap flush to clean buffer")
            else:
                self._extra_flush_flag = False
                self._buffer = ""
                self._tmp = ""
                self.msg("Cleaned buffers")
        else:
            self.chmod()

    def msg(self, s):
        self._app.direct_message(s, 0.5)

    def input(self):
        if self._extra_flush_flag:
            self._extra_flush_flag = False
            self.chmod()
            return
        result = next(self._cursor)
        self._tmp = str(result)
        self.msg("Temp input: {}".format(self._tmp))
        self.history[0] = self._tmp

    def push(self):
        if self._user_action:
            self.msg("Released user action")
            self.user_action(False)
            return
        if self._tmp:
            if self._tmp == "null":
                self._buffer += ""
            else:
                self._buffer += self._tmp
            self.msg("Typed: {} | all={}".format(self._tmp, self._buffer))
            self.history.insert(1, self._buffer)
            self._tmp = None
        elif not self._tmp and self._buffer:
            self.msg("Posting...")
            self.post()
        elif not self._tmp and not self._buffer:
            # free mnemonic
            if not self._user_action:
                self.msg("User action lock isn't exist")

    def pair(self, mnem, function):
        assert callable(function)
        self._map[mnem] = function

    def post(self):
        isok = self._app.process(
            self._buffer,
            self.user_action,
            mnemonic_handle=False,
            deny_cache=False,
            handle_ctx=True)
        if not isok:
            self.msg("Something bad")
        self._buffer = ""

    def addmod(self, function):
        self._mods.append(function)

    def handle(self, mnem):
        if mnem:
            mnem = int(mnem)
            print("Got input")
            if mnem in self._map:
                self._map[mnem]()

    def user_action(self, reject=False):
        if not self._user_action:
            print("Entering user action")
            self._user_action = True
            self._event.wait()
            if not reject:
                return True
            else:
                return False
        else:
            self._user_action = False
            self._event.set()
            self._event.clear()

    def chmod(self):
        self._selectedmod += 1
        if self._selectedmod == len(self._mods):
            self._selectedmod = 0
        self._cursor = self._mods[self._selectedmod]()
        self.msg("Selected mod: {}".format(self._cursor.__name__))


def handler(request):
    global app, manip
    if uact:
        user_action()
    if request.isdigit():
        print("Waiting for response...")
        if int(app.config.absolute_cfg("mnemonic_server.mode")) == 0x1:
            manip.handle(request)
        else:
            app.process(
                request,
                user_action,
                handle_ctx=True,
                mnemonic_handle=True,
                deny_cache=True)
            print(">> ", end="")
    else:
        if request.startswith("request/"):
            print("Waiting for response...")
            request = request.replace("request/", "")
            app.process(
                request,
                user_action,
                handle_ctx=True,
                mnemonic_handle=False,
                deny_cache=False)
            print(">> ", end="")


def user_action():
    global uact
    global event
    if not uact:
        print("Entering user action")
        uact = True
        event.wait()
        return True
    else:
        print("Released user action")
        uact = False
        event.set()
        event.clear()


socketserver.TCPServer.allow_reuse_address = True


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def _form_response(self):
        self.protocol_version = 'HTTP/1.1'
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(REQ, 'UTF-8'))

    def do_GET(self):
        data = self.requestline.split(" ")[1][1:]
        thread = Thread(target=handler, args=[data])
        thread.start()
        self._form_response()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = urllib.parse.parse_qs(self.rfile.read(content_length).decode("utf-8"))
        if "data" in post_data:
            data = post_data["data"][0]
        elif "request" in post_data:
            data = post_data["request"][0]
        else:
            data = None
        if data:
            thread = Thread(target=handler, args=["request/" + data])
            thread.start()
        self._form_response()

    def log_message(self, format, *args):
        enabled = False
        if enabled:
            http.server.SimpleHTTPRequestHandler.log_message(self, format, *args)


Handler = MyHttpRequestHandler


def server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("Http Server Serving at port", PORT)
        httpd.serve_forever()


def init(ctx):
    global app, manip
    manip = Manipulator(ctx)
    app = ctx.fork()
    thread = Thread(target=server)
    thread.setDaemon(True)
    thread.start()
