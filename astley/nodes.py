'''All nodes used of other node kinds.'''

import _ast as ast
from ast import fix_missing_locations as fix

from .node import Node

class BaseNode(Node):
    '''Node used to represent expression or statement body.'''

class Expression(ast.Expression, BaseNode):
    sym = '{self.body}'
    def compile(self, filename='<unknown>'):
        return compile(fix(self), filename, 'eval')

class Module(ast.Module, BaseNode):
    def asPython(self, index=0):
        return '\n'.join(
            '   ' * index + stmt.asPython()
            for stmt in self.body)
    def compile(self, filename='<unknown>'):
        return compile(fix(self), filename, 'exec')

#% helpers

class datanode(Node):
    '''Subsidiary data node.'''

class kind(Node):
    '''Enumerable node.'''

class expr_context(ast.expr_context, kind):
    '''Method of evaluating an expression to evaluate an expression.'''

for i in 'Load Store Del_ AugLoad AugStore Param'.split():
    exec("""
class {0}(ast.{0}, expr_context): pass
{1} = {0}()
""".format(i.replace('_', ''), i.lower()))

del i

from .datanodes import *
from .expressions import *
from .statements import *
from .ops import *