'''Statements that may only be exec'd'''

import _ast

from ..node import copy
from ..finalise import finalise
from . import Node, Module
from .expressions import Str, Expr
from .datanodes import Datanode
from .signature import arguments

class stmt(Node):
    '''Statement node - subclasses may be exec'd'''
    def compile(self, filename='<unknown>'):
        module = copy(self, Module(body=[finalise(self)]))
        return module.compile(filename)

class AssignKind(stmt):
    '''Base class for assignment statements'''

class Assign(_ast.Assign, AssignKind):
    '''Assignment of value(s)'''
    def asPython(self):
        return ' = '.join(i.asPython() for i in self.targets + [self.value])

class AugAssign(_ast.AugAssign, AssignKind):
    '''Augmented in-place assignment (eg +=)'''
    sym = '{self.target} {self.op}= {self.value}'

class AnnAssign(_ast.AnnAssign, AssignKind):
    '''Single-target type-annotated assignment'''
    _fields = 'target annotation value'.split()
    _defaults = {'value': None}
    def asPython(self):
        tgt = self.target.asPython()
        ann = self.annotation.asPython()
        if self.value:
            return '{}: {} = {}'.format(
                tgt, ann, self.value.asPython())
        return '{}: {}'.format(tgt, ann)


class Oneliner(stmt):
    '''Base class: One-line statement.'''
    _fields = 'value'.split()

class Return(_ast.Return, Oneliner):
    sym = 'return {self.value}'
class Await(_ast.Yield, Oneliner):
    sym = 'await {self.value}'
class Yield(_ast.Yield, Oneliner):
    sym = 'yield {self.value}'
class YieldFrom(_ast.YieldFrom, Oneliner):
    sym = 'yield from {self.value}'

class Raise(_ast.Raise, Oneliner):
    _fields = 'exc'.split()
    sym = 'raise {self.exc}'

class Delete(_ast.Delete, Oneliner):
    _fields = 'targets'.split()
    def asPython(self):
        return 'del ' + ', '.join(i.asPython() for i in self.targets)

class VarContextStmt(Oneliner):
    _fields = 'names'.split()
    def asPython(self):
        return self.sym + ' ' + ', '.join(self.names)

class Global(_ast.Global, VarContextStmt):
    sym = 'global'
class Nonlocal(_ast.Nonlocal, VarContextStmt):
    sym = 'nonlocal'

class Assert(_ast.Assert, Oneliner):
    def asPython(self):
        code = 'assert ' + self.test.asPython()
        if self.msg:
            return code + ', ' + self.msg.asPython()
        else:
            return code

class Word(Oneliner):
    '''Base class: Single-word statements.'''

class Pass(_ast.Pass, Word):
    sym = 'pass'
class Continue(_ast.Continue, Word):
    sym = 'continue'
class Break(_ast.Break, Word):
    sym = 'break'

class Import(_ast.Import, stmt):
    _fields = 'names'.split()
    def asPython(self):
        return 'import {}'.format(
            ', '.join(i.asPython() for i in self.names))

class ImportFrom(_ast.ImportFrom, Import):
    _fields = 'module names level'.split()
    _defaults = {'level': 0}
    def asPython(self):
        return 'from {}{} import {}'.format(
            '.' * self.level, self.module or '',
            ', '.join(i.asPython() for i in self.names))

class Block(stmt):
    pass

class AsyncBlock(Block):
    pass

def _display(item, indent=0):
    if isinstance(item, Block):
        return item.asPython(indent)
    else:
        if isinstance(item, Node):
            item = item.asPython()
        return ' ' * 4 * indent + item

def bodyfmt(body, indent=0):
    if body and isinstance(body[0], Expr) and isinstance(body[0].value, Str):
        # docstring
        body[0] = body[0].value.asFmt('"""')
    return '\n'.join(_display(i, indent) for i in body)

class If(_ast.If, Block):
    _fields = 'test body orelse'.split()
    _defaults = {'orelse': []}
    def asPython(self, indent=0):
        tab = ' ' * 4 * indent
        body = tab + 'if {}:\n'.format(self.test.asPython())
        body += bodyfmt(self.body, indent+1)

        # `elif` is just an If(orelse=If()), so we must navigate a chain
        orelse = self.orelse
        while orelse:
            body += '\n' + tab
            if len(orelse) == 1 and isinstance(orelse[0], _ast.If):
                newif = orelse[0]
                body += 'elif {}:\n'.format(newif.test.asPython())
                body += bodyfmt(newif.body, indent+1)
                orelse = newif.orelse
            else:
                body += 'else:\n' + bodyfmt(orelse, indent+1)
                orelse = None
        return body

