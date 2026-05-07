import subprocess
import sys
import re

def parse_cnf_clauses(filepath):
    """Parses the CNF file to get just the list of clauses for verification."""
    clauses = []
    current_clause = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c') or line.startswith('p') or line.startswith('%'):
                continue
            nums = list(map(int, line.split()))
            for n in nums:
                if n == 0:
                    if current_clause:
                        clauses.append(set(current_clause))
                        current_clause = []
                else:
                    current_clause.append(n)
    return clauses

def verify(clauses, assignment):
    """
    Checks if the assignment satisfies every clause.
    An assignment is a set of literals (e.g., {1, -2, 3}).
    """
    assignment_set = set(assignment)
    for i, clause in enumerate(clauses):
        # A clause is satisfied if at least one of its literals is in the assignment
        if not any(literal in assignment_set for literal in clause):
            print(f"FAILED: Clause {i+1} ({clause}) is not satisfied!")
            return False
    return True

def run_pipeline(cnf_file):
    print(f"--- Processing: {cnf_file} ---")
    
    # 1. Run the solver
    # Change 'python' to 'python3' if necessary
    try:
        result = subprocess.run(
            ['python', 'dimacs_dpll.py', cnf_file], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
    except subprocess.TimeoutExpired:
        print("ERROR: Solver timed out.")
        return

    output = result.stdout
    print("Solver Output:")
    print(output)

    # 2. Parse the output
    if "SATISFIABLE" in output:
        # Extract numbers from the 'Assignment' or 'Model' line
        # This regex looks for integers in the output string
        match = re.search(r"Assignment: \[(.*?)\]", output)
        if not match:
            # Fallback for different output formats
            match = re.search(r"v (.*?) 0", output)
            
        if match:
            # Convert string list "[1, -2, 3]" to actual integers [1, -2, 3]
            model_str = match.group(1).replace(',', '')
            model = [int(x) for x in model_str.split()]
            
            # 3. Verify
            print("Verifying model...")
            clauses = parse_cnf_clauses(cnf_file)
            if verify(clauses, model):
                print("SUCCESS: Model is valid and satisfies all clauses.")
            else:
                print("CRITICAL: Solver returned an invalid model!")
        else:
            print("ERROR: Could not parse model from solver output.")
    
    elif "UNSATISFIABLE" in output:
        print("Result is UNSAT. (Manual verification of UNSAT is significantly harder).")
    else:
        print("ERROR: Solver did not return a clear SAT/UNSAT result.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <path_to_cnf>")
    else:
        run_pipeline(sys.argv[1])