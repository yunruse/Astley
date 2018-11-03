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
from .helpers import *

from .signature import funcSignature, reprSignature

AST = Node