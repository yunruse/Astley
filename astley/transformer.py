'''Modified stateful NodeTransformer with QOL functions.'''

from ast import NodeTransformer
from _ast import AST
from types import CodeType
from io import TextIOBase
from functools import wraps

from .node import parse, Node, modify
from .nodes import Expression, expr

__all__ = 'match Language Python'.split()

def match(cls=None, **kw):
    '''Advanced Language matcher that accounts for more conditions.
    
    Wrap this around a class, then call it around functions:
    
    @match
    class NewLang(Language):
        @match(kind=BinOp, op=Add, mode='eval', bareNode=True)
        @match(kind=AugAssign, op=Add, mode='eval', bareNode=True)
        def PrintAddition(self, node):
            print(node.left, node.right)
    '''
    L = '_LanguageMatch'
    
    # Runtime shenanigans mean we must assign properties
    # to the method, then iterate over them. Fun!
    if not isinstance(cls, type):
        # given keywords, so return wrapper that binds then.
        # this is pretty eldritch so I'd steer clear
        def new(func):
            if not hasattr(func, L):
                setattr(func, L, [])
            getattr(func, L).append(kw)
            return func
        return new
    else:
        for k, func in cls.__dict__.items():
            for kw in getattr(func, L, []):
                kinds = kw.pop('kind', object)
                if not isinstance(kinds, (tuple, list)):
                    kinds = (kinds, )
                for k in kinds:
                    if k not in cls.matchCond:
                        cls.matchCond[k] = []
                    cls.matchCond[k].append(
                        (kw, func))
        return cls

def parseTry(source, filename):
    try:
        return parse(source, filename, 'eval'), 'eval'
    except SyntaxError:
        return parse(source, filename, 'exec'), 'exec'

class Language(NodeTransformer):
    '''Abstract syntax tree stateful transformer.
    
    Instances are stateful, allowing more advanced t
    
    If you want to take the state of the node and work with it,
    make sure you know if the language modifies locals and globals!
    eval, exec and compile are provided to cover these bases.
    
    Run as:
    >>> state = Language(node_or_source)
    >>> obj = state.eval()
    >>> code = state.compile()
    You can provide the mode, but with a few exceptions Astley can
    automatically determine it from source code or node.
    '''

    def _matchCond(self, kw, node):
        '''Handles advanced properties of matchCond.'''
        if not len(kw):
            return True
        
        correctBare = True
        if hasattr(self.node, 'body') and 'bareNode' in kw:
            correctBare = (
                node in self.node.body) == kw.get('bareNode')
        
        correctFields = all(
            getattr(node, i) == v
            or isinstance(getattr(node, i), v)
            for i, v in kw.items() if i in node._fields)
        
        conds = (
            self.mode == kw.get('mode', self.mode),
            correctBare, correctFields,
        )
        return all(conds)

    def visit(self, node):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor:
            return visitor(node)
        
        possibleMatches = self.matchCond.get(type(node), [])
        for kw, func in possibleMatches:
            if self._matchCond(kw, node):
                return func(self, node)
        else:
            return self.generic_visit(node)
    
    matchCond = {} # {type: [{conditions}, nodeFunc]}
    
    def __init__(self, node=None, **kw):
        
        if node is None:
            # maintain `ast` compatibility
            self.mode = 'classic'
            return
        
        if isinstance(node, TextIOBase):
            self.filename = node.name
            node = node.read(-1)
        else:
            self.filename = kw.get('filename', '<{}>'.format(
                self.__class__.__name__))
        
        self.mode = kw.get('mode')
        if isinstance(node, Node):
            self.node = node
        elif isinstance(node, AST):
            self.node = modify(node)
        elif isinstance(node, str):
            if self.mode is None:
                self.node, self.mode = parseTry(node, self.filename)
            else:
                self.node = parse(node, self.filename, self.mode)
        else:
            raise TypeError('Must be node or source.')
        
        if self.mode is None:
            isExpr = isinstance(self.node, (expr, Expression))
            self.mode = 'eval' if isExpr else 'exec'
        
        self.globals = kw.get('globals', globals())
        self.locals = kw.get('locals', dict())
        
        self.onVisitStart()
        self.visit(self.node)
        self.onVisitFinish()
    
    # overwritable methods
    
    def onVisitStart(self):
        pass
    
    def onVisitFinish(self):
        pass
    
    def compile(self, flags=0):
        return self.node.compile(self.filename)
    
    def eval(self):
        return eval(self.compile(), self.globals, self.locals)
    
    def exec(self):
        return exec(self.compile(), self.globals, self.locals)
    
    @classmethod
    def staticCompile(cls, source, filename, mode, flags=0, **kw):
        return cls(
            source, filename=filename, mode=mode, **kw).compile(flags)
    
    @classmethod
    def staticEval(cls, source, globals=None, locals=None, **kw):
        return cls(source, globals=globals, locals=locals, **kw).eval()
    
    @classmethod
    def staticExec(cls, source, **kw):
        cls(source, globals=globals, locals=locals, **kw).exec()

class Python(Language):
    '''Base language 'transformer' for code consistency.'''
    visit = lambda self, node: None    
    staticEval = eval
    staticExec = exec
    staticCompile = compile

