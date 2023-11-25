"""
A p5.js instance mode wrapper running on top of Pyodide for Basthon.

Basic usage:

x, y = 100, 50

def setup(sketch):
    sketch.createCanvas(400, 200)

def draw(sketch);
    sketch.background(0)
    sketch.fill(255)
    sketch.rect(x, y, 50, 50)

sketch = p5.instance.run(setup, draw)
p5.instance.stop(sketch)  # equivalent to sketch.stop()
"""


from . import _core  # /!\ do not remove! this ensure p5.js is loaded


__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"


__all__ = ['run', 'stop', 'delete', 'load_library']
def __dir__(): return __all__


class P5SketchInstance(_core.P5SketchBase):
    """
    P5 instance object derived from core P5SketchBase, see _core.py.
    """
    def _builder(self, setup, draw, preload):
        """ JS function to create new P5 instance. """

        def func(sketch):
            def _setup(): setup(sketch)

            def _draw(): draw(sketch)

            def _preload(): preload(sketch)

            if setup is not None:
                sketch.setup = _setup
            if draw is not None:
                sketch.draw = _draw
            if preload is not None:
                sketch.preload = _preload
        return func


def run(setup, draw=None, preload=None):
    """
    Run an existing sketch using run(sketch) or create and run a new one
    using run(setup, draw) where setup and draw are functions taking as
    first argument a p5 sketch.
    """
    if draw is None and isinstance(setup, P5SketchInstance):
        return setup.run()

    return P5SketchInstance(setup, draw, preload).run()


def stop(sketch):
    """
    Stopping call to draw from a sketch returned by p5.run.
    """
    return sketch.stop()


def delete(sketch):
    """
    Properly delete the underlying canvas.
    """
    return sketch.delete()


def load_library(url):
    """ Dynamically load a (p5) js library. """
    return _core.load_library(url)
