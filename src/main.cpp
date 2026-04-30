#include "parser.hpp"
#include <iostream>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <filename.cnf>" << std::endl;
        return 1;
    }

    try {
        std::string filename = argv[1];
        std::cout << "File: " << filename << std::endl;

        cnf my_cnf = parse_cnf(filename);

        std::cout << "Variables: " << my_cnf.num_vars << std::endl;
        std::cout << "Clauses: " << my_cnf.num_clauses << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}