import os
import sys
import time
import subprocess
import re
import statistics
import json
import argparse
import matplotlib.pyplot as plt

def run_solver(cnf_path, flags):
    cmd = ['python3', 'mySAT.py', cnf_path, '--stats'] + flags
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = proc.stdout
        
        t_match = re.search(r"Execution Time: ([\d.]+)s", output)
        d_match = re.search(r"Decisions: (\d+)", output)
        i_match = re.search(r"Implications: (\d+)", output)
        
        return {
            "time": float(t_match.group(1)) if t_match else 0.0001,
            "decisions": int(d_match.group(1)) if d_match else 0,
            "implications": int(i_match.group(1)) if i_match else 0,
            "status": "SAT" if "RESULT:SAT" in output else "UNSAT"
        }
    except subprocess.TimeoutExpired:
        return {"time": 120.0, "decisions": -1, "implications": -1, "status": "TIMEOUT"}

def run_minisat(cnf_path):
    start = time.perf_counter()
    proc = subprocess.run(['minisat', cnf_path], capture_output=True, text=True)
    end = time.perf_counter()
    res = "SAT" if proc.returncode == 10 else "UNSAT" if proc.returncode == 20 else "ERROR"
    return {"time": max(end - start, 0.0001), "status": res}

def benchmark_all(root_path):
    configs = [
        ("Base DPLL", ["--no-learning", "--no-backtrack", "--no-watched"]),
        ("+ Learning", ["--no-backtrack", "--no-watched"]),
        ("+ Backtrack", ["--no-watched"]),
        ("+ Watched", []),
        ("MiniSat", "REF")
    ]

    results = {}
    subdirs = sorted([d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))])
    
    print(f"{'Folder':<12} | {'Config':<20} | {'Avg Time':<10} | {'Avg Dec.':<8} | {'Avg Imp.'}")
    print("-" * 75)

    for folder in subdirs:
        f_path = os.path.join(root_path, folder)
        cnfs = [f for f in os.listdir(f_path) if f.endswith('.cnf')]
        if not cnfs: continue
        
        results[folder] = {c[0]: [] for c in configs}

        for c_name, flags in configs:
            for cnf in cnfs:
                cnf_full = os.path.join(f_path, cnf)
                data = run_minisat(cnf_full) if flags == "REF" else run_solver(cnf_full, flags)
                results[folder][c_name].append(data)
            
            avg_t = statistics.mean([d['time'] for d in results[folder][c_name]])
            avg_d = statistics.mean([d['decisions'] for d in results[folder][c_name] if 'decisions' in d]) if c_name != "MiniSat" else 0
            avg_i = statistics.mean([d['implications'] for d in results[folder][c_name] if 'implications' in d]) if c_name != "MiniSat" else 0
            
            print(f"{folder:<12} | {c_name:<20} | {avg_t:<10.4f} | {avg_d:<8.1f} | {avg_i:<8.1f}")

    return results

def generate_log_plot(results):
    folders = list(results.keys())
    config_names = list(results[folders[0]].keys())
    
    fig, ax = plt.subplots(figsize=(12, 7))
    x = range(len(folders))
    width = 0.15

    for i, c_name in enumerate(config_names):
        times = [[d['time'] for d in results[f][c_name]] for f in folders]
        means = [statistics.mean(t) for t in times]
        stds = [statistics.stdev(t) if len(t) > 1 else 0 for t in times]
        
        ax.bar([pos + i*width for pos in x], means, width, yerr=stds, label=c_name, capsize=3)

    ax.set_yscale('log')
    ax.set_ylabel('Execution Time (s) - Log Scale', fontweight='bold')
    ax.set_xlabel('CNF Set', fontweight='bold')
    ax.set_title('Timing Improvements with Heuristics', fontsize=14)
    ax.set_xticks([pos + 2*width for pos in x])
    ax.set_xticklabels(folders)
    ax.legend(loc='upper left')
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.tight_layout()
    plt.savefig('performance_log_analysis.png')
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comprehensive Metric Suite")
    parser.add_argument("--mode", choices=['run', 'plot'], default='run')
    parser.add_argument("--data_file", default="detailed_metrics.json")
    parser.add_argument("--dataset", help="Path to CNF subfolders")

    args = parser.parse_args()

    if args.mode == 'run':
        results_data = benchmark_all(args.dataset)
        with open(args.data_file, 'w') as f:
            json.dump(results_data, f, indent=4)
        generate_log_plot(results_data)
    elif args.mode == 'plot':
        with open(args.data_file, 'r') as f:
            generate_log_plot(json.load(f))