import sys
from pathlib import Path

if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    _pipeline = Path(__file__).resolve().parent
    for p in (_root, _pipeline):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

from scrape import scrape
from chunk_by_title import TitleChunker


def main() -> None:
    url = input("請輸入要爬取的網址：\n> ").strip()
    if not url:
        print("未輸入網址，程式結束。")
        return

    print(f"\n正在爬取 {url} ...")
    markdown_text = scrape(url)

    print(f"\n正在用 Gemma 切 chunk...")
    chunker = TitleChunker()
    chunks = chunker.chunk_from_text(markdown_text)
    
    print(f"\n共切出 {len(chunks)} 個 chunks\n")
    print("=" * 60)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n[Chunk {i}]")
        print(f"Title: {chunk['title']}")
        print(f"Text: {chunk['text']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
