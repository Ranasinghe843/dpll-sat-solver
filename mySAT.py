import sys
from dimacs_parser import parse_dimacs

class CDCLSolver:
    def __init__(self):
        self.num_variables = 0
        self.clauses = []
        self.learned = []
        self.has_empty_clause = False
        self.assignment = {}
        self.level = {}
        self.antecedent = {}
        self.trail = []
        self.decision_level = 0
        self.watches = {}
        self.clause_watch = {}
        self.propagation_queue = []

    def parse_cnf(self, file):
        self.num_variables, self.clauses = parse_dimacs(file)
        self.has_empty_clause = any(len(c) == 0 for c in self.clauses)
        for i, clause in enumerate(self.clauses):
            if len(clause) == 0: continue
            w1 = clause[0]
            w2 = clause[0] if len(clause) == 1 else clause[1]
            self.clause_watch[i] = (w1, w2)
            self.watches.setdefault(w1, []).append(i)
            if w2 != w1:
                self.watches.setdefault(w2, []).append(i)
        for clause in self.clauses:
            if len(clause) == 1:
                self.enqueue_assignment(clause[0], antecedent=clause)

    def pick_branching_literal(self):
        counts = {}
        for clause in self.clauses + self.learned:
            for lit in clause:
                v = abs(lit)
                if v in self.assignment: continue
                counts[lit] = counts.get(lit, 0) + 1
        if not counts: return None
        return max(counts.items(), key=lambda x: x[1])[0]

    def value_of_literal(self, lit):
        v = abs(lit)
        if v not in self.assignment: return None
        val = self.assignment[v]
        return val if lit > 0 else (not val)

    def unit_propagate(self):
        while self.propagation_queue:
            lit = self.propagation_queue.pop(0)
            false_lit = -lit
            watchers = list(self.watches.get(false_lit, []))
            for ci in watchers:
                clause = self.clauses[ci] if ci < len(self.clauses) else self.learned[ci - len(self.clauses)]
                w1, w2 = self.clause_watch.get(ci, (None, None))
                if w1 == false_lit:
                    other, this_watch_pos = w2, 1
                elif w2 == false_lit:
                    other, this_watch_pos = w1, 0
                else: continue
                if self.value_of_literal(other) is True: continue
                found_new = False
                for l in clause:
                    if l == other: continue
                    if self.value_of_literal(l) is not False:
                        if ci in self.watches.get(false_lit, []):
                            try: self.watches[false_lit].remove(ci)
                            except ValueError: pass
                        self.watches.setdefault(l, []).append(ci)
                        self.clause_watch[ci] = (l, other) if this_watch_pos == 0 else (other, l)
                        found_new = True
                        break
                if found_new: continue
                if self.value_of_literal(other) is None:
                    if not self.enqueue_assignment(other, antecedent=clause):
                        return clause
                elif self.value_of_literal(other) is False:
                    return clause
        return None

    def enqueue_assignment(self, lit, antecedent=None):
        v = abs(lit)
        val = lit > 0
        if v in self.assignment:
            return self.assignment[v] == val
        self.assignment[v] = val
        self.level[v] = self.decision_level
        self.antecedent[v] = antecedent
        self.trail.append(lit)
        self.propagation_queue.append(lit)
        return True

    def backtrack_to_level(self, level):
        while self.trail:
            lit = self.trail[-1]
            v = abs(lit)
            if self.level.get(v, 0) <= level: break
            self.trail.pop()
            del self.assignment[v]
            del self.level[v]
            if v in self.antecedent: del self.antecedent[v]
        self.decision_level = level

    def resolve(self, c1, c2, pivot):
        res = set(c1) | set(c2)
        res.remove(pivot)
        res.remove(-pivot)
        for lit in list(res):
            if -lit in res: return None
        return list(res)

    def analyze_conflict(self, conflict_clause):
        learned = list(conflict_clause)
        def count_lvl(cl): return sum(1 for l in cl if self.level.get(abs(l), 0) == self.decision_level)
        i = len(self.trail) - 1
        while count_lvl(learned) > 1 and i >= 0:
            v = abs(self.trail[i])
            if any(abs(l) == v for l in learned):
                ant = self.antecedent.get(v)
                if ant:
                    pivot = next(l for l in learned if abs(l) == v)
                    new = self.resolve(learned, ant, pivot)
                    if new is not None: learned = new
            i -= 1
        lvls = [self.level.get(abs(l), 0) for l in learned if self.level.get(abs(l), 0) != self.decision_level]
        return learned, (max(lvls) if lvls else 0)

    def add_learned_clause(self, clause):
        ci = len(self.clauses) + len(self.learned)
        self.learned.append(clause)
        if not clause: return
        w1 = clause[0]
        w2 = clause[0] if len(clause) == 1 else clause[1]
        self.clause_watch[ci] = (w1, w2)
        self.watches.setdefault(w1, []).append(ci)
        if w2 != w1: self.watches.setdefault(w2, []).append(ci)

    def solve(self):
        if self.has_empty_clause: return False, []
        while True:
            conflict = self.unit_propagate()
            if conflict:
                if self.decision_level == 0: return False, []
                learned, backjump = self.analyze_conflict(conflict)
                self.add_learned_clause(learned)
                self.backtrack_to_level(backjump)
                unassigned = [l for l in learned if abs(l) not in self.assignment]
                if len(unassigned) == 1: self.enqueue_assignment(unassigned[0], learned)
                continue
            if len(self.assignment) == self.num_variables:
                return True, [v if val else -v for v, val in self.assignment.items()]
            lit = self.pick_branching_literal()
            if lit is None: return True, [v if val else -v for v, val in self.assignment.items()]
            self.decision_level += 1
            self.enqueue_assignment(lit)

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
        
    solver = CDCLSolver()
    try:
        solver.parse_cnf(sys.argv[1])
        sat, model = solver.solve()
        
        if sat:
            print("RESULT:SAT")
            
            sorted_model = sorted(model, key=abs)
            assignments = []
            for lit in sorted_model:
                var = abs(lit)
                val = 1 if lit > 0 else 0
                assignments.append(f"{var}={val}")
            
            print(f"ASSIGNMENT:{' '.join(assignments)}")
        else:
            print("RESULT:UNSAT")
            
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()