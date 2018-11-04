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
    def asPython(self):
        return '{} = {}'.format(
            ', '.join(i.asPython() for i in self.targets),
            self.value)

class AugAssign(assign, ast.AugAssign):
    '''Augmented in-place assignment (eg +=)'''
    sym='{self.target} {self.op}= {self.value}'

class AnnAssign(assign, ast.AnnAssign):
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

class Return(ast.Return): sym='return'
class Delete(oneliner, ast.Delete): sym='del'
class Raise(oneliner, ast.Raise): sym='raise'
class Await(oneliner, ast.Yield): sym='await'
class Yield(oneliner, ast.Yield): sym='yield'
class YieldFrom(oneliner, ast.YieldFrom): sym='yield from'
class Global(oneliner, ast.Global): sym='global'
class Nonlocal(oneliner, ast.Nonlocal): sym='nonlocal'

class Assert(oneliner, ast.Assert):
    def asPython(self):
        code = 'assert ' + self.test.asPython()
        msg = getattr(self, 'msg', None)
        if msg:
            return code + ', ' + msg.asPython()
        else:
            return code

class word(oneliner):
    '''Base class: Single-word statements.'''

class Pass(word, ast.Pass): sym='pass'
class Continue(word, ast.Continue): sym='continue'
class Break(word, ast.Break): sym='break'

class import_(stmt):
    '''Base: Statement that imports.'''

class Import(ast.Import):
    def asPython(import_, self):
        return 'import {}'.format(
            ', '.join(i.asPython() for i in self.names))

class ImportFrom(ast.ImportFrom):
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
        ' '*4*indent +
            (i.asPython(indent+1) if isinstance(i, block)
             else i.asPython())
        for i in body)

class If(ast.If):
    defaults={'orelse': []}
    def asPython(block, self, indent=1):
        body = 'if {}:\n{}'.format( 
            self.test.asPython(),
            bodyfmt(self.body, indent))
        e = self.orelse
        if e:
            if len(e) == 1 and isinstance(e[0], ast.If):
                body += '\nel' + e[0].asPython()
            else:
                body += '\nelse:\n{}'.format(
                    bodyfmt(e, indent))
        return body

class While(ast.While):
    def asPython(block, self, indent=1):
        return 'while {}:\n{}'.format( 
            self.test, bodyfmt(self.body, indent))

class for_(block):
    defaults = {'orelse': []}
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

class For(for_, ast.For):
    symbol = 'for'
class AsyncFor(for_, asyncblock, ast.AsyncFor):
    symbol = 'async for'

class with_(block):
    def asPython(self, indent=1):
        return 'with {}:\n{}'.format(
            ', '.join(i.asPython() for i in self.items),
            bodyfmt(self.body, indent))

class With(with_, ast.With):
    symbol='with'
class AsyncWith(with_, asyncblock, ast.AsyncWith):
    symbol='async with'

class definition(block):
    pass

class function(definition):
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

class FunctionDef(function, ast.FunctionDef):
    symbol = 'def'

class AsyncFunctionDef(function, asyncblock, ast.AsyncFunctionDef):
    symbol = 'async def'

class ClassDef(block, ast.ClassDef):
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

class ExceptHandler(datanode, ast.ExceptHandler):
    def asPython(self, indent=1):
        n = 'except'
        if self.type:
            n += ' ' + self.type.asPython()
        if self.name:
            n += ' as ' + self.name.asPython()
        
        return '{}:\n{}'.format(n, bodyfmt(self.body, indent))

class Try(block, ast.Try):
    def asPython(self, indent=1):
        body = 'try:\n' + bodyfmt(self.body, indent)
        body += '\n' + '\n'.join(
            i.asPython(indent) for i in self.handlers)
        if self.orelse:
            body += '\nelse:\n' + bodyfmt(self.orelse, indent)
        if self.finalbody:
            body += '\nfinally:\n' + bodyfmt(self.finalbody, indent)
        return body