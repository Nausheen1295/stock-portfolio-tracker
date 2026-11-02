# Stock Portfolio Tracker

A Python financial-data application that tracks stock holdings, retrieves the latest available market prices, calculates portfolio performance, and visualizes diversification.

## Features

- CSV import and persistent portfolio storage
- Legacy support for the original `Price` CSV column
- Latest available daily closing prices through `yfinance`
- Cost basis, current value, profit/loss, return, and allocation calculations
- Command-line interface for quick analysis
- Streamlit dashboard with allocation and profit/loss charts
- CSV report download
- Input validation and automated tests

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Use the command line

The CSV file should contain:

```csv
Stock,Quantity,Purchase Price
AAPL,10,180
MSFT,5,400
```

Run the tracker using saved holdings:

```bash
python stock_portfolio_tracker.py --file portfolio.csv
```

If the file does not exist, the application starts interactive data entry.

## Launch the dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard supports CSV upload, portfolio metrics, allocation visualization, profit/loss visualization, and report download.

## Run tests

```bash
pytest
```

## Portfolio project description

> Built a Python financial data application that integrates Yahoo Finance market data, validates and persists portfolio holdings, calculates cost basis and investment performance with Pandas, and provides an interactive Streamlit dashboard for portfolio allocation and profit/loss analysis.

This is an educational tracking and visualization project, not investment advice.
