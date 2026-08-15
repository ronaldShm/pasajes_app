"""Sistema de logging unificado para la aplicación."""
import logging
from datetime import datetime
from pathlib import Path
from config import LOG_PATH


class AppLogger:
    def __init__(self):
        self.log_path = LOG_PATH
        self._logger = logging.getLogger("pasajes_app")
        self._logger.setLevel(logging.DEBUG)
        if not self._logger.handlers:
            self._setup_handler()
        self._ensure_log_file()

    def _ensure_log_file(self):
        if not self.log_path.exists():
            self.log_path.touch()

    def _setup_handler(self):
        handler = logging.FileHandler(
            str(self.log_path), encoding="utf-8", mode="a"
        )
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def log_processed(self, filename: str, ticket_data):
        pasajeros = ticket_data.pasajeros or "N/A"
        vuelo = ticket_data.vuelo or "N/A"
        self._logger.info(
            f"PROCESADO: {filename} | "
            f"Aerolínea: {ticket_data.aerolinea} | "
            f"Pasajeros: {pasajeros} | "
            f"Vuelo: {vuelo}"
        )

    def log_duplicate(self, filename: str, pasajeros: str, reason: str):
        self._logger.warning(
            f"DUPLICADO: {filename} | "
            f"Pasajeros: {pasajeros} | "
            f"Motivo: {reason}"
        )

    def log_error(self, filename: str, error: str):
        self._logger.error(f"ERROR: {filename} | {error}")

    def log_summary(self, result):
        self._logger.info(
            f"RESUMEN: Total={result.total_archivos} | "
            f"Procesados={result.procesados} | "
            f"Duplicados={result.duplicados} | "
            f"Errores={result.errores}"
        )

    def log_info(self, message: str):
        self._logger.info(f"INFO: {message}")

    def get_recent_logs(self, count: int = 50) -> list[str]:
        if not self.log_path.exists():
            return []
        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [line.strip() for line in lines[-count:]]
