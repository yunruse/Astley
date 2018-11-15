import _ast

from . import Node

class Datanode(Node):
    '''Subsidiary data node.'''

class Starred(_ast.Starred, Datanode):
    sym = "*{self.value}"

class keyword(_ast.keyword, Datanode):
    """Keyword used in a Call."""
    def asPython(self):
        arg = getattr(self, "arg", None)
        val = self.value.asPython()
        if arg:
            return "{}={}".format(arg, val)
        else:
            return "**{}".format(val)

class Alias(Datanode):
    def asPython(self):
        name, alias = (getattr(self, i, None) for i in self._fields)
        if alias:
            return "{} as {}".format(name, alias)
        else:
            return str(name)

class alias(_ast.alias, Alias):
    """Aliases in an import"""
    _fields = "name asname".split()
    defaults = {"asname": None}

class withitem(_ast.withitem, Alias):
    """Aliases in a With block"""
    _fields = "context_expr optional_vars".split()
    defaults = {"optional_vars": None}

class FormattedValue(_ast.FormattedValue, Datanode):
    """String and formatting used in f-string"""
    _fields = 'value format_spec'.split()
    def asPython(self):
        n, fs = (getattr(self, i, None) for i in self._fields)
        n = n.asPython()
        if fs:
            n += ":" + str(fs.asRaw())
        return "{" + n + "}"

class comprehension(_ast.comprehension, Datanode):
    """Iterator and targets in comprehenson expressions"""
    sym = "{self._async}for {self.target} in {self.iter}"
    _async = property(lambda s: "async " * getattr(s, 'is_async', False))

class SliceKind(Datanode):
    pass

class Index(_ast.Index, SliceKind):
    sym = "{self.value}"

class Slice(_ast.Slice, SliceKind):
    sym = "{self.lo}:{self.hi}{self._step}"
    _step = property(lambda s: ":" + s.step if hasattr(s, 'step') else '')
