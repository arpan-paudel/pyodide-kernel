import pydoc
import builtins
import sys
import js
from . import kernel


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
