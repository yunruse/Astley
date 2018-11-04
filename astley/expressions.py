'''Expressions, all of which may be eval'd '''

from .nodes import *
from .datanodes import keyword
from . import ops
from .helpers import copyfix

__all__ = []

def all(obj):
    __all__.append(obj.__name__)
    return obj

#% expressions

@all
class expr(Node):
    '''Expression node - subclasses may be eval'd'''
    def compile(self, filename='<unknown>'):
        expr = copyfix(self, Expression(body=self))
        return expr.compile(filename)
        
    def __call__(self, *args, **kwargs):
        return Call(
            self, list(args),
            [keyword(a, v) for a, v in kwargs.items()])
    
    def __getitem__(self, other):
        return Subscript(self, other)
    
    #def __getattr__(self, other):
    #    return Attribute(self, other)
    
    def or_(self, other):
        return boolop(Or(), [self, other])
    def and_(self, other):
        return boolop(And(), [self, other])

def modify_item(item):
    '''Replace '''
    if isinstance(item, (int, float)):
        return Num(item)
    elif isinstance(item, str):
        return Str(item)
    elif isinstance(item, (list, tuple)):
        return type(item)(map(modify_item, item))
    else:
        return item

def op_modifier(kind, f):
    new = None
    if not f:
        return
    if kind == 'cmpop':
        def new(self, other):
            return Compare(self, f(), [modify_item(other)])
    elif kind == 'operator':
        def new(self, other):
            return BinOp(self, f(), modify_item(other))
    elif kind == 'unaryop':
        def new(self):
            return UnaryOp(f(), modify_item(self))
    return new

for kind, operators in ops.operators.items():
    for name, sym, func, *prec in operators:
        new = op_modifier(kind, getattr(ops, name, None))
        if not new:
            continue
        new.__name__ = func
        setattr(expr, func, new)

@all
class Expr(expr, ast.Expr):
    sym = '{self.value}'
    def compile(self, filename='<unknown>'):
        return self.value.compile(filename)

@all
class Name(expr, ast.Name):
    defaults = {'ctx': load}
    sym = '{self.id}'

@all
class NameS(Name):
    defaults = {'ctx': store}
@all
class NameConstant(expr, ast.NameConstant):
    sym = '{self.value}'
@all
class Constant(expr, ast.Constant):
    sym = '{self.value}'
@all
class Num(expr, ast.Num):
    sym = '{self.n}'
@all
class Ellipsis(expr, ast.Ellipsis):
    sym='...'

@all
class Str(expr, ast.Str):
    sym = '{self.s!r}'
@all
class Bytes(expr, ast.Bytes):
    sym = '{self.s!r}'

@all
class JoinedStr(expr, ast.JoinedStr):
    def asRaw(self):
        return ''.join(
            i.s if isinstance(i, Str) else i.asPython()
            for i in self.values)
    
    def asPython(self):
        return 'f' + repr(self.asRaw())

@all
class Subscript(expr, ast.Subscript):
    sym='{self.value}[{self.slice}]'
@all
class Attribute(expr, ast.Attribute):
    sym='{self.value}.{self.attr}'
@all
class Call(expr, ast.Call):
    defaults = {'keywords': [], 'args': []}
    def asPython(self):
        return '{}({})'.format(
            self.func.asPython(), ', '.join(
                i.asPython() for i in self.args + self.keywords))

@all
class IfExp(expr, ast.IfExp):
    sym = '{self.body} if {self.test} else {self.orelse}'
@all
class functionKind:
    pass
@all
class Lambda(functionKind, expr, ast.Lambda):
    sym = 'lambda {self.args}: {self.body}'

# Iterables

@all
class iter(expr):
    @property
    def _elts(self):
        return ', '.join(i.asPython() for i in self.elts)

@all
class List(iter, ast.List):
    sym = '[{self._elts}]'
