import pydoc
import builtins
import sys
import js
from . import kernel


__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"


__all__ = ['patch_all', 'patch_input', 'patch_help']


def patch_input():
    """ Patching Pyodide input function and set toplevel async calls. """
    _default_input = builtins.input

    def _patched_input(prompt=None):
        if prompt is not None:
            print(prompt, end='', flush=True)
        res = js.prompt(prompt)
        print(res)
        return res

    # copying all writable attributes (usefull to keep docstring and name)
    for a in dir(_default_input):
        try:
            setattr(_patched_input, a, getattr(_default_input, a))
        except Exception:
            pass

    # replacing
    builtins.input = _patched_input

    # define async input
    async def input_async(*args, **kwargs):
        local_input = kernel.locals().get("input", builtins.input)
        if local_input != _patched_input:
            return local_input(*args, **kwargs)
        return await kernel.input_async(*args, **kwargs)
    builtins._basthon_input_async = input_async


def patch_sleep():
    """
    Patching time.sleep function for toplevel async calls.

    It is not a builtin function but the patch put stuff in builtins.
    """
    async def sleep_async(*args, **kwargs):
        import time
        local_sleep = kernel.locals().get("sleep", time.sleep)
        if local_sleep != time.sleep:
            return local_sleep(*args, **kwargs)
        return await kernel.sleep_async(*args, **kwargs)
    builtins._basthon_sleep_async = sleep_async


def patch_help():
    """ Patching help function.

    See pydoc.py in cpython:
    https://github.com/python/cpython/blob/master/Lib/pydoc.py
    It uses a class called ModuleScanner to list packages.
    This class first looks at sys.builtin_module_names then in pkgutil.
    We fake sys.builtin_module_names in order to get it right.
    """
    _default_help = pydoc.help

    def _patched_help(*args, **kwargs):
        backup = sys.builtin_module_names
        to_add = kernel.list_basthon_modules()
        sys.builtin_module_names = backup + tuple(to_add)
        res = _default_help(*args, **kwargs)
        sys.builtin_module_names = backup
        return res

    pydoc.help = _patched_help


def patch_all():
    """
    Patch all builtins by calling all patch_* methods.
    """
    for name, method in globals().items():
        if name.startswith('patch_') and name != 'patch_all':
            method()
