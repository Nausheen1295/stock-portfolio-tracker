import pandas as pd
import pytest

from stock_portfolio_tracker import (
    PortfolioError,
    build_report,
    load_portfolio,
    portfolio_summary,
    save_portfolio,
)


def sample_holdings():
    return pd.DataFrame(
        [
            {"Stock": "aapl", "Quantity": 10, "Purchase Price": 100},
            {"Stock": "MSFT", "Quantity": 5, "Purchase Price": 200},
        ]
    )


def test_build_report_calculates_value_return_and_allocation():
    report = build_report(sample_holdings(), {"AAPL": 120, "MSFT": 180}.get)

    assert report.loc[0, "Value"] == 1200
    assert report.loc[1, "Profit/Loss"] == -100
    assert report["Allocation (%)"].sum() == pytest.approx(100)


def test_portfolio_summary():
    report = build_report(sample_holdings(), {"AAPL": 120, "MSFT": 180}.get)

    assert portfolio_summary(report) == {
        "cost_basis": 2000.0,
        "value": 2100.0,
        "profit_loss": 100.0,
        "return_percent": 5.0,
    }


def test_invalid_quantity_is_rejected():
    invalid = sample_holdings()
    invalid.loc[0, "Quantity"] = 0

    with pytest.raises(PortfolioError, match="Quantities"):
        build_report(invalid, lambda _: 100)


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "portfolio.csv"
    save_portfolio(sample_holdings(), path)

    loaded = load_portfolio(path)

    assert list(loaded.columns) == ["Stock", "Quantity", "Purchase Price"]
    assert loaded.loc[0, "Stock"] == "AAPL"
