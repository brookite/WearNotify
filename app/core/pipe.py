class Pipe:
    def __init__(self, module, app):
        self._module = app.modules[module]
        self._app = app

    def init(self):
        return self._module.init()

    def swallow(self, value):
        return self._module.swallow(value)
