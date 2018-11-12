"""Astley, the extension to Python's Abstract Syntax Tree."""

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

AST = Node