class While(_ast.While, Block):
    _fields = 'test body'.split()
    def asPython(self, indent=0):
        body = ' ' * 4 * indent + 'while {}:\n'.format(self.test.asPython())
        return body + bodyfmt(self.body, indent+1)

class For(_ast.For, Block):
    _fields = 'test body'.split()
    _defaults = {'orelse': []}
    def asPython(self, indent=0):
        tab = ' ' * 4 * indent
        body = tab + '{} {} in {}:\n'.format(
            self.symbol,
            self.target.asPython(),
            self.iter.asPython())
        body += bodyfmt(self.body, indent+1)
        if self.orelse:
            body += '\n' + tab + 'else:\n'
            body += bodyfmt(self.orelse, indent+1)
        return body
    symbol = 'for'

class AsyncFor(_ast.AsyncFor, For, AsyncBlock):
    symbol = 'async for'

class With(_ast.With, Block):
    symbol = 'with'
    def asPython(self, indent=0):
        tab = ' ' * 4 * indent
        body = tab + 'with {}:\n'.format(', '.join(i.asPython() for i in self.items))
        return body + bodyfmt(self.body, indent+1)

class AsyncWith(With, AsyncBlock, _ast.AsyncWith):
    symbol = 'async with'

class Definition(Block):
    '''Class or function definition.'''

class FunctionDef(_ast.FunctionDef, Definition):
    _fields = 'name args body decorator_list returns'.split()
    _defaults = dict(returns=None, decorator_list=[], body=[], name='<astley>')
    symbol = 'def'

    @classmethod
    def withBody(cls, body, **kwargs):
        '''Decorator to inherit a real Python function's properties.

        Use as:
        @withBody(Return(Name('a') + Name('b'))):
        def add(a, b=2): ...
        '''
        wrapkw = cls._defaults.copy()
        wrapkw.update(kwargs)
        wrapkw['body'] = body
        def wrapper(func):
            kw = wrapkw.copy()
            if hasattr(func, '__name__'):
                kw['name'] = func.__name__
            if hasattr(func, '__annotations__'):
                an = func.__annotations__
                if 'return' in an:
                    kw['returns'] = an['return']
            kw['args'] = arguments.fromFunction(func)
            return cls(**kw)
        return wrapper

    def asPython(self, indent=0):
        lines = ['@' + i.asPython() for i in self.decorator_list]

        returns = ''
        if hasattr(self, 'returns') and self.returns:
            returns = ' -> ' + self.returns.asPython()

        lines.append('{} {}({}){}:'.format(
            self.symbol, self.name,
            self.args.asPython(), returns))

        return bodyfmt(lines, indent) + '\n' + bodyfmt(self.body, indent+1)

class AsyncFunctionDef(_ast.AsyncFunctionDef, FunctionDef, AsyncBlock):
    symbol = 'async def'

class ClassDef(_ast.ClassDef, Definition):
    def asPython(self, indent=0):
        lines = ['@' + i.asPython() for i in self.decorator_list]

        p = ', '.join(
            i.asPython() for i in self.bases + self.keywords).strip()
        if p:
            p = '('+p+')'

        lines.append('class {}{}:'.format(self.name, p))

        return bodyfmt(lines, indent) + '\n' + bodyfmt(self.body, indent+1)

class ExceptHandler(_ast.ExceptHandler, Datanode):
    '''Individual exception in a Try block.'''

class Try(_ast.Try, Block):
    _fields = 'body handlers orelse finalbody'.split()
    _defaults = {'orelse': [], 'finalbody': []}
    def asPython(self, indent=0):
        tab = ' ' * 4 * indent
        body = tab + 'try:\n'
        body += bodyfmt(self.body, indent+1)

        for exc in self.handlers:
            body += '\n' + tab + 'except'
            if exc.type:
                body += ' ' + exc.type.asPython()
            if exc.name:
                body += ' as ' + exc.name
            body += ':\n' + bodyfmt(exc.body, indent+1)

        if self.orelse:
            body += '\n' + tab + 'else:\n' + bodyfmt(self.orelse, indent+1)
        if self.finalbody:
            body += '\n' + tab + 'finally:\n' + bodyfmt(self.finalbody, indent+1)
        return body
