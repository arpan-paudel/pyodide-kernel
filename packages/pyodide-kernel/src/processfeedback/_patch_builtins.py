import builtins
import js


__all__ = ['patch_all', 'patch_input']


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


def patch_all():
    """
    Patch all builtins by calling all patch_* methods.
    """
    for name, method in globals().items():
        if name.startswith('patch_') and name != 'patch_all':
            method()
