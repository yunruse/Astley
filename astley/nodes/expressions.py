'''Expressions, all of which may be eval'd '''

# pylint: disable=E0102
# E0102: repetition of new in op_modifier

import _ast
from ast import copy_location
from sys import version_info

from . import Node, function_kind, Expression, load, store
from .datanodes import keyword
from .signature import arguments

__all__ = '''\
expr Expr Name NameS Constant JoinedStr \
NameConstant Num Str Bytes Ellipsis \
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

def op_modifier(op_kind, op):
    if op_kind == 'cmpop':
        def new(self, other):
            return ops.Compare(self, [op()], [other])
    elif op_kind == 'operator':
        def new(self, other):
            return ops.BinOp(self, op(), other)
    elif op_kind == 'unaryop':
        def new(self):
            return ops.UnaryOp(op(), self)
    return new


for op_kind, operators in ops.operators.items():
    if op_kind == 'boolop':
        continue

    for node_name, sym, *rest in operators:
        if rest:
            fname = rest[0].replace('eq', 'equate').replace('ne', 'nequate')
            # to avoid ambiguity, making a node of comparison is handled as
            # x ._== y and x ._!= y.

            op = getattr(ops, node_name, None)
            if not op:
                continue

            method = op_modifier(op_kind, op)
            setattr(expr, fname, method)
            if op_kind == 'operator':
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

def string_format(string, sep="'"):
    """repr(str) with your choice of separator.
    No guarantees it will work beyond internal usage.
    """
    if sep not in ("'", '"', '"""', "'''"):
        raise ValueError('Invalid separator.')

    is_bytes = isinstance(string, bytes)

    old_sep, *as_repr = repr(string)[int(is_bytes):-1]
    as_repr = ''.join(as_repr)

    if old_sep != sep:
        as_repr = as_repr.replace('\\' + old_sep, old_sep).replace(sep, '\\' + sep)
        if sep in ('"""', "'''"):
            as_repr = as_repr.replace('\\n', '\n')

    return 'b' * is_bytes + sep + as_repr + sep


class Constant(expr, _ast.Constant):
    '''Constant value: number, ellipsis, string or bytes. Used in 3.8+.'''
    __fields__ = ('value', )
    def _as_python(self):
        if isinstance(self.value, (str, bytes)):
            return string_format(self.value, '"')
        elif self.value is None:
            return 'None'
        else:
            return repr(self.value)

# In 3.8, a lot of constants are merged.
# TODO: This is really a hotfix.
# It could do with some changes if it was needed for cross-version transpilation.

if version_info >= (3, 8):
    class NameConstant(Constant):
        '''Keyword literal: True, False, None. Alias for Constant.'''

    class Ellipsis(Constant):
        '''Ellipsis literal. Useful in 3rd party packages such as numpy. Alias for Constant.'''
        def _as_python(self):
            return '...'

    class Num(Constant):
        '''Numerical literal of type int, float or complex. Alias for Constant.'''

    class Str(Constant):
        '''String literal. Alias for Constant.'''

    class Bytes(Constant):
        '''Bytes literal. Alias for Constant.'''

else:
    class NameConstant(expr, _ast.NameConstant):
        '''Keyword literal: True, False, None. Subsumed into Constant after 3.8.'''
        def _as_python(self):
            return str(self.value)

    class Ellipsis(expr, _ast.Ellipsis):
        sym = '...'

    class Num(expr, _ast.Num):
        '''Numerical literal of type int, float or complex.'''
        sym = '{self.n}'

    class Str(expr, _ast.Str):
        __fields__ = ('s', )
        def _as_python(self):
            return string_format(self.s, sep='"')

    class Bytes(expr, _ast.Bytes):
        __fields__ = ('s', )
        def _as_python(self):
            return string_format(self.s, sep='"')


class JoinedStr(expr, _ast.JoinedStr):
    def _as_python(self):
        body = ''
        for i in self.values:
            if isinstance(i, Str):
                body += i.s
            elif isinstance(i, Constant) and isinstance(i.value, str):
                body += i.value
            else:
                body += i._as_python()
        return 'f' + repr(body)

class Subscript(expr, _ast.Subscript):
    _fields = 'value slice ctx'.split()
    _defaults = {'ctx': load}

    sym = '{self.value}[{self.slice}]'
class Attribute(expr, _ast.Attribute):
    sym = '{self.value}.{self.attr}'
class Call(expr, _ast.Call):
    _defaults = {'keywords': [], 'args': []}
    def _as_python(self):
        return '{}({})'.format(
            self.func._as_python(), ', '.join(
                i._as_python() for i in self.args + self.keywords))

class IfExp(expr, _ast.IfExp):
    sym = '{self.body} if {self.test} else {self.orelse}'
class Lambda(function_kind, expr, _ast.Lambda):
    sym = 'lambda {self.args}: {self.body}'

    @classmethod
    def from_function(cls, func=None, body=None):
        return cls(arguments.from_function(func), body or None)

# Iterables

class Iterable(expr):
    @property
    def _elts(self):
        e = ', '.join(i._as_python() for i in self.elts)
        print(self, self.elts, e)
        return e

class List(Iterable, _ast.List):
    sym = '[{self._elts}]'
class Tuple(Iterable, _ast.Tuple):
    _defaults = {'ctx': load}
    def _as_python(self):
        elts = self.elts
        if len(elts) == 0:
            return '()'
        elif len(elts) == 1:
            return '({}, )'.format(elts[0]._as_python())
        else:
            return '({})'.format(self._elts)
class Dict(Iterable, _ast.Dict):
    def _as_python(self):
        return '{{{}}}'.format(', '.join(
            k._as_python() + ': ' + v._as_python()
            for k, v in zip(self.keys, self.values)))
class Set(Iterable, _ast.Set):
    def _as_python(self):
        if self.elts:
            return '{{{}}}'.format(self._elts)
        else:
            return 'set()'

class Comprehension(expr):
    '''Iterable comprehension'''
    sym = '{self.elt} {self.elements}'
    elements = property(lambda s: ' '.join(
        i._as_python() for i in s.generators))

class GeneratorExp(Comprehension, _ast.GeneratorExp):
    sym = '({self.elt} {self.elements})'
class SetComp(Comprehension, _ast.SetComp):
    sym = '{{{self.elt} {self.elements}}}'
class ListComp(Comprehension, _ast.ListComp):
    sym = '[{self.elt} {self.elements}]'
class DictComp(Comprehension, _ast.DictComp):
    sym = '{{{self.key}: {self.value} {self.elements}}}'
