"""Modified stateful NodeTransformer with QOL functions."""

from ast import NodeTransformer
from _ast import AST
from types import CodeType
from io import TextIOBase
from functools import wraps

from .node import Node, parse, modify
from .nodes import Expression, expr

__all__ = "match Language Python".split()


def match(cls=None, **kw):
    """Advanced Language matcher that accounts for more conditions.

    Wrap this around a class, then call it around functions:

    @match
    class NewLang(Language):
        @match(kind=Add, mode='eval', bare_node=True)
        @match(kind=AugAssign, op=Add, mode='eval', bare_node=True)
        def Print_Every_Add_I_see(self, node):
            print(node.left, node.right)
    """
    L = "_LanguageMatch"

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
                kinds = kw.pop("kind", object)
                if not isinstance(kinds, (tuple, list)):
                    kinds = (kinds,)
                for k in kinds:
                    if k not in cls.match_conds:
                        cls.match_conds[k] = []
                    cls.match_conds[k].append((kw, func))
        return cls


def parse_try(source, filename):
    try:
        return parse(source, filename, "eval"), "eval"
    except SyntaxError:
        return parse(source, filename, "exec"), "exec"


class Language(NodeTransformer):
    """Abstract syntax tree stateful transformer.

    Instances are stateful, allowing more advanced transformations.

    If you want to take the state of the node and work with it,
    make sure you can guarantee locals and globals are provided!
    eval, exec and compile are provided. Run as:
    >>> state = Language(node_or_source)
    >>> obj = state.eval()
    >>> code = state.compile()
    You can provide the mode, but with a few exceptions Astley can
    automatically determine it from source code or node.
    """

    def _match_cond(self, kw, node):
        """Handles advanced properties of match_cond."""
        if not len(kw):
            return True

        correct_bare = True
        if hasattr(self.node, "body") and "bare_node" in kw:
            correct_bare = (node in self.node.body) == kw.get("bare_node")

        correct_fields = all(
            getattr(node, i) == v or isinstance(getattr(node, i), v)
            for i, v in kw.items()
            if i in node._fields
        )

        conds = (self.mode == kw.get("mode", self.mode), correct_bare, correct_fields)
        return all(conds)

    def visit(self, node):
        """Visit a node."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor:
            return visitor(node)

        matches = self.match_conds.get(type(node), [])
        for kw, func in matches:
            if self._match_cond(kw, node):
                return func(self, node)
        else:
            return self.generic_visit(node)

    match_conds = {}  # {type: [{conditions}, node_func]}

    def __init__(self, node=None, **kw):
        if node is None:
            # maintain `ast` compatibility
            self.mode = "classic"
            return

        if isinstance(node, TextIOBase):
            self.filename = node.name
            node = node.read(-1)
        else:
            self.filename = kw.get("filename", "<{}>".format(self.__class__.__name__))

        self.mode = kw.get("mode")
        if isinstance(node, Node):
            self.node = node
        elif isinstance(node, AST):
            self.node = modify(node)
        elif isinstance(node, str):
            if self.mode is None:
                self.node, self.mode = parse_try(node, self.filename)
            else:
                self.node = parse(node, self.filename, self.mode)
        else:
            raise TypeError("Must be node or source.")

        if self.mode is None:
            self.mode = "eval" if isinstance(self.node, (expr, Expression)) else "exec"

        self.globals = kw.get("globals", globals())
        self.locals = kw.get("locals", dict())

        self.on_visit_start()
        self.visit(self.node)
        self.on_visit_finish()

    # overwritable methods

    def on_visit_start(self):
        pass

    def on_visit_finish(self):
        pass

    def compile(self, flags=0):
        return self.node.compile(self.filename)

    def eval(self):
        return eval(self.compile(), self.globals, self.locals)

    def exec(self):
        return exec(self.compile(), self.globals, self.locals)

    @classmethod
    def compiles(cls, source, filename, mode, flags=0, **kw):
        return cls(source, filename=filename, mode=mode, **kw).compile(flags)

    @classmethod
    def evals(cls, source, globals=None, locals=None, **kw):
        return cls(source, globals=globals, locals=locals, **kw).eval()

    @classmethod
    def execs(cls, source, globals=None, locals=None, **kw):
        cls(source, globals=globals, locals=locals, **kw).exec()


class Python(Language):
    """Base language 'transformer' for code consistency."""

    visit = lambda self, node: None
    evals = eval
    execs = exec
    compiles = compile
