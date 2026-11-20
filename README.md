# Stock Market Data Pipeline

A multi-language (Python + C++) data pipeline for quantitative trading analysis.

## Overview
This project collects real-time stock market data asynchronously using Python, 
applies data quality validation filters, logs high-frequency ticks into PostgreSQL, 
and passes data to a fast C++ Monte Carlo simulation engine.

## Features
- Asynchronous real-time data streaming with missing-field verification.
- Data quality checks using a strict ±10% price variance filter.
- Optimized feature calculations using a sliding window algorithm.
- C++ execution using pybind11 and const pointers.
- Two-tier storage partitioning via PostgreSQL.

## Prerequisites
- Python 3.10+
- CMake 3.15+
- g++ (C++17 compatible)
- PostgreSQL 14+

## Installation
```bash
pip install -r requirements.txt
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

## Usage
```bash
psql -h localhost -U postgres -d stock_db -f database/schema.sql
python main.py
```

## Output
- Charts: `output/simulation_chart.png`
- Database: Managed transactional rows inside PostgreSQL server
- Metrics: `output/metrics_report.txt` and terminal output

## Project Structure
```plaintext
stock_pipeline/
├── CMakeLists.txt
├── requirements.txt
├── main.py
├── archive.py
├── config/
│   └── settings.yaml
├── database/
│   ├── connection.py
│   ├── schema.sql
│   └── archive_job.sql
├── ingestion/
│   ├── data_fetcher.py
│   └── validator.py
├── processing/
│   ├── indicators.py
│   └── lstm_model.py
├── simulation/
│   ├── include/
│   │   └── monte_carlo.hpp
│   └── src/
│       ├── bindings.cpp
│       └── monte_carlo.cpp
└── output/
```

## Future Improvements
- Add more stocks to the active tracking matrix.
- Add live alert notifications via webhooks.
- Integrate Apache Kafka as a message buffer.
- Add a Java dashboard graphical interface.