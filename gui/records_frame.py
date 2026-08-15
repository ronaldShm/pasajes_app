"""Panel de visualización de registros con búsqueda, filtros y desplegables."""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from database.repository import PasajeRepository
from excel.exporter import ExcelExporter
from utils.backup import backup_db, restore_db, list_backups


class RecordsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.repo = PasajeRepository()
        self._all_records = []
        self._filtered_records = []
        self._solicitado_options = [""]
        self._ceco_options = [""]
        self._suppress_filters = False
        self._page_size = 25
        self._current_page = 1
        self._selected_ids = set()
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

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
            header_frame, text="Backup", width=80,
            command=self._make_backup,
            fg_color="#8e44ad", hover_color="#6c3483"
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            header_frame, text="Restaurar", width=90,
            command=self._restore_backup,
            fg_color="#d35400", hover_color="#a04000"
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            header_frame, text="Limpiar Registros", width=130,
            command=self._clear_records,
            fg_color="#c0392b", hover_color="#a93226"
        ).pack(side="right", padx=5)

        filter_frame = ctk.CTkFrame(self, fg_color="#1a1a2e")
        filter_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        filter_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            filter_frame, text="Buscar:",
            font=ctk.CTkFont(size=11)
        ).grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            filter_frame, textvariable=self.search_var,
            width=200, placeholder_text="Pasajero, ticket, reserva..."
        )
        search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        search_entry.bind("<Return>", lambda e: self._apply_filters())

        ctk.CTkButton(
            filter_frame, text="Buscar", width=60,
            command=self._apply_filters,
            fg_color="#2E86AB", hover_color="#1a6d8a"
        ).grid(row=0, column=2, padx=(2, 5), pady=5)

        ctk.CTkLabel(
            filter_frame, text="Aerolínea:",
            font=ctk.CTkFont(size=11)
        ).grid(row=0, column=3, padx=(15, 5), pady=5, sticky="w")

        self.airline_var = ctk.StringVar(value="Todas")
        self.airline_menu = ctk.CTkOptionMenu(
            filter_frame, variable=self.airline_var,
            values=["Todas"], width=100
        )
        self.airline_menu.grid(row=0, column=4, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(
            filter_frame, text="Origen:",
            font=ctk.CTkFont(size=11)
        ).grid(row=0, column=5, padx=(15, 5), pady=5, sticky="w")

        self.origin_var = ctk.StringVar(value="Todos")
        self.origin_menu = ctk.CTkOptionMenu(
            filter_frame, variable=self.origin_var,
            values=["Todos"], width=70
        )
        self.origin_menu.grid(row=0, column=6, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(
            filter_frame, text="Destino:",
            font=ctk.CTkFont(size=11)
        ).grid(row=0, column=7, padx=(15, 5), pady=5, sticky="w")

        self.dest_var = ctk.StringVar(value="Todos")
        self.dest_menu = ctk.CTkOptionMenu(
            filter_frame, variable=self.dest_var,
            values=["Todos"], width=70
        )
        self.dest_menu.grid(row=0, column=8, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(
            filter_frame, text="Solicitado:",
            font=ctk.CTkFont(size=11)
        ).grid(row=0, column=9, padx=(15, 5), pady=5, sticky="w")

        self.solicitado_var = ctk.StringVar(value="Todos")
        self.solicitado_menu = ctk.CTkOptionMenu(
            filter_frame, variable=self.solicitado_var,
            values=["Todos"], width=120
        )
        self.solicitado_menu.grid(row=0, column=10, padx=5, pady=5, sticky="w")

        ctk.CTkButton(
            filter_frame, text="Limpiar", width=70,
            command=self._clear_filters,
            fg_color="#555", hover_color="#333"
        ).grid(row=0, column=11, padx=(15, 10), pady=5)

        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.table = ctk.CTkScrollableFrame(
            table_frame, fg_color="transparent"
        )
        self.table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self._create_headers()

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        self._build_pagination(bottom_frame)
        self._build_bulk_edit(bottom_frame)

    def _create_headers(self):
        headers = [
            "✓", "Fecha", "Aerolínea", "Pasajeros", "Tickets",
            "Reserva", "Vuelo", "Origen", "Destino",
            "Fecha Vuelo", "Total", "Solicitado Por", "CECO", "Archivo"
        ]
        header_frame = ctk.CTkFrame(self.table, fg_color="#2E86AB", corner_radius=5)
        header_frame.pack(fill="x", padx=2, pady=(2, 0))

        self._widths = [30, 85, 70, 180, 140, 60, 70, 55, 55, 80, 90, 110, 100, 140]

        self._select_all_var = ctk.BooleanVar(value=False)
        select_all_cb = ctk.CTkCheckBox(
            header_frame, text="", variable=self._select_all_var,
            width=28, height=28, corner_radius=4,
            fg_color="#27ae60", hover_color="#1e8449",
            command=self._toggle_select_all
        )
        select_all_cb.grid(row=0, column=0, padx=2, pady=5)

        for i, (header, width) in enumerate(zip(headers[1:], self._widths[1:])):
            label = ctk.CTkLabel(
                header_frame, text=header, width=width,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="white", anchor="w"
            )
            label.grid(row=0, column=i + 1, padx=2, pady=5, sticky="w")

    def _load_dropdown_options(self):
        self._solicitado_options = [""] + self.repo.obtener_valores_lista("solicitado")
        self._ceco_options = [""] + self.repo.obtener_valores_lista("ceco")
        if hasattr(self, "bulk_ceco_menu"):
            self.bulk_ceco_menu.configure(values=self._ceco_options)
        if hasattr(self, "bulk_solicitado_menu"):
            self.bulk_solicitado_menu.configure(values=self._solicitado_options)

    def _update_filter_options(self):
        if not self._all_records:
            return

        airlines = sorted(set(
            r.get("aerolinea", "") for r in self._all_records if r.get("aerolinea")
        ))
        origins = sorted(set(
            r.get("origen", "") for r in self._all_records if r.get("origen")
        ))
        dests = sorted(set(
            r.get("destino", "") for r in self._all_records if r.get("destino")
        ))
        solicitados = sorted(set(
            r.get("solicitado_por", "") for r in self._all_records
            if r.get("solicitado_por")
        ))

        current_airline = self.airline_var.get()
        self.airline_menu.configure(values=["Todas"] + airlines)
        if current_airline in ["Todas"] + airlines:
            self.airline_var.set(current_airline)

        current_origin = self.origin_var.get()
        self.origin_menu.configure(values=["Todos"] + origins)
        if current_origin in ["Todos"] + origins:
            self.origin_var.set(current_origin)

        current_dest = self.dest_var.get()
        self.dest_menu.configure(values=["Todos"] + dests)
        if current_dest in ["Todos"] + dests:
            self.dest_var.set(current_dest)

        current_solicitado = self.solicitado_var.get()
        self.solicitado_menu.configure(values=["Todos"] + solicitados)
        if current_solicitado in ["Todos"] + solicitados:
            self.solicitado_var.set(current_solicitado)

    def _apply_filters(self):
        if self._suppress_filters:
            return
        search = self.search_var.get().lower().strip()
        airline = self.airline_var.get()
        origin = self.origin_var.get()
        dest = self.dest_var.get()
        solicitado = self.solicitado_var.get()

        filtered = self._all_records

        if search:
            filtered = [
                r for r in filtered
                if search in (r.get("pasajeros", "") or "").lower()
                or search in (r.get("ticket", "") or "").lower()
                or search in (r.get("reserva", "") or "").lower()
            ]

        if airline != "Todas":
            filtered = [
                r for r in filtered
                if r.get("aerolinea", "") == airline
            ]

        if origin != "Todos":
            filtered = [
                r for r in filtered
                if r.get("origen", "") == origin
            ]

        if dest != "Todos":
            filtered = [
                r for r in filtered
                if r.get("destino", "") == dest
            ]

        if solicitado != "Todos":
            filtered = [
                r for r in filtered
                if r.get("solicitado_por", "") == solicitado
            ]

        self._filtered_records = filtered
        self._current_page = 1
        self._render_current_page()

    def _clear_filters(self):
        self.search_var.set("")
        self.airline_var.set("Todas")
        self.origin_var.set("Todos")
        self.dest_var.set("Todos")
        self.solicitado_var.set("Todos")

    def refresh_data(self):
        self._suppress_filters = True
        self._load_dropdown_options()
        self._all_records = self.repo.obtener_todos()
        self._update_filter_options()
        self._clear_filters()
        self._suppress_filters = False
        self._apply_filters()

    def _render_current_page(self):
        total = len(self._filtered_records)
        total_pages = max(1, (total + self._page_size - 1) // self._page_size)
        
        if self._current_page > total_pages:
            self._current_page = total_pages
        if self._current_page < 1:
            self._current_page = 1

        start_idx = (self._current_page - 1) * self._page_size
        end_idx = min(start_idx + self._page_size, total)
        page_records = self._filtered_records[start_idx:end_idx]

        self.total_label.configure(text=f"Total: {total}")
        self.page_label.configure(text=f"Página {self._current_page} de {total_pages}")
        
        self.prev_btn.configure(state="normal" if self._current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self._current_page < total_pages else "disabled")

        self._render_records(page_records)

    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._render_current_page()

    def _next_page(self):
        total_pages = max(1, (len(self._filtered_records) + self._page_size - 1) // self._page_size)
        if self._current_page < total_pages:
            self._current_page += 1
            self._render_current_page()

    def _render_records(self, records):
        for widget in self.table.winfo_children()[1:]:
            widget.destroy()

        for idx, record in enumerate(records):
            bg_color = "#2b2b2b" if idx % 2 == 0 else "#353535"
            row_frame = ctk.CTkFrame(self.table, fg_color=bg_color, corner_radius=0)
            row_frame.pack(fill="x", padx=2, pady=1)

            record_id = record.get("id")

            cb_var = ctk.BooleanVar(value=record_id in self._selected_ids)
            cb = ctk.CTkCheckBox(
                row_frame, text="", variable=cb_var,
                width=28, height=28, corner_radius=4,
                fg_color="#27ae60", hover_color="#1e8449",
                command=lambda rid=record_id, v=cb_var: self._toggle_record(rid, v)
            )
            cb.grid(row=0, column=0, padx=2, pady=3)

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
            ]

            for i, (value, width) in enumerate(zip(values, self._widths[1:])):
                label = ctk.CTkLabel(
                    row_frame, text=value, width=width,
                    font=ctk.CTkFont(size=9), anchor="w",
                    text_color="#e0e0e0"
                )
                label.grid(row=0, column=i + 1, padx=2, pady=3, sticky="w")

            solicitado_var = ctk.StringVar(value=record.get("solicitado_por", ""))
            solicitado_menu = ctk.CTkOptionMenu(
                row_frame, variable=solicitado_var,
                values=self._solicitado_options,
                width=110, font=ctk.CTkFont(size=9),
                fg_color="#3a3a3a", button_color="#555",
                command=lambda val, rid=record_id: self._update_solicitado_por(rid, val)
            )
            solicitado_menu.grid(row=0, column=11, padx=2, pady=3, sticky="w")

            ceco_var = ctk.StringVar(value=record.get("ceco", ""))
            ceco_menu = ctk.CTkOptionMenu(
                row_frame, variable=ceco_var,
                values=self._ceco_options,
                width=100, font=ctk.CTkFont(size=9),
                fg_color="#3a3a3a", button_color="#555",
                command=lambda val, rid=record_id: self._update_ceco(rid, val)
            )
            ceco_menu.grid(row=0, column=12, padx=2, pady=3, sticky="w")

            archivo = str(record.get("archivo_origen", ""))[:25]
            label = ctk.CTkLabel(
                row_frame, text=archivo, width=140,
                font=ctk.CTkFont(size=9), anchor="w",
                text_color="#e0e0e0"
            )
            label.grid(row=0, column=13, padx=2, pady=3, sticky="w")

    def _toggle_record(self, record_id, var):
        if var.get():
            self._selected_ids.add(record_id)
        else:
            self._selected_ids.discard(record_id)
        self._update_selected_label()

    def _toggle_select_all(self):
        if self._select_all_var.get():
            page_ids = [r.get("id") for r in self._filtered_records
                        if r.get("id") is not None]
            start = (self._current_page - 1) * self._page_size
            end = min(start + self._page_size, len(self._filtered_records))
            for r in self._filtered_records[start:end]:
                rid = r.get("id")
                if rid is not None:
                    self._selected_ids.add(rid)
        else:
            start = (self._current_page - 1) * self._page_size
            end = min(start + self._page_size, len(self._filtered_records))
            for r in self._filtered_records[start:end]:
                self._selected_ids.discard(r.get("id"))
        self._update_selected_label()
        self._render_current_page()

    def _update_selected_label(self):
        count = len(self._selected_ids)
        self.selected_label.configure(text=f"Seleccionados: {count}")

    def _build_pagination(self, parent):
        self.prev_btn = ctk.CTkButton(
            parent, text="← Anterior", width=100,
            command=self._prev_page,
            fg_color="#555", hover_color="#333"
        )
        self.prev_btn.pack(side="left", padx=5)

        self.page_label = ctk.CTkLabel(
            parent, text="Página 1 de 1",
            font=ctk.CTkFont(size=12)
        )
        self.page_label.pack(side="left", padx=20)

        self.next_btn = ctk.CTkButton(
            parent, text="Siguiente →", width=100,
            command=self._next_page,
            fg_color="#555", hover_color="#333"
        )
        self.next_btn.pack(side="left", padx=5)

    def _build_bulk_edit(self, parent):
        bulk_frame = ctk.CTkFrame(parent, fg_color="transparent")
        bulk_frame.pack(side="right", padx=5)

        self.selected_label = ctk.CTkLabel(
            bulk_frame, text="Seleccionados: 0",
            font=ctk.CTkFont(size=11)
        )
        self.selected_label.pack(side="left", padx=5)

        ctk.CTkLabel(
            bulk_frame, text="CECO:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(10, 5))

        self.bulk_ceco_var = ctk.StringVar(value="")
        self.bulk_ceco_menu = ctk.CTkOptionMenu(
            bulk_frame, variable=self.bulk_ceco_var,
            values=self._ceco_options, width=100
        )
        self.bulk_ceco_menu.pack(side="left", padx=5)

        ctk.CTkLabel(
            bulk_frame, text="Solicitado:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(10, 5))

        self.bulk_solicitado_var = ctk.StringVar(value="")
        self.bulk_solicitado_menu = ctk.CTkOptionMenu(
            bulk_frame, variable=self.bulk_solicitado_var,
            values=self._solicitado_options, width=100
        )
        self.bulk_solicitado_menu.pack(side="left", padx=5)

        ctk.CTkButton(
            bulk_frame, text="Aplicar", width=80,
            command=self._apply_bulk_edit,
            fg_color="#27ae60", hover_color="#1e8449"
        ).pack(side="left", padx=5)

    def _update_solicitado_por(self, record_id: int, value: str):
        if record_id:
            self.repo.actualizar_solicitado_por(record_id, value)

    def _update_ceco(self, record_id: int, value: str):
        if record_id:
            self.repo.actualizar_ceco(record_id, value)

    def _apply_bulk_edit(self):
        selected = list(self._selected_ids)
        if not selected:
            messagebox.showwarning("Sin selección", "No hay registros seleccionados.")
            return
        
        ceco = self.bulk_ceco_var.get()
        solicitado = self.bulk_solicitado_var.get()
        
        if not ceco and not solicitado:
            messagebox.showwarning("Sin cambios", "Seleccione un valor de CECO o Solicitado para aplicar.")
            return
        
        confirm = messagebox.askyesno(
            "Confirmar edición masiva",
            f"¿Aplicar cambios a {len(selected)} registros?\n"
            f"CECO: {ceco or '(sin cambio)'}\n"
            f"Solicitado: {solicitado or '(sin cambio)'}",
            icon="question"
        )
        
        if confirm:
            updated = 0
            if ceco:
                updated += self.repo.actualizar_ceco_lote(selected, ceco)
            if solicitado:
                updated += self.repo.actualizar_solicitado_por_lote(selected, solicitado)
            
            self._selected_ids.clear()
            self._select_all_var.set(False)
            self.bulk_ceco_var.set("")
            self.bulk_solicitado_var.set("")
            self.selected_label.configure(text="Seleccionados: 0")
            self.refresh_data()
            messagebox.showinfo("Éxito", f"Se actualizaron {updated} registros.")

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

    def _make_backup(self):
        try:
            path = backup_db()
            messagebox.showinfo("Backup", f"Backup creado en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear backup:\n{e}")

    def _restore_backup(self):
        backups = list_backups()
        if not backups:
            messagebox.showinfo("Sin backups", "No hay backups disponibles en la carpeta Backups/.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Restaurar Backup")
        dialog.geometry("450x350")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="Selecciona un backup para restaurar:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(padx=15, pady=(15, 5))

        ctk.CTkLabel(
            dialog, text="Se reemplazará la base de datos actual.",
            font=ctk.CTkFont(size=11), text_color="#e74c3c"
        ).pack(padx=15, pady=(0, 10))

        list_frame = ctk.CTkScrollableFrame(dialog, height=180)
        list_frame.pack(fill="x", padx=15, pady=(0, 10))

        selected_path = [None]

        for bk in backups:
            fecha = bk.stem.replace("pasajes_", "")
            try:
                fecha_fmt = datetime.strptime(fecha, "%Y%m%d").strftime("%d/%m/%Y")
            except ValueError:
                fecha_fmt = fecha
            row = ctk.CTkFrame(list_frame, fg_color="#2b2b2b")
            row.pack(fill="x", pady=2)

            def select(p=bk, d=dialog):
                selected_path[0] = p
                d.destroy()

            ctk.CTkButton(
                row, text=f"📅 {fecha_fmt}   |   {bk.name}",
                anchor="w", fg_color="#333", hover_color="#555",
                command=lambda p=bk, d=dialog: select(p, d)
            ).pack(fill="x", padx=5, pady=5)

        def cancel():
            dialog.destroy()

        ctk.CTkButton(
            dialog, text="Cancelar", width=100,
            command=cancel, fg_color="#555", hover_color="#333"
        ).pack(side="left", padx=15, pady=10)

        dialog.wait_window()

        if selected_path[0]:
            confirm = messagebox.askyesno(
                "Confirmar restauración",
                f"¿Restaurar backup?\n\n{selected_path[0].name}\n\n"
                "Se cerrará la app para aplicar los cambios.",
                icon="warning"
            )
            if confirm:
                try:
                    restore_db(selected_path[0])
                    messagebox.showinfo(
                        "Restaurado",
                        "Base de datos restaurada.\nReinicia la app para ver los cambios."
                    )
                except Exception as e:
                    messagebox.showerror("Error", f"Error al restaurar:\n{e}")

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
