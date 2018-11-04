from .nodes import *
from .signature import reprSignature

class Starred(ast.Starred, datanode):
    sym = '*{self.value}'

class keyword(ast.keyword, datanode):
    '''Keyword in Call'''
    def asPython(self):
        arg = getattr(self, 'arg', None)
        if arg:
            return '{}={}'.format(arg, self.value)
        else:
            return '**{}'.format(self.value)

class arg(ast.arg, datanode):
    '''Definition with annotation in arguments'''
    sym = '{self.arg}'

class arguments(ast.arguments, datanode):
    '''Function signature in Lambda, FunctionDef'''
    _fields = tuple('args defaults vararg kwonlyargs kw_defaults kwarg'.split())
    def asPython(self):
        argDefaults = getattr(self, 'defaults', [])
        kwDefaults = getattr(self, 'kw_defaults', [])
        argRest = getattr(self, 'vararg', None)
        kwRest = getattr(self, 'kwarg', None)
        get = lambda col: [(a.arg, getattr(a, 'annotation', None)) for a in col]
        return reprSignature(
            get(self.args), argDefaults, argRest,
            get(self.kwonlyargs), kwDefaults, kwRest)

class alias(ast.alias, datanode):
    '''used in import, extended with withitem'''
    defaults = {'asname': None}
    vars = 'name asname'.split()
    def asPython(self):
        name, alias = (getattr(self, i, None) for i in self.vars)
        name = name.asPython()
        if alias:
            return name + ' as ' + alias.asPython()
        else:
            return name

class withitem(ast.alias):
    '''Aliases in With block'''
    defaults = {'optional_vars': None}
    vars = 'context_expr optional_vars'.split()

class FormattedValue(ast.FormattedValue, datanode):
    '''String and formatting used in f-string'''
    def asPython(self):
        n = self.value.asPython()
        if self.format_spec:
            n += ':' + str(self.format_spec.asRaw())
        return '{'+n+'}'

class comprehension(ast.comprehension, datanode):
    '''Iterator and targets in comprehenson expressions'''
    sym = '{self.async_}for {self.target} in {self.iter}'
    async_ = property(lambda s: 'async ' * s.is_async)

class slice(datanode):
    pass

class Index(ast.Index, slice):
    sym = '{self.value}'

class Slice(ast.Slice, slice):
    def asPython(self):
        lo = self.lower.asPython() if self.lower else ''
        hi = self.upper.asPython() if self.upper else ''
        if self.step:
            return '{}:{}:{}'.format(
                lo, hi, self.step.asPython())
        else:
            return '{}:{}'.format(lo, hi)