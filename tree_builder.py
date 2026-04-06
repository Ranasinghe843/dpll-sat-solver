class TreeNode:
    def __init__(self, level=0, assignment=None, decision_var=None, decision_value=None):
        self.level = level
        self.assignment = assignment if assignment is not None else {}
        self.decision_var = decision_var
        self.decision_value = decision_value
        self.left = None
        self.right = None


def get_variables_from_clauses(clauses):
    variables = set()

    for clause in clauses:
        for literal in clause:
            variables.add(abs(literal))

    return sorted(list(variables))


def build_decision_tree(variables, level=0, assignment=None, decision_var=None, decision_value=None):
    if assignment is None:
        assignment = {}

    node = TreeNode(level, assignment.copy(), decision_var, decision_value)

    if level == len(variables):
        return node

    current_var = variables[level]

    left_assignment = assignment.copy()
    left_assignment[current_var] = True
    node.left = build_decision_tree(
        variables,
        level + 1,
        left_assignment,
        current_var,
        True
    )

    right_assignment = assignment.copy()
    right_assignment[current_var] = False
    node.right = build_decision_tree(
        variables,
        level + 1,
        right_assignment,
        current_var,
        False
    )

    return node


def create_tree_from_cnf(num_vars, clauses):
    variables = get_variables_from_clauses(clauses)
    root = build_decision_tree(variables)
    return root

# testing
def test_tree_builder():
    from dimacs_parser import parse_dimacs

    # choose which file to test
    filename = "test_sat_1.cnf"

    print(f"\nTesting tree builder with file: {filename}")

    # parse input
    num_vars, clauses = parse_dimacs(filename)

    print("Variables:", num_vars)
    print("Clauses:", clauses)

    # build tree
    root = create_tree_from_cnf(num_vars, clauses)

    print("\nTree built successfully!\n")

    # print first few nodes (limited to avoid huge output)
    def print_limited(node, depth=0, max_depth=3):
        if node is None or depth > max_depth:
            return

        print("  " * depth +
              f"Level={node.level}, "
              f"Var={node.decision_var}, "
              f"Val={node.decision_value}, "
              f"Assign={node.assignment}")

        print_limited(node.left, depth + 1, max_depth)
        print_limited(node.right, depth + 1, max_depth)

    print("Tree (partial view):")
    print_limited(root)

if __name__ == "__main__":
     test_tree_builder()