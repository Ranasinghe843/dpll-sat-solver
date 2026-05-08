import os
import sys
import subprocess
import re
import time

def parse_cnf_clauses(filepath):
    clauses = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('c', 'p', '%', '0')): continue
            literals = [int(x) for x in line.split() if x != '0']
            if literals:
                clauses.append(set(literals))
    return clauses

def verify_assignment(clauses, assignment_dict):
    for i, clause in enumerate(clauses):
        satisfied = False
        for lit in clause:
            var = abs(lit)
            if var not in assignment_dict: continue
            val = assignment_dict[var]
            if (lit > 0 and val == 1) or (lit < 0 and val == 0):
                satisfied = True
                break
        if not satisfied:
            return False, f"Clause {i+1} ({clause}) failed."
    return True, "Verified."

def run_user_solver(cnf_path):
    try:
        proc = subprocess.run(['python3', 'mySAT.py', cnf_path], 
                              capture_output=True, text=True, timeout=120)
        output = proc.stdout
        
        is_sat = "RESULT:SAT" in output
        is_unsat = "RESULT:UNSAT" in output
        assignment = {}
        
        if is_sat:
            match = re.search(r"ASSIGNMENT:(.*)", output)
            if match:
                pairs = match.group(1).strip().split()
                for p in pairs:
                    if '=' in p:
                        var, val = p.split('=')
                        assignment[int(var)] = int(val)
        
        return is_sat, is_unsat, assignment
    except subprocess.TimeoutExpired:
        return False, False, {}

def run_minisat(cnf_path):
    proc = subprocess.run(['minisat', cnf_path], capture_output=True, text=True)
    if proc.returncode == 10: return "SAT"
    if proc.returncode == 20: return "UNSAT"
    return "ERROR"

def run_full_suite(root_folder):
    stats = {"total": 0, "sat_pass": 0, "unsat_pass": 0, "fail": 0}
    
    print(f"{'='*75}")
    print(f"VERIFICATION SUITE: {root_folder}")
    print(f"{'='*75}")
    print(f"{'File Path':<40} | {'Solver':<7} | {'Verifier':<7} | {'Status'}")
    print(f"{'-'*75}")

    for root, _, files in os.walk(root_folder):
        for file in sorted(files):
            if not file.endswith(".cnf"): continue
            
            stats["total"] += 1
            cnf_path = os.path.join(root, file)
            rel_path = os.path.relpath(cnf_path, root_folder)
            
            is_sat, is_unsat, assignment = run_user_solver(cnf_path)
            
            if is_sat:
                clauses = parse_cnf_clauses(cnf_path)
                success, _ = verify_assignment(clauses, assignment)
                if success:
                    print(f"{rel_path:<40} | SAT     | PASS    | OK")
                    stats["sat_pass"] += 1
                else:
                    print(f"{rel_path:<40} | SAT     | FAIL    | LOGIC ERROR")
                    stats["fail"] += 1
            
            elif is_unsat:
                m_res = run_minisat(cnf_path)
                if m_res == "UNSAT":
                    print(f"{rel_path:<40} | UNSAT   | UNSAT   | OK (MINISAT VERIFIED)")
                    stats["unsat_pass"] += 1
                else:
                    print(f"{rel_path:<40} | UNSAT   | {m_res:<7} | CRITICAL MISMATCH")
                    stats["fail"] += 1
            
            else:
                print(f"{rel_path:<40} | TIMEOUT | N/A     | SKIP")

    print(f"{'='*75}")
    print(f"VERIFICATION SUMMARY")
    print(f"Total Processed: {stats['total']}")
    print(f"Correct SAT (Verified Assignment): {stats['sat_pass']}")
    print(f"Correct UNSAT (Verified vs MiniSat): {stats['unsat_pass']}")
    print(f"Failed Instances: {stats['fail']}")
    print(f"{'='*75}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 verify.py <dataset_folder>")
    else:
        run_full_suite(sys.argv[1])