"""Base Node (= AST) class which all nodes inherit from."""

from _ast import AST
# pylint: disable=E1101
# E1101: node.attr

_locals, _globals = locals, globals

__all__ = "copy parse Node".split()

def copy(old_node, new_node):
    old_attr = getattr(old_node, '_attributes', None)
    new_attr = getattr(new_node, '_attributes', None)
    if old_attr and new_attr:
        for i in old_attr:
            if i in new_attr and not hasattr(new_node, i):
                setattr(new_node, i, getattr(old_node, i))
    return new_node

DFIELDS = ("lineno", "col_offset")
PyCF_ONLY_AST = 1024

def parse(source, filename="<unknown>", mode="exec"):
    return modify(compile(source, filename, mode, PyCF_ONLY_AST))

class CodeDisplay:
    def __init__(self, node):
        self._node = node

    def __getattr__(self, attr):
        item = getattr(self._node, attr, None)
        if isinstance(item, Node):
            return item.asPython()
        elif item is not None:
            return item
        else:
            return ""


class Node:
    sym = ""
    _defaults = {}
    def __getattr__(self, attr):
        if attr in self._defaults:
            return self._defaults[attr]
        else:
            raise AttributeError('{} has no attribute {!r}'.format(
                type(self).__name__, attr
            ))

    def __init__(self, *args, **kw):
        if not args or kw:
            return
        if len(args) == 1 and isinstance(args[0], AST):
            node = args[0]
            for n in DFIELDS + getattr(node, "_fields", ()):
                if hasattr(node, n):
                    v = modify(getattr(node, n))
                    if isinstance(v, list):
                        v = list(map(modify, v))
                    setattr(self, n, v)

        else:
            kwargs = dict()
            if args and len(args) <= len(self._fields):
                for i, val in enumerate(args):
                    name = self._fields[i]
                    kwargs[name] = val

            kwargs.update(kw)

            for name, val in kwargs.items():
                setattr(self, name, val)

    def display(self, nodesLeftToDisplay=-1, showAttributes=True, asTree=False):
        if asTree and not nodesLeftToDisplay:
            return '@'

        fields = []
        for i in tuple(self._fields) + tuple(self._attributes) * showAttributes:
            v = getattr(self, i, None)
            if v is None:
                continue
            elif isinstance(v, Node):
                v = v.display(nodesLeftToDisplay - 1, True, asTree)
            elif isinstance(v, (tuple, list)):
                v = "[{}]".format(', '.join(
                    i.display(nodesLeftToDisplay - 1, True, asTree)
                    if isinstance(i, Node) else repr(i)
                    for i in v
                ))
            else:
                v = repr(v)
            fields.append("{}={}".format(i, v))

        if fields and not nodesLeftToDisplay:
            args = '...'
        else:
            args = ', '.join(fields)

        return "{}({})".format(self.__class__.__name__, args)

    def __repr__(self):
        return self.display(1, False)

    def __str__(self):
        return self.display(-1)

    def __eq__(self, other):
        return (self._fields == other._fields
            and (getattr(self, i, None) == getattr(other, i, None)
                 for i in self._fields))

    def asPython(self):
        return finalise(self)._asPython()

    def _asPython(self, indent=1):
        return self.sym.format(self=CodeDisplay(self))

    def compile(self, filename=None):
        """Return compiled code version of node."""
        raise TypeError("Node is not a code segment.")

    def eval(self, globals=None, locals=None, **kw):
        """Evaluate and return expression given globals and locals."""
        locals = locals or dict()
        locals.update(kw)
        return eval(self.compile(), globals or _globals(), locals)

    def exec(self, globals=None, locals=None, **kw):
        """Execute node given globals and locals."""
        locals = locals or dict()
        locals.update(kw)
        exec(self.compile(), globals or _globals(), locals)


def modify(node):
    cls = node.__class__
    newcls = getattr(nodes, cls.__name__, None)

    if issubclass(cls, AST) and newcls:
        new = newcls()
        Node.__init__(new, node)
        return new
    else:
        return node

# Name mangling (interdependant functions)

from . import nodes
from .finalise import finalise
