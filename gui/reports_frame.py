"""Panel de reportes y estadísticas."""
import customtkinter as ctk
from datetime import datetime
from database.repository import PasajeRepository
from excel.exporter import ExcelExporter
import tkinter.messagebox as messagebox


class ReportsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.repo = PasajeRepository()
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header, text="Reportes y Estadísticas",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            header, text="Exportar", width=100,
            command=self._export_to_excel,
            fg_color="#27ae60", hover_color="#1e8449"
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            header, text="Actualizar", width=100,
            command=self.refresh_reports,
            fg_color="#2E86AB", hover_color="#1a6d8a"
        ).pack(side="right", padx=5)

        date_frame = ctk.CTkFrame(header, fg_color="transparent")
        date_frame.pack(side="right", padx=10)

        ctk.CTkLabel(
            date_frame, text="Desde:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 5))

        self.date_desde = ctk.CTkEntry(date_frame, width=100, placeholder_text="DD/MM/YY")
        self.date_desde.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            date_frame, text="Hasta:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 5))

        self.date_hasta = ctk.CTkEntry(date_frame, width=100, placeholder_text="DD/MM/YY")
        self.date_hasta.pack(side="left", padx=(0, 5))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        scroll.grid_columnconfigure(0, weight=1)

        self._build_kpi_cards(scroll)
        self._build_section_ceco(scroll)
        self._build_section_solicitante(scroll)
        self._build_section_aerolinea(scroll)
        self._build_section_rutas(scroll)
        self._build_section_pasajeros(scroll)

    def _get_date_filters(self):
        desde = self.date_desde.get().strip() if hasattr(self, 'date_desde') else ""
        hasta = self.date_hasta.get().strip() if hasattr(self, 'date_hasta') else ""
        return desde or None, hasta or None

    def _build_kpi_cards(self, parent):
        section = ctk.CTkFrame(parent, fg_color="#1a1a2e")
        section.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 10))
        section.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            section, text="RESUMEN GENERAL",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2E86AB"
        ).grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 5), sticky="w")

        self.kpi_total = self._kpi_box(section, "Total Pasajes", "0", "#2E86AB", 1, 0)
        self.kpi_gastado = self._kpi_box(section, "Total Gastado", "$0", "#27ae60", 1, 1)
        self.kpi_promedio = self._kpi_box(section, "Promedio/Pasaje", "$0", "#e67e22", 1, 2)
        self.kpi_pasajeros = self._kpi_box(section, "Pasajeros Únicos", "0", "#9b59b6", 1, 3)

    def _kpi_box(self, parent, title, value, color, row, col):
        frame = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=8)
        frame.grid(row=row, column=col, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(
            frame, text=title,
            font=ctk.CTkFont(size=10), text_color="#aaa"
        ).pack(padx=10, pady=(8, 0))

        lbl = ctk.CTkLabel(
            frame, text=value,
            font=ctk.CTkFont(size=18, weight="bold"), text_color=color
        )
        lbl.pack(padx=10, pady=(2, 10))
        return lbl

    def _build_section_ceco(self, parent):
        self._build_table_section(
            parent, row=1, title="GASTO POR CENTRO DE COSTO (CECO)",
            headers=["CECO", "Pasajes", "Total", "Promedio"],
            width_cols=[150, 80, 120, 120],
            fetch_method=lambda: self.repo.gasto_por_ceco(*self._get_date_filters()),
            format_fn=lambda r: [
                r.get("ceco", ""),
                str(r.get("pasajes", 0)),
                f"${r.get('total', 0):,.0f}",
                f"${r.get('promedio', 0):,.0f}",
            ]
        )

    def _build_section_solicitante(self, parent):
        self._build_table_section(
            parent, row=2, title="GASTO POR SOLICITANTE",
            headers=["Solicitante", "Pasajes", "Total", "Promedio"],
            width_cols=[150, 80, 120, 120],
            fetch_method=lambda: self.repo.gasto_por_solicitante(*self._get_date_filters()),
            format_fn=lambda r: [
                r.get("solicitado_por", ""),
                str(r.get("pasajes", 0)),
                f"${r.get('total', 0):,.0f}",
                f"${r.get('promedio', 0):,.0f}",
            ]
        )

    def _build_section_aerolinea(self, parent):
        self._build_table_section(
            parent, row=3, title="GASTO POR AEROLÍNEA",
            headers=["Aerolínea", "Pasajes", "Total", "Promedio", "Mín", "Máx"],
            width_cols=[100, 80, 120, 120, 100, 100],
            fetch_method=lambda: self.repo.gasto_por_aerolinea(*self._get_date_filters()),
            format_fn=lambda r: [
                r.get("aerolinea", ""),
                str(r.get("pasajes", 0)),
                f"${r.get('total', 0):,.0f}",
                f"${r.get('promedio', 0):,.0f}",
                f"${r.get('minimo', 0):,.0f}",
                f"${r.get('maximo', 0):,.0f}",
            ]
        )

    def _build_section_rutas(self, parent):
        self._build_table_section(
            parent, row=4, title="TOP 10 RUTAS",
            headers=["Origen", "Destino", "Viajes", "Total", "Promedio"],
            width_cols=[80, 80, 80, 120, 120],
            fetch_method=lambda: self.repo.top_rutas(10, *self._get_date_filters()),
            format_fn=lambda r: [
                r.get("origen", ""),
                r.get("destino", ""),
                str(r.get("viajes", 0)),
                f"${r.get('total', 0):,.0f}",
                f"${r.get('promedio', 0):,.0f}",
            ]
        )

    def _build_section_pasajeros(self, parent):
        self._build_table_section(
            parent, row=5, title="TOP 10 PASAJEROS",
            headers=["Pasajero", "Viajes", "Total"],
            width_cols=[200, 80, 120],
            fetch_method=lambda: self.repo.top_pasajeros(10, *self._get_date_filters()),
            format_fn=lambda r: [
                r.get("pasajeros", ""),
                str(r.get("viajes", 0)),
                f"${r.get('total', 0):,.0f}",
            ]
        )

    def _build_table_section(self, parent, row, title, headers, width_cols,
                             fetch_method, format_fn):
        section = ctk.CTkFrame(parent, fg_color="#1a1a2e")
        section.grid(row=row, column=0, sticky="ew", padx=5, pady=(0, 10))
        section.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            section, text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2E86AB"
        )
        title_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        header_frame = ctk.CTkFrame(section, fg_color="#2E86AB", corner_radius=4)
        header_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 2))

        for i, (h, w) in enumerate(zip(headers, width_cols)):
            ctk.CTkLabel(
                header_frame, text=h, width=w,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="white", anchor="w"
            ).grid(row=0, column=i, padx=4, pady=4, sticky="w")

        data_frame = ctk.CTkFrame(section, fg_color="transparent")
        data_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))

        try:
            data = fetch_method()
        except Exception:
            data = []

        if not data:
            ctk.CTkLabel(
                data_frame, text="Sin datos disponibles",
                font=ctk.CTkFont(size=10), text_color="#888"
            ).grid(row=0, column=0, padx=5, pady=10)
            return

        for idx, record in enumerate(data):
            bg = "#2b2b2b" if idx % 2 == 0 else "#353535"
            row_frame = ctk.CTkFrame(data_frame, fg_color=bg, corner_radius=0)
            row_frame.grid(row=idx, column=0, sticky="ew", pady=1)
            data_frame.grid_columnconfigure(0, weight=1)

            values = format_fn(record)
            for i, (val, w) in enumerate(zip(values, width_cols)):
                ctk.CTkLabel(
                    row_frame, text=val, width=w,
                    font=ctk.CTkFont(size=10), anchor="w",
                    text_color="#e0e0e0"
                ).grid(row=0, column=i, padx=4, pady=3, sticky="w")

    def refresh_reports(self):
        for widget in self.winfo_children():
            widget.destroy()
        self._setup_ui()

    def _export_to_excel(self):
        try:
            desde, hasta = self._get_date_filters()
            report_data = {
                "resumen": self.repo.resumen_general(desde, hasta),
                "ceco": self.repo.gasto_por_ceco(desde, hasta),
                "solicitante": self.repo.gasto_por_solicitante(desde, hasta),
                "aerolinea": self.repo.gasto_por_aerolinea(desde, hasta),
                "rutas": self.repo.top_rutas(10, desde, hasta),
                "pasajeros": self.repo.top_pasajeros(10, desde, hasta),
            }
            exporter = ExcelExporter()
            path = exporter.export_report_to_excel(report_data)
            messagebox.showinfo("Éxito", f"Reporte exportado a:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar reporte:\n{str(e)}")
