import string
import functools
import operator

from .ops import symbols

class String(str):
    def __repr__(self):
        return '"' + self.replace('"', '\"') + '"'

class Atom(str):
    def __repr__(s):
        return s

class Symbol(Atom):
    first = string.ascii_letters
    chars = first + string.digits

    @classmethod
    def matches(cls, expr):
        return (
            expr[0] in cls.first and
            set(expr).issubset(cls.chars))

class Quote(Symbol):
    def __repr__(s):
        return "'" + s

def parse_atom(e):
    f, *r = e
    
    if f == "'" and Symbol.matches(r):
        return Quote(r)

    if Symbol.matches(e) or e in symbols:
        return Symbol(e)

    for clas in (int, float):
        try:
            return clas(e)
        except ValueError:
            continue

    if len(e) > 2 and f == s[-1] and f in "\"'":
        return e[1:-1]

    raise ValueError('Could not understand atom {!r}.'.format(e))

def parse_lisp(source):
    terms = [[Symbol('body')]]
    stringDelim = None
    escapeChar = False
    atom = ''
    lastchar = ''
    for i, c in enumerate(source):
        if stringDelim:
            atom += c
            if source[i-1] != '\\' and c == stringDelim:
                terms[-1].append(String(eval(atom)))
                stringDelim = None
                atom = ''
        else:
            if c in '"':
                stringDelim = c
            elif c == '(' and not atom:
                terms.append([])
            
            if c in ('() \n\t'):
                # atom has ended
                if atom:
                    terms[-1].append(parse_atom(atom))
                    atom = ''
                if c == ')':
                    expr = terms.pop(-1)
                    if len(expr) == 1:
                        expr = expr[0]
                    terms[-1].append(Sexpr(expr))
            else:
                 atom += c
    
    if len(terms) != 1:
        raise ValueError('Invalid bracket matching')
    
    return Sexpr(terms[0])

from . import node, nodes
nodemap = {}
for cls in nodes.__dict__.values():
    if issubclass(cls, node.Node) and hasattr(cls, 'lispsym'):
        nodemap[cls.lispsym] = cls

class Sexpr(tuple):
    def __repr__(s):
        return '({})'.format(' '.join(map(repr, s)))
    
    def __new__(cls, obj):
        if isinstance(obj, str):
            return parse_lisp(obj)
        else:
            return tuple.__new__(cls, obj)

def escape(string):
    return string
