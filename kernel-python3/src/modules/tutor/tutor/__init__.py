"""
PythonTutor port to Basthon.

For privacy concern, it avoid sending user code to PythonTutor
(iframe embeding). Instead, it generates PythonTutor's traces with Basthon's
interpreter then create a PythonTutor vizualiser.
"""

import js
import pkg_resources
from urllib.parse import quote
import json
from .generate_trace import generate_trace
from basthon import kernel
import re
import builtins

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


__all__ = ['tutor', 'clear_inputs']


# we log input results to pass it to python-tutor
# WARNING: in the presence of input, the tutor() call shoud be put at the end.
# WARNING #2: this input monkey patch is in conflict with the
#             async/await input monkey patch in gernel._patch_builtins.
_input_log = []
_builtin_input = input


def _input(*args, **kwargs):
    res = _builtin_input(*args, **kwargs)
    _input_log.append(res)
    return res


builtins.input = _input


def clear_inputs():
    """ Clear all previous call to builtin input. """
    _input_log.clear()


# get iframe.html
with open(pkg_resources.resource_filename('tutor', 'iframe.html')) as f:
    iframe_template = f.read()


_iframe_count = -1


def _new_iframe_id():
    global _iframe_count
    _iframe_count += 1
    return f"basthon-pythontutor-iframe-{_iframe_count}"


# to dynamically set the iframe height we need this communication
# system between iframe and parent
def _iframe_resize(event, *args):
    data = event.data
    if data is None:
        return

    type = data.type
    if type != 'pytutor-iframe-resize':
        return

    target = data.target
    height = data.height
    if target is None or height is None:
        return
    js.document.getElementById(target).style.height = f"{int(height) + 20}px"


js.window.addEventListener('message', _to_js(_iframe_resize))


def tutor(**kwargs):
    """
    Tutor the current executed script with PythonTutor.

    See PythonTutor at http://pythontutor.com for available options.

    The code is not executed by PythonTutor itself (server side)
    but by Basthon. The solution is actually entirely executed
    in frontend.
    """
    code = kernel.locals()['__eval_data__']['code']
    lines = code.split('\n')

    # listing tutor import lines then remove
    # this is hacky... and should be implemented with inspect or tokenize
    regex_comment = re.compile(r'^([^#]*)#(.*)$')
    import_lines = [i for i, line in enumerate(lines)
                    if regex_comment.sub(r'\1', line).rstrip() in (
                            'import tutor',
                            'from tutor import tutor',
                            'from tutor import *')]
    for index in import_lines[::-1]:
        del lines[index]

    # listing tutor() call lines
    # this is hacky... and should be implemented with inspect or tokenize
    tutor_lines = [i for i, line in enumerate(lines)
                   if line.startswith('tutor.tutor(')
                   or line.startswith('tutor(')]
    # actually it could be everywhere but not nested
    if not tutor_lines:
        raise RuntimeError("tutor.tutor() should be called on first or last line.")
    # removing tutor() call lines
    for index in tutor_lines[::-1]:
        del lines[index]

    # rebuild code
    code = '\n'.join(lines).strip('\n')

    # generate PythonTutor trace
    trace = json.dumps(generate_trace(code, input=json.dumps(_input_log),
                                      **kwargs))
    # empty input logs
    clear_inputs()

    # get new iframe id
    id = _new_iframe_id()

    # building pytutor visualizer
    iframe = iframe_template.format(
        json_trace=trace,
        extern_tutor_url=f"{js.Basthon.basthonModulesRoot(True)}/extern",
        iframe_id=id)
    iframe = f'<iframe id="{id}" style="width: 100%; height: 400px;" frameborder="0" src="data:text/html;charset=utf-8,{quote(iframe)}"></iframe>'

    # sending node to Basthon for rendering
    kernel.display_event({"display_type": "tutor",
                          "content": iframe,
                          "iframe-id": id})
