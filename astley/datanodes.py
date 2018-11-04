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
    vars = 'name asname'.split()
    def asPython(self):
        name, alias = (getattr(self, i, None) for i in self.vars)
        if alias:
            return '{} as {}'.format(name, alias)
        else:
            return str(name)
    defaults = {'asname': None}

class withitem(ast.alias):
    '''Aliases in With block'''
    vars = 'context_expr optional_vars'.split()
    defaults = {'optional_vars': None}

class FormattedValue(ast.FormattedValue, datanode):
    '''String and formatting used in f-string'''
    def asPython(self):
        n = str(self.value)
        if self.format_spec:
            n += ':' + str(self.format_spec.asRaw())
        return '{'+n+'}'

class comprehension(ast.comprehension, datanode):
    '''Iterator and targets in comprehenson expressions'''
    def asPython(self):
        name = 'for {} in {}'
        if self.is_async:
            name = 'async ' + name
        return name.format(self.target, self.iter)

class slice(datanode):
    pass

class Index(ast.Index, slice):
    sym = '{self.value}'

class Slice(ast.Slice, slice):
    def asPython(self):
        lower = str(self.lower) if self.lower else ''
        upper = str(self.upper) if self.upper else ''
        if self.step:
            return '{}:{}:{}'.format(lower, upper, self.step)
        else:
            return '{}:{}'.format(lower, upper)