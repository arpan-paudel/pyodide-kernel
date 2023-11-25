import pkg_resources
import js

try:
    # Python 3.10
    from pyodide.ffi import to_js as _to_js
except ImportError:
    # Python 3.8
    _to_js = None


# loading proj4js
with open(pkg_resources.resource_filename(
            'proj4py', 'proj4.min.js')) as f:
    jscode = f.read()

js.eval(jscode)


if _to_js is None:
    # internal proj4 is main JS proj4
    proj4 = js.proj4
else:
    def wrap(func):
        def f(*args):
            return func(*(_to_js(x) for x in args))
        return f

    # internal proj4 points to main JS proj4
    def proj4(*args):
        p4 = js.proj4(*args)
        if hasattr(p4, "forward"):
            p4.forward = wrap(p4.forward)
        if hasattr(p4, "inverse"):
            p4.inverse = wrap(p4.inverse)
        return p4

    proj4.defs = wrap(js.proj4.defs)

# Lambert 93 definition
proj4.defs("EPSG:2154",
           "+proj=lcc +lat_1=49 +lat_2=44 +lat_0=46.5 +lon_0=3 +x_0=700000 +y_0=6600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")
