"""Parser de archivos .msg (Outlook) usando extract-msg con fallback a .eml."""
import logging
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Optional

import extract_msg

logger = logging.getLogger(__name__)


class MSGParser:
    @staticmethod
    def extract_text(file_path: str | Path) -> Optional[str]:
        file_path = Path(file_path)
        if not file_path.exists():
            return None

        # Intentar con extract-msg primero
        result = MSGParser._parse_with_extract_msg(file_path)
        if result:
            return result

        # Fallback: intentar como .eml (formato MIME crudo)
        result = MSGParser._parse_as_eml(file_path)
        if result:
            return result

        logger.warning("No se pudo extraer texto de %s con ningún método", file_path.name)
        return None

    @staticmethod
    def _parse_with_extract_msg(file_path: Path) -> Optional[str]:
        try:
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
        except Exception as e:
            logger.debug("extract-msg falló para %s: %s", file_path.name, e)
            return None

    @staticmethod
    def _parse_as_eml(file_path: Path) -> Optional[str]:
        try:
            with open(file_path, "rb") as f:
                msg = BytesParser(policy=policy.default).parse(f)
            parts = []
            subject = msg.get("subject")
            if subject:
                parts.append(f"ASUNTO: {subject}")
            sender = msg.get("from")
            if sender:
                parts.append(f"REMITENTE: {sender}")
            body = msg.get_body(preferencelist=("plain", "html"))
            if body:
                raw = body.get_content()
                if raw:
                    raw = MSGParser._html_to_text(raw)
                    parts.append(raw)
            return "\n".join(parts) if parts else None
        except Exception as e:
            logger.debug("parse eml falló para %s: %s", file_path.name, e)
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
