# backend.py - execute rendering, open files in viewer

import os
import re
import errno
import logging
import platform
import subprocess

import js
import base64
from basthon import download
try:
    # Python 3.10
    from pyodide.ffi import to_js as __to_js
    def _to_js(x):
        return __to_js(x, dict_converter=js.Object.fromEntries)
except ImportError:
    # Python 3.8
    def _to_js(x, **kwargs):
        return x

from . import _compat

from . import tools

__all__ = [
    'render', 'pipe', 'version', 'view',
    'ENGINES', 'FORMATS', 'RENDERERS', 'FORMATTERS',
    'ExecutableNotFound', 'RequiredArgumentError',
]

ENGINES = {  # http://www.graphviz.org/pdf/dot.1.pdf
    'dot', 'neato', 'twopi', 'circo', 'fdp', 'sfdp', 'patchwork', 'osage',
}

FORMATS = {  # http://www.graphviz.org/doc/info/output.html
    'bmp',
    'canon', 'dot', 'gv', 'xdot', 'xdot1.2', 'xdot1.4',
    'cgimage',
    'cmap',
    'eps',
    'exr',
    'fig',
    'gd', 'gd2',
    'gif',
    'gtk',
    'ico',
    'imap', 'cmapx',
    'imap_np', 'cmapx_np',
    'ismap',
    'jp2',
    'jpg', 'jpeg', 'jpe',
    'json', 'json0', 'dot_json', 'xdot_json',  # Graphviz 2.40
    'pct', 'pict',
    'pdf',
    'pic',
    'plain', 'plain-ext',
    'png',
    'pov',
    'ps',
    'ps2',
    'psd',
    'sgi',
    'svg', 'svgz',
    'tga',
    'tif', 'tiff',
    'tk',
    'vml', 'vmlz',
    'vrml',
    'wbmp',
    'webp',
    'xlib',
    'x11',
}

RENDERERS = {  # $ dot -T:
    'cairo',
    'dot',
    'fig',
    'gd',
    'gdiplus',
    'map',
    'pic',
    'pov',
    'ps',
    'svg',
    'tk',
    'vml',
    'vrml',
    'xdot',
}

FORMATTERS = {'cairo', 'core', 'gd', 'gdiplus', 'gdwbmp', 'xlib'}

PLATFORM = platform.system().lower()


log = logging.getLogger(__name__)


class ExecutableNotFound(RuntimeError):
    """Exception raised if the Graphviz executable is not found."""

    _msg = ('failed to execute %r, '
            'make sure the Graphviz executables are on your systems\' PATH')

    def __init__(self, args):
        super(ExecutableNotFound, self).__init__(self._msg % args)


class RequiredArgumentError(Exception):
    """Exception raised if a required argument is missing."""


class CalledProcessError(_compat.CalledProcessError):

    def __str__(self):
        s = super(CalledProcessError, self).__str__()
        return '%s [stderr: %r]' % (s, self.stderr)


def command(engine, format_, filepath=None, renderer=None, formatter=None):
    """Return args list for ``subprocess.Popen`` and name of the rendered file."""
    if formatter is not None and renderer is None:
        raise RequiredArgumentError('formatter given without renderer')

    if engine not in ENGINES:
        raise ValueError('unknown engine: %r' % engine)
    if format_ not in FORMATS:
        raise ValueError('unknown format: %r' % format_)
    if renderer is not None and renderer not in RENDERERS:
        raise ValueError('unknown renderer: %r' % renderer)
    if formatter is not None and formatter not in FORMATTERS:
        raise ValueError('unknown formatter: %r' % formatter)

    output_format = [f for f in (format_, renderer, formatter) if f is not None]
    cmd = [engine, '-T%s' % ':'.join(output_format)]

    if filepath is None:
        rendered = None
    else:
        cmd.extend(['-O', filepath])
        suffix = '.'.join(reversed(output_format))
        rendered = '%s.%s' % (filepath, suffix)

    return cmd, rendered


if PLATFORM == 'windows':  # pragma: no cover
    def get_startupinfo():
        """Return subprocess.STARTUPINFO instance hiding the console window."""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
else:
    def get_startupinfo():
        """Return None for startupinfo argument of ``subprocess.Popen``."""
        return None


def run(cmd, input=None, capture_output=False, check=False, encoding=None,
        quiet=False, **kwargs):
    """Run the command described by cmd and return its (stdout, stderr) tuple."""
    log.debug('run %r', cmd)

    if input is not None:
        kwargs['stdin'] = subprocess.PIPE
        if encoding is not None:
            input = input.encode(encoding)

    if capture_output:
        kwargs['stdout'] = kwargs['stderr'] = subprocess.PIPE

    try:
        proc = subprocess.Popen(cmd, startupinfo=get_startupinfo(), **kwargs)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise ExecutableNotFound(cmd)
        else:
            raise

    out, err = proc.communicate(input)

    if not quiet and err:
        _compat.stderr_write_bytes(err, flush=True)

    if encoding is not None:
        if out is not None:
            out = out.decode(encoding)
        if err is not None:
            err = err.decode(encoding)

    if check and proc.returncode:
        raise CalledProcessError(proc.returncode, cmd,
                                 output=out, stderr=err)

    return out, err


