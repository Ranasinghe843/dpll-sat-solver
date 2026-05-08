import sys
from dimacs_parser import parse_dimacs
import argparse
import time

class DimacsSolver:
    def __init__(self, use_learning=True, use_backtrack=True, use_watched=True):
        
        # flags to enable/disable heuristics
        self.use_learning = use_learning
        self.use_backtrack = use_backtrack
        self.use_watched = use_watched
        
        #initial solver state 
        self.num_variables = 0
        self.clauses = []
        self.learned = []
        self.has_empty_clause = False

        # assignment tracking
        self.assignment = {}
        self.level = {}
        self.antecedant = {}
        self.trail = []
        self.decision_level = 0

        #watched literals
        self.watches = {}
        self.clause_watch = {}
        self.propagation_queue = [] # propogation

        # benchmark - flag
        if self.use_watched:
            self.unit_propagate = self.unit_propagate_watched
        else:
            self.unit_propagate = self.unit_propagate_basic

        self.stats = {
            "decisions": 0,
            "implications": 0,
            "start_time": 0.0,
            "end_time": 0.0
        }

    # parse dimacs - clauses
    def parse_cnf(self, file):
        self.num_variables, self.clauses = parse_dimacs(file)
        self.has_empty_clause = any(len(c) == 0 for c in self.clauses)

        if self.use_watched:
            for i, clause in enumerate(self.clauses):
                if len(clause) == 0: 
                    continue
                w1 = clause[0]
                w2 = clause[0] if len(clause) == 1 else clause[1]
                self.clause_watch[i] = (w1, w2)
                self.watches.setdefault(w1, []).append(i)
                if w2 != w1:
                    self.watches.setdefault(w2, []).append(i)

        for clause in self.clauses:
            if len(clause) == 1:
                self.add_to_assignment(clause[0], antecedant=clause)

    def branching_literal(self): # most freq unassign literal
        counts = {}
        for clause in self.clauses + self.learned:
            for lit in clause:
                v = abs(lit)
                if v in self.assignment:
                    continue
                counts[lit] = counts.get(lit, 0) + 1
        if not counts: 
            return None
        return max(counts.items(), key=lambda x: x[1])[0]

    def value_of_literal(self, lit): # assignment
        v = abs(lit)
        if v not in self.assignment: 
            return None
        val = self.assignment[v]
        return val if lit > 0 else (not val)
    
    def unit_propagate_watched(self): # watched literal - propogation
        while self.propagation_queue:
            lit = self.propagation_queue.pop(0)
            false_lit = -lit
            watchers = list(self.watches.get(false_lit, []))
            for ci in watchers:
                clause = self.clauses[ci] if ci < len(self.clauses) else self.learned[ci - len(self.clauses)]
                w1, w2 = self.clause_watch.get(ci, (None, None))

                if w1 == false_lit: # which watch was false
                    other, this_watch_pos = w2, 1
                elif w2 == false_lit:
                    other, this_watch_pos = w1, 0
                else: 
                    continue

                if self.value_of_literal(other) is True: continue
                found_new = False
                for l in clause:
                    if l == other: 
                        continue
                    if self.value_of_literal(l) is not False:
                        if ci in self.watches.get(false_lit, []):
                            try: self.watches[false_lit].remove(ci)
                            except ValueError: pass
                        self.watches.setdefault(l, []).append(ci)
                        self.clause_watch[ci] = (l, other) if this_watch_pos == 0 else (other, l)
                        found_new = True
                        break
                if found_new: 
                    continue
                if self.value_of_literal(other) is None:
                    if not self.add_to_assignment(other, antecedant=clause):
                        return clause
                elif self.value_of_literal(other) is False:
                    return clause
        return None

    def unit_propagate_basic(self): # scan all clauses
        while self.propagation_queue:
            lit = self.propagation_queue.pop(0)
            for i in range(len(self.clauses) + len(self.learned)):
                clause = self.clauses[i] if i < len(self.clauses) else self.learned[i - len(self.clauses)]
                
                if any(self.value_of_literal(l) is True for l in clause):
                    continue
                
                unassigned = [l for l in clause if self.value_of_literal(l) is None]
                
                if len(unassigned) == 0:
                    return clause
                
                if len(unassigned) == 1:
                    if not self.add_to_assignment(unassigned[0], antecedant=clause):
                        return clause
        return None
    
    def add_to_assignment(self, lit, antecedant=None): #assign literal and  add to queue
        v = abs(lit)
        val = lit > 0

        if v in self.assignment:
            return self.assignment[v] == val
        
        self.assignment[v] = val
        self.level[v] = self.decision_level
        self.antecedant[v] = antecedant
        self.trail.append(lit)
        self.propagation_queue.append(lit)

        if self.decision_level > 0 and antecedant is not None:
            self.stats["implications"] += 1
        return True

    def backtrack(self, level): #undo assign till target lvl reached
        while self.trail:
            lit = self.trail[-1]
            v = abs(lit)
            if self.level.get(v, 0) <= level: 
                break
            self.trail.pop()
            del self.assignment[v]
            del self.level[v]
            if v in self.antecedant: 
                del self.antecedant[v]
        self.decision_level = level

    def resolve(self, c1, c2, pivot): # conflict analysis
        union = set(c1) | set(c2)
        union.remove(pivot)
        union.remove(-pivot)

        for lit in list(union): # check contradiction
            if -lit in union: return None
        return list(union)
    
    def _curr_level_literals(self, clause):
        return sum(1 for lit in clause 
                if self.level.get(abs(lit), 0) == self.decision_level)

    def _backjump_level(self, clause):
        other_levels = [self.level.get(abs(lit), 0) for lit in clause 
                        if self.level.get(abs(lit), 0) != self.decision_level]
        return max(other_levels) if other_levels else 0
    
    def fix_conflict(self, conflict_clause):# first UIP
        learned = list(conflict_clause)
        
        trail_idx = len(self.trail) - 1

        while self._curr_level_literals(learned) > 1:
            if trail_idx < 0:
                break
                
            assigned_var = abs(self.trail[trail_idx])

            if any(abs(lit) == assigned_var for lit in learned):
                antecedent = self.antecedant.get(assigned_var)
                
                if antecedent:
                    pivot = next(lit for lit in learned if abs(lit) == assigned_var)
                    
                    learned = self.resolve(learned, antecedent, pivot)
            
            trail_idx -= 1

        backjump_level = self._backjump_level(learned)
        
        return learned, backjump_level

    def add_learned_clause(self, clause):
        ci = len(self.clauses) + len(self.learned)
        self.learned.append(clause)
        if not clause: return
        if self.use_watched:
            w1 = clause[0]
            w2 = clause[0] if len(clause) == 1 else clause[1]
            self.clause_watch[ci] = (w1, w2)
            self.watches.setdefault(w1, []).append(ci)
            if w2 != w1: self.watches.setdefault(w2, []).append(ci)

    def solve(self):
        self.stats["start_time"] = time.perf_counter()
        if self.has_empty_clause:
            self.stats["end_time"] = time.perf_counter()
            return False, {}
        while True:
            conflict = self.unit_propagate()
            if conflict:
                if self.decision_level == 0:
                    self.stats["end_time"] = time.perf_counter()
                    return False, {}
                learned, backtrack_level = self.fix_conflict(conflict)
                if self.use_learning:
                    self.add_learned_clause(learned)
                
                if self.use_backtrack:
                    self.backtrack(backtrack_level)
                else:
                    self.backtrack(self.decision_level - 1)
                
                try:
                    unassigned = [l for l in learned if abs(l) not in self.assignment] # type: ignore
                    if len(unassigned) == 1: self.add_to_assignment(unassigned[0], learned)
                    continue
                except:
                    pass
            if len(self.assignment) == self.num_variables:
                self.stats["end_time"] = time.perf_counter()
                return True, self.assignment
            lit = self.branching_literal()
            if lit is None:
                self.stats["end_time"] = time.perf_counter()
                return True, self.assignment
            self.stats["decisions"] += 1
            self.decision_level += 1
            self.add_to_assignment(lit)

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="SAT Solver")
    
    parser.add_argument("cnf_file", help="Path to the DIMACS CNF file")
    
    parser.add_argument("--no-learning", action="store_false", dest="learning",
                        help="Disable Conflict-Driven Clause Learning")
    parser.add_argument("--no-backtrack", action="store_false", dest="backtrack",
                        help="Disable Non-chronological Backtracking")
    parser.add_argument("--no-watched", action="store_false", dest="watched",
                        help="Disable Watched Literals")
    parser.add_argument("--stats", action="store_true",
                        help="Print metrics for report")

    args = parser.parse_args()

    solver = DimacsSolver(
        use_learning=args.learning, 
        use_backtrack=args.backtrack, 
        use_watched=args.watched
    )

    solver.parse_cnf(args.cnf_file)
    sat, model = solver.solve()
    
    if sat:
        print("RESULT:SAT")
        
        sorted_vars = sorted(model.keys())
        assignments = []
        for var in sorted_vars:
            val = 1 if model[var] else 0
            assignments.append(f"{var}={val}")
        
        print(f"ASSIGNMENT:{' '.join(assignments)}")
    else:
        print("RESULT:UNSAT")
    
    if args.stats:
        total_time = solver.stats["end_time"] - solver.stats["start_time"]
        print(f"----------------------------------------------")
        print(f"Execution Time: {total_time:.4f}s")
        print(f"Decisions: {solver.stats['decisions']}")
        print(f"Implications: {solver.stats['implications']}")

if __name__ == "__main__":
    main()
