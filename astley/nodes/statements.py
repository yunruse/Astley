'''Statements that may only be exec'd'''

import _ast

from ..node import copy
from ..finalise import finalise
from . import Node, Module
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
    sym='{self.target} {self.op}= {self.value}'

class AnnAssign(_ast.AnnAssign, AssignKind):
    '''Single-value type-annotated assignment'''
    def asPython(self):
        value = getattr(self, 'value', None)
        if value:
            return '{}: {} = {}'.format(
                self.target, self.annotation, self.value)
        return '{} = {}'.format(
            ', '.join(i.asPython() for i in self.targets),
            self.value)


class Oneliner(stmt):
    '''Base class: One-line statement.'''
    def asPython(self):
        v = getattr(self, 'value', getattr(self, 'exc', None))
        sym = getattr(self, 'sym')
        if v:
            return sym + ' ' + v.asPython()
        else:
            return sym

class Return(_ast.Return, Oneliner): sym='return'
class Delete(_ast.Delete, Oneliner): sym='del'
class Raise(_ast.Raise, Oneliner): sym='raise'
class Await(_ast.Yield, Oneliner): sym='await'
class Yield(_ast.Yield, Oneliner): sym='yield'
class YieldFrom(_ast.YieldFrom, Oneliner): sym='yield from'
class Global(_ast.Global, Oneliner): sym='global'
class Nonlocal(_ast.Nonlocal, Oneliner): sym='nonlocal'

class Assert(_ast.Assert, Oneliner):
    def asPython(self):
        code = 'assert ' + self.test.asPython()
        msg = getattr(self, 'msg', None)
        if msg:
            return code + ', ' + msg.asPython()
        else:
            return code

class Word(Oneliner):
    '''Base class: Single-word statements.'''

class Pass(_ast.Pass, Word): sym='pass'
class Continue(_ast.Continue, Word): sym='continue'
class Break(_ast.Break, Word): sym='break'

class Import(_ast.Import, stmt):
    def asPython(self):
        return 'import {}'.format(
            ', '.join(i.asPython() for i in self.names))

class ImportFrom(_ast.ImportFrom, Import):
    def asPython(self):
        return 'from {} import {}'.format(
            self.module,
            ', '.join(i.asPython() for i in self.names))

class Block(stmt):
    pass

class AsyncBlock(Block):
    pass

def bodyfmt(body, indent=1):
    return '\n'.join(
        ' ' * 4 * indent + (i.asPython(indent + 1)
        if isinstance(i, Block) else i.asPython())
        for i in body)

class If(_ast.If, Block):
    _fields = 'test body orelse'.split()
    _defaults = {'orelse': []}
    def asPython(self, indent=1):
        body = 'if {}:\n{}'.format(
            self.test.asPython(),
            bodyfmt(self.body, indent))
        e = getattr(self, 'orelse', None)
        if e:
            body += '\n' + '    ' * (indent-1)
            if len(e) == 1 and isinstance(e[0], _ast.If):
                body += 'el' + e[0].asPython(indent)
            else:
                body +='else:\n' + bodyfmt(e, indent)
        return body

class While(_ast.While, Block):
    _fields = 'test body'.split()
    def asPython(self, indent=1):
        return 'while {}:\n{}'.format(
            self.test, bodyfmt(self.body, indent))

class For(_ast.For, Block):
    _fields = 'test body'.split()
    _defaults = {'orelse': []}
    def asPython(self, indent=1):
        body = '{} {} in {}:\n{}'.format(
            self.symbol,
            self.target.asPython(),
            self.iter.asPython(),
            bodyfmt(self.body, indent))
        e = getattr(self, 'orelse', None)
        if e:
            body += '\nelse:\n{}'.format(
                bodyfmt(e, indent))
        return body
    symbol = 'for'

class AsyncFor(_ast.AsyncFor, For, AsyncBlock):
    symbol = 'async for'

class With(_ast.With, Block):
    symbol = 'with'
    def asPython(self, indent=1):
        return 'with {}:\n{}'.format(
            ', '.join(i.asPython() for i in self.items),
            bodyfmt(self.body, indent))

class AsyncWith(With, AsyncBlock, _ast.AsyncWith):
    symbol = 'async with'

class Definition(Block):
    '''Class or function definition.'''

class FunctionDef(_ast.FunctionDef, Definition):
    _fields = 'name args body decorator_list returns'.split()

    @classmethod
    def withBody(cls, body, **kwargs):
        '''Decorator to inherit a real Python function's properties.

        Use as:
        @withBody(Return(Name('a') + Name('b'))):
        def add(a, b=2): ...
        '''
        def wrapper(func):
            kw = kwargs.copy()
            if hasattr(func, '__name__'):
                kw.setdefault('name', func.__name__)
            if hasattr(func, '__annotations__'):
                an = func.__annotations__
                if 'return' in an:
                    kw.setdefault('returns', an['return'])
            kw.setdefault('args', arguments.fromFunction(func))
            return cls(**kw)
        return wrapper

    def asPython(self, indent=1):
        dec = '\n'.join(
            '@' + i.asPython() for i in self.decorator_list)
        if dec:
            dec += '\n'
        returns = ''
        if self.returns:
            returns = ' -> ' + self.returns.asPython()
        return '{}{} {}({}){}:\n{}'.format(
            dec, self.symbol, self.name,
            self.args.asPython(), returns,
            bodyfmt(self.body, indent))

class AsyncFunctionDef(_ast.AsyncFunctionDef, FunctionDef, AsyncBlock):
    symbol = 'async def'

class ClassDef(_ast.ClassDef, Definition):
    def asPython(self, indent=1):
        dec = '\n'.join(
            '@' + i.asPython() for i in self.decorator_list)
        if dec:
            dec += '\n'
        p = ', '.join(
            i.asPython() for i in self.bases + self.keywords)
        if p:
            p = '('+p+')'

        return '{}class {}{}:\n{}'.format(
            dec, self.name, p,
            bodyfmt(self.body, indent))

class ExceptHandler(_ast.ExceptHandler, Datanode):
    '''Individual exception in a Try block.'''
    def asPython(self, indent=1):
        n = 'except'
        if self.type:
            n += ' ' + self.type.asPython()
        if self.name:
            n += ' as ' + self.name.asPython()

        return '{}:\n{}'.format(n, bodyfmt(self.body, indent))

class Try(_ast.Try, Block):
    _fields = 'body handlers orelse finalbody'.split()
    _defaults = {'orelse': [], 'finalbody': []}
    def asPython(self, indent=1):
        body = 'try:\n' + bodyfmt(self.body, indent)
        body += '\n' + '\n'.join(
            i.asPython(indent) for i in self.handlers)
        e, f = getattr(self, 'orelse', None), getattr(self, 'finalbody', None)
        if e:
            body += '\nelse:\n' + bodyfmt(e, indent)
        if f:
            body += '\nfinally:\n' + bodyfmt(f, indent)
        return body
