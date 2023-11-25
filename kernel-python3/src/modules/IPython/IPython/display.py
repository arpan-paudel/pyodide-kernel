import basthon
from binascii import b2a_base64
import mimetypes


__all__ = ['display', 'display_pretty', 'display_html', 'display_markdown',
           'display_svg', 'display_png', 'display_jpeg', 'display_latex', 'display_json',
           'display_javascript', 'display_pdf', 'clear_output', 'Image',
           'display_image', 'HTML', 'IFrame', 'SVG', 'Markdown', 'Latex', 'Audio']


display = basthon.display


def clear_output(*args, **kwargs):
    """ Fake function for Basthon. """
    pass


def _display_mimetype(mimetype, objs, raw=False, metadata=None):
    """internal implementation of all display_foo methods
    Parameters
    ----------
    mimetype : str
        The mimetype to be published (e.g. 'image/png')
    *objs : object
        The Python objects to display, or if raw=True raw text data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """
    if metadata:
        metadata = {mimetype: metadata}
    if raw:
        # turn list of pngdata into list of { 'image/png': pngdata }
        objs = [ {mimetype: obj} for obj in objs ]
    display(*objs, raw=raw, metadata=metadata, include=[mimetype])

#-----------------------------------------------------------------------------
# Main functions
#-----------------------------------------------------------------------------


def display_pretty(*objs, **kwargs):
    """Display the pretty (default) representation of an object.
    Parameters
    ----------
    *objs : object
        The Python objects to display, or if raw=True raw text data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """
    _display_mimetype('text/plain', objs, **kwargs)


def display_html(*objs, **kwargs):
    """Display the HTML representation of an object.
    Note: If raw=False and the object does not have a HTML
    representation, no HTML will be shown.
    Parameters
    ----------
    *objs : object
        The Python objects to display, or if raw=True raw HTML data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """
    _display_mimetype('text/html', objs, **kwargs)


def display_markdown(*objs, **kwargs):
    """Displays the Markdown representation of an object.
    Parameters
    ----------
    *objs : object
        The Python objects to display, or if raw=True raw markdown data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """

    _display_mimetype('text/markdown', objs, **kwargs)


def display_svg(*objs, **kwargs):
    """Display the SVG representation of an object.
    Parameters
    ----------
    *objs : object
        The Python objects to display, or if raw=True raw svg data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """
    _display_mimetype('image/svg+xml', objs, **kwargs)


def display_png(*objs, **kwargs):
    """Display the PNG representation of an object.
    Parameters
    ----------
    *objs : object
        The Python objects to display, or if raw=True raw png data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """
    _display_mimetype('image/png', objs, **kwargs)


def display_jpeg(*objs, **kwargs):
    """Display the JPEG representation of an object.
    Parameters
    ----------
    *objs : object
        The Python objects to display, or if raw=True raw JPEG data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """
    _display_mimetype('image/jpeg', objs, **kwargs)


def display_latex(*objs, **kwargs):
    """Display the LaTeX representation of an object.
    Parameters
    ----------
    *objs : object
        The Python objects to display, or if raw=True raw latex data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """
    _display_mimetype('text/latex', objs, **kwargs)


def display_json(*objs, **kwargs):
    """Display the JSON representation of an object.
    Note that not many frontends support displaying JSON.
    Parameters
    ----------
    *objs : object
        The Python objects to display, or if raw=True raw json data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """
    _display_mimetype('application/json', objs, **kwargs)


def display_javascript(*objs, **kwargs):
    """Display the Javascript representation of an object.
    Parameters
    ----------
    *objs : object
        The Python objects to display, or if raw=True raw javascript data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """
    _display_mimetype('application/javascript', objs, **kwargs)


def display_pdf(*objs, **kwargs):
    """Display the PDF representation of an object.
    Parameters
    ----------
    *objs : object
        The Python objects to display, or if raw=True raw javascript data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    metadata : dict (optional)
        Metadata to be associated with the specific mimetype output.
    """
    _display_mimetype('application/pdf', objs, **kwargs)


class Image:
    """ Display an image from raw data. """
    def __init__(self, data, format='png'):
        if format.lower() != 'png':
            raise ValueError("Only PNG format is supported.")
        self.format = format
        self.data = data

    def _repr_png_(self):
        return b2a_base64(self.data).decode('ascii')


def display_image(img):
    """ Displaying image from numpy array  """
    from matplotlib import image
    import base64
    import io

    def _repr_png_():
        raw = io.BytesIO()
        image.imsave(raw, img, format="png", cmap='gray')
        raw.seek(0)
        return base64.b64encode(raw.read()).decode()

    dummy = type('image', (), {})()
    dummy._repr_png_ = _repr_png_
    display(dummy)


