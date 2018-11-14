from os import path, walk, remove
from unittest import TestCase

from astley import parse

def replace(fn):
    return fn.replace(
        path.join('astley', 'astley'),
        path.join('astley', '_test_astley')
    )

FILES = []
for dirpath, dirnames, filenames in walk('../astley/astley'):
    for fn in filenames:
        if fn.endswith('.py'):
            fn = path.abspath(path.join(dirpath, fn))
            fn2 = replace(fn)
            FILES.append((fn, fn2))

class TestFile(TestCase):
    def setUp(self):
        # Delete all files for easier testing
        for fn, fn2 in FILES:
            if path.isfile(fn2):
                remove(fn2)

    def test_files(self):
        for fn, fn2 in FILES:
            print('parsing', fn)
            with open(fn) as f:
                old = f.read(-1)
            expr = parse(old, fn)
            new = expr.asPython()
            with open(fn2, 'w') as f:
                f.write(new)
            expr2 = parse(new, fn2)
            self.assertEqual(expr, expr2)
            self.assertEqual(new, expr2.asPython())
