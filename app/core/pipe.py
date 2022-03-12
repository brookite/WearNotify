class Pipe:
    def __init__(self, module, app):
        if not app.config.relative_cfg("isolated_module", app.modules[module]) \
                and not app.config.absolute_cfg("isolated_module"):
            self._module = app.modules[module]
            self._app = app
        else:
            raise PermissionError("Specified module is isolated")

    def init(self):
        return self._module.init()

    def swallow(self, value):
        return self._module.swallow(value)
