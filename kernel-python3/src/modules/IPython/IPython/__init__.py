"""
Partial IPython implementation to access usefull methods in Basthon.
"""


from . import display


__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"


__all__ = ['get_ipython', 'display']


def get_ipython():
    """ IPython is only partially implemented in Basthon so we
    can't return an IPython instance here.
    """
    return None
