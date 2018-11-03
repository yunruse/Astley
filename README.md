# Astley

Astley is an enhancement to Python's `ast` module, keeping full compatability. It currently offers:

* Extended nodes, allowing for easy code creation with familiar syntax;
* `Language`, an extended version of `NodeTransformer`.

Currently, Astley is still in development, so it promises no compatability to versions other than Python 3.7. Please submit any bugs with 3.7 on the tracker.

## Usage

```python

import astley as ast
code = 'f(x**2 + y, end="!")'
node1 = ast.parse(code, mode='eval')
print(node1) # f(x ** 2 + y, end='!')
f, x, y = map(ast.Name, 'fxy')
node2 = f(x**2 + y, end="!")
print(node2) # f(x ** 2 + y, end='!')

f, x, y = print, 10, 4
node1.eval(locals()) # 116!
node2 = ast.copyfix(node1, node2)
node2.eval(locals()) # 116!
```

## Legal

Copyright (c) Jack Dobson (yunru.se) 2018.

This work is licensed under a Creative Commons Attribution 4.0 International
license. In non-legal terms: do whatever you like, but credit me.

The full license is available here:
https://creativecommons.org/licenses/by/4.0/

