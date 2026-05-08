import json
import statistics
import os

def calculate_stats(json_file):
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found.")
        return

    with open(json_file, 'r') as f:
        data = json.load(f)

    # Required configs in order of addition
    configs = ["Base DPLL", "+ Learning", "+ Backtrack", "+ Watched"]
    
    print("% --- LATEX TABLE GENERATED FROM METRICS ---")
    print("\\begin{table}[H]")
    print("\\centering")
    print("\\begin{tabular}{|l|c|c|c|c|}")
    print("\\hline")
    print("Benchmark & Config & Avg Decisions & Avg Implications & Speedup \\\\ \\hline")

    for folder, config_data in data.items():
        base_time = statistics.mean([d['time'] for d in config_data["Base DPLL"]])
        
        for i, config in enumerate(configs):
            if config not in config_data: continue
            
            runs = config_data[config]
            avg_time = statistics.mean([r['time'] for r in runs])
            # Filter out timeouts for decision/implication averages
            valid_runs = [r for r in runs if r['decisions'] != -1]
            
            if valid_runs:
                avg_dec = statistics.mean([r['decisions'] for r in valid_runs])
                avg_imp = statistics.mean([r['implications'] for r in valid_runs])
            else:
                avg_dec, avg_imp = 0, 0

            speedup = base_time / avg_time if avg_time > 0 else 0
            
            # Print row for console/LaTeX
            # Using folder name only on first config of the group for clean LaTeX
            folder_label = folder if i == 0 else ""
            print(f"{folder_label:<12} & {config:<15} & {avg_dec:<12.1f} & {avg_imp:<12.1f} & {speedup:.2f}x \\\\")
        
        print("\\hline")

    print("\\end{tabular}")
    print("\\caption{Performance metrics and speedup ratios across benchmark sets.}")
    print("\\label{tab:metrics}")
    print("\\end{table}")

    # Additional Insight: Propagation Throughput
    print("\n\n% --- PROPAGATION THROUGHPUT ANALYSIS ---")
    for folder, config_data in data.items():
        full_cdcl = config_data.get("+ Watched", [])
        if full_cdcl:
            total_imp = sum([r['implications'] for r in full_cdcl if r['implications'] != -1])
            total_time = sum([r['time'] for r in full_cdcl])
            throughput = total_imp / total_time if total_time > 0 else 0
            print(f"% {folder} Throughput: {throughput:.2f} implications/second")

if __name__ == "__main__":
    calculate_stats("detailed_metrics.json")