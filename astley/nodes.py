'''Miscellaneous node kinds and abstract base classes.'''

import _ast

from .node import Node

class BaseNode(Node):
    '''Node used to represent expression or statement body.'''

class Expression(_ast.Expression, BaseNode):
    sym = '{self.body}'
    def compile(self, filename='<unknown>'):
        return compile(finalise(self), filename, 'eval')

class Module(_ast.Module, BaseNode):
    def asPython(self, index=0):
        return '\n'.join(
            '   ' * index + stmt.asPython()
            for stmt in self.body)
    def compile(self, filename='<unknown>'):
        return compile(finalise(self), filename, 'exec')

class functionKind(Node):
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
from .finalise import finalise
