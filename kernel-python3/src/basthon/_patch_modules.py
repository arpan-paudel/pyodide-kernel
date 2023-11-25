from . import kernel
from js import document
from . import importhook
from pathlib import Path

__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"


# Permanent fix for lolviz: since it is not packaged as a wheel but
# as a tgz, it is extracted at the wrong location...
Path("/lib/python3.11/site-packages/lolviz.py").symlink_to("lolviz-1.4.4/lolviz.py")

# Fake cairosvg module (for drawSvg)
Path("/lib/python3.11/site-packages/cairosvg.py").touch()


@importhook.on_import("time")
def patch_time(time):
    """
    Patch time.sleep to do active wait since we can't do better ATM.
    """

    def sleep(secs):
        t = time.perf_counter() + secs
        while time.perf_counter() < t:
            pass

    sleep.__doc__ = time.sleep.__doc__
    time.sleep = sleep


@importhook.on_import("matplotlib")
def patch_matplotlib(mpl):
    """
    Patch the Wasm backend of matplotlib to render figures.
    """
    from matplotlib_pyodide.browser_backend import FigureCanvasWasm as browser_backend
    from matplotlib_pyodide.html5_canvas_backend import (
        FigureCanvasHTMLCanvas as html5_backend,
    )

    # already patched?
    if hasattr(browser_backend, "_original_show"):
        return

    import matplotlib_pyodide.browser_backend as browser_backend_module
    from matplotlib.animation import FuncAnimation

    # fix timer for animated matplotlib (self._timer not defined)
    def __init__(self, *args, **kwargs):
        self._timer = None
        browser_backend_module.TimerBase.__init__(self, *args, **kwargs)

    browser_backend_module.TimerWasm.__init__ = __init__

    # calling original draw_idle only when figure is shown
    _original_draw_idle = browser_backend.draw_idle

    def draw_idle(self, *args, **kwargs):
        if getattr(self, "_shown", False):
            return _original_draw_idle(self, *args, **kwargs)

    browser_backend.draw_idle = draw_idle

    # Allow start/stop animation
    def start(self):
        try:
            self.event_source._timer_start()
        except:
            pass

    def stop(self):
        try:
            self.event_source._timer_stop()
        except:
            pass

    def show_ani(self):
        kernel.display(self)

    FuncAnimation.start = start
    FuncAnimation.stop = stop
    FuncAnimation.show = show_ani
    FuncAnimation.display = show_ani

    # _repr_html_ for FuncAnimation redirects to to_jshtml
    mpl.rcParams["animation.html"] = "jshtml"

    # patching root node creation
    def create_root_element(self):
        self.root = document.createElement("div")
        return self.root

    del html5_backend.create_root_element
    browser_backend.create_root_element = create_root_element

    # patching element getter carefully addressing the case where the
    # root node is not yet added to the DOM
    def get_element(self, name):
        if name == "" or not hasattr(self, "root"):
            root = document
        else:
            root = self.root
        return root.querySelector("#" + self._id + name)

    browser_backend.get_element = get_element

    # patching show
    browser_backend._original_show = browser_backend.show

    def show(self):
        self._shown = True
        res = self._original_show()
        kernel.display_event({"display_type": "matplotlib", "content": self.root})
        return res

    show.__doc__ = browser_backend._original_show.__doc__
    browser_backend.show = show

    # uncomment this to use HTML5 backend by default
    # mpl.use("module://matplotlib_pyodide.html5_canvas_backend")


@importhook.on_import("turtle")
def patch_turtle(turtle):
    """
    Patch Turtle to render and download figures.
    """
    Screen = turtle.Screen

    def show_scene(self):
        root = self.end_scene().cloneNode(True)
        kernel.display_event({"display_type": "turtle", "content": root})
        self.restart()

    show_scene.__doc__ = Screen.show_scene.__doc__

    Screen.show_scene = show_scene

    def download(filename="turtle.svg"):
        """Download screen as svg file."""
        return kernel.download(filename, turtle.svg())

    turtle.download = download
    turtle.__all__.append("download")


@importhook.on_import("sympy")
def patch_sympy(sympy):
    """
    Patch Sympy to render expression using LaTeX (and probably MathJax).
    """

    def pretty_print(*args, sep=" "):
        """
        Print arguments in latex form.
        """
        latex = sep.join(sympy.latex(expr) for expr in args)
        kernel.display_event({"display_type": "sympy", "content": f"$${latex}$$"})

    sympy.pretty_print = pretty_print

    def init_printing():
        """ """
        from sympy.printing.defaults import Printable

        def _repr_latex_(expr):
            return f"$${sympy.latex(expr)}$$"

        Printable._repr_latex_ = _repr_latex_

    sympy.init_printing = init_printing


@importhook.on_import("folium")
def patch_folium(folium):
    """
    Patch Folium to render maps.
    """
    from folium import Map

    def display(self):
        """
        Render map to html.
        """
        kernel.display(self)

    Map.display = display


@importhook.on_import("pandas")
def patch_pandas(pandas):
    """
    Patch Pandas to render data frames.
    """

    def display(self):
        """
        Render data frame to html.
        """
        kernel.display(self)

    pandas.DataFrame.display = display


