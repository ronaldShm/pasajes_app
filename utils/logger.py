"""Sistema de logging para la aplicación."""
from datetime import datetime
from pathlib import Path
from config import LOG_PATH


class AppLogger:
    def __init__(self):
        self.log_path = LOG_PATH
        self._ensure_log_file()

    def _ensure_log_file(self):
        if not self.log_path.exists():
            self.log_path.touch()

    def _write(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)

    def log_processed(self, filename: str, ticket_data):
        pasajeros = ticket_data.pasajeros or "N/A"
        vuelo = ticket_data.vuelo or "N/A"
        self._write(
            f"PROCESADO: {filename} | "
            f"Aerolínea: {ticket_data.aerolinea} | "
            f"Pasajeros: {pasajeros} | "
            f"Vuelo: {vuelo}"
        )

    def log_duplicate(self, filename: str, pasajeros: str, reason: str):
        self._write(
            f"DUPLICADO: {filename} | "
            f"Pasajeros: {pasajeros} | "
            f"Motivo: {reason}"
        )

    def log_error(self, filename: str, error: str):
        self._write(f"ERROR: {filename} | {error}")

    def log_summary(self, result):
        self._write(
            f"RESUMEN: Total={result.total_archivos} | "
            f"Procesados={result.procesados} | "
            f"Duplicados={result.duplicados} | "
            f"Errores={result.errores}"
        )

    def log_info(self, message: str):
        self._write(f"INFO: {message}")

    def get_recent_logs(self, count: int = 50) -> list[str]:
        if not self.log_path.exists():
            return []
        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [line.strip() for line in lines[-count:]]
