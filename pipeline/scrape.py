import os
import requests
from dotenv import load_dotenv


def scrape(url: str, output_path: str | None = None) -> str:
    """呼叫 Firecrawl API，回傳 Markdown 字串。若給 output_path 則另存檔。"""
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
            "onlyMainContent": True,
        },
        timeout=120,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Firecrawl API 回傳錯誤 ({resp.status_code}): {resp.text}")

    data = resp.json()
    markdown = data.get("data", {}).get("markdown", "")

    if not markdown:
        raise RuntimeError("Firecrawl 未回傳任何 Markdown 內容")

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"Markdown 已儲存至：{output_path}")
    print(f"共 {len(markdown)} 字元")
    return markdown
