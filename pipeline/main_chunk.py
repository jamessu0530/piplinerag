"""
程式二的進入點：依標題將 Markdown 切成 chunks。
互動式輸入檔案路徑後，呼叫 TitleChunker 並寫出結果。

用法（從 piplinerag 目錄）：python -m pipeline.main_chunk
"""

import os
import sys
from pathlib import Path

# 讓從專案根目錄或 pipeline 目錄執行時都能正確 import
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    _pipeline = Path(__file__).resolve().parent
    if str(_pipeline) not in sys.path:
        sys.path.insert(0, str(_pipeline))

from chunk_by_title import TitleChunker


def main() -> None:
    markdown_path = input(
        "請輸入 Markdown 檔案路徑（預設 output/scraped.md）：\n> "
    ).strip()
    if not markdown_path:
        markdown_path = "output/scraped.md"

    if not os.path.exists(markdown_path):
        print(f"檔案不存在：{markdown_path}")
        return

    output_path = input(
        "輸出 JSON 路徑（預設 output/chunks.json）：\n> "
    ).strip()
    if not output_path:
        output_path = "output/chunks.json"

    chunker = TitleChunker()
    chunker.chunk(markdown_path, output_path)


if __name__ == "__main__":
    main()
