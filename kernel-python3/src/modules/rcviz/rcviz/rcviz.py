# rcviz : a small recursion call graph vizualization decorator
# Copyright (c) Ran Dugal 2014
# Licensed under the GPLv2, which is available at
# http://www.gnu.org/licenses/gpl-2.0.html
# Rewriten for Basthon by Romain Casati and licenced under the same license

import inspect
import logging
import copy
import os
import graphviz as gviz

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def trim_stack(stack):
    for i in range(len(stack) - 1, -1, -1):
        if os.path.basename(stack[i].filename).startswith("<input>"):
            break
    return stack[:i+1]


class CallGraph(object):
    '''class that stores global graph data draw graph using pygraphviz
    '''
    def __init__(self):
        self._callers = {}  # caller_fn_id : NodeData
        self._counter = 1  # track call order
        self._unwindcounter = 1  # track unwind order
        self._frames = []  # keep frame objects reference

    def get_callers(self):
        return self._callers

    def get_counter(self):
        return self._counter

    def get_unwindcounter(self):
        return self._unwindcounter

    def increment(self):
        self._counter += 1

    def increment_unwind(self):
        self._unwindcounter += 1

    def get_frames(self):
        return self._frames

    def callgraph(self, show_null_returns=True):
        g = gviz.Digraph()
        g.graph_attr['label'] = 'nodes=%s' % len(self._callers)
        g.graph_attr['fontname'] = "helvetica"
        g.node_attr['fontname'] = "helvetica"
        g.edge_attr['fontname'] = "helvetica"

        # create nodes
        for frame_id, node in self._callers.items():

            auxstr = ""
            for param, val in node.auxdata.items():
                auxstr += " | %s: %s" % (param, val)

            if not show_null_returns and node.ret is None:
                label = "{ %s(%s) %s }" % (node.fn_name, node.argstr(), auxstr)
            else:
                label = "{ %s(%s) %s | ret: %s }" % (node.fn_name,
                                                     node.argstr(),
                                                     auxstr, node.ret)
            g.node(str(frame_id), shape='Mrecord', label=label,
                   fontsize=str(13), labelfontsize=str(13))

        # edge colors
        step = 200 // self._counter
        cur_color = 0

        # create edges
        for frame_id, node in self._callers.items():
            child_nodes = []
            for child_id, counter, unwind_counter in node.child_methods:
                child_nodes.append(child_id)
                cur_color = step * counter
                color = "#%2x%2x%2x" % (cur_color, cur_color, cur_color)
                label = "%s (&uArr;%s)" % (counter, unwind_counter)
                g.edge(str(frame_id), str(child_id), label=label, fontcolor="#999999",
                       color=str(color), fontsize=str(8), labelfontsize=str(8))

            # order edges l to r
            # FIXME: This code doesn't seem to do anything
            # It causes the Graphviz dot command to issue 
            # compilation errors (it affects Jupyter's display due to the
            # non-zero return value).
            """if len(child_nodes) > 1:
                sg = gviz.Digraph(name="foo")
                sg.graph_attr['rank'] = 'same'
                prev_node = None
                for child_node in child_nodes:
                    if prev_node:
                        sg.edge(str(prev_node), str(child_node),
                                color="#ffffff")
                    prev_node = child_node
                g.subgraph(sg)"""

        return g

    def _repr_svg_(self):
        return self.callgraph._repr_svg_()


class NodeData(object):
    def __init__(self, _args=None, _kwargs=None, _fnname="",
                 _ret=None, _childmethods=[]):
        self.args = _args
        self.kwargs = _kwargs
        self.fn_name = _fnname
        self.ret = _ret
        self.child_methods = _childmethods    # [ (method, gcounter) ]

        self.auxdata = {}  # user assigned track data

    def __str__(self):
        return "%s -> child_methods: %s" % (self.nodestr(), self.child_methods)

    def nodestr(self):
        return "%s = %s(%s)" % (self.ret, self.fn_name, self.argstr())

    def argstr(self):
        s_args = ",".join([str(arg) for arg in self.args])
        s_kwargs = ",".join([(str(k), str(v))
                             for (k, v) in self.kwargs.items()])
        return "%s%s" % (s_args, s_kwargs)


def viz(f, *args, **kwargs):
    _callgraph = None
    _callcount = 0  # incremented and decremented at each call

    def track(**kwargs):
        fullstack = trim_stack(inspect.stack())
        call_frame_id = id(fullstack[2][0])
        g_callers = callgraph.get_callers()
        node = g_callers.get(call_frame_id)
        if node:
            node.auxdata.update(copy.deepcopy(kwargs))

    def callgraph(*args, **kwargs):
        nonlocal _callgraph

        if _callgraph is not None:
            return _callgraph.callgraph(*args, **kwargs)

    def wrapped_f(*args, **kwargs):
        nonlocal _callgraph, _callcount

        if _callcount == 0:
            _callgraph = CallGraph()

        _callcount += 1

        # Expected parameters for the function being wrapped
        g_callers = _callgraph.get_callers()
        g_frames = _callgraph.get_frames()

        # find the caller frame, and add self as a child node
        caller_frame_id = None

        fullstack = trim_stack(inspect.stack())

        if len(fullstack) > 2:
            caller_frame_id = id(fullstack[2][0])

        this_frame_id = id(fullstack[0][0])

        if this_frame_id not in g_frames:
            g_frames.append(fullstack[0][0])

        if this_frame_id not in g_callers.keys():
            g_callers[this_frame_id] = NodeData(args, kwargs,
                                                f.__name__,
                                                None, [])

        edgeinfo = None
        if caller_frame_id:
            edgeinfo = [this_frame_id, _callgraph.get_counter()]
            g_callers[caller_frame_id].child_methods.append(edgeinfo)
            _callgraph.increment()

        ret = f(*args, **kwargs)
        g_callers[this_frame_id].ret = copy.deepcopy(ret)

        if edgeinfo:
            edgeinfo.append(_callgraph.get_unwindcounter())
            _callgraph.increment_unwind()

        _callcount -= 1

        return ret

    wrapped_f.track = track
    wrapped_f.callgraph = callgraph
    return wrapped_f
