from . import _patch_builtins

_patch_builtins.patch_all()


# avoid poluting __dict__
del _patch_builtins
