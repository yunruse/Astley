'''Astley: Finalisation of a node.'''

# This file exists due to a strange import tree:
# it relies on .expressions, which relies on .

from _ast import AST
from .expressions import Num, Str, Name

def finalise(node, lineno=1, col_offset=0, _lvl=0, printDebug=False):
    """
    Finalise a node for use in non-Astley contexts.

    Fixes line numbers (similar to ast.fix_missing_locations),
    provides node defaults, and serialises literals to their node form.
    """
    if isinstance(node, (int, float)):
        return Num(node)
    elif isinstance(node, str):
        return Str(node)
    elif callable(node) and hasattr(node, '__name__'):
        return Name(node.__name__)
    elif isinstance(node, (list, tuple)):
        return type(node)(finalise(n, lineno, col_offset, _lvl) for n in node)
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

        if printDebug:
            nodeOld = repr(node)
            sep = max(0, lvl-1) * '  ' + '\\ ' if lvl else ''
            print(sep + nodeOld)

        for name in node._fields:
            field = getattr(node, name, None)
            if isinstance(field, (list, AST)):
                setattr(node, name, finalise(field, lineno, col_offset, lvl+1))

        if printDebug:
            nodeNew = str(node)
            if nodeNew != nodeOld:
                repr(sep + nodeNew)
    return node
