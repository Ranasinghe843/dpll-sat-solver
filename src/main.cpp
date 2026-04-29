#include <iostream>
#include "solver.hpp"

int main() {
    solution s = solver_try(100);
    std::cout << "------------------------------------" << std::endl;
    std::cout << "DPLL Solver initialized on M4 ARM64" << std::endl;
    std::cout << s.x << std::endl;
    std::cout << "------------------------------------" << std::endl;
    return 0;
}