from __future__ import annotations

from typing import List, Dict
import logging


logger = logging.getLogger(__name__)


class DocumentParserService:
    """
    Lightweight document parser used by the web routes.
    NOTE: This is a minimal implementation to keep the app running without
    heavy dependencies. It focuses on text splitting and simple heuristics.
    """

    def __init__(self, openai_service=None):
        self.openai_service = openai_service

    async def parse_bulk_content(self, bulk_content: str, content_type: str = "knowledge_base") -> List[Dict]:
        """Parse pasted bulk content into simple entries.

        Heuristic: split by double newlines or lines starting with a dash/number.
        Returns a list of dicts with title/content/category.
        """
        if not bulk_content:
            return []

        blocks: List[str] = []
        current: List[str] = []
        for line in bulk_content.splitlines():
            if line.strip() == "" or line.strip().startswith(("- ", "* ", "1. ", "2. ", "3. ")):
                if current:
                    blocks.append("\n".join(current).strip())
                    current = []
            current.append(line)
        if current:
            blocks.append("\n".join(current).strip())

        entries: List[Dict] = []
        for i, block in enumerate(b for b in blocks if b):
            # Title is first sentence/line up to 120 chars
            first_line = block.splitlines()[0].strip()
            title = first_line[:120]
            entries.append(
                {
                    "title": title or f"Entry {i+1}",
                    "content": block[:5000],
                    "category": "General",
                }
            )

        return entries

    async def parse_file_content(self, file_content: bytes, filename: str) -> List[Dict]:
        """Parse uploaded file content into entries.
        For .txt we decode; for .pdf we attempt a naive decode; for others we
        fall back to a single entry with raw text where possible.
        """
        if not file_content:
            return []

        text = ""
        lower = filename.lower()
        try:
            if lower.endswith(".txt"):
                text = file_content.decode("utf-8", errors="ignore")
            elif lower.endswith(".pdf"):
                # Minimal placeholder extraction; real PDF parsing would require an extra dependency
                text = await self._extract_from_pdf(file_content)
            else:
                # Default attempt at decoding
                text = file_content.decode("utf-8", errors="ignore")
        except Exception as ex:
            logger.warning(f"Could not decode file {filename}: {ex}")
            text = ""

        if not text:
            return []

        return await self.parse_bulk_content(text, content_type="knowledge_base")

    def analyze_document_structure(self, extracted_text: str) -> Dict:
        """Return simple structural stats for the debug endpoint."""
        lines = extracted_text.splitlines() if extracted_text else []
        paragraphs = [p for p in extracted_text.split("\n\n") if p.strip()] if extracted_text else []
        return {
            "total_characters": len(extracted_text or ""),
            "total_lines": len(lines),
            "potential_sections": max(0, len(paragraphs)),
            "preview": (extracted_text or "")[:500],
        }

    async def _extract_from_pdf(self, file_content: bytes) -> str:
        """Very naive PDF text extraction placeholder.
        Consider installing a PDF library for production use (e.g., pdfminer.six).
        """
        try:
            # Some PDFs have plain text chunks; this will yield something readable sometimes
            return file_content.decode("latin1", errors="ignore")
        except Exception:
            return ""
