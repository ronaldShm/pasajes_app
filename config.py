"""Configuración central de la aplicación."""
from pathlib import Path
import json

APP_NAME = "Gestor de Pasajes Aéreos"
APP_VERSION = "1.0.0"
DB_NAME = "pasajes.db"
EXCEL_NAME = "Pasajes.xlsx"
LOG_NAME = "Log.txt"
CONFIG_NAME = "config.ini"

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / DB_NAME
EXCEL_PATH = BASE_DIR / EXCEL_NAME
LOG_PATH = BASE_DIR / LOG_NAME
CONFIG_PATH = BASE_DIR / CONFIG_NAME

PROCESADOS_DIR = "Procesados"
ERRORES_DIR = "Errores"

SUPPORTED_EXTENSIONS = {".pdf", ".eml", ".msg"}

COLUMNAS_EXCEL = [
    "Fecha Registro",
    "Aerolínea",
    "Pasajeros",
    "Cantidad Pasajeros",
    "Tickets",
    "Reserva",
    "Fecha Emisión",
    "Vuelo",
    "Origen",
    "Destino",
    "Fecha Vuelo",
    "Total Pagado",
    "Forma Pago",
    "Solicitado Por",
    "Archivo Origen",
]


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(data: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
