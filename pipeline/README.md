# Pipeline：爬蟲 + 依標題分段

## 環境設定（虛擬環境）

專案已內建虛擬環境 `.venv`，請先啟用再執行程式：

```bash
cd piplinerag
source .venv/bin/activate   # macOS / Linux
# 或 Windows:  .venv\Scripts\activate

pip install -r requirements.txt
```

之後執行爬蟲或分段時，**請用虛擬環境的 Python**（二選一）：

- **有先啟用 venv 時：** 用 `python`（不要用 `python3`，否則會用到系統 Python）
- **不想啟用時：** 直接用  
  `./.venv/bin/python pipeline/scrape.py`  
  `./.venv/bin/python -m pipeline.main_chunk`

## 程式一：爬蟲（Firecrawl）

- **腳本：** `scrape.py`
- **執行：** 從 `piplinerag` 目錄執行  
  `./.venv/bin/python pipeline/scrape.py`  
  或先 `source .venv/bin/activate` 再用 `python pipeline/scrape.py`。  
  輸入網址後，Markdown 會存到 `output/scraped.md`（可自訂）。

## 程式二：依標題分段（Gemma）

- **模組：** `chunk_by_title.py`（`TitleChunker` 類別）
- **互動式主程式：** `main_chunk.py`

**執行主程式：**

```bash
cd piplinerag
./.venv/bin/python -m pipeline.main_chunk
```
（若已 `source .venv/bin/activate`，可改為 `python -m pipeline.main_chunk`）

或先進入 pipeline 再執行：

```bash
cd piplinerag/pipeline
python main_chunk.py
```

依提示輸入 Markdown 檔案路徑與輸出 JSON 路徑即可。

---

## 如何測試

### 1. 單元／整合測試（不開 Ollama）

在測試裡 mock `_call_gemma`，只驗證「給定假回傳，能正確解析成 chunks」：

```python
# tests/test_chunk_by_title.py（範例）
import pytest
from pipeline.chunk_by_title import TitleChunker, Chunk

def test_extract_chunks_without_ollama():
    chunker = TitleChunker()
    # 用 monkeypatch 或 patch 替換 chunker._call_gemma
    fake_response = '''[
        {"title": "標題一", "text": "內文一"},
        {"title": "標題二", "text": "內文二"}
    ]'''
    chunks = chunker._parse_segment("")  # 需要改為可注入 response，或直接測 _extract_json
    # 或直接測 chunk_from_text，並 mock requests.post
```

較簡單的方式：只測「純解析邏輯」與「分段邏輯」，不呼叫 Ollama。例如在專案裡加一個 `tests/test_chunk_by_title.py`，用 `unittest.mock.patch` 把 `TitleChunker._call_gemma` 改成回傳固定 JSON，再檢查 `chunk_from_text` 回傳的 `list[Chunk]` 是否正確。

### 2. 手動端對端測試（需 Ollama + Gemma）

1. **確認 Ollama 與模型：**
   ```bash
   ollama list
   # 需有 gemma3:4b（或你在 .env 設的 GEMMA_MODEL）
   ollama serve   # 若尚未在背景執行
   ```

2. **準備一份 Markdown：**
   - 先跑程式一：`python pipeline/scrape.py`，輸入任一網址，產生 `output/scraped.md`  
   - 或手動建一個 `output/test.md`，內容幾段帶標題的 Markdown 即可。

3. **跑程式二：**
   ```bash
   cd piplinerag
   python -m pipeline.main_chunk
   ```
   - Markdown 路徑輸入：`output/scraped.md` 或 `output/test.md`
   - 輸出 path 可直接 Enter 用預設 `output/chunks.json`

4. **檢查結果：**
   - 終端會印出每個 chunk 的 title 與文字預覽。
   - 打開 `output/chunks.json`，確認每個元素都是 `{"title": "...", "text": "..."}` 且內容合理。

### 3. 在 Python REPL 裡快速試

```bash
cd piplinerag
python
```

```python
from pipeline.chunk_by_title import TitleChunker

chunker = TitleChunker()
# 檢查設定（預設應為 gemma3:4b）
print(chunker.model)   # gemma3:4b
print(chunker.ollama_url)

# 用一小段文字測試（會真的呼叫 Ollama）
md = """
# 第一章
這是第一段內容。

## 第二章
這是第二段內容。
"""
chunks = chunker.chunk_from_text(md)
for c in chunks:
    print(c["title"], "->", c["text"][:50])
```

這樣就完成「改預設模型、OOP、main 獨立」以及測試方式說明。
