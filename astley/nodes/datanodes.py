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
    pass

class alias(_ast.alias, Alias):
    """Aliases in an import"""
    _fields = "name asname".split()
    _defaults = {"asname": None}
    def asPython(self):
        alias = getattr(self, 'asname', '')
        if alias:
            return self.name + " as " + alias
        else:
            return self.name

class withitem(_ast.withitem, Alias):
    """Aliases in a With block"""
    _fields = "context_expr optional_vars".split()
    _defaults = {"optional_vars": None}
    def asPython(self):
        expr = self.context_expr.asPython()
        alias = getattr(self, 'optional_vars', None)
        if alias:
            return expr + " as " + alias.asPython()
        else:
            return expr

class FormattedValue(_ast.FormattedValue, Datanode):
    """String and formatting used in f-string"""
    _fields = 'value format_spec'.split()
    _defaults = {'format_spec': ''}
    def asPython(self):
        n, fs = (getattr(self, i, None) for i in self._fields)
        n = n.asPython()
        if fs:
            n += ":" + str(fs.asRaw())
        return "{" + n + "}"

class comprehension(_ast.comprehension, Datanode):
    """Iterator and targets in comprehenson expressions"""
    _fields = 'target iter ifs is_async'.split()
    _defaults = {'ifs': [], 'is_async': False}
    def asPython(self):
        text = "for {} in {}".format(
            self.target.asPython(),
            self.iter.asPython()
        )
        if getattr(self, 'is_async', False):
            text = 'async ' + text
        ifs = getattr(self, 'ifs', [])
        if ifs:
            text += ' ' + ' '.join(
                'if ' + a.asPython() for a in ifs
            )
        return text

class SliceKind(Datanode):
    pass

class Index(_ast.Index, SliceKind):
    sym = "{self.value}"

class Slice(_ast.Slice, SliceKind):
    sym = "{self.lower}:{self.upper}{self._step}"
    @property
    def _step(self):
        s = getattr(self, 'step', None)
        if s:
            return ':' + s.asPython()
        return ''
