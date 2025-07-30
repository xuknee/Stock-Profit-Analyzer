# Financial Web Scraping & Data Analysis

## Overview

This project provides an automated, end-to-end data pipeline for collecting, cleaning, and analyzing financial market data from leading online sources. It supports real-time data tracking, time-series normalization, strategy backtesting, and interactive visualization. Designed for finance enthusiasts and analysts seeking to automate and scale their data workflows.

## Data Collection

The pipeline scrapes data directly from public financial websites (e.g., Yahoo Finance) using Python scripts.

**To get started:**
1. Ensure you have internet access.
2. Set your desired financial symbols (tickers) in the configuration section of `DataCollection.py`.
3. Run the script to fetch, process, and visualize the latest financial data.

## Requirements

- **Python version:** 3.7 or higher (Python 3.8/3.9/3.10+ recommended)
- **Key Python libraries:**
  - `requests`
  - `beautifulsoup4`
  - `pandas`
  - `numpy`
  - `matplotlib`
  - `seaborn`
- *(Optional: `yfinance`, `ta-lib` for advanced analysis)*

**To install all required libraries, run:**
```bash
pip install requests beautifulsoup4 pandas numpy matplotlib seaborn
