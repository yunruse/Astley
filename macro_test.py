from astley import *
from astley.macros import match, Ruleset, extended_nodes as e

# Let's match some nodes.
# Conditions can be equals on fields (or `kind`),
# and may include a lambda.

#breakpoint()

is_zero = match(kind=Num, n=0)
is_positive = match(lambda x: x.n > 0, kind=Num)

# You can add matches together either as a condition or with
# the symbols | and &
is_natural = is_positive | is_zero

def all_elements(cond):
    return match(lambda n: all(map(
        cond, getattr(n, 'elts', [])
    )))

all_natural = all_elements(is_natural)

# Call a match on a node, as you'd expect.

def assert_match(match, code, isMatched=True):
    node = parse(code, mode='eval').body
    assert isMatched == match(node)

assert_match(all_natural, '[3, 2, 1, 0]')
assert_match(all_natural, '[3, 2, 1, 0, -1]', False)

# Let's make a few more conditions.

is_binop = match(kind=BinOp)
is_add = match(is_binop, op=match(kind=Add))

assert_match(is_add, '1 + 2')
assert_match(is_add, '1 + 2 + 3')
assert_match(is_add, '1 * 2', False)

zeroOnLeft = match(is_add, left=is_zero)

# Let's make a rule that applies for this condition.
# Our mathematician knows that `a ± 0` is just `a`,
# so let's make something that only changes this.

# If we call a match object with a function, we will get
# a Rule object, which will only apply the function if
# the node matches.

@match(is_add, right=is_zero)
def noZeroRight(node):
    return node.left

# If you're short on time, you can simplify in quite a few ways.

@zeroOnLeft
def noZeroLeft(node):
    return node.right
noZeroLeft = zeroOnLeft(lambda n: n.right)

# Our budding mathematician wants to apply a lot of rules. At the moment,
# they want to match a few basic simplications, that a * 1 = a + 0 = a.

is_one = match(kind=Num, n=1)
is_mul = match(is_binop, op=match(kind=Mult))

class linearSimplification(Ruleset):
    simpleAddL = match(is_add, left=is_zero)(lambda n: n.right)
    simpleAddR = match(is_add, right=is_zero)(lambda n: n.left)
    simpleMulL = match(is_mul, left=is_one)(lambda n: n.right)
    simpleMulR = match(is_mul, right=is_one)(lambda n: n.left)

# Ruleset is similar to NodeTransformer, if you know it.
# You can use either transform(node) to transform a single node,
# or use visit(node) to visit all children nodes.
# There is no guarantee the node will NOT be modified in place, watch out!

ls = linearSimplification
code = 'a + 0+ (b * 1 * c)'
node = parse(code, mode='eval').body
node = ls().visit(node)
assert(node.asPython() == 'a + b * c')

# Our mathematician wants to change some syntax in Python. In particular,
# they're sick of typing `print`, and want to use the fairly benign
# %= operator to mean 'set and print'. Good idea!

# We want to match every module (pretty much a whole file).
# See how we use onStart, onEnd and `self.node` to keep track of things.
# The `node` here is the main node we called the ruleset on,
# not each node that smaller rules match.

@match(kind=Module)
class printModulo:

    def onStart(self):
        self.equated = [] #(target, value)

    @match(kind=AugAssign, op=Mod)
    def accumulate(self, node):
        self.equated.append(node.target.id)

        return Assign([node.target], node.value)

    def onEnd(self):
        for var in self.equated:
            printer = Name('print')(
                 Str(var) + ' = ' + Name(var)
            )
            self.node.body += printer