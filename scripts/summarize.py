"""
summarize.py
raw_news.json を読み込み、Claude API（Haiku）で要約・日本語訳して news.json を生成する
JST 7時の実行時は朝刊ダイジェストも生成する
"""

import os
import json
import re
import time
from datetime import datetime, timezone, timedelta
import anthropic

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
            "出力ルール:\n"
            "- 要約本文のみを出力する（前置き・見出し・ラベルは一切不要）\n"
            "- マークダウン記号（#、*、**、-など）は絶対に使わない\n"
            "- 箇条書きや記号は使わず、自然な文章で書く\n\n"
        )
    else:
        instruction = (
            "以下の英語ニュース記事を日本語に翻訳し、3行以内に要約してください。\n"
            "出力ルール:\n"
            "- 要約本文のみを出力する（前置き・見出し・ラベルは一切不要）\n"
            "- マークダウン記号（#、*、**、-など）は絶対に使わない\n"
            "- 箇条書きや記号は使わず、自然な文章で書く\n\n"
        )
    return instruction + content


def clean_summary(text):
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]*)\*", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-・]\s*", "", text, flags=re.MULTILINE)
    labels = ["翻訳と要約", "タイトル翻訳", "本文翻訳", "本文抜粋", "要約", "タイトル"]
    for label in labels:
        text = text.replace(f"{label}：", "").replace(f"{label}:", "")
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def summarize_article(article):
    try:
        prompt = build_prompt(article)
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = message.content[0].text.strip()
        return clean_summary(summary)
    except Exception as e:
        print(f"[SUMMARIZE ERROR] {article.get('title', '')[:40]}: {e}")
        return clean_summary(article.get("description", "")[:200])


def is_morning_run():
    """JST 7時台の実行かどうかを判定"""
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    return now_jst.hour == 7


def generate_digest(summarized_articles):
    """全ニュースから朝刊ダイジェストを生成"""
    try:
        # 各カテゴリから代表的な記事を集める
        lines = []
        for a in summarized_articles[:20]:  # 最大20件を渡す
            lines.append(f"・[{a['category']}] {a['title']}：{a['summary']}")
        news_text = "\n".join(lines)

        prompt = (
            "以下は今朝のニュース一覧です。この中から特に重要・注目すべきニュースを3つ選び、"
            "それぞれ2〜3文で解説してください。\n"
            "出力ルール:\n"
            "- JSON形式で出力する\n"
            "- マークダウン記号は使わない\n"
            "- 形式: [{\"title\": \"見出し\", \"body\": \"解説文\"}, ...]\n"
            "- JSON以外のテキストは一切出力しない\n\n"
            f"{news_text}"
        )

        message = client.messages.create(
            model=MODEL,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        digest_items = json.loads(raw)
        print(f"✅ 朝刊ダイジェスト生成完了: {len(digest_items)}件")
        return digest_items
    except Exception as e:
        print(f"[DIGEST ERROR] {e}")
        return []


def main():
    base = os.path.join(os.path.dirname(__file__), "..", "docs")
    raw_path = os.path.join(base, "raw_news.json")
    stocks_path = os.path.join(base, "stocks.json")
    out_path = os.path.join(base, "news.json")

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_articles = json.load(f)

    # 既存の要約キャッシュを読み込み
    existing_summaries = {}
    existing_digest = []
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            for a in existing_data.get("news", []):
                existing_summaries[a["url"]] = a.get("summary", "")
            existing_digest = existing_data.get("digest", [])
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

    # 朝刊ダイジェスト（7時の実行時のみ更新）
    if is_morning_run():
        print("\n🌅 朝刊ダイジェストを生成します...")
        digest = generate_digest(summarized)
    else:
        digest = existing_digest
        print(f"\n📋 朝刊ダイジェストは前回のものを使用 ({len(digest)}件)")

    # 株価データ
    stocks = []
    if os.path.exists(stocks_path):
        with open(stocks_path, "r", encoding="utf-8") as f:
            stocks = json.load(f)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "stocks": stocks,
        "digest": digest,
        "news": summarized,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ news.json 生成完了: {len(summarized)}件")


if __name__ == "__main__":
    main()
