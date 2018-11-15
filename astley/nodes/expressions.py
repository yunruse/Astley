'''Expressions, all of which may be eval'd '''

# pylint: disable=E0102
# E0102: repetition of new in op_modifier

import _ast
from ast import copy_location

from . import Node, functionKind, Expression, load, store
from .datanodes import keyword
from .signature import arguments

__all__ = '''\
expr Expr Name NameS NameConstant Constant \
Num Ellipsis Str Bytes JoinedStr \
Subscript Attribute Call IfExp Lambda \
Iterable List Tuple Dict Set \
Comprehension GeneratorExp ListComp DictComp SetComp
'''.split()

class expr(Node):
    '''Expression node - subclasses may be eval'd'''
    def compile(self, filename='<unknown>'):
        expr = copy_location(Expression(body=self), self)
        return expr.compile(filename)

    def __call__(self, *args, **kwargs):
        return Call(
            self, list(args),
            [keyword(a, v) for a, v in kwargs.items()])

    def __getitem__(self, other):
        return Subscript(self, other)

from . import ops

def op_modifier(opKind, op):
    if opKind == 'cmpop':
        def new(self, other):
            return ops.Compare(self, [op()], [other])
    elif opKind == 'operator':
        def new(self, other):
            return ops.BinOp(self, op(), other)
    elif opKind == 'unaryop':
        def new(self):
            return ops.UnaryOp(op(), self)
    return new


for opKind, operators in ops.operators.items():
    if opKind == 'boolop':
        continue

    for nodeName, sym, *rest in operators:
        if rest:
            fname = rest[0]

            op = getattr(ops, nodeName, None)
            if not op:
                continue

            method = op_modifier(opKind, op)
            setattr(expr, fname, method)
            if opKind == 'operator':
                # BinOps have reversible dundermethods
                rname = fname.replace('__', '__r', 1)
                setattr(expr, rname, method)

class Expr(expr, _ast.Expr):
    '''Expression that may be used in a Module'''
    sym = '{self.value}'
    def compile(self, filename='<unknown>'):
        return self.value.compile(filename)

class Name(expr, _ast.Name):
    _defaults = {'ctx': load}
    sym = '{self.id}'

class NameS(Name):
    _defaults = {'ctx': store}
class NameConstant(expr, _ast.NameConstant):
    '''Keyword name, such as True, False, None'''
    def asPython(self):
        return str(self.value)
class Constant(expr, _ast.Constant):
    sym = '{self.value}'
class Num(expr, _ast.Num):
    sym = '{self.n}'
class Ellipsis(expr, _ast.Ellipsis):
    sym = '...'

class Str(expr, _ast.Str):
    def asFmt(self, sep="'"):
        """repr(str) with your choice of separator. Not complete.
        """
        if sep not in ("'", '"', '"""', "'''"):
            raise ValueError('Invalid separator.')

        asRepr = repr(self.s)[:-1]
        oldSep = asRepr[0]
        asRepr = asRepr[1:]

        if oldSep != sep:
            asRepr = asRepr.replace('\\' + oldSep, oldSep).replace(sep, '\\' + sep)
            if sep in ('"""', "'''"):
                asRepr = asRepr.replace('\\n', '\n')

        return sep + asRepr + sep

    def asPython(self):
        return self.asFmt(sep='"')

class Bytes(expr, _ast.Bytes):
    sym = '{self.s!r}'

class JoinedStr(expr, _ast.JoinedStr):
    def asRaw(self):
        return ''.join(
            i.s if isinstance(i, Str) else i.asPython()
            for i in self.values)

    def asPython(self):
        return 'f' + repr(self.asRaw())

class Subscript(expr, _ast.Subscript):
    sym = '{self.value}[{self.slice}]'
class Attribute(expr, _ast.Attribute):
    sym = '{self.value}.{self.attr}'
class Call(expr, _ast.Call):
    _defaults = {'keywords': [], 'args': []}
    def asPython(self):
        return '{}({})'.format(
            self.func.asPython(), ', '.join(
                i.asPython() for i in self.args + self.keywords))

class IfExp(expr, _ast.IfExp):
    sym = '{self.body} if {self.test} else {self.orelse}'
class Lambda(functionKind, expr, _ast.Lambda):
    sym = 'lambda {self.args}: {self.body}'

    @classmethod
    def fromFunction(cls, func=None, body=None):
        return cls(arguments.fromFunction(func), body or None)

# Iterables

class Iterable(expr):
    @property
    def _elts(self):
        return ', '.join(i.asPython() for i in self.elts)

class List(Iterable, _ast.List):
    sym = '[{self._elts}]'
class Tuple(Iterable, _ast.Tuple):
    _defaults = {'ctx': load}
    def asPython(self):
        elts = self.elts
        if len(elts) == 0:
            return '()'
        elif len(elts) == 1:
            return '({}, )'.format(elts[0].asPython())
        else:
            return '({})'.format(self._elts)
class Dict(Iterable, _ast.Dict):
    def asPython(self):
        return '{{{}}}'.format(', '.join(
            k.asPython() + ': ' + v.asPython()
            for k, v in zip(self.keys, self.values)))
class Set(Iterable, _ast.Set):
    def asPython(self):
        if self.elts:
            return '{{{}}}'.format(self._elts)
        else:
            return 'set()'

class Comprehension(expr):
    '''Iterable comprehension'''
    sym = '{self.elt} {self.elements}'
    elements = property(lambda s: ' '.join(
        i.asPython() for i in s.generators))

class GeneratorExp(Comprehension, _ast.GeneratorExp):
    sym = '({self.elt} {self.elements})'
class SetComp(Comprehension, _ast.SetComp):
    sym = '{{{self.elt} {self.elements}}}'
class ListComp(Comprehension, _ast.ListComp):
    sym = '[{self.elt} {self.elements}]'
class DictComp(Comprehension, _ast.DictComp):
    sym = '{{{self.key}: {self.value} {self.elements}}}'
