"""Astley, thextension to Abstract Syntax Tree.

100% feature-complete extension of AST, featuring a
WIP AST-to-code translator, useful base classes,
and an extended NodeTransformer.
"""

# flake8: noqa

from ast import (
    walk,
    dump,
    literal_eval,
    iter_fields,
    iter_child_nodes,
    get_docstring,
    copy_location,
    fix_missing_locations,
    increment_lineno,
    NodeVisitor,
    NodeTransformer,
)

from .node import *
from .nodes import *
from .transformer import *

def copy(old_node, new_node):
    return copy_location(new_node, old_node)

AST = Node
