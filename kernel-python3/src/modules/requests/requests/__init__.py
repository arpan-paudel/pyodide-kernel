"""
This is not the real requests Python module
but a partial API implementation for Basthon.
"""

import js

__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"


__all__ = ['request']


# This warning is no longer needed.
# print("Warning: this is not the real requests Python module"
#       " but a partial API implementation for Basthon.")


class ConnectionError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Headers(dict):
    """ Case insensitive dict build from request """
    def __init__(self, req):
        for h in req.getAllResponseHeaders().rstrip().split('\r\n'):
            h = h.split(':')
            self[h[0]] = ':'.join(h[1:]).lstrip()

    def __setitem__(self, key, value):
        super(Headers, self).__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super(Headers, self).__getitem__(key.lower())


class Response(object):
    """ See requests.Response API """
    def __init__(self, req):
        self._req = req  # only for debuging purpose
        self.url = req.responseURL
        self.headers = Headers(req)
        self.status_code = req.status
        self.reason = req.statusText
        self.ok = self.status_code < 400
        self.cookies = None
        content_type = self.headers.get('content-type', '')
        self.encoding = next((x.replace("charset=", '').replace(' ', '')
                              for x in content_type.split(';')
                              if "charset=" in x), None)
        # throw away high-order bytes (& 255)
        self.content = bytes([ord(c) & 255 for c in req.response])
        try:
            self.text = self.decode(self.encoding)
        except Exception:
            self.text = req.responseText

    def decode(self, charset="utf-8"):
        return self.content.decode(charset)

    def json(self, charset="utf-8", **kwargs):
        import json
        return json.loads(self.decode(charset), **kwargs)


def request(method, url, **kwargs):
    """ See requests.request """
    # url params
    if "params" in kwargs:
        url += "?" + "&".join((f"{k}={v}" for k, v in kwargs["params"].items()))
    req = js.eval("var __basthon_req = new XMLHttpRequest(); __basthon_req")  # hack for using js try/catch (see below)
    req.open(method.lower(), url, False)  # synchronous request
    req.overrideMimeType('text/plain; charset=x-user-defined')
    # headers
    for k, v in kwargs.get('headers', {}).items():
        req.setRequestHeader(k, v)

    def send():
        req.send(kwargs.get('data'))

    def onerror(error):
        cors_message = ""
        url_origin = js.URL.new(url).origin
        origin = js.window.location.origin
        if url_origin != origin:
            cors_message = " Requested URL is not on this domain. You may have CORS issue."
        raise ConnectionError(f"{error.js_error.toString()}{cors_message} Please check error message in browser console.")

    req._patched_send = send
    req._patched_onerror = onerror
    # big hack since try/catch of JS code is not available on Python side
    js.eval("try { __basthon_req._patched_send(); } catch (e) { __basthon_req._patched_onerror(e); }")
    return Response(req)


for name in ('GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE'):
    __all__.append(name.lower())
    globals()[name.lower()] = lambda url, _=name, **kwargs: request(_, url, **kwargs)
