"""
程式一：使用 Firecrawl API 爬取指定網頁，將結果以 Markdown 格式存檔。
用法：python pipeline/scrape.py
"""

import os
import json
import requests
from dotenv import load_dotenv


def scrape(url: str, output_path: str = "output/scraped.md") -> str:
    """呼叫 Firecrawl API，將網頁轉成 Markdown 並存檔。"""
    load_dotenv()

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise RuntimeError("請在 .env 中設定 FIRECRAWL_API_KEY")

    print(f"正在爬取：{url} ...")

    resp = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "url": url,
            "formats": ["markdown"],
        },
        timeout=120,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Firecrawl API 回傳錯誤 ({resp.status_code}): {resp.text}")

    data = resp.json()
    markdown = data.get("data", {}).get("markdown", "")

    if not markdown:
        raise RuntimeError("Firecrawl 未回傳任何 Markdown 內容")

    # 確保輸出目錄存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Markdown 已儲存至：{output_path}")
    print(f"共 {len(markdown)} 字元")
    return output_path


def main():
    url = input("請輸入要爬取的網址：\n> ").strip()
    if not url:
        print("未輸入網址，程式結束。")
        return

    output_path = input("輸出檔案路徑（預設 output/scraped.md）：\n> ").strip()
    if not output_path:
        output_path = "output/scraped.md"

    scrape(url, output_path)


if __name__ == "__main__":
    main()