@all
class Tuple(iter, ast.Tuple):
    defaults = {'ctx': load}
    def asPython(self):
        elts = self.elts
        if len(elts) == 1:
            elts = (*elts, '')
        if elts:
            return self._elts
        else:
            return '()'
@all
class Dict(iter, ast.Dict):
    def asPython(self):
        return '{{{}}}'.format(', '.join(
            k.asPython() + ': ' + v.asPython()
            for k, v in zip(self.keys, self.values)))
@all
class Set(iter, ast.Set):
    def asPython(self):
        if self.elts:
            return '{{{}}}'.format(self._elts)
        else:
            return 'set()'
@all
class comp(expr):
    '''Iterable comprehension'''
    sym = '{self.elt} {self.elements}'
    elements = property(lambda s: ' '.join(
        i.asPython() for i in s.generators))

@all
class GeneratorExp(comp, ast.GeneratorExp):
    pass
@all
class SetComp(comp, ast.SetComp):
    sym = '{{{self.elt} {self.elements}}}'
@all
class ListComp(comp, ast.ListComp):
    sym = '[{self.elt} {self.elements}]'
@all
class DictComp(comp, ast.DictComp):
    sym = '{{{self.key}: {self.value} {self.elements}}}'

#% Operators
@all
class OpApplier(expr):
    '''Node that applies an Op to some values.'''
    pass

'A and B or C -> (A and B) or c'
'A and (B or C)'

requiresParentheses = (
    ast.IfExp, ast.Lambda, ast.GeneratorExp
)

@all
class BinOp(OpApplier, ast.BinOp):
    '''Binary infix operator (+, -, and, etc) '''
    def asPython(self):
        # Add brackets to ensure cases such as '(a + b) * c'
        # are represented correctly
        pm = ops.precedence[self.op.__class__.__name__]

        def name(node):
            name = node.asPython()
            if isinstance(node, ast.BinOp):
                pinner = ops.precedence[node.op.__class__.__name__]
                if pm > pinner:
                    return '(' + name + ')'
            elif isinstance(node, requiresParentheses):
                return '(' + name + ')'
            
            return name
        
        return "{} {} {}".format(
            name(self.left), self.op.asPython(), name(self.right))

@all
class BoolOp(OpApplier, ast.BoolOp):
    '''Binary infix operator that works on booleans (and, or)'''
    def asPython(self):
        values = list(map(str, self.values))
        # try to map 'A and (B or C)' nicely
        if isinstance(self.op, ast.Or):
            for i, v in enumerate(self.values):
                if (isinstance(v, ast.BinOp)
                and isinstance(v.op, ast.And)):
                    self.values[i] = '(' + values[i] + ')'
        
        return (' '+self.op.asPython()+' ').join(
            i.asPython() for i in self.values)
    
    def and_(self, other):
        if isinstance(self.op, ast.And):
            self.values.append(other)
            return self
        else:
            return BoolOp(ops.And(), [self, other])
    
    def or_(self, other):
        if isinstance(self.op, ast.Or):
            self.values.append(other)
            return self
        else:
            return BoolOp(ops.Or(), [self, other])

@all
class UnaryOp(OpApplier, ast.UnaryOp):
    '''Unary prefix operator.'''
    sym = "{self.op}{self.operand}"

@all
class Compare(OpApplier, ast.Compare):
    '''Chain of comparators.'''
    _fields = 'left ops comparators'.split()
    def asPython(self):
        chain = map(
            '{0[0]} {0[1]}'.format,
            zip(self.ops, self.comparators))
        return ' '.join((str(self.left), *chain))
    
    def _op(self, other, operator):
        if isinstance(self.op, operator):
            self.comparators.append(other)
            return self
        else:
            return Compare(self, operator, other)
    
    def __eq__(s, o): s._op(o, Eq)
    def __ne__(s, o): s._op(o, NotEq)
    def __lt__(s, o): s._op(o, Lt)
    def __le__(s, o): s._op(o, LtE)
    def __gt__(s, o): s._op(o, Gt)
    def __ge__(s, o): s._op(o, GtE)
    