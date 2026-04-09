import sys

def parse_dimacs(filename):
    clauses = []
    num_vars = 0
    num_clauses_declared = 0
    current_clause = []

    with open(filename, "r") as file:
        for line in file:
            line = line.strip()

            if line == "":
                continue

            if line.startswith("c"): #comment
                continue

            if line.startswith('%'):
                    break

            if line.startswith("p"): #start
                parts = line.split()
                if len(parts) != 4 or parts[1] != "cnf":
                    raise ValueError("Invalid DIMACS header.")
                num_vars = int(parts[2])
                num_clauses_declared = int(parts[3])
                continue

            values = list(map(int, line.split()))

            for value in values:
                if value == 0:
                    clauses.append(current_clause)
                    current_clause = []
                else:
                    current_clause.append(value)

    if current_clause:
        raise ValueError("Last clause was not ended with 0.")

    if num_clauses_declared != 0 and len(clauses) != num_clauses_declared:
        raise ValueError(
            f"Clause count mismatch: expected {num_clauses_declared}, got {len(clauses)}"
        )

    return num_vars, clauses


if __name__ == "__main__":
    filename = sys.argv[1]

    print("\nFile:", filename)
    num_vars, clauses = parse_dimacs(filename)
    print("Variables:", num_vars)
    print("Clauses:", len(clauses))
