"""Parser de archivos PDF usando pdfplumber."""
from pathlib import Path
from typing import Optional
import pdfplumber


class PDFParser:
    @staticmethod
    def extract_text(file_path: str | Path) -> Optional[str]:
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            with pdfplumber.open(str(file_path)) as pdf:
                texts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        texts.append(text)
                return "\n".join(texts) if texts else None
        except Exception:
            return None

    @staticmethod
    def extract_pages(file_path: str | Path) -> list[str]:
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return []
            with pdfplumber.open(str(file_path)) as pdf:
                pages = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                return pages
        except Exception:
            return []
