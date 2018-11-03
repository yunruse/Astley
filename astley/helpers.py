import ast

fix = ast.fix_missing_locations

# inverted for easier syntax
def copy(old_node, new_node):
    return ast.copy_location(new_node, old_node)
def copyfix(old_node, new_node):
    return fix(copy(old_node, new_node))
