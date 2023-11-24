"""A JupyterLite kernel powered by Pyodide."""
import builtins
import js 
from . import kernel as __kernel__
from . import _patch_builtins
from ._version import __version__


__all__ = ["__version__", "_jupyter_labextension_paths"]


def _jupyter_labextension_paths():
    from .constants import PYODIDE_KERNEL_NPM_NAME

    return [{"src": "labextension", "dest": PYODIDE_KERNEL_NPM_NAME}]


_patch_builtins.patch_all()


# avoid polluting __dict__
del _patch_builtins
