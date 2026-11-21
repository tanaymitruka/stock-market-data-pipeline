#include "monte_carlo.hpp"

#include <algorithm> // For std::sort, std::min
#include <cmath>     // For std::exp, std::sqrt
#include <numeric>   // For std::accumulate (sum)
#include <random>    // For random numbers (Mersenne Twister & Bell curve)
#include <thread>    // To run simulations on multiple CPU cores in parallel
#include <vector>    // Dynamic arrays (lists)

namespace simulation {

// Constructor: Saves the user settings (initial price, drift, volatility, etc.)
MonteCarloSimulator::MonteCarloSimulator(const SimulationConfig& config)
    : config_(config) {}

// Main function: Runs the Monte Carlo simulation and returns the results
SimulationResult MonteCarloSimulator::run() const {
    SimulationResult result;
    result.initial_price = config_.initial_price;

    if (config_.num_paths <= 0 || config_.time_steps <= 0) {
        return result;
    }
    
    // Drift term: (mu - 0.5 * sigma^2) * dt
    double drift_term = (config_.drift - 0.5 * config_.volatility * config_.volatility) * config_.dt;

    // Volatility term: sigma * sqrt(dt)
    double vol_term = config_.volatility * std::sqrt(config_.dt);

    // Find how many CPU cores your computer has (e.g., 4 or 8)
    unsigned int num_threads = std::thread::hardware_concurrency();
    if (num_threads == 0) num_threads = 4; // Fallback if detection fails

    int total_paths = config_.num_paths;
    int paths_per_thread = total_paths / num_threads;

    // How many sample paths to save for drawing charts later (e.g., 50 paths)
    int sample_target = std::min(config_.num_sample_paths, total_paths);

    // Temporary storage for each thread's results so they don't overwrite each other
    std::vector<std::vector<double>> thread_final_prices(num_threads);
    std::vector<std::vector<std::vector<double>>> thread_sample_paths(num_threads);

    //Worker class
    auto worker_task = [&](int thread_id, int start_path_idx, int num_paths_to_run) {
        // Each thread gets its own random number generator with a unique seed
        // (This avoids thread collisions and makes random numbers high quality)
        std::mt19937_64 rng(1337 + thread_id * 9999);
        std::normal_distribution<double> bell_curve(0.0, 1.0); // Mean = 0, StdDev = 1

        thread_final_prices[thread_id].reserve(num_paths_to_run);

        // OUTER LOOP: Simulate each path (future scenario)
        for (int i = 0; i < num_paths_to_run; ++i) {
            int global_path_idx = start_path_idx + i;

            bool save_this_path = (global_path_idx < sample_target);

            std::vector<double> single_path_history;
            if (save_this_path) {
                single_path_history.reserve(config_.time_steps + 1);
                single_path_history.push_back(config_.initial_price); // Day 0 price
            }

            double current_price = config_.initial_price;

            // INNER LOOP: Step through each trading day (Day 1 to 252)
            for (int day = 0; day < config_.time_steps; ++day) {

                // Random shock from standard normal bell curve
                double random_shock = bell_curve(rng);

                // Ito's Lemma Formula: updates price to next day
                current_price *= std::exp(drift_term + vol_term * random_shock);

                if (save_this_path) {
                    single_path_history.push_back(current_price);
                }
            }

            // Save the final price at the end of the year (Day 252)
            thread_final_prices[thread_id].push_back(current_price);

            // If we tracked this path for charting, save the whole line
            if (save_this_path) {
                thread_sample_paths[thread_id].push_back(single_path_history);
            }
        }
    };

    std::vector<std::thread> threads;
    int current_offset = 0;

    for (unsigned int t = 0; t < num_threads; ++t) {
        // Last thread takes any remaining paths if 100,000 doesn't divide evenly
        int paths_for_this_thread = (t == num_threads - 1) 
                                      ? (total_paths - current_offset) 
                                      : paths_per_thread;

        // Start worker thread
        threads.emplace_back(worker_task, t, current_offset, paths_for_this_thread);
        current_offset += paths_for_this_thread;
    }

    // Wait for all CPU cores to complete their simulations
    for (auto& t : threads) {
        if (t.joinable()) {
            t.join();
        }
    }

    //Combine results
    result.final_prices.reserve(total_paths);
    result.sample_paths.reserve(sample_target);

    for (unsigned int t = 0; t < num_threads; ++t) {
        // Collect all final prices into one big list
        result.final_prices.insert(
            result.final_prices.end(),
            thread_final_prices[t].begin(),
            thread_final_prices[t].end()
        );

        // Collect the 50 chart lines
        for (auto& path : thread_sample_paths[t]) {
            result.sample_paths.push_back(std::move(path));
        }
    }

    //Calculate metrics
    size_t n = result.final_prices.size();

    // 1. Mean (Average price across all 100,000 futures)
    double sum = std::accumulate(result.final_prices.begin(), result.final_prices.end(), 0.0);
    result.mean_final_price = sum / static_cast<double>(n);

    // 2. Standard Deviation (Spread / volatility of final prices)
    double variance_sum = 0.0;
    for (double price : result.final_prices) {
        variance_sum += (price - result.mean_final_price) * (price - result.mean_final_price);
    }
    result.std_dev_final_price = std::sqrt(variance_sum / static_cast<double>(n));

    // Sort prices from smallest to largest to easily find percentiles
    std::sort(result.final_prices.begin(), result.final_prices.end());

    result.min_final_price = result.final_prices.front(); // Worst outcome
    result.max_final_price = result.final_prices.back();  // Best outcome

    // 3. Percentiles (5th, 25th, 50th/Median, 75th, 95th)
    result.percentile_5  = result.final_prices[static_cast<size_t>(n * 0.05)];
    result.percentile_25 = result.final_prices[static_cast<size_t>(n * 0.25)];
    result.median_final_price = result.final_prices[static_cast<size_t>(n * 0.50)]; // Exact middle
    result.percentile_75 = result.final_prices[static_cast<size_t>(n * 0.75)];
    result.percentile_95 = result.final_prices[static_cast<size_t>(n * 0.95)];

    // 4. Value at Risk (VaR): Maximum dollar loss we expect with 95% confidence
    result.var_95 = std::max(0.0, config_.initial_price - result.percentile_5);

    double percentile_1 = result.final_prices[static_cast<size_t>(n * 0.01)];
    result.var_99 = std::max(0.0, config_.initial_price - percentile_1);

    // 5. Expected Shortfall (CVaR): If the worst 5% crash happens, what is our average loss?
    size_t tail_count_5 = static_cast<size_t>(n * 0.05);
    double tail_loss_sum = 0.0;
    for (size_t i = 0; i < tail_count_5; ++i) {
        tail_loss_sum += std::max(0.0, config_.initial_price - result.final_prices[i]);
    }
    result.expected_shortfall_95 = tail_loss_sum / static_cast<double>(tail_count_5);

    return result;
}

} // namespace simulation
