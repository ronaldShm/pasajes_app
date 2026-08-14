"""Conexión y gestión de la base de datos SQLite."""
import sqlite3
from pathlib import Path
from config import DB_PATH


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db_path = DB_PATH
        self._create_tables()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _create_tables(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pasajes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_registro TEXT NOT NULL,
                    aerolinea TEXT NOT NULL,
                    pasajeros TEXT NOT NULL,
                    cantidad_pasajeros INTEGER DEFAULT 1,
                    ticket TEXT,
                    reserva TEXT,
                    fecha_emision TEXT,
                    vuelo TEXT,
                    origen TEXT,
                    destino TEXT,
                    fecha_vuelo TEXT,
                    total_pagado REAL,
                    forma_pago TEXT,
                    archivo_origen TEXT NOT NULL,
                    estado TEXT DEFAULT 'procesado',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticket ON pasajes(ticket)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_reserva ON pasajes(reserva)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_archivo ON pasajes(archivo_origen)
            """)
            conn.commit()
