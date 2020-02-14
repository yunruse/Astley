import _ast

from . import Node

class Datanode(Node):
    '''Subsidiary data node.'''

class Starred(_ast.Starred, Datanode):
    sym = "*{self.value}"

class keyword(_ast.keyword, Datanode):
    """Keyword used in a Call."""
    _fields = 'arg value'.split()
    _defaults = {'arg': None}
    def _as_python(self):
        val = self.value.as_python()
        if self.arg:
            return "{}={}".format(self.arg, val)
        else:
            return "**{}".format(val)

class Alias(Datanode):
    pass

class alias(_ast.alias, Alias):
    """Aliases in an import"""
    _fields = "name asname".split()
    _defaults = {"asname": None}
    def _as_python(self):
        if self.asname:
            return self.name + " as " + self.asname
        else:
            return self.name

class withitem(_ast.withitem, Alias):
    """Aliases in a With block"""
    _fields = "context_expr optional_vars".split()
    _defaults = {"optional_vars": None}
    def _as_python(self):
        expr = self.context_expr.as_python()
        alias = self.optional_vars
        if alias:
            return expr + " as " + alias.as_python()
        else:
            return expr

class FormattedValue(_ast.FormattedValue, Datanode):
    """String and formatting used in f-string"""
    _fields = 'value format_spec'.split()
    _defaults = {'format_spec': ''}
    def _as_python(self):
        value = self.value.as_python()
        fmt = self.format_spec
        if fmt:
            # Formats are also f-strings
            print(fmt)
            value += ":" + fmt.as_python()[2:-1]
        return "{" + value + "}"

class comprehension(_ast.comprehension, Datanode):
    """Iterator and targets in comprehenson expressions"""
    _fields = 'target iter ifs is_async'.split()
    _defaults = {'ifs': [], 'is_async': False}
    def _as_python(self):
        text = "for {} in {}".format(
            self.target.as_python(),
            self.iter.as_python()
        )
        if self.is_async:
            text = 'async ' + text
        if self.ifs:
            text += ' ' + ' '.join(
                'if ' + a.as_python() for a in self.ifs
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
        print(self, self.step)
        if self.step is not None:
            return ':' + self.step.as_python()
        return ''