def render(engine, format, filepath, renderer=None, formatter=None, quiet=False, scale=1):
    """Render file with Graphviz ``engine`` into ``format``,  return result filename.

    Args:
        engine: The layout commmand used for rendering (``'dot'``, ``'neato'``, ...).
        format: The output format used for rendering (``'pdf'``, ``'png'``, ...).
        filepath: Path to the DOT source file to render.
        renderer: The output renderer used for rendering (``'cairo'``, ``'gd'``, ...).
        formatter: The output formatter used for rendering (``'cairo'``, ``'gd'``, ...).
        quiet (bool): Suppress ``stderr`` output from the layout subprocess.
    Returns:
        The (possibly relative) path of the rendered file.
    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter`` are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz executable is not found.
        subprocess.CalledProcessError: If the exit status is non-zero.

    The layout command is started from the directory of ``filepath``, so that
    references to external files (e.g. ``[image=...]``) can be given as paths
    relative to the DOT source file.
    """
    if format not in ('svg', 'png'):
        raise ValueError("Only svg and png format are supported in Graphviz.")

    dirname, filename = os.path.split(filepath)

    with open(filepath, 'rb') as f:
        data = f.read()

    del filepath

    rendered = "%s.%s" % (os.path.splitext(filename)[0], format)

    svg = pipe(engine, 'svg', data, renderer, formatter, quiet)

    if format == 'svg':
        download(rendered, svg)
    else:
        download_png_from_svg(svg, rendered, scale)
    return rendered


def download_png_from_svg(svg, filename, scale):
    """ Download PNG image converted from bytes svg (encoded). """
    svg_image = js.document.createElement('img')
    svg_data_url = 'data:image/svg+xml;base64,'
    svg_data_url += base64.b64encode(svg).decode()

    def img_loaded(event):
        canvas = js.document.createElement('canvas')
        canvas.width = svg_image.width * scale
        canvas.height = svg_image.height * scale

        context = canvas.getContext("2d")
        context.drawImage(svg_image, 0, 0, canvas.width, canvas.height)

        data = canvas.toDataURL("image/png")
        data = base64.b64decode(data.split(',')[-1])
        download(filename, data)

    svg_image.onload = img_loaded
    svg_image.src = svg_data_url


def pipe(engine, format, data, renderer=None, formatter=None, quiet=False):
    """Return ``data`` piped through Graphviz ``engine`` into ``format``.

    Args:
        engine: The layout commmand used for rendering (``'dot'``, ``'neato'``, ...).
        format: The output format used for rendering (``'pdf'``, ``'png'``, ...).
        data: The binary (encoded) DOT source string to render.
        renderer: The output renderer used for rendering (``'cairo'``, ``'gd'``, ...).
        formatter: The output formatter used for rendering (``'cairo'``, ``'gd'``, ...).
        quiet (bool): Suppress ``stderr`` output from the layout subprocess.
    Returns:
        Binary (encoded) stdout of the layout command.
    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter`` are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz executable is not found.
        subprocess.CalledProcessError: If the exit status is non-zero.
    """

    if format != 'svg':
        raise ValueError("Only svg format is supported in pipe fucnction (Graphviz).")
    viz = js.Viz.new()
    options = _to_js({'engine': engine, 'format': 'svg'})
    return viz.renderString(data.decode(), options).encode()


def version():
    """Return the version number tuple from the ``stderr`` output of ``dot -V``.

    Returns:
        Two, three, or four ``int`` version ``tuple``.
    Raises:
        graphviz.ExecutableNotFound: If the Graphviz executable is not found.
        subprocess.CalledProcessError: If the exit status is non-zero.
        RuntimmeError: If the output cannot be parsed into a version number.

    Note:
        Ignores the ``~dev.<YYYYmmdd.HHMM>`` portion of development versions.

    See also Graphviz Release version entry format:
    https://gitlab.com/graphviz/graphviz/-/blob/f94e91ba819cef51a4b9dcb2d76153684d06a913/gen_version.py#L17-20
    """
    return (2, 40, 1)


def view(filepath, quiet=False):
    """Open filepath with its default viewing application (platform-specific).

    Args:
        filepath: Path to the file to open in viewer.
        quiet (bool): Suppress ``stderr`` output from the viewer process
                      (ineffective on Windows).
    Raises:
        RuntimeError: If the current platform is not supported.

    Note:
        There is no option to wait for the application to close, and no way
        to retrieve the application's exit status.
    """
    try:
        view_func = getattr(view, PLATFORM)
    except AttributeError:
        raise RuntimeError('platform %r not supported' % PLATFORM)
    view_func(filepath, quiet)


@tools.attach(view, 'darwin')
def view_darwin(filepath, quiet):
    """Open filepath with its default application (mac)."""
    cmd = ['open', filepath]
    log.debug('view: %r', cmd)
    popen_func = _compat.Popen_stderr_devnull if quiet else subprocess.Popen
    popen_func(cmd)


@tools.attach(view, 'linux')
@tools.attach(view, 'freebsd')
def view_unixoid(filepath, quiet):
    """Open filepath in the user's preferred application (linux, freebsd)."""
    cmd = ['xdg-open', filepath]
    log.debug('view: %r', cmd)
    popen_func = _compat.Popen_stderr_devnull if quiet else subprocess.Popen
    popen_func(cmd)


@tools.attach(view, 'windows')
def view_windows(filepath, quiet):
    """Start filepath with its associated application (windows)."""
    # TODO: implement quiet=True
    filepath = os.path.normpath(filepath)
    log.debug('view: %r', filepath)
    os.startfile(filepath)
