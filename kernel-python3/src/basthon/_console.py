from pyodide import console as _pyodide_console
from pyodide.console import _CommandCompiler, CodeRunner, _WriteStream
from . import kernel
import sys
import traceback
import ast


__author__ = "Romain Casati"
__license__ = "GNU GPL v3"
__email__ = "romain.casati@basthon.fr"


__all__ = ["InteractiveConsole"]

#################################
# pyodide.console monkey-patches
#################################

# force 'exec' mode (forced to 'single' by Pyodide) so monkey-patch!
_call = _CommandCompiler.__call__


def __call(self, source, filename, symbol):
    return _call(self, source, filename, "exec")


_CommandCompiler.__call__ = __call

# monkey-patch pyodide.console.CodeRunner to modify ast before compile
_unpatched_compile = CodeRunner.compile


class RewriteAST(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self._input_async_name = "_basthon_input_async"
        self._sleep_async_name = "_basthon_sleep_async"
        self._ignore = False

        def ignore(node):
            self._ignore = True
            self.generic_visit(node)
            self._ignore = False
            return node

        # ignoring function/class definition
        # otherwise functions should be async...
        to_ignore = ["FunctionDef", "Lambda", "ClassDef"]
        for d in to_ignore:
            setattr(self, f"visit_{d}", ignore)

    def visit_Call(self, node):
        res = node
        if not self._ignore:
            func = node.func
            set_await = True
            if isinstance(func, ast.Name) and func.id == "input":
                # input(...) -> await _basthon_input_async(...)
                func.id = self._input_async_name
            elif isinstance(func, ast.Name) and func.id == "sleep":
                # sleep(...) -> await _basthon_sleep_async(...)
                func.id = self._sleep_async_name
            elif (isinstance(func, ast.Attribute)
                  and isinstance(func.value, ast.Name)
                  and func.value.id == 'time'
                  and func.attr == 'sleep'):
                # time.sleep(...) -> await _basthon_sleep_async(...)
                node.func = ast.Name(self._sleep_async_name, func.ctx)
            else:
                set_await = False
            if set_await:
                res = ast.Await(node)
        self.generic_visit(node)
        return res


def patched_compile(self, *args, **kwargs):
    RewriteAST().visit(self.ast)
    return _unpatched_compile(self, *args, **kwargs)


CodeRunner.compile = patched_compile

# this is absent from Pyodide and is e.g. needed by doctest
_WriteStream.encoding = "utf8"


class InteractiveConsole(_pyodide_console.PyodideConsole):
    """This is the Python's part of Basthon kernel"""

    def __init__(self, *args, **kwargs):
        self.execution_count = None
        kwargs['globals'] = kwargs.get('globals', sys.modules['__main__'].__dict__)
        kwargs['filename'] = kwargs.get('filename', "<input>")
        kwargs['persistent_stream_redirection'] = True

        # setup persistent stream redirection
        def stdout_callback(text):
            return self._stdout_callback(text)
        kwargs['stdout_callback'] = stdout_callback

        def stderr_callback(text):
            return self._stderr_callback(text)
        kwargs['stderr_callback'] = stderr_callback

        super().__init__(*args, **kwargs)
        self.locals = self.globals
        self.start()

    # overload to fix filename not taken into account
    def num_frames_to_keep(self, tb):
        import traceback
        keep_frames = False
        kept_frames = 0
        # Try to trim out stack frames inside our code
        for (frame, _) in traceback.walk_tb(tb):
            keep_frames = keep_frames or frame.f_code.co_filename == self.filename
            keep_frames = keep_frames or frame.f_code.co_filename == "<exec>"
            if keep_frames:
                kept_frames += 1
        return kept_frames

    def banner(self):
        """ REPL banner. Taken from PyodideConsole. """
        return _pyodide_console.BANNER

    def roll_in_history(self, code):
        """ Manage storing in 'In' ala IPython. """
        self.locals['In'].append(code)

    def roll_out_history(self, out):
        """ Manage storing in 'Out', _, __, ___ ala IPython. """
        outputs = self.locals['Out']
        # out is not always stored
        if out is not None and out is not outputs:
            outputs[self.execution_count] = out
            self.locals['___'] = self.locals['__']
            self.locals['__'] = self.locals['_']
            self.locals['_'] = out

    def start(self):
        """
        Start the Basthon kernel and fill the namespace.
        """
        self.execution_count = 0
        self.locals.clear()
        self.locals.update({
            '__name__': '__main__',
            '__doc__': None,
            '_': '',
            '__': '',
            '___': '',
            'In': [''],
            'Out': {},
        })

    def stop(self):
        """
        Stop the Basthon kernel.
        """
        pass

    def restart(self):
        """
        Restart the Basthon kernel.
        """
        self.stop()
        self.start()

    def more(self, source):
        """ Is the source ready to be evaluated or want we more?

        Usefull to set ps1/ps2 for teminal prompt.
        """
        try:
            code = self._compile(source, self.filename, "exec")
        except (OverflowError, SyntaxError, ValueError):
            return False

        if code is None:
            return True

        return False

    async def eval(self, code, stdout_callback, stderr_callback, data=None):
        """
        Evaluation of Python code with communication managment
        with the JS part of Basthon and stdout/stderr catching.
        data can be accessed in code through '__eval_data__' variable
        in global namespace.

        Results:
        --------
        A promise that resolves with the formated result.
        """
        self.locals['__eval_data__'] = data.to_py()
        self.execution_count += 1
        self._stdout_callback = stdout_callback
        self._stderr_callback = stderr_callback

        self.roll_in_history(code)

        fut = self.runsource(code, self.filename)
        try:
            result = await fut
        except Exception:
            return fut.formatted_error
        # if fut is incomplete, we should raise an error so recompile
        if fut.syntax_check == "incomplete":
            try:
                self._compile.compiler(code, self.filename, "exec")
            except Exception as e:
                if e.__traceback__:
                    traceback.clear_frames(e.__traceback__)
                return self.formatsyntaxerror(e)
            raise RuntimeError("Internal Basthon error")

        self.roll_out_history(result)
        if result is not None:
            result = kernel.format_repr(result)
        return result, self.execution_count
