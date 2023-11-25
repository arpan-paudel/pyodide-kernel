from . import kernel as __kernel__
from . import _patch_builtins


__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"


__all__ = ['display', 'download']


display = __kernel__.display
download = __kernel__.download


_patch_builtins.patch_all()


# avoid poluting __dict__
del _patch_builtins
