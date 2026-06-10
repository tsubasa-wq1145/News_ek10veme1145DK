"""
fetch_stocks.py
yfinance で株価を取得して stocks.json に保存する
市場が閉まっている場合は直近の終値を表示する
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
        t = yf.Ticker(ticker_def["ticker"])

        # 直近5日分の終値履歴を取得
        # 市場が開いていれば最新値、閉まっていれば直近の終値が末尾に入る
        hist = t.history(period="5d")

        if hist.empty or len(hist) < 2:
            raise ValueError("履歴データが取得できません")

        price = round(float(hist["Close"].iloc[-1]), 2)
        prev_close = round(float(hist["Close"].iloc[-2]), 2)
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
