'''Function arguments and their derivation.'''

import _ast

from .datanodes import Datanode
from . import Node

__all__ = 'arg arguments funcSignature'.split()

class arg(_ast.arg, Datanode):
    """Name and optional annotation."""
    _fields = 'arg annotation'.split()
    _defaults = {'annotation': None}

class arguments(_ast.arguments, Datanode):
    """Function argument signature"""

    _fields = "args defaults vararg kwonlyargs kw_defaults kwarg".split()
    _defaults = dict(
        args=[], defaults=[], vararg=None,
        kwonlyargs=[], kw_defaults=[], kwarg=None
    )

    def asPython(self):
        n_required = len(self.args) - len(self.defaults)
        words = []

        def argify(variables, defaults, isKwargsOnly):
            for n, arg in enumerate(variables):

                defa = None
                if isKwargsOnly:
                    defa = defaults[n]
                elif defaults:
                    # __defaults__ applies to the tail of the variables
                    dindex = n - n_required
                    if dindex >= 0:
                        defa = defaults[dindex]

                if isinstance(defa, Node):
                    defa = defa.asPython()

                word = arg.arg
                ann = arg.annotation

                if ann is not None:
                    word += ': {}'.format(ann.asPython())
                    if defa is not None:
                        word += ' = ' + defa
                else:
                    if defa is not None:
                        word += '=' + defa

                words.append(word)

        argify(self.args, self.defaults, False)

        if self.vararg:
            words.append('*' + self.vararg.arg)
        elif self.kwonlyargs:
            words.append('*')

        argify(self.kwonlyargs, self.kw_defaults, True)

        if self.kwarg:
            words.append('**' + self.kwarg.arg)

        return ', '.join(words)

    @classmethod
    def fromFunction(cls, f):
        '''Extract signature from compiled function.'''
        c = f.__code__
        n = c.co_argcount
        n_k = c.co_kwonlyargcount

        hasKwargs = (c.co_flags & 0b0001000) >> 3
        hasArgs = (c.co_flags & 0b0000100) >> 2

        def args(q):
            return [arg(name, f.__annotations__.get(name, None)) for name in q]

        return cls(
            args = args(c.co_varnames[:n]),
            defaults = f.__defaults__ or tuple(),
            vararg = arg(c.co_varnames[n + 1]) if hasArgs else None,
            kwonlyargs = args(c.co_varnames[n : n+n_k]),
            kw_defaults = f.__kwdefaults__ or tuple(),
            kwarg = arg(c.co_varnames[n + 1 + hasArgs]) if hasKwargs else None
        )

def funcSignature(f):
    return arguments.fromFunction(f).asPython()
