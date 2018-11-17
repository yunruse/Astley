import os
from os import path
from sys import version_info
from unittest import TestCase

from astley import parse

class TestFile(TestCase):
    def file_test(self, fn1, fn2):
        with open(fn1, encoding='utf8') as f:
            source = f.read(-1)
        expr1 = parse(source, fn1)
        new = expr1.asPython()
        with open(fn2, 'w', encoding='utf8') as f:
            f.write(new)
        self.assertEqual(source, new)
        expr2 = parse(new, fn2)
        self.assertEqual(expr1, expr2)

# Append each example*.py file to TestCase
TESTS_PATH = path.dirname(__file__)
for name in os.listdir(TESTS_PATH):
    if name.startswith('sample') and name.endswith('.py'):
        major, minor = name[7:-3].split('_')
        if (int(major), int(minor)) > version_info:
            # sample is for newer Python
            continue
        test_name = 'test_sample_{}_{}'.format(major, minor)
        name2 = name.replace('sample_', 'result_')
        fn1 = path.abspath(path.join(TESTS_PATH, name))
        fn2 = path.abspath(path.join(TESTS_PATH, name2))
        closure_fix = lambda *a: lambda s: s.file_test(*a)
        setattr(TestFile, test_name, closure_fix(fn1, fn2))
