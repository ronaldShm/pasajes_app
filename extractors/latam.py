"""Extractor de información para LATAM Airlines."""
import re
from typing import Optional
from extractors.base import BaseExtractor, TicketData

CITY_TO_IATA = {
    "SANTIAGO": "SCL", "ANTOFAGASTA": "ANF", "COPIAPÓ": "CJC", "COPIAPO": "CJC",
    "CALAMA": "CJC", "IQUIQUE": "IQQ", "LA SERENA": "LSC",
    "ARICA": "ARI", "PUNTA ARENAS": "PUQ", "BALMACEDA": "BBA",
    "TEMUCO": "ZCO", "VALDIVIA": "ZAL", "PUERTO MONTT": "PMC",
    "OSORNO": "ZOS", "CONCEPCIÓN": "CCP", "BUCARAMANGA": "BGA",
}


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

        iatas = re.findall(r"\b([A-Z]{3})\b", text)
        valid_iatas = [c for c in iatas if c in CITY_TO_IATA.values()]
        unique_iatas = list(dict.fromkeys(valid_iatas))
        if len(unique_iatas) >= 2:
            data.origen = unique_iatas[0]
            data.destino = unique_iatas[1]

        date_match = re.search(r"(\d{2}/\w{3}/\d{4})", text)
        if date_match:
            data.fecha_vuelo = date_match.group(1)

        total_match = re.search(r"Tarifa total\s+CLP\s+([\d.,]+)", text)
        if total_match:
            data.total_pagado = _parse_money(total_match.group(1))

        forma_match = re.search(r"Forma de pago\s+(.*?)(?:\n|$)", text)
        if forma_match:
            data.forma_pago = forma_match.group(1).strip()

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

        origen = ""
        destino = ""

        itinerario_match = re.search(
            r"N[°o]\s*(?:de\s*)?[Vv]uelo\s+Origen\s+Destino(.*?)(?:Información|Condiciones|Detalle)",
            text, re.DOTALL
        )
        if itinerario_match:
            itin_text = itinerario_match.group(1)
            cities_in_itin = re.findall(
                r"(SANTIAGO|ANTOFAGASTA|COPIAPÓ|COPIAPO|CALAMA|IQUIQUE|LA SERENA|ARICA|PUNTA ARENAS|BALMACEDA|TEMUCO|VALDIVIA|PUERTO MONTT|OSORNO|CONCEPCIÓN)",
                itin_text, re.IGNORECASE
            )
            unique_cities_itin = list(dict.fromkeys([c.upper() for c in cities_in_itin]))
            if len(unique_cities_itin) >= 2:
                origen = CITY_TO_IATA.get(unique_cities_itin[0], unique_cities_itin[0])
                destino = CITY_TO_IATA.get(unique_cities_itin[-1], unique_cities_itin[-1])

        if not origen:
            cities_found = re.findall(
                r"(SANTIAGO|ANTOFAGASTA|COPIAPÓ|CALAMA|IQUIQUE|LA SERENA|ARICA|PUNTA ARENAS|BALMACEDA|TEMUCO|VALDIVIA|PUERTO MONTT|OSORNO|CONCEPCIÓN)",
                text, re.IGNORECASE
            )
            unique_cities = list(dict.fromkeys([c.upper() for c in cities_found]))
            if len(unique_cities) >= 2:
                origen = CITY_TO_IATA.get(unique_cities[0], unique_cities[0])
                destino = CITY_TO_IATA.get(unique_cities[-1], unique_cities[-1])

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

        total = None
        total_match = re.search(r"Total pagado\s+(?:CLP\s+)?([\d.,]+)", text)
        if total_match:
            total = _parse_money(total_match.group(1))
        else:
            total_match2 = re.search(r"Total\s+CLP\s+([\d.,]+)", text)
            if total_match2:
                total = _parse_money(total_match2.group(1))

        forma_pago = ""
        if "CC/BA/OT" in text:
            forma_pago = "Tarjeta de crédito/débito"
        elif "Tarjeta de crédito" in text or "Tarjeta de débito" in text:
            forma_pago = "Tarjeta de crédito/débito"
        else:
            fp_match = re.search(r"Forma de Pago\s+.*?Tipo\s+(.*?)(?:\s+Monto|\s+\n)", text, re.DOTALL)
            if fp_match:
                forma_pago = fp_match.group(1).strip()

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


def _parse_money(value: str) -> Optional[float]:
    if not value:
        return None
    try:
        clean = value.replace(",", "").replace(".", "")
        return float(clean)
    except (ValueError, TypeError):
        return None
