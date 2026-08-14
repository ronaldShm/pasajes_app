"""Parser de archivos .msg (Outlook) usando extract-msg."""
import re
from pathlib import Path
from typing import Optional
import extract_msg


class MSGParser:
    @staticmethod
    def extract_text(file_path: str | Path) -> Optional[str]:
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            msg = extract_msg.openMsg(str(file_path))
            try:
                body_parts = []
                if msg.subject:
                    body_parts.append(f"ASUNTO: {msg.subject}")
                if msg.sender:
                    body_parts.append(f"REMITENTE: {msg.sender}")
                html = getattr(msg, "htmlBody", None)
                if html:
                    text = MSGParser._html_to_text(html)
                    if text:
                        body_parts.append(text)
                elif msg.body:
                    body_parts.append(msg.body)
                return "\n".join(body_parts) if body_parts else None
            finally:
                msg.close()
        except Exception:
            return None

    @staticmethod
    def _html_to_text(html) -> str:
        try:
            if isinstance(html, bytes):
                text = html.decode("utf-8", errors="replace")
            else:
                text = str(html)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
            text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
            text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception:
            return ""

    @staticmethod
    def get_sender(file_path: str | Path) -> Optional[str]:
        try:
            msg = extract_msg.openMsg(str(file_path))
            try:
                return msg.sender
            finally:
                msg.close()
        except Exception:
            return None

    @staticmethod
    def get_subject(file_path: str | Path) -> Optional[str]:
        try:
            msg = extract_msg.openMsg(str(file_path))
            try:
                return msg.subject
            finally:
                msg.close()
        except Exception:
            return None
