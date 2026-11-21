#pragma once

#include <vector>
#include <string>

namespace simulation {

/**
 * Configuration parameters for the Geometric Brownian Motion simulation.
 */
struct SimulationConfig {
    double initial_price = 100.0;     // Starting asset price (S_0)
    double drift = 0.08;              // Annual expected return (mu)
    double volatility = 0.20;         // Annual volatility (sigma)
    int time_steps = 252;             // Number of trading days in projection
    int num_paths = 100000;           // Total Monte Carlo simulation trajectories
    int num_sample_paths = 50;        // Number of paths to retain for charting
    double dt = 1.0 / 252.0;          // Time delta step size (fraction of year)
};

/**
 * Result structure packaging risk metrics, percentiles, and sample paths.
 */
struct SimulationResult {
    double initial_price = 0.0;
    double mean_final_price = 0.0;
    double median_final_price = 0.0;
    double std_dev_final_price = 0.0;
    double min_final_price = 0.0;
    double max_final_price = 0.0;

    // Percentiles of the final price distribution
    double percentile_5 = 0.0;
    double percentile_25 = 0.0;
    double percentile_75 = 0.0;
    double percentile_95 = 0.0;

    // Value at Risk (VaR): maximum dollar loss with given confidence
    double var_95 = 0.0;
    double var_99 = 0.0;

    // Conditional VaR (Expected Shortfall): average loss in tail crash scenarios
    double expected_shortfall_95 = 0.0;
    double expected_shortfall_99 = 0.0;

    // Sample paths for visual plotting: [num_sample_paths x (time_steps + 1)]
    std::vector<std::vector<double>> sample_paths;

    // All terminal prices (useful for distribution/histogram plotting)
    std::vector<double> final_prices;
};

/**
 * High-performance, multi-threaded Monte Carlo simulation engine.
 */
class MonteCarloSimulator {
public:
    explicit MonteCarloSimulator(const SimulationConfig& config);

    // Run parallel simulation across all available hardware threads
    SimulationResult run() const;

private:
    SimulationConfig config_;
};

} // namespace simulation
