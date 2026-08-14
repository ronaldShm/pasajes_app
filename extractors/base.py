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


class BaseExtractor(ABC):
    @abstractmethod
    def detect(self, text: str) -> bool:
        pass

    @abstractmethod
    def extract(self, text: str, filename: str) -> list[TicketData]:
        pass
