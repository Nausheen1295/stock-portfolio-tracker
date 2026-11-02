"""Interactive Streamlit dashboard for the stock portfolio tracker."""

from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

from stock_portfolio_tracker import (
    PORTFOLIO_COLUMNS,
    PortfolioError,
    build_report,
    load_portfolio,
    portfolio_summary,
    save_portfolio,
)

DEFAULT_FILE = Path("portfolio.csv")

st.set_page_config(page_title="Stock Portfolio Tracker", page_icon="📈", layout="wide")
st.title("Stock Portfolio Tracker")
st.caption("Market data is provided by Yahoo Finance through yfinance.")

try:
    holdings = load_portfolio(DEFAULT_FILE)
except PortfolioError:
    holdings = None

with st.sidebar:
    st.header("Portfolio holdings")
    uploaded_file = st.file_uploader("Load a CSV", type="csv")
    if uploaded_file is not None:
        import pandas as pd

        uploaded = pd.read_csv(uploaded_file)
        if "Price" in uploaded.columns and "Purchase Price" not in uploaded.columns:
            uploaded = uploaded.rename(columns={"Price": "Purchase Price"})
        try:
            holdings = uploaded[PORTFOLIO_COLUMNS]
            save_portfolio(holdings, DEFAULT_FILE)
            st.success("Portfolio loaded and saved.")
        except (KeyError, PortfolioError) as error:
            st.error(str(error))

if holdings is None:
    st.info("Upload a CSV with Stock, Quantity, and Purchase Price columns to begin.")
    st.stop()

try:
    report = build_report(holdings)
except PortfolioError as error:
    st.error(str(error))
    st.stop()

summary = portfolio_summary(report)
metric_columns = st.columns(4)
metric_columns[0].metric("Current value", f"${summary['value']:,.2f}")
metric_columns[1].metric("Cost basis", f"${summary['cost_basis']:,.2f}")
metric_columns[2].metric("Profit/Loss", f"${summary['profit_loss']:,.2f}")
metric_columns[3].metric("Return", f"{summary['return_percent']:.2f}%")

st.subheader("Holdings")
st.dataframe(
    report.style.format(
        {
            "Purchase Price": "${:,.2f}",
            "Current Price": "${:,.2f}",
            "Cost Basis": "${:,.2f}",
            "Value": "${:,.2f}",
            "Profit/Loss": "${:,.2f}",
            "Return (%)": "{:,.2f}%",
            "Allocation (%)": "{:,.2f}%",
        }
    ),
    use_container_width=True,
)

chart_columns = st.columns(2)
with chart_columns[0]:
    figure, axis = plt.subplots()
    axis.pie(
        report["Allocation (%)"],
        labels=report["Stock"],
        autopct="%1.1f%%",
        startangle=140,
    )
    axis.set_title("Portfolio allocation")
    st.pyplot(figure)
    plt.close(figure)

with chart_columns[1]:
    figure, axis = plt.subplots()
    colors = ["#2ca02c" if value >= 0 else "#d62728" for value in report["Profit/Loss"]]
    axis.bar(report["Stock"], report["Profit/Loss"], color=colors)
    axis.set_title("Profit/Loss by holding")
    axis.set_ylabel("Profit/Loss ($)")
    axis.tick_params(axis="x", rotation=45)
    st.pyplot(figure)
    plt.close(figure)

st.download_button(
    "Download portfolio report",
    report.to_csv(index=False),
    "portfolio_report.csv",
    "text/csv",
)
