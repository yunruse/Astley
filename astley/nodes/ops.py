'''Operators and their appliers'''

import _ast

from . import kind
from .expressions import expr

__all__ = [
    'OpKind', 'boolop', 'cmpop', 'operator', 'unaryop',
    'OpApplier', 'BoolOp', 'Compare', 'BinOp', 'UnaryOp',
    'operators', 'precedence',
]

class OpKind(kind):
    """Operator kind."""
    def _as_python(self):
        return self.symbol

class boolop(_ast.boolop, OpKind):
    def __new__(cls, values=None):
        self = super().__new__(cls)
        if values:
            self = UnaryOp(op=self, values=values)
        return self

class cmpop(_ast.cmpop, OpKind):
    def __new__(cls, left=None, *comparators):
        self = super().__new__(cls)
        if left and comparators:
            self = Compare(
                ops=[self] * len(comparators), left=left, comparators=comparators)
        return self

class operator(_ast.operator, OpKind):
    def __new__(cls, left=None, right=None):
        self = super().__new__(cls)
        if left and right:
            self = BinOp(op=self, left=left, right=right)
        return self

class unaryop(_ast.unaryop, OpKind):
    def __new__(cls, operand=None):
        self = super().__new__(cls)
        if operand:
            self = UnaryOp(op=self, operand=operand)
        return self


operators = dict(
    boolop=(
        ('Or', 'or', None, 1),
        ('And', 'and', None, 2),
    ),
    operator=(
        ('BitOr', '|', '__or__', 3),
        ('BitXor', '^', '__xor__', 4),
        ('BitAnd', '&', '__and__', 5),
        ('LShift', '<<', '__lshift__', 6),
        ('RShift', '>>', '__rshift__', 6),
        ('Add', '+', '__add__', 7),
        ('Sub', '-', '__sub__', 7),
        ('Mult', '*', '__mul__', 8),
        ('MatMult', '@', '__matmul__', 8),
        ('Div', '/', '__truediv__', 8),
        ('FloorDiv', '//', '__floordiv__', 8),
        ('Mod', '%', '__mod__', 8),
        ('Pow', '**', '__pow__', 9),
    ),
    cmpop=(
        ('In', 'in'),
        ('NotIn', 'not in'),
        ('Is', 'is'),
        ('IsNot', 'is not'),
        ('Lt', '<', '__lt__'),
        ('LtE', '<=', '__le__'),
        ('Gt', '>', '__gt__'),
        ('GtE', '>=', '__ge__'),
        ('NotEq', '!=', '__ne__'),
        ('Eq', '==', '__eq__'),
    ),
    unaryop=(
        ('Not', 'not '),
        ('Invert', '~', '__invert__'),
        ('UAdd', '+', '__pos__'),
        ('USub', '-', '__neg__'),
    )
)

precedence = {}

for op_kind, ops in operators.items():
    for node_name, symbol, *r in ops:
        if len(r) == 2:
            precedence[node_name] = r[1]

        exec('class {0}(_ast.{0}, {2}): symbol = "{1}"'.format(
             node_name, symbol, op_kind), globals())
        __all__.append(node_name)


class OpApplier(expr):
    '''Node that applies an Op to some values.'''
    pass

requires_parentheses = (
    _ast.IfExp, _ast.Lambda, _ast.GeneratorExp
)

class BinOp(OpApplier, _ast.BinOp):
    '''Binary infix operator (+, -, and, etc) '''
    def _as_python(self):
        # Add brackets to ensure cases such as '(a + b) * c'
        # are represented correctly
        pm = precedence[self.op.__class__.__name__]

        def name(node):
            name = node.as_python()
            if isinstance(node, _ast.BinOp):
                pinner = precedence[node.op.__class__.__name__]
                if pm > pinner:
                    return '(' + name + ')'
            elif isinstance(node, requires_parentheses):
                return '(' + name + ')'

            return name

        return "{} {} {}".format(
            name(self.left), self.op.symbol, name(self.right))

class BoolOp(OpApplier, _ast.BoolOp):
    '''Binary infix operator that works on booleans (and, or)'''
    def _as_python(self):
        values = [i.as_python() for i in self.values]
        # try to map 'A and (B or C)' nicely
        if isinstance(self.op, _ast.Or):
            for i, v in enumerate(self.values):
                if isinstance(v, _ast.BinOp) and isinstance(v.op, _ast.And):
                    self.values[i] = '(' + values[i] + ')'

        return (' ' + self.op.symbol + ' ').join(
            i.as_python() for i in self.values)

class UnaryOp(OpApplier, _ast.UnaryOp):
    '''Unary prefix operator.'''
    sym = "{self.op}{self.operand}"

class Compare(OpApplier, _ast.Compare):
    '''Chain of comparators.'''
    _fields = 'left ops comparators'.split()
    def _as_python(self):
        chain = [self.left.as_python()]
        for o, c in zip(self.ops, self.comparators):
            chain.append(o.symbol)
            chain.append(c.as_python())
        return ' '.join(chain)

    def _op(self, other, operator):
        self.ops.append(operator)
        self.comparators.append(other)
        return self

    __eq__ = lambda s, o: s._op(o, Eq)
    __ne__ = lambda s, o: s._op(o, NotEq)
    __lt__ = lambda s, o: s._op(o, Lt)
    __le__ = lambda s, o: s._op(o, LtE)
    __gt__ = lambda s, o: s._op(o, Gt)
    __ge__ = lambda s, o: s._op(o, GtE)
