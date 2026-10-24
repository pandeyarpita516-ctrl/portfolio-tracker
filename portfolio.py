#!/usr/bin/env python3
"""Stock Portfolio Performance Tracker (console).

- Enter ticker, buy price and number of shares for each holding.
- Current prices come from 'prices.csv' (next to this script) if present,
  otherwise from a built-in sample table. Unknown tickers: you type the price.
- Shows value and % gain/loss per holding and for the whole portfolio.
- Appends a timestamped summary to 'portfolio_summary.csv'.

Standard library only (csv, os, datetime).
"""

import csv
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRICES_FILE = os.path.join(BASE_DIR, "prices.csv")
SUMMARY_FILE = os.path.join(BASE_DIR, "portfolio_summary.csv")

# Sample prices (illustrative only, not live data)
SAMPLE_PRICES = {
    "AAPL": 190.00, "MSFT": 410.00, "GOOGL": 150.00, "AMZN": 180.00,
    "TSLA": 240.00, "META": 480.00, "NVDA": 900.00, "NFLX": 600.00,
    "JPM": 195.00, "KO": 60.00,
}

SYMBOL_COLUMNS = ("symbol", "ticker")
PRICE_COLUMNS = ("price", "current price", "close", "last", "last price")


def load_prices():
    """Load {ticker: price} from prices.csv, else return the sample table."""
    prices = {}
    try:
        with open(PRICES_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cols = {c.strip().lower(): c for c in (reader.fieldnames or [])}
            sym_col = next((cols[c] for c in SYMBOL_COLUMNS if c in cols), None)
            price_col = next((cols[c] for c in PRICE_COLUMNS if c in cols), None)
            if sym_col and price_col:
                for row in reader:
                    try:
                        prices[row[sym_col].strip().upper()] = float(row[price_col])
                    except (ValueError, AttributeError):
                        continue  # skip rows with bad data
    except OSError:
        pass
    return prices or dict(SAMPLE_PRICES)


def ask_positive_number(prompt):
    """Keep asking until the user types a number greater than 0."""
    while True:
        raw = input(prompt).strip().replace(",", "")
        try:
            value = float(raw)
            if value > 0:
                return value
            print("  Value must be greater than 0.")
        except ValueError:
            print("  Please enter a valid number.")


def add_position(portfolio):
    """Ask for one holding and store it in the portfolio dictionary."""
    ticker = input("Ticker symbol (e.g. AAPL): ").strip().upper()
    if not ticker.isalpha():
        print("  Ticker must contain letters only.")
        return
    buy_price = ask_positive_number("Buy price per share: ")
    shares = ask_positive_number("Number of shares: ")

    if ticker in portfolio:  # same stock bought again -> average the price
        old = portfolio[ticker]
        total_shares = old["shares"] + shares
        avg = (old["shares"] * old["buy_price"] + shares * buy_price) / total_shares
        portfolio[ticker] = {"shares": total_shares, "buy_price": avg}
        print(f"  Updated {ticker}: {total_shares:g} shares @ avg {avg:.2f}")
    else:
        portfolio[ticker] = {"shares": shares, "buy_price": buy_price}
        print(f"  Added {ticker}.")


def get_current_price(ticker, prices):
    """Look up the price; if missing, ask the user and remember it."""
    if ticker not in prices:
        print(f"  No price found for {ticker}.")
        prices[ticker] = ask_positive_number(f"  Enter current price for {ticker}: ")
    return prices[ticker]


def calculate(portfolio, prices):
    """Return (rows, total_invested, total_value)."""
    rows = []
    total_invested = total_value = 0.0
    for ticker, pos in portfolio.items():
        current = get_current_price(ticker, prices)
        invested = pos["shares"] * pos["buy_price"]
        value = pos["shares"] * current
        gain = value - invested
        pct = gain / invested * 100
        rows.append({
            "ticker": ticker, "shares": pos["shares"],
            "buy_price": pos["buy_price"], "current_price": current,
            "invested": invested, "value": value, "gain": gain, "pct": pct,
        })
        total_invested += invested
        total_value += value
    return rows, total_invested, total_value


def print_report(rows, total_invested, total_value):
    line = "-" * 86
    print("\n" + "=" * 86)
    print("PORTFOLIO PERFORMANCE REPORT".center(86))
    print("=" * 86)
    print(f"{'Ticker':<8}{'Shares':>8}{'Buy':>10}{'Now':>10}"
          f"{'Invested':>13}{'Value':>13}{'Gain/Loss':>13}{'%':>9}")
    print(line)
    for r in rows:
        print(f"{r['ticker']:<8}{r['shares']:>8g}{r['buy_price']:>10.2f}"
              f"{r['current_price']:>10.2f}{r['invested']:>13,.2f}"
              f"{r['value']:>13,.2f}{r['gain']:>+13,.2f}{r['pct']:>+8.2f}%")
    print(line)
    total_gain = total_value - total_invested
    total_pct = total_gain / total_invested * 100 if total_invested else 0.0
    print(f"{'TOTAL':<8}{'':>8}{'':>10}{'':>10}{total_invested:>13,.2f}"
          f"{total_value:>13,.2f}{total_gain:>+13,.2f}{total_pct:>+8.2f}%")
    print("=" * 86)
    status = "PROFIT" if total_gain > 0 else "LOSS" if total_gain < 0 else "BREAK-EVEN"
    print(f"Overall status: {status}")


def save_summary(rows, total_invested, total_value):
    """Append this run to portfolio_summary.csv (header written once)."""
    is_new = not os.path.exists(SUMMARY_FILE)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = ["timestamp", "ticker", "shares", "buy_price", "current_price",
              "invested", "current_value", "gain_loss", "gain_loss_pct"]
    try:
        with open(SUMMARY_FILE, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if is_new:
                w.writerow(fields)
            for r in rows:
                w.writerow([stamp, r["ticker"], f"{r['shares']:g}",
                            f"{r['buy_price']:.2f}", f"{r['current_price']:.2f}",
                            f"{r['invested']:.2f}", f"{r['value']:.2f}",
                            f"{r['gain']:.2f}", f"{r['pct']:.2f}"])
            gain = total_value - total_invested
            pct = gain / total_invested * 100 if total_invested else 0.0
            w.writerow([stamp, "TOTAL", "", "", "", f"{total_invested:.2f}",
                        f"{total_value:.2f}", f"{gain:.2f}", f"{pct:.2f}"])
        print(f"Summary saved to: {SUMMARY_FILE}")
    except OSError as err:
        print(f"Could not write CSV file: {err}")


def main():
    print("=" * 40)
    print("  STOCK PORTFOLIO PERFORMANCE TRACKER")
    print("=" * 40)
    prices = load_prices()
    portfolio = {}

    while True:
        add_position(portfolio)
        if input("Add another stock? (y/n): ").strip().lower() != "y":
            break

    if not portfolio:
        print("No holdings entered. Goodbye!")
        return
    rows, invested, value = calculate(portfolio, prices)
    print_report(rows, invested, value)
    save_summary(rows, invested, value)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