@importhook.on_import("PIL")
def patch_PIL(PIL):
    from base64 import b64encode
    import io
    from PIL import Image, ImageShow

    # pluging for Notebook
    def _repr_png_(self):
        byio = io.BytesIO()
        self.save(byio, format="PNG")
        return b64encode(byio.getvalue()).decode()

    Image.Image._repr_png_ = _repr_png_

    # pluging image.show()
    class basthonviewer(ImageShow.Viewer):
        def show_image(self, image, **options):
            kernel.display(image)

    ImageShow._viewers = []
    ImageShow.register(basthonviewer)


@importhook.on_import("qrcode")
def patch_qrcode(qrcode):
    """
    * Adding `_repr_svg_` and `show` to qrcode svg images.
    * Fix issue in `qrcode.image.svg.SvgPathImage._write`
    * Add shortcut format to `qrcode.make`
    * Add `download` function to `qrcode.image.base.BaseImage`
    """
    import qrcode.image.base as baseimage
    import qrcode.image.svg as svg
    import qrcode.image.pil as pil

    # display svg images
    def _repr_svg_(self):
        import io

        res = io.BytesIO()
        self.save(res)
        return res.getvalue().decode("utf8")

    svg.SvgFragmentImage._repr_svg_ = _repr_svg_

    def show(self):
        """
        Display this image.
        """
        kernel.display(self)

    svg.SvgFragmentImage.show = show

    # fix qrcode.image.svg.SvgPathImage._write
    def _write(self, stream):
        flag = "_path_appended"
        if not hasattr(self, flag):
            self._img.append(self.make_path())
            setattr(self, flag, True)
        super(svg.SvgPathImage, self)._write(stream)

    svg.SvgPathImage._write = _write

    # shortcut format in qrcode.make
    qrcode._original_make = qrcode.make

    def make(*args, **kwargs):
        if "format" in kwargs:
            format = kwargs.pop("format")
            factories = {"png": pil.PilImage, "svg": svg.SvgPathImage}
            if isinstance(format, str):
                format = format.lower()
            if format not in factories:
                raise ValueError(
                    f"{format} is not supported "
                    f"(should be one of {', '.join(factories.keys())})."
                )
            kwargs["image_factory"] = factories[format]
        return qrcode._original_make(*args, **kwargs)

    qrcode.make = make

    # download
    def meta_download(ext=""):
        def download(self, filename=f"qrcode.{ext}"):
            """Download image as file."""
            import io

            f = io.BytesIO()
            self.save(f)
            f.seek(0)
            # f will be closed by download
            return kernel.download(filename, f.read())

        return download

    baseimage.BaseImage.download = meta_download()
    pil.PilImage.download = meta_download("png")
    svg.SvgFragmentImage.download = meta_download("svg")


@importhook.on_import("pyroutelib3")
def patch_pyroutelib3(pyroutelib3):
    """
    Using requests.get instead of urllib.request.urlretrieve.
    """
    import pyroutelib3.datastore as ds
    import requests

    def urlretrieve(url, filename):
        response = requests.get(url)
        with open(filename, "wb") as f:
            f.write(response.content)

    ds.urlretrieve = urlretrieve


@importhook.on_import("ipythonblocks")
def patch_ipythonblocks(ipythonblocks):
    """
    Apply https://github.com/jiffyclub/ipythonblocks/commit/6ab0067f8dce0ee7bd0cb68b21524f9c1025b5ea

    Since it's not included in version 1.9.0
    """
    import ipythonblocks.ipythonblocks as _ipythonblocks
    from collections.abc import Iterable
    from collections.abc import Sequence

    _ipythonblocks.collections.Iterable = Iterable
    _ipythonblocks.collections.Sequence = Sequence


@importhook.on_import("pkg_resources")
def patch_pkg_resources(pkg_resources):
    """
    Import setuptools in order to have distutils in sys.modules.
    Otherwise, _distutils_hack will warn about old distutils import
    before setuptools. See https://github.com/pypa/setuptools/blob/main/_distutils_hack/__init__.py
    """
    import setuptools


@importhook.on_import("cv2")
def patch_cv2(cv2):
    import io
    import base64

    def imshow(winname, mat):
        is_success, buffer = cv2.imencode(".png", mat)
        io_buf = io.BytesIO(buffer)
        png = base64.b64encode(io_buf.read()).decode()
        dummy = type("Dummy", (object,), {})
        dummy._repr_png_ = lambda: png
        kernel.display(dummy)

    imshow.__doc__ = cv2.imshow.__doc__
    cv2.imshow = imshow


@importhook.on_import("drawSvg")
def patch_drawSvg(drawSvg):
    def download(self, filename="draw.svg"):
        """Download drawing as SVG file."""
        kernel.download(filename, self.asSvg())

    drawSvg.Drawing.download = download


@importhook.on_import("plotly")
def patch_plotly(plotly):
    import js
    import os

    # expose define and require
    js.eval(
        """
window.define = window.requirejsVars?.define;
window.require = window.requirejsVars?.require;
"""
    )

    # do not use notebook_connected to save bandwidth
    # (plotly.js already downloaded)
    os.environ["PLOTLY_RENDERER"] = "notebook"

    from plotly.offline import init_notebook_mode

    init_notebook_mode(connected=False)
