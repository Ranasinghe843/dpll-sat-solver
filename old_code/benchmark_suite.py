import os
import sys
import time
import subprocess
import re
import glob
import statistics
import matplotlib.pyplot as plt

# --- Verification & Parsing Logic (Keep as is) ---

def parse_cnf_clauses(filepath):
    clauses = []
    current_clause = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('c', 'p', '%')): continue
            nums = list(map(int, line.split()))
            for n in nums:
                if n == 0:
                    if current_clause:
                        clauses.append(set(current_clause))
                        current_clause = []
                else: current_clause.append(n)
    return clauses

def verify_model(clauses, assignment):
    assignment_set = set(assignment)
    for clause in clauses:
        if not any(literal in assignment_set for literal in clause):
            return False
    return True

# --- Benchmarking Engine ---

def run_multi_folder_benchmark(root_path):
    # Dictionary to store results: { folder_name: [list_of_times] }
    folder_data = {}
    
    # Get all subdirectories in the root path
    subdirs = [d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))]
    subdirs.sort() # Ensure consistent order

    if not subdirs:
        print(f"No subdirectories found in {root_path}. Point the script to the parent folder.")
        return

    print(f"{'Folder Name':<20} | {'Files':<8} | {'Avg Time (s)':<12} | {'Variance'}")
    print("-" * 65)

    for folder in subdirs:
        folder_full_path = os.path.join(root_path, folder)
        cnf_files = glob.glob(os.path.join(folder_full_path, "*.cnf"))
        
        if not cnf_files:
            continue

        execution_times = []
        for file_path in cnf_files:
            start_time = time.perf_counter()
            try:
                # Run the solver
                process = subprocess.run(
                    ['python', 'mySAT.py', file_path],
                    capture_output=True, text=True, timeout=120
                )
                duration = time.perf_counter() - start_time
                output = process.stdout
                
                # Verification step (only for SAT)
                if "RESULT:SAT" in output:
                    match = re.search(r"Assignment: \[(.*?)\]", output)
                    if match:
                        model = [int(x) for x in match.group(1).replace(',', '').split()]
                        clauses = parse_cnf_clauses(file_path)
                        if not verify_model(clauses, model):
                            print(f"WARNING: Verification failed for {file_path}")
                
                execution_times.append(duration)

            except subprocess.TimeoutExpired:
                execution_times.append(120.0) # Penalty for timeout
            except Exception:
                continue

        if execution_times:
            avg_time = statistics.mean(execution_times)
            # Variance requires at least 2 data points
            var_time = statistics.variance(execution_times) if len(execution_times) > 1 else 0.0
            folder_data[folder] = execution_times
            
            print(f"{folder:<20} | {len(execution_times):<8} | {avg_time:<12.4f} | {var_time:.6f}")

    produce_summary_plot(folder_data)

def produce_summary_plot(folder_data):
    labels = list(folder_data.keys())
    means = [statistics.mean(times) for times in folder_data.values()]
    
    # Calculate Standard Deviation for error bars (Square root of Variance)
    # This represents the "spread" of the data around the mean
    stds = [statistics.stdev(times) if len(times) > 1 else 0.0 for times in folder_data.values()]
    
    plt.figure(figsize=(10, 7))
    
    # Create bar chart with error bars
    # capsize adds the horizontal lines at the top/bottom of the error bars
    bars = plt.bar(labels, means, yerr=stds, capsize=10, color='skyblue', edgecolor='navy', alpha=0.8)
    
    plt.xlabel('Dataset', fontweight='bold')
    plt.ylabel('Average Execution Time (seconds)', fontweight='bold')
    plt.title('DPLL Solver Performance without advanced Heuristics', fontsize=14)
    
    # Add values on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + (max(means)*0.02), f'{yval:.3f}s', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('folder_comparison_benchmark.png')
    print("\nGlobal benchmark complete. Plot saved as 'folder_comparison_benchmark.png'.")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python benchmark_suite.py <root_folder_path>")
    else:
        run_multi_folder_benchmark(sys.argv[1])