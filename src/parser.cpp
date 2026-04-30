#include "parser.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>

cnf parse_cnf(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error("Could not open file: " + filename);
    }

    cnf result;
    result.num_vars = 0;
    result.num_clauses = 0;
    
    int num_clauses_declared = 0;
    std::vector<int> current_clause;
    std::string line;
    bool header_found = false;

    while (std::getline(file, line)) {
        // 1. Handle empty lines and comments (line.strip() behavior)
        if (line.empty()) continue;
        
        // Find first non-whitespace character
        size_t first = line.find_first_not_of(" \t\r\n");
        if (first == std::string::npos) continue; 

        char first_char = line[first];

        if (first_char == 'c') continue;      // Comment
        if (first_char == '%') break;         // EOF marker

        // 2. Handle the header line (p cnf ...)
        if (first_char == 'p') {
            std::stringstream ss(line);
            std::string p, type;
            if (!(ss >> p >> type >> result.num_vars >> num_clauses_declared) || type != "cnf") {
                throw std::runtime_error("Invalid DIMACS header.");
            }
            result.clauses.reserve(num_clauses_declared); // Optimization
            header_found = true;
            continue;
        }

        // 3. Parse literals (values = list(map(int, line.split())))
        std::stringstream ss(line);
        int val;
        while (ss >> val) {
            if (val == 0) {
                result.clauses.push_back(current_clause);
                current_clause.clear();
            } else {
                current_clause.push_back(val);
            }
        }
    }

    // 4. Final Validation
    if (!current_clause.empty()) {
        throw std::runtime_error("Last clause was not ended with 0.");
    }

    if (num_clauses_declared != 0 && result.clauses.size() != (size_t)num_clauses_declared) {
        throw std::runtime_error("Clause count mismatch: expected " + 
                                 std::to_string(num_clauses_declared) + 
                                 ", got " + std::to_string(result.clauses.size()));
    }

    result.num_clauses = static_cast<int>(result.clauses.size());
    return result;
}