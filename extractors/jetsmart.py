"""Extractor de información para JetSMART (correos .msg)."""
import re
from typing import Optional
from extractors.base import BaseExtractor, TicketData

VALID_IATAS = {
    "SCL", "ANF", "CJC", "LSC", "IQQ", "ARI", "PUQ", "BBA",
    "ZCO", "ZAL", "PMC", "ZOS", "CCP", "MAD", "LIM", "BOG",
}


class JetSMARTExtractor(BaseExtractor):
    def detect(self, text: str) -> bool:
        indicators = [
            "JetSMART",
            "jetsmart@mg.jetsmart.com",
            "JETSMART AIRLINES",
        ]
        return any(ind.lower() in text.lower() for ind in indicators)

    def extract(self, text: str, filename: str) -> list[TicketData]:
        reserva_match = re.search(r"(?:Confirmación Reserva|Reserva)\s+([A-Z0-9]{6})", text)
        reserva = reserva_match.group(1) if reserva_match else ""

        fecha_emision = ""
        fecha_match = re.search(r"FECHA EMISIÓN\s+(\d{2}/\d{2}/\d{4})", text)
        if fecha_match:
            fecha_emision = fecha_match.group(1)

        vuelo = ""
        flight_match = re.search(r"\*?Vuelo\s+(JA|H2|LA)\s+(\d+)", text)
        if flight_match:
            vuelo = f"{flight_match.group(1)} {flight_match.group(2)}"

        fecha_vuelo = ""
        date_match = re.search(r"(?:Fecha:\s*)(\d{2}/\d{2}/\d{4})", text)
        if date_match:
            fecha_vuelo = date_match.group(1)

        all_iatas = re.findall(r"\b([A-Z]{3})\b", text)
        valid_iatas = [c for c in all_iatas if c in VALID_IATAS]
        unique_iatas = list(dict.fromkeys(valid_iatas))

        origen = unique_iatas[0] if len(unique_iatas) >= 1 else ""
        destino = unique_iatas[1] if len(unique_iatas) >= 2 else ""

        pasajeros = []
        tickets = []

        passenger_blocks = re.finditer(
            r"PASAJERO\s+\d+\s+NOMBRE PASAJERO\s+ID PASAJERO\s+[Nn][°º]\s*TICKET\s+FECHA EMISIÓN\s+"
            r"(?:MR|SRA|SR|MRS|MS)?\s*([A-ZÁÉÍÓÚ\s]+?)\s+(\d{13,16})\s+(\d{13,16})\s+(\d{2}/\d{2}/\d{4})",
            text, re.IGNORECASE
        )
        for m in passenger_blocks:
            nombre = m.group(1).strip()
            nombre = re.sub(r"\s+", " ", nombre)
            if nombre:
                pasajeros.append(nombre)
                tickets.append(m.group(3))

        if not pasajeros:
            simple_blocks = re.finditer(
                r"(?:PASAJERO\s+\d+\s+)?(?:MR|SRA|SR|MRS|MS)\s+([A-ZÁÉÍÓÚ]{2,}(?:\s+[A-ZÁÉÍÓÚ]+){1,})\s+(\d{13,16})",
                text, re.IGNORECASE
            )
            for m in simple_blocks:
                nombre = m.group(1).strip()
                ticket_num = m.group(2)
                if ticket_num not in tickets:
                    pasajeros.append(nombre)
                    tickets.append(ticket_num)

        total = None
        total_match = re.search(r"TOTAL de Pago:\s*CLP\s*\$?\s*([\d.,]+)", text)
        if not total_match:
            total_match = re.search(r"Total con tasas e impuestos:\s*CLP\s*\$?\s*([\d.,]+)", text)
        if total_match:
            total = _parse_money(total_match.group(1))

        forma_pago = "Tarjeta de crédito"

        results = []
        if pasajeros:
            pasajeros_str = ", ".join(pasajeros)
            cantidad = len(pasajeros)
            tickets_str = ", ".join(tickets)

            t = TicketData(
                aerolinea="JetSMART",
                pasajeros=pasajeros_str,
                cantidad_pasajeros=cantidad,
                ticket=tickets_str,
                reserva=reserva,
                fecha_emision=fecha_emision,
                vuelo=vuelo,
                origen=origen,
                destino=destino,
                fecha_vuelo=fecha_vuelo,
                total_pagado=total,
                forma_pago=forma_pago,
                archivo_origen=filename,
            )
            results.append(t)
        else:
            t = TicketData(
                aerolinea="JetSMART",
                pasajeros="",
                cantidad_pasajeros=1,
                ticket="",
                reserva=reserva,
                fecha_emision=fecha_emision,
                vuelo=vuelo,
                origen=origen,
                destino=destino,
                fecha_vuelo=fecha_vuelo,
                total_pagado=total,
                forma_pago=forma_pago,
                archivo_origen=filename,
            )
            results.append(t)

        return results


def _parse_money(value: str) -> Optional[float]:
    if not value:
        return None
    try:
        clean = value.replace(",", "").replace(".", "")
        return float(clean)
    except (ValueError, TypeError):
        return None
