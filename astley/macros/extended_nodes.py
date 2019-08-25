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
    def _asPython(self):
        text = ''
        ops = sorted(self.operands, key=is_neg | is_inv, reverse=True)
        isAdd = isinstance(self.op, Add)
        isMul = isinstance(self.op, Mult)
        for a in ops:
            if isAdd:
                if is_neg(a):
                    a = a.operand
                    if text:
                        text += ' - '
                    else:
                        text = '-'
                elif text:
                    text += ' + '

            elif isMul:
                if is_inv(a):
                    a = a.value
                    if text:
                        text += ' / '
                    else:
                        text = '1 / '
                elif text:
                    text += ' * '

            text += a.asPython()
        return text.strip()