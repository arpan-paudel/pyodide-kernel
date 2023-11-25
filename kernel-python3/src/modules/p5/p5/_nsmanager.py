"""
A scope/namespace manager for managing tricky 'from p5 import *'.
"""

from basthon import kernel


__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"


__all__ = ['NSManager']
def __dir__(): return __all__


class NSManager(object):
    """
    A namespace manager for tracking p5.js global impot (import *).
    Basic usage is:
      (1) create object before p5 import *
      (2) call to update_attributes after import
    """
    def __init__(self, attributes):
        self._initial_ns = set(kernel.locals().keys())
        self._attributes = attributes.copy()
        self._tracked_attributes = None

    def _init_tracked_attributes(self, namespace):
        """ Initialize tracked attributes from updated namespace. """
        namespace = set(namespace.keys())
        self._tracked_attributes = (namespace - self._initial_ns) & self._attributes

    def update_attributes(self, from_object, namespace=None):
        """ Updating namespace attributes from object ones. """
        if self._tracked_attributes is None:
            self._init_tracked_attributes(namespace)
        if namespace is None:
            namespace = kernel.locals()
        for a in self._tracked_attributes:
            namespace[a] = getattr(from_object, a)

    def get_from_global_ns(self, name):
        """ Bonus: get an attribute from global (Basthon) namespace. """
        return kernel.locals().get(name)
