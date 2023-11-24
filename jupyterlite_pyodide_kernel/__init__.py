"""A JupyterLite kernel powered by Pyodide."""
import builtins
import js 

from ._version import __version__

__all__ = ["__version__", "_jupyter_labextension_paths","patch_input"]


def _jupyter_labextension_paths():
    from .constants import PYODIDE_KERNEL_NPM_NAME

    return [{"src": "labextension", "dest": PYODIDE_KERNEL_NPM_NAME}]

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