class TextDisplayObject:
    """ Base class for SVG, HTML, Markdown, Latex..."""
    def __init__(self, data):
        self.data = data
        if self.data is not None and not isinstance(self.data, str):
            raise TypeError("%s expects text, not %r" % (self.__class__.__name__, self.data))


class HTML(TextDisplayObject):
    """ Sending html string to IPython notebook. """
    def _repr_html_(self):
        return self.data


class SVG(TextDisplayObject):
    """ Sending svg string to IPython notebook. """
    def _repr_svg_(self):
        return self.data


class Latex(TextDisplayObject):
    """ Sending latex string to IPython notebook. """
    def _repr_latex_(self):
        return self.data


class Markdown(TextDisplayObject):
    """ Sending markdown string to IPython notebook. """
    def _repr_markdown_(self):
        return self.data


class IFrame(HTML):
    """ Embed an iframe in IPython notebook. """
    def __init__(self, src, width, height):
        super().__init__(f'<iframe src="{src}" allowfullscreen="" width="{width}" height="{height}" frameborder="0"></iframe>')


# ogg is not recognized, fix this
mimetypes.add_type("application/ogg", ".ogg")


class Audio:
    """Create an audio object.
    When this object is returned by an input cell or passed to the
    display function, it will result in Audio controls being displayed
    in the frontend (only works in the notebook).
    Parameters
    ----------
    data : numpy array, list, unicode, str or bytes
        Can be one of
          * Numpy 1d array containing the desired waveform (mono)
          * Numpy 2d array containing waveforms for each channel.
            Shape=(NCHAN, NSAMPLES). For the standard channel order, see
            http://msdn.microsoft.com/en-us/library/windows/hardware/dn653308(v=vs.85).aspx
          * List of float or integer representing the waveform (mono)
          * String containing the filename
          * Bytestring containing raw PCM data or
          * URL pointing to a file on the web.
        If the array option is used, the waveform will be normalized.
        If a filename or url is used, the format support will be browser
        dependent.
    url : unicode
        A URL to download the data from.
    filename : unicode
        Path to a local file to load the data from.
    embed : boolean
        Should the audio data be embedded using a data URI (True) or should
        the original source be referenced. Set this to True if you want the
        audio to playable later with no internet connection in the notebook.
        Default is `True`, unless the keyword argument `url` is set, then
        default value is `False`.
    rate : integer
        The sampling rate of the raw data.
        Only required when data parameter is being used as an array
    autoplay : bool
        Set to True if the audio should immediately start playing.
        Default is `False`.
    normalize : bool
        Whether audio should be normalized (rescaled) to the maximum possible
        range. Default is `True`. When set to `False`, `data` must be between
        -1 and 1 (inclusive), otherwise an error is raised.
        Applies only when `data` is a list or array of samples; other types of
        audio are never normalized.
    Examples
    --------
    >>> import pytest
    >>> np = pytest.importorskip("numpy")
    Generate a sound
    >>> import numpy as np
    >>> framerate = 44100
    >>> t = np.linspace(0,5,framerate*5)
    >>> data = np.sin(2*np.pi*220*t) + np.sin(2*np.pi*224*t)
    >>> Audio(data, rate=framerate)
    <IPython.lib.display.Audio object>
    Can also do stereo or more channels
    >>> dataleft = np.sin(2*np.pi*220*t)
    >>> dataright = np.sin(2*np.pi*224*t)
    >>> Audio([dataleft, dataright], rate=framerate)
    <IPython.lib.display.Audio object>
    From URL:
    >>> Audio("http://www.nch.com.au/acm/8k16bitpcm.wav")  # doctest: +SKIP
    >>> Audio(url="http://www.w3schools.com/html/horse.ogg")  # doctest: +SKIP
    From a File:
    >>> Audio('/path/to/sound.wav')  # doctest: +SKIP
    >>> Audio(filename='/path/to/sound.ogg')  # doctest: +SKIP
    From Bytes:
    >>> Audio(b'RAW_WAV_DATA..')  # doctest: +SKIP
    >>> Audio(data=b'RAW_WAV_DATA..')  # doctest: +SKIP
    See Also
    --------
    ipywidgets.Audio
    
         AUdio widget with more more flexibility and options.
    
    """
    _read_flags = 'rb'

    def __init__(self, data=None, filename=None, url=None, embed=None, rate=None, autoplay=False, normalize=True, *,
                 element_id=None):
        if filename is None and url is None and data is None:
            raise ValueError("No audio data found. Expecting filename, url, or data.")
        if embed is False and url is None:
            raise ValueError("No url found. Expecting url when embed=False")

        if url is not None and embed is not True:
            self.embed = False
        else:
            self.embed = True
        self.autoplay = autoplay
        self.element_id = element_id
        self.url = url
        self.filename = filename
        self.data = data
        self.reload()

        if self.data is not None and not isinstance(self.data, bytes):
            if rate is None:
                raise ValueError("rate must be specified when data is a numpy array or list of audio samples.")
            self.data = Audio._make_wav(data, rate, normalize)

    def reload(self):
        """Reload the raw data from file or URL."""
        import mimetypes
        if self.embed:
            pass#super(Audio, self).reload()

        if self.filename is not None:
            self.mimetype = mimetypes.guess_type(self.filename)[0]
        elif self.url is not None:
            self.mimetype = mimetypes.guess_type(self.url)[0]
        else:
            self.mimetype = "audio/wav"

    @staticmethod
    def _make_wav(data, rate, normalize):
        """ Transform a numpy array to a PCM bytestring """
        from io import BytesIO
        # bypass audioop
        try:
            import wave
        except ImportError:
            # fix audioop not present in pyodide
            from types import ModuleType
            m = ModuleType("audioop")
            import sys
            sys.modules[m.__name__] = m
            m.__file__ = m.__name__ + ".py"
            import wave

        try:
            scaled, nchan = Audio._validate_and_normalize_with_numpy(data, normalize)
        except ImportError:
            scaled, nchan = Audio._validate_and_normalize_without_numpy(data, normalize)

        fp = BytesIO()
        waveobj = wave.open(fp,mode='wb')
        waveobj.setnchannels(nchan)
        waveobj.setframerate(rate)
        waveobj.setsampwidth(2)
        waveobj.setcomptype('NONE','NONE')
        waveobj.writeframes(scaled)
        val = fp.getvalue()
        waveobj.close()

        return val

    @staticmethod
    def _validate_and_normalize_with_numpy(data, normalize):
        import numpy as np

        data = np.array(data, dtype=float)
        if len(data.shape) == 1:
            nchan = 1
        elif len(data.shape) == 2:
            # In wave files,channels are interleaved. E.g.,
            # "L1R1L2R2..." for stereo. See
            # http://msdn.microsoft.com/en-us/library/windows/hardware/dn653308(v=vs.85).aspx
            # for channel ordering
            nchan = data.shape[0]
            data = data.T.ravel()
        else:
            raise ValueError('Array audio input must be a 1D or 2D array')
        
        max_abs_value = np.max(np.abs(data))
        normalization_factor = Audio._get_normalization_factor(max_abs_value, normalize)
        scaled = data / normalization_factor * 32767
        return scaled.astype("<h").tobytes(), nchan

    @staticmethod
    def _validate_and_normalize_without_numpy(data, normalize):
        import array
        import sys

        data = array.array('f', data)

        try:
            max_abs_value = float(max([abs(x) for x in data]))
        except TypeError as e:
            raise TypeError('Only lists of mono audio are '
                'supported if numpy is not installed') from e

        normalization_factor = Audio._get_normalization_factor(max_abs_value, normalize)
        scaled = array.array('h', [int(x / normalization_factor * 32767) for x in data])
        if sys.byteorder == 'big':
            scaled.byteswap()
        nchan = 1
        return scaled.tobytes(), nchan

    @staticmethod
    def _get_normalization_factor(max_abs_value, normalize):
        if not normalize and max_abs_value > 1:
            raise ValueError('Audio data must be between -1 and 1 when normalize=False.')
        return max_abs_value if normalize else 1

    def _data_and_metadata(self):
        """shortcut for returning metadata with url information, if defined"""
        md = {}
        if self.url:
            md['url'] = self.url
        if md:
            return self.data, md
        else:
            return self.data

    def _repr_html_(self):
        src = """
                <audio {element_id} controls="controls" {autoplay}>
                    <source src="{src}" type="{type}" />
                    Your browser does not support the audio element.
                </audio>
              """
        return src.format(src=self.src_attr(), type=self.mimetype, autoplay=self.autoplay_attr(),
                          element_id=self.element_id_attr())

    def src_attr(self):
        import base64
        if self.embed and (self.data is not None):
            data = base64=base64.b64encode(self.data).decode('ascii')
            return """data:{type};base64,{base64}""".format(type=self.mimetype,
                                                            base64=data)
        elif self.url is not None:
            return self.url
        else:
            return ""

    def autoplay_attr(self):
        if(self.autoplay):
            return 'autoplay="autoplay"'
        else:
            return ''
    
    def element_id_attr(self):
        if (self.element_id):
            return 'id="{element_id}"'.format(element_id=self.element_id)
        else:
            return ''
