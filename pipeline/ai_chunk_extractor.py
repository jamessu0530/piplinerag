import os
import json
import re
import requests
from dotenv import load_dotenv
from typing import TypedDict


class Chunk(TypedDict):
    title: str
    text: str


SYSTEM_PROMPT = """你的任務是分析 Markdown 文字，辨識每個段落的「標題 (title)」與「內文 (text)」。

重要規則：
1. title 必須是 Markdown 裡的【原文】，可能是 # 標題、粗體文字、或你判斷為標題的句子。
2. text 必須是該 title 下的【原文內容】，一字不改地擷取。
3. 絕對不可以改寫、總結、或修改任何文字，只能原封不動地擷取。
4. 如果某段沒有明確標題，可自行產生簡短標題，但 text 仍須保持原文。
5. 每個 chunk 必須有 title 和 text。

回傳格式（只回傳 JSON，不要其他文字）：
[
  {
    "title": "原文標題",
    "text": "原文內容..."
  }
]"""


def extract_json_from_response(response_text: str) -> list:
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


class AIChunkExtractor:
    """呼叫 Ollama/Gemma，將一段 Markdown 擷取成 title + text 的 chunks。"""

    DEFAULT_OLLAMA_URL = "http://localhost:11434"
    DEFAULT_MODEL = "gemma3:4b"

    def __init__(
        self,
        ollama_url: str | None = None,
        model: str | None = None,
    ):
        load_dotenv()
        self.ollama_url = ollama_url or os.getenv(
            "OLLAMA_BASE_URL", self.DEFAULT_OLLAMA_URL
        )
        self.model = model or os.getenv("GEMMA_MODEL", self.DEFAULT_MODEL)

    def _call_api(self, markdown_text: str) -> str:
        """呼叫 Ollama chat API，回傳模型產生的文字。"""
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

    def extract_chunks(self, markdown_text: str) -> list[Chunk]:
        """
        對一段 Markdown 呼叫 AI，回傳 [{"title": ..., "text": ...}, ...]。
        """
        response = self._call_api(markdown_text)
        raw_chunks = extract_json_from_response(response)
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
