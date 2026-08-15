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
                    ceco, archivo_origen, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                data.get("ceco", ""),
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

    def actualizar_ceco(self, id: int, ceco: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE pasajes SET ceco = ? WHERE id = ?",
                (ceco, id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def agregar_lista(self, tipo: str, valor: str) -> bool:
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO listas (tipo, valor) VALUES (?, ?)",
                    (tipo, valor.strip())
                )
                conn.commit()
                return True
        except Exception:
            return False

    def eliminar_lista_item(self, item_id: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM listas WHERE id = ?", (item_id,))
            conn.commit()
            return cursor.rowcount > 0

    def obtener_lista(self, tipo: str) -> list[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, tipo, valor FROM listas WHERE tipo = ? ORDER BY valor",
                (tipo,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def obtener_valores_lista(self, tipo: str) -> list[str]:
        items = self.obtener_lista(tipo)
        return [item["valor"] for item in items]

    def resumen_general(self) -> dict:
        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_pasajes,
                    COUNT(DISTINCT pasajeros) as total_pasajeros,
                    COALESCE(SUM(total_pagado), 0) as total_gastado,
                    COALESCE(AVG(total_pagado), 0) as promedio,
                    COALESCE(MIN(total_pagado), 0) as minimo,
                    COALESCE(MAX(total_pagado), 0) as maximo
                FROM pasajes
            """).fetchone()
            return dict(row)

    def gasto_por_ceco(self) -> list[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT ceco,
                    COUNT(*) as pasajes,
                    COALESCE(SUM(total_pagado), 0) as total,
                    COALESCE(AVG(total_pagado), 0) as promedio
                FROM pasajes
                WHERE ceco != ''
                GROUP BY ceco
                ORDER BY total DESC
            """)
            return [dict(r) for r in cursor.fetchall()]

    def gasto_por_solicitante(self) -> list[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT solicitado_por,
                    COUNT(*) as pasajes,
                    COALESCE(SUM(total_pagado), 0) as total,
                    COALESCE(AVG(total_pagado), 0) as promedio
                FROM pasajes
                WHERE solicitado_por != ''
                GROUP BY solicitado_por
                ORDER BY total DESC
            """)
            return [dict(r) for r in cursor.fetchall()]

    def gasto_por_aerolinea(self) -> list[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT aerolinea,
                    COUNT(*) as pasajes,
                    COALESCE(SUM(total_pagado), 0) as total,
                    COALESCE(AVG(total_pagado), 0) as promedio,
                    COALESCE(MIN(total_pagado), 0) as minimo,
                    COALESCE(MAX(total_pagado), 0) as maximo
                FROM pasajes
                GROUP BY aerolinea
                ORDER BY total DESC
            """)
            return [dict(r) for r in cursor.fetchall()]

    def top_rutas(self, limit: int = 10) -> list[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT origen, destino,
                    COUNT(*) as viajes,
                    COALESCE(SUM(total_pagado), 0) as total,
                    COALESCE(AVG(total_pagado), 0) as promedio
                FROM pasajes
                WHERE origen != '' AND destino != ''
                GROUP BY origen, destino
                ORDER BY viajes DESC
                LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def top_pasajeros(self, limit: int = 10) -> list[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT pasajeros,
                    COUNT(*) as viajes,
                    COALESCE(SUM(total_pagado), 0) as total
                FROM pasajes
                WHERE pasajeros != ''
                GROUP BY pasajeros
                ORDER BY viajes DESC
                LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def gasto_por_mes(self) -> list[dict]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT substr(fecha_vuelo, 4, 2) as mes,
                       substr(fecha_vuelo, 7, 2) as anio,
                       COUNT(*) as pasajes,
                       COALESCE(SUM(total_pagado), 0) as total
                FROM pasajes
                WHERE fecha_vuelo != ''
                GROUP BY anio, mes
                ORDER BY anio, mes
            """)
            return [dict(r) for r in cursor.fetchall()]
