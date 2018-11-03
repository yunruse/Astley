'''Base Node (= AST) class which all nodes inherit from.'''

import _ast as ast

from . import nodes

__all__ = 'Node parse PyCF_ONLY_AST'.split()

PyCF_ONLY_AST = 1024

def parse(source, filename='<unknown>', mode='exec'):
    return modify(compile(source, filename, mode, PyCF_ONLY_AST))

def modify(node):
    cls = node.__class__
    newcls = getattr(nodes, cls.__name__, None)
    
    if issubclass(cls, ast.AST) and newcls:
        new = newcls()
        Node.__init__(new, node)
        return new
    else:
        return node

DFIELDS = ('lineno', 'col_offset')

class Node:
    defaults = dict()
    sym = '<{self.__class__.__name__}>'
    
    def __init__(self, *args, **kw):
        if not args or kw:
            return
        if len(args) == 1 and isinstance(args[0], ast.AST):
            node = args[0]
            for n in DFIELDS + getattr(node, '_fields', ()):
                if hasattr(node, n):
                    v = modify(getattr(node, n))
                    if isinstance(v, list):
                        v = list(map(modify, v))
                    setattr(self, n, v)
        
        else:
            kwargs = dict()
            kwargs.update(self.defaults)
            if args and len(args) <= len(self._fields):
                for i, val in enumerate(args):
                    name = self._fields[i]
                    kwargs[name] = val
            
            kwargs.update(kw)

            for name, val in kwargs.items():
                setattr(self, name, val)
    
    def _repr(self, noLimit=True):
        attributes = []
        for i in self._fields + self._attributes:
            v = getattr(self, i, None)
            if v is None:
                continue
            elif isinstance(v, Node):
                if noLimit:
                    v = v._repr(True)
                else:
                    v = '{.__class__.__name__}(...)'.format(v)
            elif isinstance(v, list):
                v = '[{}]'.format(', '.join(
                    i._repr(True) if isinstance(i, Node) else repr(i) for i in v))
            else:
                v = repr(v)
            attributes.append('{}={}'.format(i, v))
        
        return '{}({})'.format(
            self.__class__.__name__, ', '.join(attributes))

    def __repr__(self):
        return self._repr(False)

    def __str__(self, indent=1):
        return self.sym.format(self=self)

    def compile(self, filename=None):
        '''Return compiled code version of node.'''
        raise TypeError('Node is not a code segment.')

    def eval(self, globa=None, loca=None):
        '''Evaluate node given globals and locals.'''
        return eval(
            self.compile(),
            globa or globals(), loca or dict())

    def exec(self, globa=None, loca=None):
        '''Execute node given globals and locals.'''
        exec(self.compile(), globa or globals(), loca or dict())
