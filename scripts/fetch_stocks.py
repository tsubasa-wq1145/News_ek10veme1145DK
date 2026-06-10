"""
fetch_stocks.py
yfinance で株価を取得して stocks.json に保存する
"""

import os
import json
import yfinance as yf
from datetime import datetime, timezone

TICKERS = [
    {"id": "nikkei",  "name": "日経225",  "ticker": "^N225"},
    {"id": "topix",   "name": "TOPIX",    "ticker": "^TPX"},
    {"id": "jpx",     "name": "JPX",      "ticker": "8697.T"},
    {"id": "dow",     "name": "NYダウ",   "ticker": "^DJI"},
    {"id": "nasdaq",  "name": "NASDAQ",   "ticker": "^IXIC"},
]


def fetch_stock(ticker_def):
    try:
        df = yf.download(
            ticker_def["ticker"],
            period="5d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )

        if df is None or len(df) < 2:
            raise ValueError("データ不足")

        price = round(float(df["Close"].iloc[-1]), 2)
        prev_close = round(float(df["Close"].iloc[-2]), 2)
        change = round(price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2)

        return {
            "id": ticker_def["id"],
            "name": ticker_def["name"],
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "direction": "up" if change >= 0 else "down",
        }
    except Exception as e:
        print(f"[STOCK ERROR] {ticker_def['name']}: {e}")
        return {
            "id": ticker_def["id"],
            "name": ticker_def["name"],
            "price": None,
            "change": None,
            "change_pct": None,
            "direction": "flat",
        }


def main():
    stocks = []
    for t in TICKERS:
        stock = fetch_stock(t)
        stocks.append(stock)
        direction = "↑" if stock["direction"] == "up" else "↓" if stock["direction"] == "down" else "-"
        print(f"[株価] {stock['name']}: {stock['price']} {direction}{stock['change_pct']}%")

    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "stocks.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)
    print(f"保存完了: {out_path}")


if __name__ == "__main__":
    main()
