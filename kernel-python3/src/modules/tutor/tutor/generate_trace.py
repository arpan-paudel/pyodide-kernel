# This file is from PythonTutor, modified for Basthon's purpose.

from . import pg_logger
import json


def finalizer(input_code, output_trace):
    return dict(code=input_code, trace=output_trace)


def generate_trace(code,
                   cumulative=False,
                   heapPrimitives=False,
                   allmodules=False,
                   input=False,
                   probe_exprs=None):
    """ Generate dictionary trace for pytutor.js

    parameters
    ----------

    code
        user code.

    cumulative
        output cumulative trace.

    heapPrimitives
        render primitives as heap objects.

    allmodules
        allow importing of all installed Python modules.

    input
        JSON list of strings for simulated raw_input.

    create_jsvar
        Create a JavaScript variable out of the trace

    probe_exprs
        A JSON list of strings representing expressions whose values to probe at each step (advanced)
    """

    if probe_exprs:
        probe_exprs = json.loads(probe_exprs)

    return pg_logger.exec_script_str_local(
        code,
        input,
        cumulative,
        heapPrimitives,
        finalizer,
        probe_exprs=probe_exprs,
        allow_all_modules=bool(allmodules))
