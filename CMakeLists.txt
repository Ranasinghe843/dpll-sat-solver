cmake_minimum_required(VERSION 3.25)
project(DPLL_SAT_Solver VERSION 1.0)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(dpll_sat_solver src/main.cpp src/solver.cpp)

target_include_directories(dpll_sat_solver PUBLIC include)