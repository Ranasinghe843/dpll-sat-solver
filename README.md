## DPLL SAT Solver with Advanced Heuristics
Group 19: Samitha Ranasinghe, Milen Manoj
<ol>
<li> Directory Structure
• mySAT.py: The main entry point for the solver. Contains the DimacsSolver class and execution logic.
• dimacs_parser.py: A utility script used to parse CNF files in the standard DIMACS format.
• /benchmarks: Contains the input datasets used for evaluation, including uf20, uf50, and uf100 from SATLIB.
• performance_analysis.png: (Optional) Visual summary of solver performance across benchmarks.
• detailed_metrics.json: (Optional) Saved metrics from benchmarking for report generation.
<li> Compilation and Setup
This solver is implemented in Python 3.
• Environment: The code is designed to run on the ECEPROG cluster (eceprog.ecn.purdue.edu) [cite: 46-47].
• Dependencies: Uses standard Python libraries (sys, time, argparse, re, json). [cite_start]No external package installation is required to run the core solver.
• Setup: Ensure mySAT.py and dimacs_parser.py are in the same directory.
<li> Execution Interface
The solver adheres to the mandatory command-line interface specified in the project guidelines.
Standard Usage
python3 mySAT.py path/to/benchmark.cnf

Heuristic Toggles (for Benchmarking)
To support the experimental analysis required for the project report, the following switches are included:
• --no-learning: Disables Conflict-Driven Clause Learning.
• --no-backtrack: Disables Non-chronological Backtracking (defaults to chronological).
• --no-watched: Disables Two-Watched Literals (defaults to basic BCP).
• --stats: Prints execution time, number of decisions, and total implications found.
<li> Documentation of Functions and Data Structures
[cite: 50-51]
Key Data Structures
• self.watches: A dictionary-based implementation of Two-Watched Literals. [cite_start]It maps literals to the indices of clauses they are currently monitoring for efficient BCP.
• self.trail: A chronological list of literal assignments used to support non-chronological backtracking.
• self.antecedent: A mapping of variables to the clauses that forced their assignment, forming the basis for conflict resolution and 1-UIP analysis.
Primary Functions
• unit_propagate: Implements Boolean Constraint Propagation (BCP) using the Two-Watched Literals optimization.
• analyze_conflict: Performs conflict analysis using resolution to generate Learned Clauses.
• backtrack_to_level: Implements Non-chronological Backtracking (Backjumping), allowing the solver to jump to the decision level responsible for a conflict.
<li> **Output Format:** The solver provides output in the exact format required for automated grading
<ul>
<li> Satisfiable: **RESULT:SAT**, **ASSIGNMENT: 1=1 2=0 3=1 ...**.
<li> Unsatisfiable: **RESULT:UNSAT**.
</ul>
</ol>