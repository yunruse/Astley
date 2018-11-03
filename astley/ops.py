'''Operators used by various OpAppliers.'''

from .nodes import ast, kind

__all__ = (
    'Op', 'boolop', 'cmpop', 'operator', 'unaryop',
    'operators', 'precedence', 'symbols'
)

class Op(kind):
    '''Operator that is applied with an OpApplier.'''

class boolop(ast.boolop, Op): pass
class cmpop(ast.cmpop, Op): pass
class operator(ast.operator, Op): pass
class unaryop(ast.unaryop, Op): pass

operators = dict(
    boolop=(
        ('Or', 'or', 'or_', 1),
        ('And', 'and', 'and_', 2),
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
        ('In', 'in', 'in_'),
        ('NotIn', 'not in', 'notin_'),
        ('Is', 'is', 'is_'),
        ('IsNot', 'is not', 'isnot_'),
        ('Lt', '<', '__lt__'),
        ('LtE', '<=', '__le__'),
        ('Gt', '>', '__gt__'),
        ('GtE', '>=', '__ge__'),
        ('NotEq', '!=', '__ne__'),
        ('Eq', '==', '__eq__'),
    ),
    unaryop=(
        ('Not', 'not ', 'not_'),
        ('Invert', '~', '__invert__'),
        ('UAdd', '+', '__pos__'),
        ('USub', '-', '__neg__'),
    )
)

precedence = {}
symbols = []

for kind, ops in operators.items():
    for name, sym, func, *prec in ops:
        __all__ += (name ,)
        symbols.append(sym.strip())
        if prec:
            precedence[name] = prec[0]
        
        exec('class {0}(ast.{0}, {2}): sym = "{1}"'.format(
            name, sym, kind), globals())
