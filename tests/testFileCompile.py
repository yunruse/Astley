import os
from os import path
from unittest import TestCase

from astley import parse

# pylint: disable=E0211
# E0211: setUpClass() requires no arguments

class TestFile(TestCase):
    def setUpClass():
        for fn2 in REMOVE_ON_START:
            if path.isfile(fn2):
                os.remove(fn2)

    def file_test(self, fn1, fn2):
        with open(fn1) as f:
            source = f.read(-1)
        expr = parse(source, fn1)
        new = expr.asPython()
        with open(fn2, 'w') as f:
            f.write(new)
        expr2 = parse(new, fn2)
        self.assertEqual(expr, expr2)
        self.assertEqual(new, expr2.asPython())

# Discover path names to test
PATH_SRC = path.abspath('../astley')
DIRS = {'astley', 'tests', 'nodes'}
PATH_MOD = path.join(PATH_SRC, '_test')

REMOVE_ON_START = []
for dirpath, dirnames, filenames in os.walk(PATH_SRC, topdown=True):
    dirnames[:] = list(set(dirnames) & DIRS)
    dir_rel = path.relpath(dirpath, PATH_SRC)
    for dn in dirnames:
        dn2 = path.join(PATH_MOD, dir_rel, dn)
        os.makedirs(dn2, exist_ok=True)

    for fn in filenames:
        if not fn.endswith('.py'):
            continue

        fn_rel = path.join(dir_rel, fn)
        fn1 = path.join(PATH_SRC, fn_rel)
        fn2 = path.join(PATH_MOD, fn_rel)
        REMOVE_ON_START.append(fn2)
        test_name = 'test_' + fn_rel.replace(os.sep, '_').replace('.py', '')
        closure_fix = lambda fn1, fn2: lambda s: s.file_test(fn1, fn2)
        setattr(TestFile, test_name, closure_fix(fn1, fn2))
