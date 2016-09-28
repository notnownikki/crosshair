import importlib
import sys

plugins = set()
command_handlers = {}

try:
    # python 2.7
    reloader = reload
except NameError:
    # python 3.4+
    reloader = importlib.reload


def load(name, force_reload_if_unmanaged=False):
    if name in sys.modules and name not in plugins:
        # we're getting an already loaded module, which we has not been
        # loaded here, return it from sys.modules and add it to our list
        module = sys.modules[name]
        if force_reload_if_unmanaged:
            importlib.reload(module)
    else:
        module = importlib.import_module(name)
    plugins.add(name)
    return module


def reload():
    for name in plugins:
        module = importlib.import_module(name)
        reloader(module)


def register_command_handler(handler_name, handler):
    command_handlers[handler_name] = handler


def get_command_handler(name):
    klass = command_handlers.get(name)
    if klass is None:
        return
    return klass(name)
