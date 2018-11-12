'''Statements that may only be exec'd'''

import _ast
from ast import copy_location

from .nodes import Node, Module
from .datanodes import datanode
from .signature import arguments

class stmt(Node):
    '''Statement node - subclasses may be exec'd'''
    def compile(self, filename='<unknown>'):
        module = copy_location(Module(body=[self]), self)
        return module.compile(filename)

class assign(stmt):
    '''Base class for assignment statements'''

class Assign(assign, _ast.Assign):
    '''Assignment of value(s)'''
    def asPython(self):
        return '{} = {}'.format(
            ', '.join(i.asPython() for i in self.targets),
            self.value)

class AugAssign(assign, _ast.AugAssign):
    '''Augmented in-place assignment (eg +=)'''
    sym='{self.target} {self.op}= {self.value}'

class AnnAssign(assign, _ast.AnnAssign):
    '''Single-value type-annotated assignment'''
    def asPython(self):
        value = getattr(self, 'value', None)
        if value:
            return '{}: {} = {}'.format(
                self.target, self.annotation, self.value)
        return '{} = {}'.format(
            ', '.join(i.asPython() for i in self.targets),
            self.value)


class oneliner(stmt):
    '''Base class: One-line statement.'''
    def asPython(self):
        v = getattr(self, 'value', getattr(self, 'exc', None))
        sym = getattr(self, 'sym')
        if v:
            return sym + ' ' + v.asPython()
        else:
            return sym

class Return(_ast.Return): sym='return'
class Delete(oneliner, _ast.Delete): sym='del'
class Raise(oneliner, _ast.Raise): sym='raise'
class Await(oneliner, _ast.Yield): sym='await'
class Yield(oneliner, _ast.Yield): sym='yield'
class YieldFrom(oneliner, _ast.YieldFrom): sym='yield from'
class Global(oneliner, _ast.Global): sym='global'
class Nonlocal(oneliner, _ast.Nonlocal): sym='nonlocal'

class Assert(oneliner, _ast.Assert):
    def asPython(self):
        code = 'assert ' + self.test.asPython()
        msg = getattr(self, 'msg', None)
        if msg:
            return code + ', ' + msg.asPython()
        else:
            return code

class word(oneliner):
    '''Base class: Single-word statements.'''

class Pass(word, _ast.Pass): sym='pass'
class Continue(word, _ast.Continue): sym='continue'
class Break(word, _ast.Break): sym='break'

class import_(stmt):
    '''Base: Statement that imports.'''

class Import(import_, _ast.Import):
    def asPython(self):
        return 'import {}'.format(
            ', '.join(i.asPython() for i in self.names))

class ImportFrom(import_, _ast.ImportFrom):
    def asPython(self):
        return 'from {} import {}'.format(
            self.module,
            ', '.join(i.asPython() for i in self.names))

class block(stmt):
    pass

class asyncblock(block):
    pass

def bodyfmt(body, indent=1):
    return '\n'.join(
        ' ' * 4 * indent + (i.asPython(indent + 1)
        if isinstance(i, block) else i.asPython())
        for i in body)

class If(_ast.If):
    _defaults = {'orelse': []}
    def asPython(self, indent=1):
        body = 'if {}:\n{}'.format(
            self.test.asPython(),
            bodyfmt(self.body, indent))
        e = self.orelse
        if e:
            if len(e) == 1 and isinstance(e[0], _ast.If):
                body += '\nel' + e[0].asPython()
            else:
                body += '\nelse:\n{}'.format(
                    bodyfmt(e, indent))
        return body

class While(_ast.While):
    def asPython(self, indent=1):
        return 'while {}:\n{}'.format(
            self.test, bodyfmt(self.body, indent))

class for_(block):
    _defaults = {'orelse': []}
    def asPython(self, indent=1):
        body = '{} {} in {}:\n{}'.format(
            self.symbol,
            self.target.asPython(),
            self.iter.asPython(),
            bodyfmt(self.body, indent))
        if self.orelse:
            body += '\nelse:\n{}'.format(
                bodyfmt(self.orelse, indent))
        return body

class For(for_, _ast.For):
    symbol = 'for'
class AsyncFor(for_, asyncblock, _ast.AsyncFor):
    symbol = 'async for'

class with_(block):
    def asPython(self, indent=1):
        return 'with {}:\n{}'.format(
            ', '.join(i.asPython() for i in self.items),
            bodyfmt(self.body, indent))

class With(with_, _ast.With):
    symbol='with'
class AsyncWith(with_, asyncblock, _ast.AsyncWith):
    symbol='async with'

class definition(block):
    pass

class function(definition):
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

class FunctionDef(function, _ast.FunctionDef):
    symbol = 'def'

class AsyncFunctionDef(function, asyncblock, _ast.AsyncFunctionDef):
    symbol = 'async def'

class ClassDef(block, _ast.ClassDef):
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

class ExceptHandler(datanode, _ast.ExceptHandler):
    ''''''
    def asPython(self, indent=1):
        n = 'except'
        if self.type:
            n += ' ' + self.type.asPython()
        if self.name:
            n += ' as ' + self.name.asPython()

        return '{}:\n{}'.format(n, bodyfmt(self.body, indent))

class Try(block, _ast.Try):
    def asPython(self, indent=1):
        body = 'try:\n' + bodyfmt(self.body, indent)
        body += '\n' + '\n'.join(
            i.asPython(indent) for i in self.handlers)
        if self.orelse:
            body += '\nelse:\n' + bodyfmt(self.orelse, indent)
        if self.finalbody:
            body += '\nfinally:\n' + bodyfmt(self.finalbody, indent)
        return body
