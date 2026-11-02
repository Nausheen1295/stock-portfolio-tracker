"""Stock portfolio tracker with CSV persistence and market-data integration."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import pandas as pd
import yfinance as yf

PORTFOLIO_COLUMNS = ["Stock", "Quantity", "Purchase Price"]
REPORT_COLUMNS = [
    "Stock",
    "Quantity",
    "Purchase Price",
    "Current Price",
    "Cost Basis",
    "Value",
    "Profit/Loss",
    "Return (%)",
    "Allocation (%)",
]


class PortfolioError(ValueError):
    """Raised when portfolio data is invalid."""


def get_stock_price(ticker: str) -> float:
    """Return the latest available closing price for a ticker."""
    symbol = ticker.strip().upper()
    if not symbol:
        raise PortfolioError("Ticker symbol cannot be empty.")

    try:
        history = yf.Ticker(symbol).history(period="5d", auto_adjust=False)
    except Exception as error:
        raise PortfolioError(f"Unable to fetch price for {symbol}: {error}") from error

    if history.empty or "Close" not in history:
        raise PortfolioError(f"No market data was returned for {symbol}.")

    prices = pd.to_numeric(history["Close"], errors="coerce").dropna()
    if prices.empty or float(prices.iloc[-1]) <= 0:
        raise PortfolioError(f"No valid price was returned for {symbol}.")
    return float(prices.iloc[-1])


def validate_portfolio(data: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize portfolio holdings."""
    required = set(PORTFOLIO_COLUMNS)
    missing = required - set(data.columns)
    if missing:
        raise PortfolioError(f"Missing required columns: {', '.join(sorted(missing))}.")

    holdings = data[PORTFOLIO_COLUMNS].copy()
    holdings["Stock"] = holdings["Stock"].astype(str).str.strip().str.upper()
    holdings["Quantity"] = pd.to_numeric(holdings["Quantity"], errors="coerce")
    holdings["Purchase Price"] = pd.to_numeric(
        holdings["Purchase Price"], errors="coerce"
    )
    if holdings.empty:
        raise PortfolioError("The portfolio has no holdings.")
    if holdings["Stock"].eq("").any() or holdings["Stock"].eq("NAN").any():
        raise PortfolioError("Ticker symbols cannot be empty.")
    if holdings["Quantity"].isna().any() or (holdings["Quantity"] <= 0).any():
        raise PortfolioError("Quantities must be positive numbers.")
    if holdings["Purchase Price"].isna().any() or (
        holdings["Purchase Price"] <= 0
    ).any():
        raise PortfolioError("Purchase prices must be positive numbers.")
    return holdings.reset_index(drop=True)


def load_portfolio(path: str | Path) -> pd.DataFrame:
    """Load holdings from CSV, including the original legacy format."""
    file_path = Path(path)
    if not file_path.exists():
        raise PortfolioError(f"Portfolio file does not exist: {file_path}")
    data = pd.read_csv(file_path)
    if "Purchase Price" not in data.columns and "Price" in data.columns:
        data = data.rename(columns={"Price": "Purchase Price"})
    data = data.loc[data["Stock"].astype(str).str.upper() != "TOTAL INVESTMENT"]
    return validate_portfolio(data)


def save_portfolio(data: pd.DataFrame, path: str | Path) -> None:
    """Validate and save holdings to CSV."""
    holdings = validate_portfolio(data)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    holdings.to_csv(path, index=False)


def build_report(
    holdings: pd.DataFrame,
    price_lookup: Callable[[str], float] = get_stock_price,
) -> pd.DataFrame:
    """Build valuation, return, and allocation metrics for each holding."""
    holdings = validate_portfolio(holdings)
    report = holdings.copy()
    report["Current Price"] = report["Stock"].map(price_lookup)
    report["Cost Basis"] = report["Quantity"] * report["Purchase Price"]
    report["Value"] = report["Quantity"] * report["Current Price"]
    report["Profit/Loss"] = report["Value"] - report["Cost Basis"]
    report["Return (%)"] = report["Profit/Loss"] / report["Cost Basis"] * 100
    total_value = report["Value"].sum()
    report["Allocation (%)"] = (
        report["Value"] / total_value * 100 if total_value else 0
    )
    return report[REPORT_COLUMNS]


def portfolio_summary(report: pd.DataFrame) -> dict[str, float]:
    """Return aggregate portfolio metrics from a report."""
    cost_basis = float(report["Cost Basis"].sum())
    value = float(report["Value"].sum())
    profit_loss = value - cost_basis
    return {
        "cost_basis": cost_basis,
        "value": value,
        "profit_loss": profit_loss,
        "return_percent": profit_loss / cost_basis * 100 if cost_basis else 0,
    }


def run_cli(path: str | Path) -> None:
    """Run the interactive command-line tracker."""
    try:
        holdings = load_portfolio(path) if Path(path).exists() else collect_holdings()
        report = build_report(holdings)
    except PortfolioError as error:
        print(f"Error: {error}")
        return

    print("\nPortfolio Summary")
    print(report.to_string(index=False, float_format=lambda value: f"{value:,.2f}"))
    summary = portfolio_summary(report)
    print(f"\nCurrent value: ${summary['value']:,.2f}")
    print(f"Profit/Loss: ${summary['profit_loss']:,.2f}")
    print(f"Return: {summary['return_percent']:.2f}%")


def collect_holdings() -> pd.DataFrame:
    """Collect and validate holdings interactively."""
    while True:
        try:
            count = int(input("Enter the number of holdings: "))
            if count <= 0:
                raise ValueError("number of holdings must be greater than zero")
            break
        except ValueError as error:
            print(f"Invalid input: {error}")

    rows = []
    for index in range(count):
        while True:
            try:
                stock = input(f"Ticker for holding {index + 1}: ").strip().upper()
                quantity = float(input(f"Quantity of {stock}: "))
                purchase_price = float(input(f"Purchase price of {stock}: $"))
                row = pd.DataFrame(
                    [{"Stock": stock, "Quantity": quantity, "Purchase Price": purchase_price}]
                )
                rows.append(validate_portfolio(row).iloc[0].to_dict())
                break
            except (ValueError, PortfolioError) as error:
                print(f"Invalid holding: {error}")
    return pd.DataFrame(rows, columns=PORTFOLIO_COLUMNS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file",
        default="portfolio.csv",
        help="CSV file containing Stock, Quantity, and Purchase Price columns.",
    )
    run_cli(parser.parse_args().file)
