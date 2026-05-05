import sys
import time

# DIMACS parser
def parse_dimacs(filename):
    clauses = []
    num_vars = 0
    num_clauses_declared = 0
    current_clause = []
    # read file bytes and try common encodings (handles UTF-16 BOM files)
    raw = open(filename, 'rb').read()
    text = None
    for enc in ('utf-8', 'utf-8-sig', 'utf-16', 'latin-1'):
        try:
            text = raw.decode(enc)
            break
        except Exception:
            continue
    if text is None:
        text = raw.decode('latin-1', errors='ignore')

    for line in text.splitlines():
        line = line.strip()
        if line == "":
            continue
        if line.startswith("c"):
            # some generators prefix the header with 'c p cnf ...'
            if 'p cnf' in line:
                # strip leading 'c' and fall through to header parsing
                line = line.lstrip('c').strip()
            else:
                continue
        if line.startswith('%'):
            # treat '%' as a comment/section marker but allow trailing data
            continue
        if line.startswith("p"):
            parts = line.split()
            if len(parts) != 4 or parts[1] != "cnf":
                raise ValueError("Invalid DIMACS header.")
            num_vars = int(parts[2])
            num_clauses_declared = int(parts[3])
            continue
        parts = line.split()
        values = []
        for p in parts:
            try:
                values.append(int(p))
            except ValueError:
                continue
        for value in values:
            if value == 0:
                clauses.append(current_clause)
                current_clause = []
            else:
                current_clause.append(value)
    if current_clause:
        raise ValueError("Last clause was not ended with 0.")
    if num_clauses_declared != 0 and len(clauses) != num_clauses_declared:
        # tolerate mismatch between header and actual clauses (some generators append trailing zeros)
        print(f"Warning: Clause count mismatch: header={num_clauses_declared}, parsed={len(clauses)}", file=sys.stderr)
    return num_vars, clauses


