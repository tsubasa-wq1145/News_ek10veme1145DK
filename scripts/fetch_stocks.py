"""
fetch_stocks.py
yfinance で株価4指数を取得して stocks.json に保存する
"""

import os
import json
import yfinance as yf
from datetime import datetime, timezone

TICKERS = [
    {"id": "nikkei",  "name": "日経225",  "ticker": "^N225"},
    {"id": "topix",   "name": "TOPIX",    "ticker": "^TPX"},
    {"id": "dow",     "name": "NYダウ",   "ticker": "^DJI"},
    {"id": "nasdaq",  "name": "NASDAQ",   "ticker": "^IXIC"},
]


def fetch_stock(ticker_def):
    try:
        t = yf.Ticker(ticker_def["ticker"])
        info = t.fast_info

        price = round(float(info.last_price), 2)
        prev_close = round(float(info.previous_close), 2)
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
        direction = "↑" if stock["direction"] == "up" else "↓"
        print(f"[株価] {stock['name']}: {stock['price']} {direction}{stock['change_pct']}%")

    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "stocks.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)
    print(f"保存完了: {out_path}")


if __name__ == "__main__":
    main()
