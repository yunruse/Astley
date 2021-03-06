'''Miscellaneous node kinds and abstract base classes.'''

import _ast

from ..node import Node

# pylint: disable=W0614,E1101
# W0614: import *
# E1101: node.attr

class BaseNode(Node):
    '''Node used to represent expression or statement body.'''

class Expression(_ast.Expression, BaseNode):
    sym = '{self.body}'
    def compile(self, filename='<unknown>'):
        return compile(finalise(self), filename, 'eval')

class Module(_ast.Module, BaseNode):
    def _as_python(self, index=0):
        return '\n'.join(
            '   ' * index + stmt.as_python()
            for stmt in self.body)
    def compile(self, filename='<unknown>'):
        return compile(finalise(self), filename, 'exec')

class function_kind(Node):
    pass

class kind(Node):
    '''Enumerable node.'''

class expr_context(_ast.expr_context, kind):
    '''Method of evaluating an expression.'''


for i in 'Load Store Del_ AugLoad AugStore Param'.split():
    exec("""
class {0}(_ast.{0}, expr_context): pass
{1} = {0}()
""".format(i.replace('_', ''), i.lower()))

del i, _ast

from .datanodes import *
from .expressions import *
from .statements import *
from .ops import *
from .signature import *
from ..finalise import finalise
