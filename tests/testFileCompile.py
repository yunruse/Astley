from os import path, walk
from unittest import TestCase

from astley import parse

FILES = []
for dirpath, dirnames, filenames in walk('../astley'):
    for f in filenames:
        if f.endswith('.py'):
            FILES.append(path.abspath(path.join(dirpath, f)))

def replace(fn):
    return fn.replace(
        path.join('astley', 'astley'),
        path.join('astley', '_test_astley')
    )

class TestFile(TestCase):
    def test_files(self):
        for fn in FILES:
            print('parsing', fn)
            with open(fn) as f:
                old = f.read(-1)
            expr = parse(old, fn)
            new = expr.asPython()
            fn2 = replace(fn)
            with open(fn2, 'w') as f:
                f.write(new)
            expr2 = parse(new, fn2)
            self.assertEqual(expr, expr2)
            self.assertEqual(new, expr2.asPython())
