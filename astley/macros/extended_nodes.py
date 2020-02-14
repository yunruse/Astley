from abc import abstractmethod

from ..node import Node
from ..nodes import Add, Mult, UnaryOp, USub
from .match import match

class CustomNode(Node):
    _attributes = ()
    @abstractmethod
    def finalise(self):
        return self

class UInv(CustomNode):
    _fields = 'value'.split()
    def finalise(self):
        return 1 / self.value

is_neg = match(kind=UnaryOp, op=match(kind=USub))
is_inv = match(kind=UInv)

class Chain(CustomNode):
    _fields = 'op operands'.split()
    def _as_python(self):
        text = ''
        ops = sorted(self.operands, key=is_neg | is_inv, reverse=True)
        is_add = isinstance(self.op, Add)
        is_mul = isinstance(self.op, Mult)
        for a in ops:
            if is_add:
                if is_neg(a):
                    a = a.operand
                    if text:
                        text += ' - '
                    else:
                        text = '-'
                elif text:
                    text += ' + '

            elif is_mul:
                if is_inv(a):
                    a = a.value
                    if text:
                        text += ' / '
                    else:
                        text = '1 / '
                elif text:
                    text += ' * '

            text += a.as_python()
        return text.strip()
