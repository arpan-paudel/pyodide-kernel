"""
A p5.js wrapper running on top of Pyodide for Basthon.

Basic usage:

from p5 import *

x, y = 100, 50

def setup():
    createCanvas(400, 200)

def draw();
    background(0)
    fill(255)
    rect(x, y, 50, 50)

run(setup, draw)  # equivalent to show(setup, draw)
# or even better
run()  # equivalent to show()
# you can stop drawing
stop()

Be careful when using import *. We assume:
 + no new variable declaration with same name as p5.js one
   between import and first call to run
 + setup and draw are declared in the global namespace
 + only one import statement

otherwise, behavior is undefined.
"""

from . import _global


__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"


__all__ = _global.__all__
__dir__ = _global.__dir__

__getattr__ = _global.__getattr__
