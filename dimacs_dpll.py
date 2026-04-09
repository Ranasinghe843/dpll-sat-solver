from dimacs_parser import parse_dimacs
import sys
from collections import Counter
import itertools
import copy

class DPLLSolver():
    def __init__(self):

        self.num_variables = 0
        self.clauses = []
        self.curr_clauses = []
    
    def parse_cnf(self, file):

        self.num_variables, self.clauses = parse_dimacs(file)
    
    def most_common_literal(self, clauses):

        counter = Counter(itertools.chain.from_iterable(clauses))
        
        if not counter:
            return None
        else:
            return counter.most_common(1)[0][0]
    
    def satisfy_literal(self, clauses, literal):

        curr_clauses = []
        for clause in clauses:
            if literal in clause:
                continue

            if -literal in clause:
                clause.remove(-literal)
                if not clause:
                    return None
            
            curr_clauses.append(clause)
        
        return curr_clauses
    
    def unit_clauses(self, clauses, model):

        if clauses is None:
            return None, model
        
        for clause in clauses:
            if len(clause) != 1:
                continue

            literal = clause[0]
            model.append(literal)
            clauses = self.satisfy_literal(clauses, literal)

            if clauses is None:
                return None, model
        
        return clauses, model
    
    def solve(self, clauses, model):

        clauses, model = self.unit_clauses(clauses, model)

        if clauses is None:
            return False, []
        
        if not clauses:
            return True, model
        
        best_literal = self.most_common_literal(clauses)

        correct, temp_model = self.solve(self.satisfy_literal(copy.deepcopy(clauses), best_literal), model + [best_literal])
        if correct:
            return True, temp_model
        
        return self.solve(self.satisfy_literal(copy.deepcopy(clauses), -best_literal), model + [-best_literal]) # type: ignore

def main():
    file = sys.argv[1]

    solver = DPLLSolver()
    solver.parse_cnf(file)

    success, model = solver.solve(solver.clauses, [])

    if success:
        print("SATISFIABLE")
        print("Assignment:", sorted(model, key=abs))
    else:
        print("UNSATISFIABLE")

if __name__ == "__main__":
    main()