#include "parser.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>

cnf parse_cnf(const std::string& filename) {
    std::ifstream file(filename);

    if (!file.is_open()) {
        throw std::runtime_error("Could not open file: " + filename);
    }

    cnf formula;
    formula.num_vars = 0;
    formula.num_clauses = 0;
    
    int num_clauses_declared = 0;

    std::vector<int> current_clause;
    std::string line;

    bool header_found = false;

    while (std::getline(file, line)) {
        if (line.empty()) continue;
        
        size_t first = line.find_first_not_of(" \t\r\n");
        if (first == std::string::npos) continue;

        if (line[first] == 'c') continue;
        if (line[first] == '%') break;

        if (line[first] == 'p') {
            std::stringstream ss(line);
            std::string p, type;

            if (!(ss >> p >> type >> formula.num_vars >> num_clauses_declared) || type != "cnf") {
                throw std::runtime_error("Invalid DIMACS header.");
            }
            
            formula.clauses.reserve(num_clauses_declared);
            header_found = true;
            continue;
        }

        std::stringstream ss(line);
        
        int val;
        while (ss >> val) {
            if (val == 0) {
                formula.clauses.push_back(current_clause);
                current_clause.clear();
            } else {
                current_clause.push_back(val);
            }
        }
    }

    if (!current_clause.empty()) {
        throw std::runtime_error("Last clause was not ended with 0.");
    }

    if (num_clauses_declared != 0 && formula.clauses.size() != (size_t)num_clauses_declared) {
        throw std::runtime_error("Clause count mismatch: expected " + 
                                 std::to_string(num_clauses_declared) + 
                                 ", got " + std::to_string(formula.clauses.size()));
    }

    formula.num_clauses = static_cast<int>(formula.clauses.size());

    return formula;
}