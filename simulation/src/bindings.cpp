#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // Automatically converts C++ std::vector to Python lists
#include "monte_carlo.hpp"

namespace py = pybind11;
using namespace simulation;

// This macro creates the Python module named 'simulation_engine'
// In Python, this allows: `import simulation_engine`
PYBIND11_MODULE(simulation_engine, m) {
    m.doc() = "High-performance multi-threaded C++ Monte Carlo simulation engine";

    // Expose the SimulationConfig struct to Python
    // Allows Python to create: cfg = simulation_engine.SimulationConfig(...)
    py::class_<SimulationConfig>(m, "SimulationConfig")
        .def(py::init<double, double, double, int, int, int, double>(),
             py::arg("initial_price") = 100.0,
             py::arg("drift") = 0.08,
             py::arg("volatility") = 0.20,
             py::arg("time_steps") = 252,
             py::arg("num_paths") = 100000,
             py::arg("num_sample_paths") = 50,
             py::arg("dt") = 1.0 / 252.0)
        .def_readwrite("initial_price", &SimulationConfig::initial_price)
        .def_readwrite("drift", &SimulationConfig::drift)
        .def_readwrite("volatility", &SimulationConfig::volatility)
        .def_readwrite("time_steps", &SimulationConfig::time_steps)
        .def_readwrite("num_paths", &SimulationConfig::num_paths)
        .def_readwrite("num_sample_paths", &SimulationConfig::num_sample_paths)
        .def_readwrite("dt", &SimulationConfig::dt);

    // Expose the SimulationResult struct to Python
    // Read-only so Python can inspect metrics: result.mean_final_price, result.var_95, etc.
    py::class_<SimulationResult>(m, "SimulationResult")
        .def_readonly("initial_price", &SimulationResult::initial_price)
        .def_readonly("mean_final_price", &SimulationResult::mean_final_price)
        .def_readonly("median_final_price", &SimulationResult::median_final_price)
        .def_readonly("std_dev_final_price", &SimulationResult::std_dev_final_price)
        .def_readonly("min_final_price", &SimulationResult::min_final_price)
        .def_readonly("max_final_price", &SimulationResult::max_final_price)
        .def_readonly("percentile_5", &SimulationResult::percentile_5)
        .def_readonly("percentile_25", &SimulationResult::percentile_25)
        .def_readonly("percentile_75", &SimulationResult::percentile_75)
        .def_readonly("percentile_95", &SimulationResult::percentile_95)
        .def_readonly("var_95", &SimulationResult::var_95)
        .def_readonly("var_99", &SimulationResult::var_99)
        .def_readonly("expected_shortfall_95", &SimulationResult::expected_shortfall_95)
        .def_readonly("expected_shortfall_99", &SimulationResult::expected_shortfall_99)
        .def_readonly("sample_paths", &SimulationResult::sample_paths)
        .def_readonly("final_prices", &SimulationResult::final_prices);

    // Expose the MonteCarloSimulator class and its .run() method to Python
    py::class_<MonteCarloSimulator>(m, "MonteCarloSimulator")
        .def(py::init<const SimulationConfig&>(), py::arg("config"))
        .def("run", &MonteCarloSimulator::run, "Execute parallel Monte Carlo simulation");
}
