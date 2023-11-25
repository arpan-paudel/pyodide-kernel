# This is the graphviz package by Sebastian Bank adapted to Basthon by
# Romain Casati under the GNU GPL v3 License.

# graphviz - create dot, save, render, view

"""Assemble DOT source code and render it with Graphviz.

>>> dot = Digraph(comment='The Round Table')

>>> dot.node('A', 'King Arthur')
>>> dot.node('B', 'Sir Bedevere the Wise')
>>> dot.node('L', 'Sir Lancelot the Brave')

>>> dot.edges(['AB', 'AL'])

>>> dot.edge('B', 'L', constraint='false')

>>> print(dot)  #doctest: +NORMALIZE_WHITESPACE
// The Round Table
digraph {
    A [label="King Arthur"]
    B [label="Sir Bedevere the Wise"]
    L [label="Sir Lancelot the Brave"]
    A -> B
    A -> L
    B -> L [constraint=false]
}
"""

######
# Added for Basthon support -- start

import pkg_resources
import js


# loading viz.js
with open(pkg_resources.resource_filename(
            'graphviz', 'viz.min.js')) as f:
    jscode = f.read()
js.eval(jscode)

# loading full.render.min.js
with open(pkg_resources.resource_filename(
            'graphviz', 'full.render.min.js')) as f:
    jscode = f.read()
js.eval(jscode)

# Added for Basthon support -- end
######

from .dot import Graph, Digraph
from .files import Source
from .lang import escape, nohtml
from .backend import (render, pipe, version, view,
                      ENGINES, FORMATS, RENDERERS, FORMATTERS,
                      ExecutableNotFound, RequiredArgumentError)


__all__ = [
    'Graph', 'Digraph',
    'Source',
    'escape', 'nohtml',
    'render', 'pipe', 'version', 'view',
    'ENGINES', 'FORMATS', 'RENDERERS', 'FORMATTERS',
    'ExecutableNotFound', 'RequiredArgumentError',
]

__title__ = 'graphviz'
__version__ = '0.15.dev0'
__author__ = 'Sebastian Bank <sebastian.bank@uni-leipzig.de>'
__license__ = 'MIT, see LICENSE.txt'
__copyright__ = 'Copyright (c) 2013-2020 Sebastian Bank'

#: Set of known layout commands used for rendering (``'dot'``, ``'neato'``, ...)
ENGINES = ENGINES

#: Set of known output formats for rendering (``'pdf'``, ``'png'``, ...)
FORMATS = FORMATS

#: Set of known output formatters for rendering (``'cairo'``, ``'gd'``, ...)
FORMATTERS = FORMATTERS

#: Set of known output renderers for rendering (``'cairo'``, ``'gd'``, ...)
RENDERERS = RENDERERS

ExecutableNotFound = ExecutableNotFound

RequiredArgumentError = RequiredArgumentError
