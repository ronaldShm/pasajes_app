"""Repositorio de acceso a datos para la tabla pasajes."""
from typing import Optional
from database.connection import Database


class PasajeRepository:
    def __init__(self):
        self.db = Database()

    def existe_ticket(self, ticket: str) -> bool:
        if not ticket:
            return False
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM pasajes WHERE ticket LIKE ?",
                (f"%{ticket}%",)
            )
            return cursor.fetchone()[0] > 0

    def existe_reserva(self, reserva: str) -> bool:
        if not reserva:
            return False
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM pasajes WHERE reserva = ?",
                (reserva,)
            )
            return cursor.fetchone()[0] > 0

    def buscar_similar(self, pasajeros: str, fecha_vuelo: str, vuelo: str, total: float) -> list:
        with self.db.get_connection() as conn:
            conditions = []
            params = []
            if pasajeros:
                conditions.append("pasajeros LIKE ?")
                params.append(f"%{pasajeros}%")
            if fecha_vuelo:
                conditions.append("fecha_vuelo LIKE ?")
                params.append(f"%{fecha_vuelo}%")
            if vuelo:
                conditions.append("vuelo LIKE ?")
                params.append(f"%{vuelo}%")
            if total:
                conditions.append("total_pagado = ?")
                params.append(total)

            if not conditions:
                return []

            where_clause = " AND ".join(conditions)
            query = f"SELECT * FROM pasajes WHERE {where_clause}"
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def guardar(self, data: dict) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO pasajes (
                    fecha_registro, aerolinea, pasajeros, cantidad_pasajeros,
                    ticket, reserva, fecha_emision, vuelo, origen, destino,
                    fecha_vuelo, total_pagado, forma_pago, solicitado_por,
                    archivo_origen, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("fecha_registro", ""),
                data.get("aerolinea", ""),
                data.get("pasajeros", ""),
                data.get("cantidad_pasajeros", 1),
                data.get("ticket", ""),
                data.get("reserva", ""),
                data.get("fecha_emision", ""),
                data.get("vuelo", ""),
                data.get("origen", ""),
                data.get("destino", ""),
                data.get("fecha_vuelo", ""),
                data.get("total_pagado"),
                data.get("forma_pago", ""),
                data.get("solicitado_por", ""),
                data.get("archivo_origen", ""),
                data.get("estado", "procesado"),
            ))
            conn.commit()
            return cursor.lastrowid

    def obtener_todos(self) -> list:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM pasajes ORDER BY created_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def contar_por_estado(self) -> dict:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT estado, COUNT(*) as total FROM pasajes GROUP BY estado"
            )
            return {row["estado"]: row["total"] for row in cursor.fetchall()}

    def eliminar_por_archivo(self, archivo: str) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM pasajes WHERE archivo_origen = ?",
                (archivo,)
            )
            conn.commit()
            return cursor.rowcount

    def eliminar_todos(self) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM pasajes")
            conn.commit()
            return cursor.rowcount

    def actualizar_solicitado_por(self, id: int, solicitado_por: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE pasajes SET solicitado_por = ? WHERE id = ?",
                (solicitado_por, id)
            )
            conn.commit()
            return cursor.rowcount > 0
