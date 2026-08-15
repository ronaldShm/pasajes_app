"""Clase base abstracta para extractores de aerolíneas."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TicketData:
    aerolinea: str = ""
    pasajeros: str = ""
    cantidad_pasajeros: int = 1
    ticket: str = ""
    reserva: str = ""
    fecha_emision: str = ""
    vuelo: str = ""
    origen: str = ""
    destino: str = ""
    fecha_vuelo: str = ""
    total_pagado: Optional[float] = None
    forma_pago: str = ""
    archivo_origen: str = ""

    def to_dict(self) -> dict:
        return {
            "aerolinea": self.aerolinea,
            "pasajeros": self.pasajeros,
            "cantidad_pasajeros": self.cantidad_pasajeros,
            "ticket": self.ticket,
            "reserva": self.reserva,
            "fecha_emision": self.fecha_emision,
            "vuelo": self.vuelo,
            "origen": self.origen,
            "destino": self.destino,
            "fecha_vuelo": self.fecha_vuelo,
            "total_pagado": self.total_pagado,
            "forma_pago": self.forma_pago,
            "archivo_origen": self.archivo_origen,
        }


def normalize_payment_method(value: str) -> str:
    """Reduce las formas de pago con tarjeta a las siglas usadas por la app."""
    normalized = (value or "").lower()
    if "débito" in normalized or "debito" in normalized:
        if "crédito" not in normalized and "credito" not in normalized:
            return "TDD"
        # LATAM puede informar crédito/débito sin distinguir la tarjeta.
        return "TDC"
    if "crédito" in normalized or "credito" in normalized:
        return "TDC"
    return value.strip()


class BaseExtractor(ABC):
    @abstractmethod
    def detect(self, text: str) -> bool:
        pass

    @abstractmethod
    def extract(self, text: str, filename: str) -> list[TicketData]:
        pass
