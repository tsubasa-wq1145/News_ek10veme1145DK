"""
run_all.py
ニュース取得 → 株価取得 → 要約 の順に実行する
"""

import subprocess
import sys
import os

BASE = os.path.dirname(__file__)


def run(script_name):
    script_path = os.path.join(BASE, script_name)
    print(f"\n{'='*50}")
    print(f"▶ {script_name} を実行中...")
    print("=" * 50)
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=False,
    )
    if result.returncode != 0:
        print(f"❌ {script_name} が失敗しました（終了コード: {result.returncode}）")
        sys.exit(result.returncode)
    print(f"✅ {script_name} 完了")


if __name__ == "__main__":
    run("fetch_news.py")
    run("fetch_stocks.py")
    run("summarize.py")
    print("\n🎉 全処理完了！news.json を更新しました。")
