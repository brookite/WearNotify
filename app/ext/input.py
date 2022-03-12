import readline


class ConsoleInputCompleter:
    def __init__(self, commands):
        self._set_commands(commands)

    @property
    def commands(self):
        return self._commands

    @commands.setter
    def commands(self, value):
        self._set_commands(value)

    def _set_commands(self, commands):
        if not isinstance(commands, dict) and hasattr(commands, "__iter__"):
            commands = dict.fromkeys(commands, [])
        elif not hasattr(commands, "__iter__"):
            raise TypeError("Incorrect commands type, needed iterable")
        self._commands = commands
        self._suggestions = []

    def complete(self, text, state):
        if state == 0:
            line_begin = readline.get_begidx()
            line_end = readline.get_endidx()
            current_line = readline.get_line_buffer()
            words = current_line.split()
            current_line = current_line[line_begin:line_end]

            if not words:
                # empty string
                self._suggestions = sorted(self._commands.keys())
            else:
                if line_begin == 0:
                    candidates = self._commands.keys()
                else:
                    if words[0] in self._commands:
                        candidates = self._commands[words[0]]
                    else:
                        candidates = []

                if current_line:
                    self._suggestions = [word for word in candidates
                                         if word.startswith(current_line)]
                else:
                    self._suggestions = candidates
        try:
            response = self._suggestions[state]
            return response
        except IndexError:
            return None


def init_completing(commands=[]):
    completer = ConsoleInputCompleter(commands)
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')
    return completer


def set_history(history):
    readline.clear_history()
    for item in history:
        readline.add_history(item)


def set_history_autofilling(enabled):
    readline.set_auto_history(enabled)


def clear_history():
    readline.clear_history()
