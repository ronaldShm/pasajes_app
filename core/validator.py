"""Validador de duplicados de pasajes."""
from dataclasses import dataclass
from database.repository import PasajeRepository


@dataclass
class ValidationResult:
    es_duplicado: bool = False
    razon: str = ""
    es_sospechoso: bool = False
    razon_sospecha: str = ""


class DuplicateValidator:
    def __init__(self):
        self.repo = PasajeRepository()

    def validate(self, ticket: str, pasajeros: str, fecha_vuelo: str,
                 vuelo: str, total_pagado: float, reserva: str) -> ValidationResult:
        result = ValidationResult()

        if ticket and self.repo.existe_ticket(ticket):
            result.es_duplicado = True
            result.razon = f"Ticket {ticket} ya registrado"
            return result

        if reserva and self.repo.existe_reserva(reserva):
            similares = self.repo.buscar_similar(
                pasajeros=pasajeros,
                fecha_vuelo=fecha_vuelo,
                vuelo=vuelo,
                total=total_pagado
            )
            if similares:
                result.es_sospechoso = True
                result.razon_sospecha = (
                    f"Reserva {reserva} ya existe con pasajeros similares"
                )
                return result

        if pasajeros and fecha_vuelo and vuelo:
            similares = self.repo.buscar_similar(
                pasajeros=pasajeros,
                fecha_vuelo=fecha_vuelo,
                vuelo=vuelo,
                total=total_pagado
            )
            if similares:
                confianza = self._calcular_confianza(
                    pasajeros, fecha_vuelo, vuelo, total_pagado, reserva, similares
                )
                if confianza > 0.8:
                    result.es_duplicado = True
                    result.razon = (
                        f"Duplicado detectado (confianza: {confianza:.0%})"
                    )
                elif confianza > 0.5:
                    result.es_sospechoso = True
                    result.razon_sospecha = (
                        f"Posible duplicado (confianza: {confianza:.0%})"
                    )

        return result

    def _calcular_confianza(self, pasajeros, fecha_vuelo, vuelo,
                            total_pagado, reserva, similares) -> float:
        score = 0.0
        total_campos = 4.0

        for s in similares:
            if pasajeros and s.get("pasajeros", ""):
                if pasajeros.lower() in s["pasajeros"].lower():
                    score += 0.35
            if fecha_vuelo and s.get("fecha_vuelo", ""):
                if fecha_vuelo == s["fecha_vuelo"]:
                    score += 0.25
            if vuelo and s.get("vuelo", ""):
                if vuelo == s["vuelo"]:
                    score += 0.2
            if total_pagado and s.get("total_pagado"):
                if abs(total_pagado - s["total_pagado"]) < 1:
                    score += 0.2

        return min(score, 1.0)
