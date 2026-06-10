"""
fetch_stocks.py
Alpha Vantage API で株価を取得して stocks.json に保存する
"""

import os
import json
import time
import requests
from datetime import datetime, timezone

ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")

TICKERS = [
    {"id": "nikkei",  "name": "日経225",  "symbol": "^N225",   "av_symbol": "N225",    "market": "JP"},
    {"id": "topix",   "name": "TOPIX",    "symbol": "^TPX",    "av_symbol": "TOPX",    "market": "JP"},
    {"id": "jpx",     "name": "JPX",      "symbol": "8697.T",  "av_symbol": "8697.TYO","market": "JP"},
    {"id": "dow",     "name": "NYダウ",   "symbol": "^DJI",    "av_symbol": "DJI",     "market": "US"},
    {"id": "nasdaq",  "name": "NASDAQ",   "symbol": "^IXIC",   "av_symbol": "COMP",    "market": "US"},
]

BASE_URL = "https://www.alphavantage.co/query"


def fetch_stock(ticker_def):
    try:
        # GLOBAL_QUOTE で最新の終値・前日比を取得
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker_def["av_symbol"],
            "apikey": ALPHA_VANTAGE_KEY,
        }
        resp = requests.get(BASE_URL, params=params, timeout=15)
        data = resp.json()

        quote = data.get("Global Quote", {})
        if not quote or not quote.get("05. price"):
            raise ValueError(f"データなし: {data}")

        price = round(float(quote["05. price"]), 2)
        change = round(float(quote["09. change"]), 2)
        change_pct_str = quote["10. change percent"].replace("%", "")
        change_pct = round(float(change_pct_str), 2)

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
    for i, t in enumerate(TICKERS):
        stock = fetch_stock(t)
        stocks.append(stock)
        direction = "↑" if stock["direction"] == "up" else "↓"
        print(f"[株価] {stock['name']}: {stock['price']} {direction}{stock['change_pct']}%")
        # Alpha Vantage 無料枠はリクエスト間隔を空ける必要あり
        if i < len(TICKERS) - 1:
            time.sleep(15)

    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "stocks.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)
    print(f"保存完了: {out_path}")


if __name__ == "__main__":
    main()
