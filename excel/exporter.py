"""Exportador y gestor de archivos Excel."""
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from config import EXCEL_PATH, COLUMNAS_EXCEL


class ExcelExporter:
    def __init__(self):
        self.excel_path = EXCEL_PATH
        self.wb = None
        self.ws = None
        self._load_or_create()

    def _load_or_create(self):
        if self.excel_path.exists():
            try:
                self.wb = load_workbook(str(self.excel_path))
                self.ws = self.wb.active
                return
            except Exception:
                pass
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.title = "Pasajes"
        self._create_headers()

    def _create_headers(self):
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(
            start_color="2E86AB", end_color="2E86AB", fill_type="solid"
        )
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        for col_idx, col_name in enumerate(COLUMNAS_EXCEL, 1):
            cell = self.ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        col_widths = {
            1: 18, 2: 12, 3: 45, 4: 15, 5: 30, 6: 10,
            7: 14, 8: 18, 9: 12, 10: 12, 11: 14,
            12: 15, 13: 22, 14: 30,
        }
        for col, width in col_widths.items():
            self.ws.column_dimensions[self._get_column_letter(col)].width = width

    def _get_column_letter(self, col: int) -> str:
        result = ""
        while col > 0:
            col, remainder = divmod(col - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def add_record(self, data: dict):
        row = self.ws.max_row + 1
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        values = [
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
            data.get("total_pagado", ""),
            data.get("forma_pago", ""),
            data.get("archivo_origen", ""),
        ]
        for col_idx, value in enumerate(values, 1):
            cell = self.ws.cell(row=row, column=col_idx, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center")

    def save(self):
        if self.wb:
            self.wb.save(str(self.excel_path))

    def clear_data(self):
        if self.ws and self.ws.max_row > 1:
            self.ws.delete_rows(2, self.ws.max_row - 1)

    def export_from_records(self, records: list[dict]):
        self.clear_data()
        for record in records:
            self.add_record(record)
        self.save()

    def get_all_records(self) -> list[dict]:
        if not self.ws or self.ws.max_row <= 1:
            return []
        records = []
        headers = [cell.value for cell in self.ws[1]]
        for row in self.ws.iter_rows(min_row=2, values_only=True):
            record = dict(zip(headers, row))
            records.append(record)
        return records
