"""
This is the Python part of the Basthon Kernel.
"""
import os
import sys
import importlib
import asyncio
import js
from ._console import InteractiveConsole
from . import _patch_modules
from pyodide.ffi import to_js, JsProxy

__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"

# where we put user supplied modules
_user_modules_root = "/basthon_user_modules"
# we don't insert at position 0 since
# https://github.com/iodide-project/pyodide/issues/737#issuecomment-750858417
sys.path.insert(2, _user_modules_root)
# can't figure out why this is needed...
importlib.invalidate_caches()


# interpretation system is the Pyodide's interactive console
_console = InteractiveConsole()


def locals():
    """Global evaluation namespace."""
    return _console.locals


def display_event(data):
    """Dispatching eval.display event with display data."""
    display_data = {}
    # Updating display data with evaluation data.
    # get evaluation data from namespace
    eval_data = _console.locals["__eval_data__"]
    if eval_data is not None:
        display_data.update(eval_data)
    display_data.update(data)
    js.Basthon.dispatchEvent(
        "eval.display", to_js(display_data, dict_converter=js.Object.fromEntries)
    )


async def input_async(prompt=None, password=False):
    """Dispatching eval.input event with data."""
    eval_data = _console.locals["__eval_data__"]
    eval_data = to_js(eval_data, dict_converter=js.Object.fromEntries)
    return await js.Basthon.inputAsync(prompt, False, eval_data)


async def sleep_async(secs):
    """Suspend execution for secs seconds."""
    await asyncio.sleep(secs)


def format_repr(obj):
    """Format data to support different repr types."""
    res = {"text/plain": repr(obj)}
    mimes = {
        "text/html": "_repr_html_",
        "image/svg+xml": "_repr_svg_",
        "image/png": "_repr_png_",
        "text/latex": "_repr_latex_",
        "text/markdown": "_repr_markdown_",
    }
    for mime, _repr in mimes.items():
        if hasattr(obj, _repr):
            try:
                representation = getattr(obj, _repr)()
                if representation is not None:
                    res[mime] = representation
            except Exception:
                pass
    return res


def display(
    *objs,
    include=None,
    exclude=None,
    metadata=None,
    transient=None,
    display_id=None,
    raw=False,
    clear=False,
    **kwargs
):
    """Display a Python object in all frontends.
    By default all representations will be computed and sent to the frontends.
    Frontends can decide which representation is used and how.
    In terminal IPython this will be similar to using :func:`print`, for use in richer
    frontends see Jupyter notebook examples with rich display logic.
    Parameters
    ----------
    *objs : object
        The Python objects to display.
    raw : bool, optional
        Are the objects to be displayed already mimetype-keyed dicts of raw display data,
        or Python objects that need to be formatted before display? [default: False]
    include : list, tuple or set, optional
        A list of format type strings (MIME types) to include in the
        format data dict. If this is set *only* the format types included
        in this list will be computed.
    exclude : list, tuple or set, optional
        A list of format type strings (MIME types) to exclude in the format
        data dict. If this is set all format types will be computed,
        except for those included in this argument.
    metadata : dict, optional
        A dictionary of metadata to associate with the output.
        mime-type keys in this dictionary will be associated with the individual
        representation formats, if they exist.
    transient : dict, optional
        A dictionary of transient data to associate with the output.
        Data in this dict should not be persisted to files (e.g. notebooks).
    display_id : str, bool optional
        Set an id for the display.
        This id can be used for updating this display area later via update_display.
        If given as `True`, generate a new `display_id`
    clear : bool, optional
        Should the output area be cleared before displaying anything? If True,
        this will wait for additional output before clearing. [default: False]
    **kwargs : additional keyword-args, optional
        Additional keyword-arguments are passed through to the display publisher."""
    for obj in objs:
        if not raw:
            obj = format_repr(obj)
        display_event({"display_type": "multiple", "content": obj})


def download(filename, data=None):
    """
    Download a file from the local filesystem.

    Usage:
        download("path_to_file")
        download("filename", data)
    """
    if data is None:
        data = get_file(filename)
        _, filename = os.path.split(filename)
    if isinstance(data, str):
        data = data.encode()
    js.Basthon.download(to_js(data), filename)


def put_file(filepath, content):
    """
    Put a file on the (emulated) local filesystem.
    """
    if isinstance(content, JsProxy):
        content = content.to_py()
    dirname, _ = os.path.split(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    with open(filepath, "wb") as f:
        f.write(content)


async def put_module(filename, content):
    """
    Put a module (*.py file) on the (emulated) local filesystem
    """
    if isinstance(content, JsProxy):
        content = content.to_py()
    source = content.tobytes().decode()
    await js.pyodide.loadPackagesFromImports(source)

    _, fname = os.path.split(filename)
    module_path = os.path.join(_user_modules_root, fname)
    put_file(module_path, content)
    file_finder = sys.path_importer_cache.get(_user_modules_root)
    if file_finder is None:
        # can't figure out why this is needed...
        importlib.invalidate_caches()
    else:
        file_finder.invalidate_caches()


def user_modules():
    """
    List modules launched via put_module.
    """
    if not os.path.exists(_user_modules_root):
        return []
    return [f for f in os.listdir(_user_modules_root) if f.endswith(".py")]


def get_file(filepath):
    """
    Get a file content from the (emulated) local filesystem.
    """
    with open(filepath, "rb") as fd:
        return fd.read()


def get_user_module_file(filename):
    """
    Get a module content (*.py) put in the user modules directory
    (via put_module).
    """
    return get_file(os.path.join(_user_modules_root, filename))


def list_basthon_modules(pure_basthon=False):
    """
    List modules provided by Pyodide and Basthon from repodata.json.

    if `pure_basthon` is True, return modules added by Basthon.
    """

    if pure_basthon:
        packages = js.pyodide._api.repodata_packages.to_py()
        root_url = js.Basthon.basthonModulesRoot(True)
        packages = [
            p["name"] for p in packages.values() if p["file_name"].startswith(root_url)
        ]
    else:
        packages = js.pyodide._api._import_name_to_package_name.to_py()
        packages = [p for p in packages.keys() if "." not in p] + ["js"]
    return packages


def importables():
    """List of all importable modules."""
    import pkgutil

    from_sys = set(x for x in sys.modules.keys() if "." not in x)
    from_pkgutil = set(p.name for p in pkgutil.iter_modules())
    from_basthon = set(list_basthon_modules())
    return sorted(from_sys.union(from_pkgutil, from_basthon))


def restart():
    return _console.restart()


def execution_count():
    return _console.execution_count


# copying methods from _console to this module
for f in ("eval", "complete", "banner", "more"):
    globals()[f] = getattr(_console, f)
