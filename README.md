# Astley

Astley is a module designed for manipulating Python's Abstract Syntax tree. It features:

* An extended node syntax, allowing for nodes to be created via (mostly) native syntax;
* `match`, `Rule` and `Ruleset` objects for easier transformation of nodes;
* The ability to print out nodes as Python code - useful for transpilation.

Currently, Astley is still in early stages of development, so it promises no stability other than that its unit tests should *probably* pass. 

## Usage

```python

>>> import astley as ast
>>> code = 'f(x**2 + y, end="!")'
>>> node1 = astley.parse(code, mode='eval')
>>> f, x, y = map(astley.Name, 'fxy')
>>> node2 = f(x**2 + y, end="!")
>>> print(node1.asPython(), node2.asPython())
f(x ** 2 + y, end='!') f(x ** 2 + y, end='!')

>>> f, x, y = print, 10, 4
>>> node2.eval(locals())
104!
```

## Legal

Copyright (c) Mia Dobson ([yunruse]) 2019.

This work is licensed under a Creative Commons Attribution 4.0 International
license. In non-legal terms: do whatever you like, but credit me.
The full license is available here:
https://creativecommons.org/licenses/by/4.0/

[yunruse]: https://yunru.se/
