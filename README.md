# Astley

Astley is a module designed for manipulating Python's Abstract Syntax tree. It features:

* An extended node syntax, allowing for nodes to be created via (mostly) native syntax;
* The ability to print out nodes as Python code - useful for transpilation.

Astley is more of a toy than anything – there are many ways it could be useful, but that would require a lot more time than I can afford. Still, it's functional, and should hopefully work on most versions of Python 3.

## Usage

Create code with native syntax, fast:

```python

>>> from astley import parse, f, x, y
>>> code = 'f(x**2 + y, end="!")'
>>> node1 = parse(code, mode='eval')
>>> node2 = f(x**2 + y, end="!")
>>> print(node1.as_python(), node2.as_python())
f(x ** 2 + y, end='!') f(x ** 2 + y, end='!')
>>> node1 == node2
True
>>> node2.eval(f=print, x=10, y=4)
104!
```

For the most part all operators 'just work' on any node. For certain operators, however – `.`, `==` and `!=` – there's no easy way to realise this, so instead use `._.`, `._==` and `._!=` instead. 

```python
>>> from astley import x, y
>>> node = x._.y ._== 2
>>> print(node.as_python())
x.y == 2
```

## Legal

Copyright (c) Mia Dobson ([yunruse](yunruse)) 2018-2021.

This work is licensed under a Creative Commons Attribution 4.0 International
license. In non-legal terms: do whatever you like, but credit me.
The full license is available here:
https://creativecommons.org/licenses/by/4.0/

[yunruse]: https://yunru.se/
