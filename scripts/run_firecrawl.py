import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

from pipeline.scrape import scrape

if __name__ == "__main__":
    url = input("請輸入要爬取的網址：\n> ").strip()
    if not url:
        print("未輸入網址，結束。")
        sys.exit(0)
    markdown = scrape(url)
    print("\n" + "=" * 60 + "\n")
    print(markdown)
