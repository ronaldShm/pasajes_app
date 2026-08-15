"""Procesador principal de pasajes aéreos."""
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional
from config import (
    SUPPORTED_EXTENSIONS, PROCESADOS_DIR, ERRORES_DIR
)
from parsers.pdf_parser import PDFParser
from parsers.msg_parser import MSGParser
from core.detector import AirlineDetector
from core.validator import DuplicateValidator, ValidationResult
from extractors.base import TicketData
from database.repository import PasajeRepository
from utils.logger import AppLogger
from utils.file_manager import FileManager


class ProcessingResult:
    def __init__(self):
        self.total_archivos: int = 0
        self.procesados: int = 0
        self.duplicados: int = 0
        self.errores: int = 0
        self.nuevos: int = 0
        self.detalles: list[str] = []


class TicketProcessor:
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.detector = AirlineDetector()
        self.validator = DuplicateValidator()
        self.repo = PasajeRepository()
        self.logger = AppLogger()
        self.file_manager = FileManager()
        self.progress_callback = progress_callback

    def process_folder(self, folder_path: str) -> ProcessingResult:
        result = ProcessingResult()
        folder = Path(folder_path)

        if not folder.exists() or not folder.is_dir():
            result.detalles.append(f"Error: La carpeta {folder_path} no existe")
            return result

        self.file_manager.create_folder(folder / PROCESADOS_DIR)
        self.file_manager.create_folder(folder / ERRORES_DIR)

        files = [
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        result.total_archivos = len(files)

        for idx, file_path in enumerate(files):
            if self.progress_callback:
                self.progress_callback(idx + 1, len(files), file_path.name)

            try:
                file_result = self._process_file(file_path, folder)
                if file_result == "duplicado":
                    result.duplicados += 1
                elif file_result == "error":
                    result.errores += 1
                else:
                    result.procesados += 1
                    result.nuevos += 1
            except Exception as e:
                result.errores += 1
                self.logger.log_error(file_path.name, str(e))
                try:
                    self.file_manager.move_to_errors(file_path, folder)
                except Exception:
                    self.logger.log_error(file_path.name, "No se pudo mover a Errores/")
                result.detalles.append(f"Error procesando {file_path.name}: {e}")

        self.logger.log_summary(result)
        return result

    def _process_file(self, file_path: Path, base_folder: Path) -> str:
        text = self._read_file(file_path)
        if not text:
            self.logger.log_error(file_path.name, "No se pudo leer el contenido")
            try:
                self.file_manager.move_to_errors(file_path, base_folder)
            except Exception:
                self.logger.log_error(file_path.name, "No se pudo mover a Errores/")
            return "error"

        extractor = self.detector.detect(text)
        if not extractor:
            self.logger.log_error(file_path.name, "Aerolínea no reconocida")
            try:
                self.file_manager.move_to_errors(file_path, base_folder)
            except Exception:
                self.logger.log_error(file_path.name, "No se pudo mover a Errores/")
            return "error"

        tickets_data = extractor.extract(text, file_path.name)
        if not tickets_data:
            self.logger.log_error(file_path.name, "No se pudo extraer información")
            try:
                self.file_manager.move_to_errors(file_path, base_folder)
            except Exception:
                self.logger.log_error(file_path.name, "No se pudo mover a Errores/")
            return "error"

        all_duplicates = True
        for ticket_data in tickets_data:
            if ticket_data.cantidad_pasajeros > 1 and ticket_data.total_pagado is not None:
                ticket_data.total_pagado = round(
                    ticket_data.total_pagado / ticket_data.cantidad_pasajeros, 2
                )

            validation = self.validator.validate(
                ticket=ticket_data.ticket,
                pasajeros=ticket_data.pasajeros,
                fecha_vuelo=ticket_data.fecha_vuelo,
                vuelo=ticket_data.vuelo,
                total_pagado=ticket_data.total_pagado or 0,
                reserva=ticket_data.reserva,
            )

            if validation.es_duplicado:
                self.logger.log_duplicate(
                    file_path.name, ticket_data.pasajeros, validation.razon
                )
                continue

            all_duplicates = False
            record = ticket_data.to_dict()
            record["fecha_registro"] = datetime.now().strftime("%d-%m-%Y")
            record["estado"] = "procesado"

            self.repo.guardar(record)

            self.logger.log_processed(file_path.name, ticket_data)

        try:
            if all_duplicates:
                self.file_manager.move_to_processed(file_path, base_folder)
                return "duplicado"

            self.file_manager.move_to_processed(file_path, base_folder)
            return "ok"
        except Exception as e:
            self.logger.log_error(file_path.name, f"No se pudo mover archivo: {e}")
            return "ok"

    def _read_file(self, file_path: Path) -> Optional[str]:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return PDFParser.extract_text(file_path)
        elif suffix == ".msg":
            return MSGParser.extract_text(file_path)
        elif suffix == ".eml":
            return self._read_eml(file_path)
        return None

    def _read_eml(self, file_path: Path) -> Optional[str]:
        try:
            from email import policy
            from email.parser import BytesParser
            with open(file_path, "rb") as f:
                msg = BytesParser(policy=policy.default).parse(f)
            parts = []
            if msg["subject"]:
                parts.append(f"ASUNTO: {msg['subject']}")
            if msg["from"]:
                parts.append(f"REMITENTE: {msg['from']}")
            body = msg.get_body(preferencelist=("plain", "html"))
            if body:
                parts.append(body.get_content())
            return "\n".join(parts) if parts else None
        except Exception:
            return None