class CDCLSolver:
    def __init__(self):
        self.num_variables = 0
        self.clauses = []
        self.learned = []
        self.has_empty_clause = False

        # assignment state
        self.assignment = {}  # var -> bool
        self.level = {}  # var -> decision level
        self.antecedent = {}  # var -> clause that implied it (None for decisions)
        self.trail = []  # list of assigned literals in order
        self.decision_level = 0
        # watched literals structures
        self.watches = {}  # lit -> list of clause indices watching this lit
        self.clause_watch = {}  # clause_idx -> (watch1, watch2)
        self.propagation_queue = []

    def parse_cnf(self, file):
        self.num_variables, self.clauses = parse_dimacs(file)
        # detect empty clause (immediate UNSAT)
        self.has_empty_clause = any(len(c) == 0 for c in self.clauses)
        # initialize watches for clauses
        self.watches = {}
        self.clause_watch = {}
        for i, clause in enumerate(self.clauses):
            if len(clause) == 0:
                # empty clause: nothing to watch
                continue
            if len(clause) == 1:
                w1 = clause[0]
                w2 = clause[0]
            else:
                w1, w2 = clause[0], clause[1]
            self.clause_watch[i] = (w1, w2)
            self.watches.setdefault(w1, []).append(i)
            if w2 != w1:
                self.watches.setdefault(w2, []).append(i)
        # enqueue initial unit clauses (level 0)
        for clause in self.clauses:
            if len(clause) == 1:
                self.enqueue_assignment(clause[0], antecedent=clause)

    def pick_branching_literal(self):
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

    def value_of_literal(self, lit):
        v = abs(lit)
        if v not in self.assignment:
            return None
        val = self.assignment[v]
        return val if lit > 0 else (not val)

    def unit_propagate(self):
        # watched-literals based propagation
        while self.propagation_queue:
            lit = self.propagation_queue.pop(0)
            false_lit = -lit
            watchers = list(self.watches.get(false_lit, []))
            for ci in watchers:
                clause = self.clauses[ci] if ci < len(self.clauses) else self.learned[ci - len(self.clauses)]
                w1, w2 = self.clause_watch.get(ci, (None, None))
                if w1 == false_lit:
                    other = w2
                    this_watch_pos = 1
                elif w2 == false_lit:
                    other = w1
                    this_watch_pos = 0
                else:
                    continue
                if self.value_of_literal(other) is True:
                    continue
                found_new = False
                for l in clause:
                    if l == other:
                        continue
                    if self.value_of_literal(l) is not False:
                        if ci in self.watches.get(false_lit, []):
                            try:
                                self.watches[false_lit].remove(ci)
                            except ValueError:
                                pass
                        self.watches.setdefault(l, []).append(ci)
                        if this_watch_pos == 0:
                            self.clause_watch[ci] = (l, other)
                        else:
                            self.clause_watch[ci] = (other, l)
                        found_new = True
                        break
                if found_new:
                    continue
                val_other = self.value_of_literal(other)
                if val_other is None:
                    v = abs(other)
                    value = other > 0
                    if v in self.assignment:
                        if self.assignment[v] != value:
                            return clause
                        continue
                    self.assignment[v] = value
                    self.level[v] = self.decision_level
                    self.antecedent[v] = clause
                    self.trail.append(other)
                    self.propagation_queue.append(other)
                else:
                    return clause
        return None

    def enqueue_assignment(self, lit, antecedent=None):
        v = abs(lit)
        val = lit > 0
        if v in self.assignment:
            if self.assignment[v] != val:
                return False
            return True
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
            if self.level.get(v, 0) <= level:
                break
            self.trail.pop()
            del self.assignment[v]
            del self.level[v]
            if v in self.antecedent:
                del self.antecedent[v]
        self.decision_level = level

    def resolve(self, c1, c2, pivot):
        set1 = set(c1)
        set2 = set(c2)
        res = (set1 | set2) - {pivot, -pivot}
        for lit in list(res):
            if -lit in res:
                return None
        return list(res)

    def analyze_conflict(self, conflict_clause):
        learned = list(conflict_clause)
        def count_current_level_literals(clause_list):
            return sum(1 for l in clause_list if self.level.get(abs(l), 0) == self.decision_level)
        path_count = count_current_level_literals(learned)
        i = len(self.trail) - 1
        while path_count > 1 and i >= 0:
            lit_on_trail = self.trail[i]
            v = abs(lit_on_trail)
            if any(abs(l) == v for l in learned) and self.level.get(v, 0) == self.decision_level:
                antecedent = self.antecedent.get(v)
                if antecedent is None:
                    i -= 1
                    continue
                pivot_lit = next((l for l in learned if abs(l) == v), None)
                if pivot_lit is None:
                    i -= 1
                    continue
                new_clause = self.resolve(learned, antecedent, pivot_lit)
                if new_clause is None:
                    break
                learned = new_clause
                path_count = count_current_level_literals(learned)
            i -= 1
        levels = [self.level.get(abs(l), 0) for l in learned if self.level.get(abs(l), 0) != self.decision_level]
        backjump_level = max(levels) if levels else 0
        return learned, backjump_level

    def add_learned_clause(self, clause):
        ci = len(self.clauses) + len(self.learned)
        self.learned.append(clause)
        if len(clause) == 0:
            return
        if len(clause) == 1:
            w1 = clause[0]
            w2 = clause[0]
        else:
            w1, w2 = clause[0], clause[1]
        self.clause_watch[ci] = (w1, w2)
        self.watches.setdefault(w1, []).append(ci)
        if w2 != w1:
            self.watches.setdefault(w2, []).append(ci)

    def solve(self):
        # immediate UNSAT if empty clause present in input
        if getattr(self, 'has_empty_clause', False):
            return False, []
        while True:
            conflict = self.unit_propagate()
            if conflict is not None:
                if self.decision_level == 0:
                    return False, []
                learned, backjump_level = self.analyze_conflict(conflict)
                if learned is None:
                    return False, []
                self.add_learned_clause(learned)
                self.backtrack_to_level(backjump_level)
                unassigned = [l for l in learned if abs(l) not in self.assignment]
                if len(unassigned) == 1:
                    lit = unassigned[0]
                    self.enqueue_assignment(lit, antecedent=learned)
                continue
            if len(self.assignment) == self.num_variables:
                model = []
                for v, val in self.assignment.items():
                    model.append(v if val else -v)
                return True, model
            lit = self.pick_branching_literal()
            if lit is None:
                model = []
                for v, val in self.assignment.items():
                    model.append(v if val else -v)
                return True, model
            self.decision_level += 1
            self.enqueue_assignment(lit, antecedent=None)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mySAT.py <input.cnf>")
        sys.exit(1)
    file = sys.argv[1]
    solver = CDCLSolver()
    solver.parse_cnf(file)
    success, model = solver.solve()
    if success:
        # Print minimal output as required
        print("SATISFIABLE")
        # print assignment as v-line
        out = ' '.join(str(l) for l in sorted(model, key=abs)) + ' 0'
        print(out)
    else:
        print("UNSATISFIABLE")


if __name__ == "__main__":
    main()
