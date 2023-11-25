"""
Core part of p5 wrapper. p5.js loading is done here.
"""


import pkg_resources
import js
from basthon import kernel

try:
    # Python 3.10
    from pyodide.ffi import to_js as _to_js
except ImportError:
    # Python 3.8
    def _to_js(x, **kwargs):
        return x


__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"


__all__ = ['P5SketchBase', 'load_library']
def __dir__(): return __all__


# loading p5.js
if not hasattr(js, 'p5'):
    with open(pkg_resources.resource_filename(
            'p5', 'p5.min.js')) as f:
        jscode = f.read()
    js.eval(jscode)


class P5SketchBase(object):
    """
    P5 instance object that you can run and stop. Most of the time,
    this object is not build manualy but used as the return of p5.run.
    """
    def __init__(self, setup, draw, preload=None):
        if setup is None:
            raise ValueError("P5: setup function not set!")
        if draw is None:
            raise ValueError("P5: draw function not set!")
        self._preload = preload
        self._setup = setup
        self._draw = draw
        self._node = None
        self._sketch = None

    def _builder(self, setup, draw):
        raise NotImplementedError

    def run(self):
        """
        Start the P5 sketch.
        """
        if self._sketch is not None:
            self._sketch.loop()
            return self

        # new node that will contains canvas
        node = js.document.createElement("div")
        node.style.width = "100%"
        node.style.textAlign = "center"

        build_func = self._builder(self._setup, self._draw, self._preload)

        # main p5 call: create canvas and start drawing
        self._sketch = js.p5.new(build_func, node)

        # fix: in 3D, a blank canvas is added before... remove it
        while len(node.children) > 1:
            node.removeChild(node.children[0])

        # by default, node is hidden
        for n in node.children:
            n.style.visibility = "visible"

        # sending node to Basthon for rendering
        kernel.display_event({"display_type": "p5",
                              "content": node})
        self._node = node
        return self

    def stop(self):
        """
        Stopping call to draw.
        """
        if self._sketch is not None:
            self._sketch.noLoop()

    def delete(self):
        """
        Properly delete the underlying canvas.
        """
        if self._sketch is not None:
            self._sketch.remove()
        if self._node is not None:
            self._node.parentNode.removeChild(self._node)


def load_library(url):
    """ Dynamically load a (p5) js library. """
    return js.Basthon.loadScript(url)
