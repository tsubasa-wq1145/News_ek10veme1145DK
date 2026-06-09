"""
summarize.py
raw_news.json を読み込み、Claude API（Haiku）で要約・日本語訳して news.json を生成する
"""

import os
import json
import time
import anthropic
from datetime import datetime, timezone

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 400

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def build_prompt(article):
    title = article.get("title", "")
    description = article.get("description", "")
    lang = article.get("lang", "en")

    content = f"タイトル: {title}\n本文抜粋: {description}"

    if lang == "ja":
        instruction = (
            "以下のニュース記事を日本語で3行以内に要約してください。\n"
            "箇条書きや記号は使わず、自然な文章で。\n\n"
        )
    else:
        instruction = (
            "以下の英語ニュース記事を日本語に翻訳し、3行以内に要約してください。\n"
            "箇条書きや記号は使わず、自然な文章で。\n\n"
        )

    return instruction + content


def summarize_article(article):
    try:
        prompt = build_prompt(article)
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = message.content[0].text.strip()
        return summary
    except Exception as e:
        print(f"[SUMMARIZE ERROR] {article.get('title', '')[:40]}: {e}")
        return article.get("description", "")[:200]


def main():
    base = os.path.join(os.path.dirname(__file__), "..", "docs")
    raw_path = os.path.join(base, "raw_news.json")
    stocks_path = os.path.join(base, "stocks.json")
    out_path = os.path.join(base, "news.json")

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_articles = json.load(f)

    existing_summaries = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            for a in existing_data.get("news", []):
                existing_summaries[a["url"]] = a.get("summary", "")
        except Exception:
            pass

    summarized = []
    for i, article in enumerate(raw_articles):
        url = article.get("url", "")

        if url in existing_summaries and existing_summaries[url]:
            summary = existing_summaries[url]
            print(f"[CACHE] ({i+1}/{len(raw_articles)}) {article['title'][:40]}")
        else:
            summary = summarize_article(article)
            print(f"[API]   ({i+1}/{len(raw_articles)}) {article['title'][:40]}")
            time.sleep(0.3)

        summarized.append({
            "id": str(abs(hash(url)))[:8],
            "category": article.get("category", ""),
            "title": article.get("title", ""),
            "summary": summary,
            "url": url,
            "source": article.get("source", ""),
            "published_at": article.get("published_at", ""),
            "lang": article.get("lang", "en"),
        })

    stocks = []
    if os.path.exists(stocks_path):
        with open(stocks_path, "r", encoding="utf-8") as f:
            stocks = json.load(f)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "stocks": stocks,
        "news": summarized,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ news.json 生成完了: {len(summarized)}件")


if __name__ == "__main__":
    main()
