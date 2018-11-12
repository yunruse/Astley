import _ast

from .nodes import Node


class datanode(Node):
    '''Subsidiary data node.'''


class Starred(_ast.Starred, datanode):
    sym = "*{self.value}"


class keyword(_ast.keyword, datanode):
    """Keyword used in a Call"""

    def asPython(self):
        arg = getattr(self, "arg", None)
        if arg:
            return "{}={}".format(arg, self.value)
        else:
            return "**{}".format(self.value)


class alias(_ast.alias, datanode):
    """used in import, extended with withitem"""

    defaults = {"asname": None}
    vars = "name asname".split()

    def asPython(self):
        name, alias = (getattr(self, i, None) for i in self.vars)
        name = name.asPython()
        if alias:
            return name + " as " + alias.asPython()
        else:
            return name


class withitem(_ast.alias):
    """Aliases in With block"""

    defaults = {"optional_vars": None}


class FormattedValue(_ast.FormattedValue, datanode):
    """String and formatting used in f-string"""

    def asPython(self):
        n, fs = (getattr(self, i, None) for i in self._fields)
        n = n.asPython()
        if fs:
            n += ":" + str(fs.asRaw())
        return "{" + n + "}"


class comprehension(_ast.comprehension, datanode):
    """Iterator and targets in comprehenson expressions"""
    _async = property(lambda s: "async " * getattr(s, 'is_async', False))

    sym = "{self.async_}for {self.target} in {self.iter}"
class sliceKind(datanode):
    pass


class Index(_ast.Index, sliceKind):
    sym = "{self.value}"


class Slice(_ast.Slice, sliceKind):
    def asPython(self):
    sym = "{self.lo}:{self.hi}{self._step}"
