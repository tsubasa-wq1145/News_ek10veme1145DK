"""
fetch_news.py
RSS フィード + NewsAPI からニュースを取得して raw_news.json に保存する
"""

import os
import json
import feedparser
import requests
from datetime import datetime, timezone
from dateutil import parser as dateparser

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")

RSS_FEEDS = {
    "経済・ビジネス（日本）": [
        "https://www3.nhk.or.jp/rss/news/cat6.xml",
        "https://feeds.bloomberg.co.jp/bloomberg/economics",
    ],
    "経済・ビジネス（世界）": [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.bbci.co.uk/news/business/rss.xml",
    ],
   "台湾・中台関係": [
        "https://focustaiwan.tw/rss/cross-strait.xml",
        "https://focustaiwan.tw/rss/politics.xml",
        "https://focustaiwan.tw/rss/business.xml",
        "https://www.rfa.org/english/news/taiwan/rss",
        "https://www.rfa.org/english/news/china/rss",
    ],
    "テクノロジー・AI": [
        "https://techcrunch.com/feed/",
        "https://feeds.feedburner.com/technologyreview/frdm",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    ],
}

NEWS_API_QUERIES = [
    {
        "category": "台湾・中台関係",
        "q": "Taiwan AND (China OR military OR strait OR Taipei OR cross-strait)",
        "language": "en",
    },
    {
        "category": "テクノロジー・AI",
        "q": "artificial intelligence OR generative AI",
        "language": "en",
    },
]

MAX_PER_CATEGORY = 8


def parse_date(date_str):
    try:
        dt = dateparser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def fetch_rss(category, urls):
    articles = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
            source = feed.feed.get("title", url)
            for entry in feed.entries[:MAX_PER_CATEGORY]:
                articles.append({
                    "category": category,
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "source": source,
                    "published_at": parse_date(entry.get("published", "")),
                    "description": entry.get("summary", ""),
                    "lang": "ja" if "nhk" in url or "bloomberg.co.jp" in url else "en",
                })
        except Exception as e:
            print(f"[RSS ERROR] {url}: {e}")
    return articles


def fetch_newsapi(query_def):
    if not NEWS_API_KEY:
        print("[NewsAPI] APIキーが設定されていないためスキップ")
        return []
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query_def["q"],
                "language": query_def["language"],
                "pageSize": MAX_PER_CATEGORY,
                "sortBy": "publishedAt",
                "apiKey": NEWS_API_KEY,
            },
            timeout=10,
        )
        data = resp.json()
        articles = []
        for item in data.get("articles", []):
            if item.get("title") == "[Removed]":
                continue
            articles.append({
                "category": query_def["category"],
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": item.get("source", {}).get("name", "NewsAPI"),
                "published_at": parse_date(item.get("publishedAt", "")),
                "description": item.get("description", ""),
                "lang": query_def["language"],
            })
        return articles
    except Exception as e:
        print(f"[NewsAPI ERROR] {e}")
        return []


def deduplicate(articles):
    seen = set()
    result = []
    for a in articles:
        if a["url"] not in seen and a["url"]:
            seen.add(a["url"])
            result.append(a)
    return result


def main():
    all_articles = []

    for category, urls in RSS_FEEDS.items():
        articles = fetch_rss(category, urls)
        all_articles.extend(articles)
        print(f"[RSS] {category}: {len(articles)}件取得")

    for q in NEWS_API_QUERIES:
        articles = fetch_newsapi(q)
        all_articles.extend(articles)
        print(f"[NewsAPI] {q['category']}: {len(articles)}件取得")

    all_articles = deduplicate(all_articles)

    from collections import defaultdict
    by_category = defaultdict(list)
    for a in all_articles:
        by_category[a["category"]].append(a)

    limited = []
    for cat, arts in by_category.items():
        arts.sort(key=lambda x: x["published_at"], reverse=True)
        limited.extend(arts[:MAX_PER_CATEGORY])

    print(f"\n合計: {len(limited)}件（重複除去・件数制限後）")

    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "raw_news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(limited, f, ensure_ascii=False, indent=2)
    print(f"保存完了: {out_path}")


if __name__ == "__main__":
    main()
