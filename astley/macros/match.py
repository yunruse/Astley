
from ..node import Node

from astley import NodeTransformer, iter_child_nodes

__all__ = 'match Rule Ruleset Transformation'.split()

class match:
    '''Matching condition(s) for a node.'''
    __slots__ = ('conditions', 'field_conditions', 'node_kind', 'all_condition')

    def is_kind_only(self):
        return not (self.conditions or self.field_conditions)

    def __init__(self, *conditions, all_condition=True, **field_conditions):
        kw = self.field_conditions = field_conditions
        self.conditions = []
        self.all_condition = all_condition

        # Propagate node_kind to ensure matches all agree

        kind = kw.pop('kind', None)
        for i in conditions:
            if isinstance(i, match):
                other_kind = i.node_kind
                if other_kind is not None:
                    if kind is not None:
                        if all_condition and kind != other_kind:
                            raise TypeError('Cannot match to multiple node types!')
                    else:
                        kind = other_kind

                if i.is_kind_only():
                    continue

            self.conditions.append(i)

        self.node_kind = kind

    def __repr__(self, args=None):
        # Represent raw | or & a little nicer
        if self.conditions and not (args or self.field_conditions):
            if all(isinstance(f, match) for f in self.conditions):
                joiner = ' & ' if self.all_condition else ' | '
                return joiner.join(map(repr, self.conditions))

        args = args or []
        args += self.conditions
        if self.node_kind:
            args.append('kind={!r}'.format(self.node_kind))
        if not self.all_condition:
            args.append('all_condition=False')

        return '{}({})'.format(type(self).__name__,
            ', '.join(
                list(map(str, args))
                + ['{}={}'.format(k, v) for k, v in self.field_conditions.items()]
        ))

    def _field_match(self, node, k, v_request):
        if hasattr(node, k):
            v_node = getattr(node, k)
        else:
            return False

        if isinstance(v_request, (list, tuple)):
            return v_node in v_request
        elif isinstance(v_request, match) or callable(v_request):
            return v_request(v_node)
        else:
            return v_node == v_request

    def matches(self, node):
        if self.node_kind is not None and not isinstance(node, self.node_kind):
            return False

        match_mode = all if self.all_condition else any

        if self.conditions:
            node_matches = [f(node) for f in self.conditions]
            if not match_mode(node_matches):
                return False

        if self.field_conditions:
            field_matches = [
                self._field_match(node, k, v)
                for k, v in self.field_conditions.items()
            ]
            if not match_mode(field_matches):
                return False

        return True

    def transform(self, node):
        return node

    def __call__(self, node_or_func):
        if isinstance(node_or_func, Node):
            return self.matches(node_or_func)
        elif callable(node_or_func):
            return Rule(node_or_func, self)

    def __and__(self, other):
        return match(self, other, all_condition=True)

    def __or__(self, other):
        return match(self, other, all_condition=False)

class Rule(match):
    '''A single node rule which only applies if matched.'''
    __slots__ = match.__slots__ + ('transform', )

    def __init__(self, transform, *conditions, **field_conditions):
        match.__init__(self, *conditions, **field_conditions)
        self.transform = transform

    def __repr__(self):
        return match.__repr__(self, [self.transform])

    def __call__(self, node):
        if self.matches(node):
            return self.transform(node)
        else:
            return node

class Ruleset(match, NodeTransformer):
    '''Non-stateful set of rules which may transform a node directly.'''
    __slots__ = ('rules', )

    def __init__(self):
        self.rules = {}
        for name, rule in type(self).__dict__.items():
            if not isinstance(rule, Rule):
                continue
            kind = rule.node_kind or 'generic'
            if kind not in self.rules:
                self.rules[kind] = [(name, rule)]
            else:
                self.rules[kind].append((name, rule))

    def rules_for(self, node):
        return self.rules.get(type(node), []) + self.rules.get('generic', [])

    def matches(self, node):
        return any(rule.matches(node) for name, rule in self.rules_for(node))

    def _transform_round(self, node):
        rules_for = self.rules_for(node)
        if len(rules_for):
            print(f"-- Round for {type(node).__name__} `{node.as_python()}`:")
        for name, rule in rules_for:
            if rule.matches(node):
                print('Matched', name)
                return rule.transform(node)
        else:
            return None

    def transform(self, node):
        '''Non-recursively visit a node'''
        while True:
            result = self._transform_round(node)
            if result is not None:
                node = result
            else:
                return node

    def visit(self, node):
        node = self.transform(node)
        return self.generic_visit(node)

    # Being technically a match object, we include these properties for compatability
    # and analysis. A Ruleset may be treated as a Rule for all purposes, allowing
    # Rulesets to be nested.

    all_condition = False
    field_conditions = []
    node_kind = None

    @property
    def conditions(self):
        return self.rules

class Transformation(Ruleset):
    '''A stateful ruleset using an instance for each transformation.'''
