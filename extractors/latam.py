"""Extractor de información para LATAM Airlines."""
import re
from typing import Optional
from extractors.base import (
    BaseExtractor, TicketData, normalize_payment_method, normalize_date,
    parse_money, CITY_TO_IATA, _ACCENT_MAP,
)


class LATAMExtractor(BaseExtractor):
    def detect(self, text: str) -> bool:
        indicators = [
            "LATAM AIRLINES GROUP",
            "AEROLÍNEA EMISORA LATAM",
        ]
        return any(ind in text for ind in indicators)

    def extract(self, text: str, filename: str) -> list[TicketData]:
        if "AEROLÍNEA EMISORA LATAM" in text:
            return self._extract_recibo(text, filename)
        return self._extract_info_pasaje(text, filename)

    def _extract_recibo(self, text: str, filename: str) -> list[TicketData]:
        data = TicketData(aerolinea="LATAM", archivo_origen=filename)

        ticket_match = re.search(r"NÚMERO DE TICKET\s+(\d+)", text)
        if ticket_match:
            data.ticket = ticket_match.group(1)

        reserva_match = re.search(r"C[ÓO]DIGO DE RESERVA\s+([A-Z0-9]{6})", text)
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

        flight_match = re.search(r"VUELO\s+(H2|LA|JJ|4C)\s+(\d+)", text)
        if flight_match:
            data.vuelo = f"{flight_match.group(1)} {flight_match.group(2)}"

        data.origen, data.destino = _extract_route(text)

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

    def _extract_info_pasaje(self, text: str, filename: str) -> list[TicketData]:
        reserva_match = re.search(r"C[ÓO]digo de Reserva\s+([A-Z0-9]{6})", text)
        if not reserva_match:
            reserva_match = re.search(r"Código de Reserva\s+([A-Z0-9]{6})", text)
        reserva = reserva_match.group(1) if reserva_match else ""

        fecha_emision = ""
        fecha_match = re.search(
            r"Ciudad y Fecha de\s*\n.*?emisi[oó]n.*?(\d{2}/\d{2}/\d{2})",
            text, re.DOTALL
        )
        if fecha_match:
            fecha_emision = fecha_match.group(1)
        else:
            fecha_match2 = re.search(r"Santiago.*?(\d{2}/\d{2}/\d{2})", text)
            if fecha_match2:
                fecha_emision = fecha_match2.group(1)
            else:
                fecha_match3 = re.search(r"Fecha de emisión\s+(\d{2}-\w{3}-\d{2})", text)
                if fecha_match3:
                    fecha_emision = fecha_match3.group(1)

        ticket_lines = re.findall(r"\b045\d{10}\b", text)
        tickets = list(dict.fromkeys(ticket_lines))

        pasajeros_clean = []
        pasajero_section = re.search(
            r"Nombre Pasajero.*?Tipo de pasajero(.*?)(?:Itinerario|Salida)",
            text, re.DOTALL
        )
        if pasajero_section:
            section_text = pasajero_section.group(1)
            name_matches = re.findall(
                r"([A-ZÁÉÍÓÚ]{2,}(?:\s+[A-ZÁÉÍÓÚ]+)+)\s+(?:Adulto|Niño|Infante)",
                section_text
            )
            for nm in name_matches:
                nm = nm.strip()
                if nm:
                    pasajeros_clean.append(nm)

        if not pasajeros_clean:
            single_name = re.search(
                r"Nombre Pasajero\s+([A-ZÁÉÍÓÚ]{2,}(?:\s+[A-ZÁÉÍÓÚ]+)+)\s+Documento",
                text
            )
            if single_name:
                nm = single_name.group(1).strip()
                nm = re.sub(r"\s+MR\s+", " ", nm, flags=re.IGNORECASE).strip()
                nm = re.sub(r"\s+SRA\s+", " ", nm, flags=re.IGNORECASE).strip()
                if nm:
                    pasajeros_clean.append(nm)

        pasajeros_str = ", ".join(pasajeros_clean) if pasajeros_clean else ""
        cantidad = len(pasajeros_clean) if pasajeros_clean else 1

        vuelo = ""
        vuelos_section = re.search(
            r"Aerolíneas en este viaje(.*?)(?:Información local|Condiciones)",
            text, re.DOTALL
        )
        if vuelos_section:
            vuelos_found = re.findall(r"(LA\s+\d+)", vuelos_section.group(1))
            vuelos_unicos = list(dict.fromkeys(vuelos_found))
            if vuelos_unicos:
                vuelo = ", ".join(vuelos_unicos)

        if not vuelo:
            vuelo_match = re.search(r"(LA\s+\d+)", text)
            if vuelo_match:
                all_vuelos = re.findall(r"(LA\s+\d+)", text)
                vuelo = ", ".join(dict.fromkeys(all_vuelos))

        origen, destino = _extract_route(text)

        fecha_vuelo = ""
        fecha_vuelo_match = re.search(
            r"(\d{2}/\d{2}/\d{2})\s+\d{2}:\d{2}", text
        )
        if fecha_vuelo_match:
            fecha_vuelo = fecha_vuelo_match.group(1)
        else:
            fecha_vuelo_match2 = re.search(
                r"(\d{2}-\w{3}-\d{2})", text
            )
            if fecha_vuelo_match2:
                fecha_vuelo = fecha_vuelo_match2.group(1)
            else:
                fecha_vuelo_match3 = re.search(
                    r"(\d{2})-.*?([A-Z]{3})-(\d{2})", text, re.DOTALL
                )
                if fecha_vuelo_match3:
                    fecha_vuelo = f"{fecha_vuelo_match3.group(1)}-{fecha_vuelo_match3.group(2)}-{fecha_vuelo_match3.group(3)}"
        fecha_vuelo = normalize_date(fecha_vuelo)

        total = None
        total_match = re.search(r"Total pagado\s+(?:CLP\s+)?([\d.,]+)", text)
        if total_match:
            total = parse_money(total_match.group(1))
        else:
            total_match2 = re.search(r"Total\s+CLP\s+([\d.,]+)", text)
            if total_match2:
                total = parse_money(total_match2.group(1))

        forma_pago = ""
        if "CC/BA/OT" in text:
            forma_pago = "TDC"
        else:
            fp_match = re.search(
                r"Tarjeta\s+de\s+(?:crédito|credito|débito|debito)"
                r"(?:\s*/\s*(?:crédito|credito|débito|debito))?",
                text,
                re.IGNORECASE,
            )
            if fp_match:
                forma_pago = normalize_payment_method(fp_match.group(0))
            else:
                fp_match = re.search(r"Forma de Pago\s+.*?Tipo\s+(.*?)(?:\s+Monto|\s+\n)", text, re.DOTALL)
                if fp_match:
                    forma_pago = normalize_payment_method(fp_match.group(1))

        results = []
        if pasajeros_clean and len(pasajeros_clean) > 1:
            ticket_idx = 0
            for pasajero in pasajeros_clean:
                t = TicketData(
                    aerolinea="LATAM",
                    pasajeros=pasajero,
                    cantidad_pasajeros=cantidad,
                    ticket=tickets[ticket_idx] if ticket_idx < len(tickets) else "",
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
                ticket_idx += 1
        else:
            pasajero_str = pasajeros_clean[0] if pasajeros_clean else ""
            t = TicketData(
                aerolinea="LATAM",
                pasajeros=pasajero_str,
                cantidad_pasajeros=cantidad,
                ticket=tickets[0] if tickets else "",
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


_CITY_PATTERN = (
    r"SANTIAGO(?:\s+DE\s+CHILE)?|ANTOFAGASTA|COPIA(?:PÓ|PO)|CALAMA|"
    r"IQUIQUE|LA\s+SERENA|ARICA|PUNTA\s+ARENAS|BALMACEDA|TEMUCO|VALDIVIA|"
    r"PUERTO\s+MONTT|OSORNO|CONCEPCI(?:ÓN|ON)|CASTRO|PUERTO\s+NATALES"
)

_AIRPORT_KEYWORDS = {
    "BENITEZ": "SCL",
    "BENÍTEZ": "SCL",
    "EL LOA": "CJC",
    "SABELLA": "ANF",
    "ARACENA": "IQQ",
    "ATACAMA": "CPO",
    "FLORIDA": "LSC",
    "CARRIEL": "CCP",
    "MAQUEHUE": "ZCO",
    "PICHOY": "ZAL",
    "HOTT": "ZOS",
    "TEPUAL": "PMC",
    "MOCOPULLI": "MHC",
    "BALMACEDA": "BBA",
    "GALLARDO": "PNT",
    "IBAÑEZ": "PUQ",
    "IBANEZ": "PUQ",
    "CHACALLUTA": "ARI",
}


def _normalize_city(city: str) -> str:
    normalized = re.sub(r"\s+", " ", city.upper().translate(_ACCENT_MAP)).strip()
    return normalized


def _find_cities(text: str) -> list[str]:
    return list(dict.fromkeys(
        _normalize_city(city) for city in re.findall(_CITY_PATTERN, text, re.IGNORECASE)
    ))


def _find_iatas(text: str) -> list[str]:
    valid = set(CITY_TO_IATA.values())
    return list(dict.fromkeys(
        code for code in re.findall(r"\b([A-Z]{3})\b", text) if code in valid
    ))


def _find_airports(text: str) -> list[str]:
    """Detecta aeropuertos por palabras clave del nombre del aeropuerto."""
    results = []
    for keyword, iata in _AIRPORT_KEYWORDS.items():
        if keyword in text.upper():
            results.append((text.upper().index(keyword), iata))
    results.sort(key=lambda x: x[0])
    return list(dict.fromkeys(iata for _, iata in results))


def _extract_route(text: str) -> tuple[str, str]:
    """Extrae origen y destino desde el itinerario LATAM."""
    itinerary_match = re.search(
        r"Itinerario(.*?)(?:Detalle de tu pago|Aerolíneas en este viaje|"
        r"Información local|Condiciones)",
        text, re.DOTALL | re.IGNORECASE,
    )
    if not itinerary_match:
        return "", ""

    itinerary = itinerary_match.group(1)

    # Estrategia 1: nombres de aeropuerto (más fiable con pdfplumber).
    airports = _find_airports(itinerary)
    if len(airports) >= 2:
        return airports[0], airports[-1]

    # Estrategia 2: buscar ciudades antes del primer vuelo.
    flight_positions = [
        m.start() for m in re.finditer(r'(?:LA|H2)\s+\d+', itinerary)
    ]

    if flight_positions:
        pre_text = itinerary[:flight_positions[0]]
        cities = _find_cities(pre_text)
        if len(cities) >= 2:
            return (
                CITY_TO_IATA.get(cities[0], cities[0]),
                CITY_TO_IATA.get(cities[-1], cities[-1]),
            )

    # Estrategia 3: códigos IATA en el itinerario.
    iatas = _find_iatas(itinerary)
    if len(iatas) >= 2:
        return iatas[0], iatas[-1]

    return "", ""
