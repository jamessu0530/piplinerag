"""
使用 Gemma 模型（透過 Ollama）辨識 Markdown 中的段落標題，
將內容切成 title + text 的 chunks。

可作為模組被 main 或測試程式匯入使用。
"""

import os
import json
import re
import requests
from dotenv import load_dotenv
from typing import TypedDict


class Chunk(TypedDict):
    title: str
    text: str


SYSTEM_PROMPT = """你是一個專業的文件結構分析助手。
你的任務是分析使用者提供的 Markdown 文字，辨識出每個段落的「標題 (title)」以及其對應的「內文 (text)」。

規則：
1. 每一個段落必須有一個 title 和一個 text。
2. title 是段落的主題或標題（可能是 Markdown 的 # ## ### 標題，也可能是粗體文字、或段落開頭的關鍵句）。
3. text 是該 title 底下的所有內容文字（不包含 title 本身）。
4. 如果某段文字沒有明確標題，請根據內容自行產生一個簡短的描述性標題。
5. 保持原文內容完整，不要省略或修改任何原文。

請以下列 JSON 格式回傳結果，只回傳 JSON，不要加任何其他文字：
[
  {
    "title": "段落標題",
    "text": "段落內文..."
  },
  ...
]"""


def _extract_json_from_response(response_text: str) -> list:
    """從模型回應中提取 JSON 陣列。"""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    start = response_text.find("[")
    end = response_text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(response_text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise RuntimeError(
        f"無法從模型回應中解析 JSON。\n原始回應：\n{response_text[:500]}"
    )


def _split_markdown_roughly(text: str, max_size: int) -> list[str]:
    """將過長的 Markdown 粗略分段。"""
    segments: list[str] = []
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_size and current.strip():
            segments.append(current)
            current = ""
        current += line + "\n"

    if current.strip():
        segments.append(current)

    return segments


class TitleChunker:
    """使用 Gemma 模型將 Markdown 依標題切成 title + text 的 chunks。"""

    DEFAULT_OLLAMA_URL = "http://localhost:11434"
    DEFAULT_MODEL = "gemma3:4b"
    DEFAULT_MAX_SEGMENT_SIZE = 6000

    def __init__(
        self,
        ollama_url: str | None = None,
        model: str | None = None,
        max_segment_size: int | None = None,
    ):
        load_dotenv()
        self.ollama_url = ollama_url or os.getenv(
            "OLLAMA_BASE_URL", self.DEFAULT_OLLAMA_URL
        )
        self.model = model or os.getenv("GEMMA_MODEL", self.DEFAULT_MODEL)
        self.max_segment_size = max_segment_size or self.DEFAULT_MAX_SEGMENT_SIZE

    def _call_gemma(self, markdown_text: str) -> str:
        """呼叫 Ollama API，取得模型回傳內容。"""
        resp = requests.post(
            f"{self.ollama_url.rstrip('/')}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"請分析以下 Markdown 文字，辨識段落標題與內文：\n\n{markdown_text}",
                    },
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 8192,
                },
            },
            timeout=300,
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Ollama API 錯誤 ({resp.status_code}): {resp.text}")

        return resp.json().get("message", {}).get("content", "")

    def _parse_segment(self, segment: str) -> list[Chunk]:
        """對一段 Markdown 呼叫模型並解析成 chunks。"""
        response = self._call_gemma(segment)
        raw_chunks = _extract_json_from_response(response)
        chunks: list[Chunk] = []

        for item in raw_chunks:
            if "title" not in item or "text" not in item:
                continue
            chunks.append(
                Chunk(
                    title=str(item["title"]).strip(),
                    text=str(item["text"]).strip(),
                )
            )

        return chunks

    def chunk_from_text(self, markdown_text: str) -> list[Chunk]:
        """
        從 Markdown 字串產生 chunks（不讀寫檔案，方便測試）。
        """
        if len(markdown_text) <= self.max_segment_size:
            segments = [markdown_text]
        else:
            segments = _split_markdown_roughly(
                markdown_text, self.max_segment_size
            )

        all_chunks: list[Chunk] = []
        for segment in segments:
            all_chunks.extend(self._parse_segment(segment))
        return all_chunks

    def chunk(
        self,
        markdown_path: str,
        output_path: str = "output/chunks.json",
        *,
        print_preview: bool = True,
    ) -> list[Chunk]:
        """
        讀取 Markdown 檔案，產生 chunks 並寫入 output_path。
        回傳產生的 chunks 列表。
        """
        with open(markdown_path, "r", encoding="utf-8") as f:
            markdown_text = f.read()

        print(f"讀取 Markdown 檔案：{markdown_path}（{len(markdown_text)} 字元）")

        if len(markdown_text) <= self.max_segment_size:
            segments = [markdown_text]
        else:
            segments = _split_markdown_roughly(
                markdown_text, self.max_segment_size
            )
            print(f"文字過長，已分成 {len(segments)} 段分別處理")

        all_chunks: list[Chunk] = []
        for i, segment in enumerate(segments):
            print(f"正在處理第 {i + 1}/{len(segments)} 段...")
            all_chunks.extend(self._parse_segment(segment))

        print(f"\n共產生 {len(all_chunks)} 個 chunks")

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)

        print(f"Chunks 已儲存至：{output_path}")

        if print_preview:
            self._print_preview(all_chunks)

        return all_chunks

    def _print_preview(self, chunks: list[Chunk]) -> None:
        """印出 chunks 預覽。"""
        print("\n===== Chunks 預覽 =====\n")
        for i, c in enumerate(chunks):
            print(f"--- Chunk {i + 1} ---")
            print(f"  Title: {c['title']}")
            preview = c["text"][:100].replace("\n", " ")
            if len(c["text"]) > 100:
                preview += "..."
            print(f"  Text:  {preview}\n")
