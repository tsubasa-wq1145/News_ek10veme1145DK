"""
fetch_stocks.py
Stooq API で株価を取得して stocks.json に保存する
登録不要・APIキー不要
"""

import os
import json
import requests
from datetime import datetime, timezone

TICKERS = [
    {"id": "nikkei",  "name": "日経225",  "symbol": "^nkx"},
    {"id": "topix",   "name": "TOPIX",    "symbol": "^tpx"},
    {"id": "jpx",     "name": "JPX",      "symbol": "8697.jp"},
    {"id": "dow",     "name": "NYダウ",   "symbol": "^dji"},
    {"id": "nasdaq",  "name": "NASDAQ",   "symbol": "^ndq"},
]


def fetch_stock(ticker_def):
    try:
        url = f"https://stooq.com/q/l/?s={ticker_def['symbol']}&f=sd2t2ohlcv&h&e=csv"
        resp = requests.get(url, timeout=10)
        lines = resp.text.strip().split("\n")

        if len(lines) < 2:
            raise ValueError("データなし")

        cols = lines[1].split(",")
        # 列: Symbol,Date,Time,Open,High,Low,Close,Volume
        if len(cols) < 7:
            raise ValueError(f"列数不足: {cols}")

        price = round(float(cols[6]), 2)
        open_price = round(float(cols[3]), 2)
        change = round(price - open_price, 2)
        change_pct = round((change / open_price) * 100, 2) if open_price else 0

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
