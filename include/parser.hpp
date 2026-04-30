#ifndef PARSER_HPP
#define PARSER_HPP

#include <vector>
#include <string>

struct cnf {
    int num_vars;
    int num_clauses;
    std::vector<std::vector<int>> clauses;
};

cnf parse_cnf(const std::string& file);

#endif