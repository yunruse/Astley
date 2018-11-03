'''Extension to Abstract Syntax Tree.

100% feature-complete extension of AST, featuring a
WIP AST-to-code translator, useful base classes,
and an extended NodeTransformer.
'''

from ast import (
    walk, dump, literal_eval,
    iter_fields, iter_child_nodes, get_docstring,
    copy_location, fix_missing_locations, increment_lineno,
    NodeVisitor, NodeTransformer)

from .nodes import *
from .node import *
from .transformer import *

from .signature import funcSignature, reprSignature

AST = Node
fix = fix_missing_locations

# inverted for easier syntax
def copy(old_node, new_node):
    return copy_location(new_node, old_node)
def copyfix(old_node, new_node):
    return fix(copy_location(new_node, old_node))
