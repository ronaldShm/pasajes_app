"""Panel de visualización de registros."""
import customtkinter as ctk
from tkinter import messagebox
from database.repository import PasajeRepository
from excel.exporter import ExcelExporter


class RecordsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.repo = PasajeRepository()
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header_frame, text="Registros de Pasajes",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=10)

        self.total_label = ctk.CTkLabel(
            header_frame, text="Total: 0",
            font=ctk.CTkFont(size=13)
        )
        self.total_label.pack(side="left", padx=20)

        ctk.CTkButton(
            header_frame, text="Refrescar", width=100,
            command=self.refresh_data,
            fg_color="#2E86AB", hover_color="#1a6d8a"
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            header_frame, text="Exportar Excel", width=120,
            command=self._export_excel,
            fg_color="#27ae60", hover_color="#219a52"
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            header_frame, text="Limpiar Registros", width=130,
            command=self._clear_records,
            fg_color="#c0392b", hover_color="#a93226"
        ).pack(side="right", padx=5)

        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.table = ctk.CTkScrollableFrame(
            table_frame, fg_color="transparent"
        )
        self.table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self._create_headers()

    def _create_headers(self):
        headers = [
            "Fecha", "Aerolínea", "Pasajeros", "Tickets",
            "Reserva", "Vuelo", "Origen", "Destino",
            "Fecha Vuelo", "Total", "Solicitado Por", "Archivo"
        ]
        header_frame = ctk.CTkFrame(self.table, fg_color="#2E86AB", corner_radius=5)
        header_frame.pack(fill="x", padx=2, pady=(2, 0))

        widths = [85, 70, 180, 140, 60, 70, 55, 55, 80, 90, 100, 140]
        for i, (header, width) in enumerate(zip(headers, widths)):
            label = ctk.CTkLabel(
                header_frame, text=header, width=width,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="white", anchor="w"
            )
            label.grid(row=0, column=i, padx=2, pady=5, sticky="w")

    def refresh_data(self):
        for widget in self.table.winfo_children()[1:]:
            widget.destroy()

        records = self.repo.obtener_todos()
        self.total_label.configure(text=f"Total: {len(records)}")

        widths = [85, 70, 180, 140, 60, 70, 55, 55, 80, 90, 100, 140]
        for idx, record in enumerate(records):
            bg_color = "#2b2b2b" if idx % 2 == 0 else "#353535"
            row_frame = ctk.CTkFrame(self.table, fg_color=bg_color, corner_radius=0)
            row_frame.pack(fill="x", padx=2, pady=1)

            values = [
                str(record.get("fecha_registro", ""))[:10],
                str(record.get("aerolinea", "")),
                str(record.get("pasajeros", ""))[:30],
                str(record.get("ticket", ""))[:20],
                str(record.get("reserva", "")),
                str(record.get("vuelo", "")),
                str(record.get("origen", "")),
                str(record.get("destino", "")),
                str(record.get("fecha_vuelo", "")),
                f"${record.get('total_pagado', 0):,.0f}" if record.get("total_pagado") else "",
                str(record.get("solicitado_por", "")),
                str(record.get("archivo_origen", ""))[:25],
            ]

            for i, (value, width) in enumerate(zip(values, widths)):
                if i == 10:  # Columna "Solicitado Por" editable
                    entry = ctk.CTkEntry(
                        row_frame, width=width,
                        font=ctk.CTkFont(size=9),
                        fg_color="#3a3a3a", text_color="#e0e0e0",
                        border_color="#555"
                    )
                    entry.insert(0, value)
                    entry.grid(row=0, column=i, padx=2, pady=3, sticky="w")
                    record_id = record.get("id")
                    entry.bind(
                        "<FocusOut>",
                        lambda e, rid=record_id, ent=entry: self._update_solicitado_por(rid, ent.get())
                    )
                    entry.bind(
                        "<Return>",
                        lambda e, rid=record_id, ent=entry: self._update_solicitado_por(rid, ent.get())
                    )
                else:
                    label = ctk.CTkLabel(
                        row_frame, text=value, width=width,
                        font=ctk.CTkFont(size=9), anchor="w",
                        text_color="#e0e0e0"
                    )
                    label.grid(row=0, column=i, padx=2, pady=3, sticky="w")

    def _update_solicitado_por(self, record_id: int, value: str):
        if record_id:
            self.repo.actualizar_solicitado_por(record_id, value)

    def _export_excel(self):
        try:
            excel = ExcelExporter()
            records = self.repo.obtener_todos()
            excel.export_from_records(records)
            messagebox.showinfo(
                "Exportar Excel",
                f"Excel actualizado con {len(records)} registros"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar:\n{e}")

    def _clear_records(self):
        records = self.repo.obtener_todos()
        if not records:
            messagebox.showinfo(
                "Sin registros",
                "No hay registros para eliminar."
            )
            return

        confirm = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Borrar los {len(records)} registros?\n\n"
            "Esta acción no se puede deshacer.",
            icon="warning"
        )
        if confirm:
            deleted = self.repo.eliminar_todos()
            self.refresh_data()
            messagebox.showinfo(
                "Eliminados",
                f"Se eliminaron {deleted} registros."
            )
