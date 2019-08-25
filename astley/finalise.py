'''Astley: Finalisation of a node.'''

# This file exists due to a strange import tree:
# it relies on .expressions, which relies on .

from _ast import AST
from .nodes import Constant, Bytes, Num, Str, Name, NameConstant
from sys import version_info

NODE_ONLY_FIELDS = "body value left right".split()

def finalise(node, lineno=1, col_offset=0, _lvl=0):
    """
    Finalise a node for use in non-Astley contexts.

    Fixes line numbers (similar to ast.fix_missing_locations),
    provides node defaults, and serialises literals to their node form.
    """
    if version_info >= (3, 8) and isinstance(
            node, (bool, int, float, complex, str, bytes)):
        return Constant(node)

    elif isinstance(node, bool):
        return NameConstant(node)
    elif isinstance(node, (int, float, complex)):
        return Num(node)
    elif isinstance(node, str):
        return Str(node)
    elif isinstance(node, bytes):
        return Bytes(node)

    elif callable(node) and hasattr(node, '__name__'):
        # Allow functions to be placed in - a little unreliable?
        return Name(node.__name__)

    elif isinstance(node, (list, tuple)):
        # We assume the user will use List() and Tuple() for actual usages
        return list(finalise(n, lineno, col_offset, _lvl) for n in node)
    elif isinstance(node, AST):
        # Copy line and column data
        if 'lineno' in node._attributes:
            if not hasattr(node, 'lineno'):
                node.lineno = lineno
            else:
                lineno = node.lineno
        if 'col_offset' in node._attributes:
            if not hasattr(node, 'col_offset'):
                node.col_offset = col_offset
            else:
                col_offset = node.col_offset

        # Instantiate default fields not provided
        defaults = getattr(type(node), '_defaults', {})
        for name, field in defaults.items():
            if not hasattr(node, name):
                setattr(node, name, field)

        for name in node._fields:
            field = getattr(node, name, None)
            # Convert tuple-fields into lists
            if isinstance(field, tuple):
                field = list(field)
            if isinstance(field, (list, AST)) or field in NODE_ONLY_FIELDS:
                setattr(node, name, finalise(field, lineno, col_offset, _lvl+1))


    return node
