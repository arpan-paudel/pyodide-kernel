"""
A wrapper for p5.js global mode.
This is not intended to be used directly but from
 p5 with from p5 import * .

This is a bit tricky since we have to:
 + get all members names (functions + attributes)
 + exposes them to global scope for import *
 + wrap function that gets a pointer to global instance
 + update attributes (int, str, float, ...) before each call to setup/draw.
This last step is a bit dirty since we modify them (carefully)
directly in the global namespace.
"""

from . import _core  # /!\ do not remove! this ensure p5.js is loaded
from ._nsmanager import NSManager
import js


__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"

try:
    # Python 3.10
    from pyodide.ffi import JsProxy, to_js as _to_js

    def isJsProxy(obj):
        return isinstance(obj, JsProxy)

    def isJsFunc(obj):
        return isJsProxy(obj) and callable(obj)
except ImportError:
    # Python 3.8
    def isJsProxy(obj):
        return type(obj).__name__ == 'JsProxy'

    def isJsFunc(obj):
        return type(obj).__name__ == 'JsBoundMethod'

    def _to_js(x, **kwargs):
        return x


__all__ = ['run', 'show', 'stop', 'load_library', 'update_variables']
def __dir__(): return __all__


# the global p5.js instance
_instance = None
# the global P5SketchGlobal instance
_wrapped_instance = None
# functions that callback global instance
_wrapped_functions = None
# ignored p5.js functions (avoid conflict with builtins)
_ignored_p5_functions = ('setup', 'draw', 'preload', 'abs', 'float',
                         'hex', 'int', 'max', 'min', 'pow', 'print',
                         'round', 'str')
_custom_p5_functions = ('filter', 'map', 'set')


def _p5_members():
    """
    Dynamically recover functions/attributes of a p5 instance.
    """
    # using detached node to ensure canvas is hidden
    node = js.document.createElement('div')
    dummy = js.p5.new(lambda _: None, node)
    members = {a: getattr(dummy, a) for a in dir(dummy)
               if not a.startswith('_')
               and a not in _ignored_p5_functions}
    dummy.remove()
    return members


# splitting members in functions/attributes
_members = _p5_members()
_functions = set()
_attributes = set()
for (k, v) in _members.items():
    if isJsProxy(v):
        if isJsFunc(v):
            _functions.add(k)
        else:
            # JsProxy (canvas, drawingContext, pixels, touches) are ignored
            pass
    else:
        _attributes.add(k)


# import * imports functions and attributes
__all__ += _functions
__all__ += _attributes

# we check for name collision
if len(__all__) != len(set(__all__)):
    duplicate = next(x for x in __all__ if __all__.count(x) > 1)
    raise NameError(f"Internal collision name in p5 for {duplicate}.")


class FunctionWrapper(object):
    """
    A function wrapper for p5.js golbal instance functions.
    """
    def __init__(self, func_name):
        self._func_name = func_name

    def __call__(self, *args):
        args = tuple(_to_js(a) for a in args)
        # calling corresponding function from global instance
        return getattr(_instance, self._func_name)(*args)


# wrapping functions
_wrapped_functions = {f: FunctionWrapper(f) for f in _functions}


# custom wrappers
def _custom_filter(*args):
    if len(args) > 1 and (args[0] is None or callable(args[0])):
        return filter(*args)
    else:
        return _instance.filter(*args)
_wrapped_functions['filter'] = _custom_filter


def _custom_map(*args):
    if len(args) > 1 and callable(args[0]):
        return map(*args)
    else:
        return _instance.map(*args)
_wrapped_functions['map'] = _custom_map


def _custom_set(*args):
    if len(args) < 2:
        return set(*args)
    else:
        return _instance.set(*args)
_wrapped_functions['set'] = _custom_set


def __getattr__(name):
    """
    Wrapping member access:
      + attributes access is delegate to global instance ;
      + function access is delegate to _wrapped_functions.
    """
    if name in _attributes:
        return getattr(_instance, name) if _instance is not None else None
    elif name in _wrapped_functions:
        return _wrapped_functions[name]
    else:
        try:
            return globals()[name]
        except KeyError:
            raise AttributeError(name)


nsmanager = NSManager(_attributes)


def _update_global_attributes(func):
    """
     Updating attributes in the global scope of func with sketch ones.
    """
    nsmanager.update_attributes(_instance, func.__globals__)


def _reset_instance(sketch):
    """
    Reset global instance (stoping current one).
    """
    global _instance
    if _instance is not None:
        # stoping and removing setup/draw seems OK
        # but if strange things appends, it could be safe
        # to remove it with _instance.remove()
        _instance.noLoop()
        _instance.setup = _instance.draw = lambda: None
    _instance = sketch


class P5SketchGlobal(_core.P5SketchBase):
    """
    P5 global object derived from core P5SketchBase, see _core.py.
    """
    def _builder(self, setup, draw, preload):
        """ JS function to create new P5 global instance. """

        def decorator_update_before(f):
            """ update globals attributes of f before calling it. """
            def res(*args, **kwargs):
                _update_global_attributes(f)
                f(*args, **kwargs)
            return res

        def func(sketch):
            _reset_instance(sketch)
            if preload is not None:
                sketch.preload = decorator_update_before(preload)
            if setup is not None:
                sketch.setup = decorator_update_before(setup)
            if draw is not None:
                sketch.draw = decorator_update_before(draw)
        return func


def run(setup=None, draw=None, preload=None):
    """
    Run a new sketch using run(setup, draw) where setup and draw
    are standard p5.js functions.
    If a function is omited, we try to recover it from global namespace.
    """
    global _wrapped_instance

    # trying to recover setup and draw from global namespace
    if setup is None:
        setup = nsmanager.get_from_global_ns('setup')
    if draw is None:
        draw = nsmanager.get_from_global_ns('draw')
    # preload is not recovered from global namespace
    # otherwise next sketch will get previous preload

    _wrapped_instance = P5SketchGlobal(setup, draw, preload).run()


show = run


def stop():
    """
    Stopping global p5 instance.
    """
    return _wrapped_instance.stop()


def load_library(url):
    """ Dynamically load a (p5) js library. """
    return _core.load_library(url)


def update_variables():
    """
    Force p5 variable update. E.g. this can be usefull after createCanvas
    to get width and height updated values.
    """
    nsmanager.update_attributes(_instance)
