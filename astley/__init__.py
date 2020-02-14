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
from .finalise import finalise

AST = Node

LETTERS = [chr(i) for i in range(0x0, 0x400) if chr(i).isalpha()]
for l in LETTERS:
    globals()[l] = Name(l)
