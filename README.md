# Astley

Astley is a module designed for manipulating Python's Abstract Syntax tree. It features:

* An extended node syntax, allowing for nodes to be created via (mostly) native syntax;
* `match`, `Rule` and `Ruleset` objects for easier transformation of nodes;
* The ability to print out nodes as Python code - useful for transpilation.

Currently, Astley is still in early stages of development, so it promises no stability other than that its unit tests should *probably* pass. 

## Usage

Create code with native syntax, fast:

```python

>>> from astley import parse, f, x, y
>>> code = 'f(x**2 + y, end="!")'
>>> node1 = parse(code, mode='eval')
>>> node2 = f(x**2 + y, end="!")
>>> print(node1.as_python(), node2.as_python())
f(x ** 2 + y, end='!') f(x ** 2 + y, end='!')
>>> node2.eval(f=print, x=10, y=4)
104!
```

## Legal

Copyright (c) Mia Dobson ([yunruse](yunruse)) 2018-2020.

This work is licensed under a Creative Commons Attribution 4.0 International
license. In non-legal terms: do whatever you like, but credit me.
The full license is available here:
https://creativecommons.org/licenses/by/4.0/

[yunruse]: https://yunru.se/
