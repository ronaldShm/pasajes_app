"""Extractor de información para SKY Airline."""
import re
from typing import Optional
from extractors.base import (
    BaseExtractor, TicketData, normalize_payment_method, normalize_date,
    parse_money, CITY_TO_IATA, _ACCENT_MAP,
)


def _normalize_city(city: str) -> str:
    return city.upper().translate(_ACCENT_MAP)


class SKYExtractor(BaseExtractor):
    def detect(self, text: str) -> bool:
        indicators = [
            "SKY AIRLINE",
            "AEROLÍNEA EMISORA SKY",
        ]
        return any(ind in text for ind in indicators)

    def extract(self, text: str, filename: str) -> list[TicketData]:
        data = TicketData(aerolinea="SKY", archivo_origen=filename)

        ticket_match = re.search(r"NÚMERO DE TICKET\s+(\d+)", text)
        if ticket_match:
            data.ticket = ticket_match.group(1)

        reserva_match = re.search(r"C[ÓO]DIGO DE RESERVA\s+([A-Z0-9]{6})", text)
        if not reserva_match:
            reserva_match = re.search(r"NÚMERO DE TICKET\s+\d+\s+([A-Z0-9]{6})", text)
        if reserva_match:
            data.reserva = reserva_match.group(1)

        nombre_match = re.search(r"NOMBRE DEL PASAJERO\s+([^\n]+)", text)
        if nombre_match:
            nombre = nombre_match.group(1).strip()
            nombre = re.sub(r"\s*(SR|SRA|MR|MRS|MS)\s*$", "", nombre, flags=re.IGNORECASE).strip()
            parts = nombre.split("/")
            if len(parts) == 2:
                data.pasajeros = f"{parts[1].strip()} {parts[0].strip()}"
            else:
                data.pasajeros = nombre

        fecha_match = re.search(r"FECHA DE EMISIÓN\s+(\d{1,2}\s+\w+\s+\d{2,4})", text)
        if fecha_match:
            data.fecha_emision = fecha_match.group(1)

        flight_match = re.search(r"(H2|JA|LA)\s+(\d{3,4})", text)
        if flight_match:
            data.vuelo = f"{flight_match.group(1)} {flight_match.group(2)}"

        flight_line = re.search(
            r"(?:VUELO|FLIGHT).*?(H2|JA|LA)\s+(\d{3,4})\s+(.*?)(?:\n|$)",
            text, re.DOTALL | re.IGNORECASE
        )
        if flight_line:
            flight_text = flight_line.group(3)
            origin_dest_match = re.search(
                r"([A-ZÁÉÍÓÚ\s]+?),\s*([A-ZÁÉÍÓÚ\s]+?),\s*CHILE\s*\((\w+)\)",
                flight_text
            )
            if origin_dest_match:
                origin_city = _normalize_city(origin_dest_match.group(1).strip())
                dest_city = _normalize_city(origin_dest_match.group(2).strip())
                dest_iata = origin_dest_match.group(3)
                data.origen = CITY_TO_IATA.get(origin_city, origin_city)
                data.destino = dest_iata

        if not data.origen:
            all_iatas_match = re.findall(r"\b(SCL|ANF|CJC|CPO|LSC|IQQ|ARI|PUQ|PNT|BBA|MHC|ZCO|ZAL|PMC|ZOS|CCP)\b", text)
            unique_iatas = list(dict.fromkeys(all_iatas_match))
            if len(unique_iatas) >= 2:
                data.origen = unique_iatas[0]
                data.destino = unique_iatas[1]

        date_match = re.search(r"(\d{2}/\w{3}/\d{4})", text)
        if date_match:
            data.fecha_vuelo = normalize_date(date_match.group(1))

        total_match = re.search(r"Tarifa total\s+CLP\s+([\d.,]+)", text)
        if total_match:
            data.total_pagado = parse_money(total_match.group(1))

        forma_match = re.search(
            r"Tarjeta\s+de\s+(?:crédito|credito|débito|debito)"
            r"(?:\s*/\s*(?:crédito|credito|débito|debito))?",
            text,
            re.IGNORECASE,
        )
        if forma_match:
            data.forma_pago = normalize_payment_method(forma_match.group(0))

        return [data]
