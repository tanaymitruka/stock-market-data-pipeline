cmake_minimum_required(VERSION 3.15)
project(stock_pipeline_engine LANGUAGES CXX)

# Force the compiler to use modern C++17 standards
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 1. Find the Python installation and pybind11 extension tool
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# 2. Tell CMake where to look for your .hpp header files
include_directories(simulation/include)

# 3. Define the native Python module name and list the C++ source files
pybind11_add_module(simulation_engine
    simulation/src/bindings.cpp
    simulation/src/monte_carlo.cpp
)

# 4. Enable multi-threading support (required for parallel Monte Carlo)
find_package(Threads REQUIRED)
target_link_libraries(simulation_engine PRIVATE Threads::Threads)