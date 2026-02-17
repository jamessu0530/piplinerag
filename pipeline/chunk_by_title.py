import os
import json
from ai_chunk_extractor import AIChunkExtractor, Chunk
__all__ = ["Chunk", "TitleChunker"]
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

    DEFAULT_MAX_SEGMENT_SIZE = 6000

    def __init__(
        self,
        ollama_url: str | None = None,
        model: str | None = None,
        max_segment_size: int | None = None,
    ):
        self._ai_extractor = AIChunkExtractor(ollama_url=ollama_url, model=model)
        self.max_segment_size = max_segment_size or self.DEFAULT_MAX_SEGMENT_SIZE

    def _parse_segment(self, segment: str) -> list[Chunk]:
        """對一段 Markdown 呼叫 AI 並解析成 chunks。"""
        return self._ai_extractor.extract_chunks(segment)

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
