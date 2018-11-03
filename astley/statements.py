'''Statements that may only be exec'd'''

from .nodes import *
from .helpers import copyfix

class stmt(Node):
    '''Statement node - subclasses may be exec'd'''
    def compile(self, filename='<unknown>'):
        module = copyfix(self, Module(body=[self]))
        return module.compile(filename)

class assign(stmt):
    '''Base class for assignment statements'''

class Assign(assign, ast.Assign):
    '''Assignment of value(s)'''
    def __str__(self):
        return '{} = {}'.format(
            ', '.join(map(str, self.targets)), self.value)

class AugAssign(assign, ast.AugAssign):
    '''Augmented in-place assignment (eg +=)'''
    sym='{self.target} {self.op}= {self.value}'

class AnnAssign(assign, ast.AnnAssign):
    '''Single-value type-annotated assignment'''
    def __str__(self):
        value = getattr(self, 'value', None)
        if value:
            return '{}: {} = {}'.format(
                self.target, self.annotation, self.value)
        return '{} = {}'.format(
            ', '.join(map(str, self.targets)), self.value)
    sym='{self.target}: {self.value}'


class oneliner(stmt):
    '''Base class: One-line statement.'''
    def __str__(self):
        v = getattr(self, 'value', getattr(self, 'exc', None))
        return getattr(self, 'sym') + (' '+str(v))*bool(v)

class Return(ast.Return): sym='return'
class Delete(oneliner, ast.Delete): sym='del'
class Raise(oneliner, ast.Raise): sym='raise'
class Await(oneliner, ast.Yield): sym='await'
class Yield(oneliner, ast.Yield): sym='yield'
class YieldFrom(oneliner, ast.YieldFrom): sym='yield from'
class Global(oneliner, ast.Global): sym='global'
class Nonlocal(oneliner, ast.Nonlocal): sym='nonlocal'

class Assert(oneliner, ast.Assert):
    def __str__(self):
        msg = getattr(self, 'msg', None)
        if msg:
            return 'assert {}, {}'.format(self.test, msg)
        else:
            return 'assert {}'.format(self.test)

class word(oneliner):
    '''Base class: Single-word statements.'''

class Pass(ast.Pass): sym='pass'
class Continue(word, ast.Continue): sym='continue'
class Break(word, ast.Break): sym='break'

class import_(stmt):
    '''Base: Statement that imports.'''

class Import(ast.Import):
    def __str__(import_, self):
        return 'import {}'.format(', '.join(map(str, self.names)))

class ImportFrom(ast.ImportFrom):
    def __str__(self):
        return 'from {} import {}'.format(
            self.module, ', '.join(map(str, self.names)))

class block(stmt):
    pass

class asyncblock(block):
    pass

def bodyfmt(body, indent=1):
    return '\n'.join(
        ' '*4*indent +
        (i.__str__(indent+1) if isinstance(i, block) else str(i))
        for i in body)

class If(ast.If):
    defaults={'orelse': []}
    def __str__(block, self, indent=1):
        body = 'if {}:\n{}'.format( 
            self.test, bodyfmt(self.body, indent))
        e = self.orelse
        if e:
            if len(e) == 1 and isinstance(e[0], ast.If):
                body += '\nel' + str(e[0])
            else:
                body += '\nelse:\n{}'.format(
                    bodyfmt(e, indent))
        return body

class While(ast.While):
    def __str__(block, self, indent=1):
        return 'while {}:\n{}'.format( 
            self.test, bodyfmt(self.body, indent))

class for_(block):
    defaults = {'orelse': []}
    def __str__(self, indent=1):
        body = '{} {} in {}:\n{}'.format(
            self.symbol, self.target, self.iter,
            bodyfmt(self.body, indent))
        if self.orelse:
            body += '\nelse:\n{}'.format(
                bodyfmt(self.orelse, indent))
        return body

class For(for_, ast.For):
    symbol = 'for'
class AsyncFor(for_, asyncblock, ast.AsyncFor):
    symbol = 'async for'

class with_(block):
    def __str__(self, indent=1):
        return 'with {}:\n{}'.format(
            ', '.join(map(str, self.items)),
            bodyfmt(self.body, indent))

class With(with_, ast.With):
    symbol='with'
class AsyncWith(with_, asyncblock, ast.AsyncWith):
    symbol='async with'

class definition(block):
    pass

class function(definition):
    def __str__(self, indent=1):
        decorators = list(map('@{}'.format, self.decorator_list))
        if decorators:
            decorators.append('')
        returns = ''
        if self.returns:
            returns = ' -> ' + str(self.returns)
        return '{}{} {}({}){}:\n{}'.format(
            '\n'.join(decorators), self.symbol, self.name,
            self.args, returns,
            bodyfmt(self.body, indent))

class FunctionDef(function, ast.FunctionDef):
    symbol = 'def'

class AsyncFunctionDef(function, asyncblock, ast.AsyncFunctionDef):
    symbol = 'async def'

class ClassDef(block, ast.ClassDef):
    def __str__(self, indent=1):
        decorators = list(map(str, self.decorator_list))
        if decorators:
            decorators.append('')
        p = ', '.join(map(str, self.bases + self.keywords))
        if p:
            p = '('+p+')'
            
        return '{}class {}{}:\n{}'.format(
            '\n'.join(decorators), self.name, p,
            bodyfmt(self.body, indent))

class ExceptHandler(datanode, ast.ExceptHandler):
    def __str__(self, indent=1):
        n = 'except'
        if self.type:
            n += ' ' + str(self.type)
        if self.name:
            n += ' as ' + str(self.name)
        
        return '{}:\n{}'.format(n, bodyfmt(self.body, indent))

class Try(block, ast.Try):
    def __str__(self, indent=1):
        body = 'try:\n' + bodyfmt(self.body, indent)
        body += '\n' + '\n'.join(
            i.__str__(indent) for i in self.handlers)
        if self.orelse:
            body += '\nelse:\n' + bodyfmt(self.orelse, indent)
        if self.finalbody:
            body += '\nfinally:\n' + bodyfmt(self.finalbody, indent)
        return body