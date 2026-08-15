"""Panel de gestión de listas (Solicitado Por y CECO)."""
import customtkinter as ctk
from tkinter import messagebox
from database.repository import PasajeRepository


class ListsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.repo = PasajeRepository()
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 15))

        ctk.CTkLabel(
            header, text="Gestión de Listas",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=10)

        self._build_list_panel(
            row=0, col=0, title="Solicitado Por",
            tipo="solicitado"
        )
        self._build_list_panel(
            row=0, col=1, title="Centro de Costo (CECO)",
            tipo="ceco"
        )

    def _build_list_panel(self, row: int, col: int, title: str, tipo: str):
        panel = ctk.CTkFrame(self)
        panel.grid(row=row, column=col, sticky="nsew", padx=10, pady=(0, 10))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            panel, text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        input_frame = ctk.CTkFrame(panel, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        input_frame.grid_columnconfigure(0, weight=1)

        entry = ctk.CTkEntry(
            input_frame, placeholder_text="Nuevo ítem..."
        )
        entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        def add_item(_event=None):
            value = entry.get().strip()
            if not value:
                return
            if self.repo.agregar_lista(tipo, value):
                entry.delete(0, "end")
                self._refresh_list(list_frame, tipo)
            else:
                messagebox.showwarning(
                    "Duplicado",
                    f"'{value}' ya existe en la lista."
                )

        entry.bind("<Return>", add_item)

        ctk.CTkButton(
            input_frame, text="Agregar", width=80,
            fg_color="#27ae60", hover_color="#219a52",
            command=add_item
        ).grid(row=0, column=1)

        list_frame = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        list_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))

        self._refresh_list(list_frame, tipo)

        # Guardar referencia para actualizaciones externas
        if tipo == "solicitado":
            self._solicitado_list_frame = list_frame
            self._solicitado_tipo = tipo
        else:
            self._ceco_list_frame = list_frame
            self._ceco_tipo = tipo

    def _refresh_list(self, list_frame: ctk.CTkScrollableFrame, tipo: str):
        for widget in list_frame.winfo_children():
            widget.destroy()

        items = self.repo.obtener_lista(tipo)

        for idx, item in enumerate(items):
            bg_color = "#2b2b2b" if idx % 2 == 0 else "#353535"
            row_frame = ctk.CTkFrame(list_frame, fg_color=bg_color, corner_radius=0)
            row_frame.pack(fill="x", padx=2, pady=1)
            row_frame.grid_columnconfigure(0, weight=1)

            label = ctk.CTkLabel(
                row_frame, text=item["valor"],
                font=ctk.CTkFont(size=11), anchor="w",
                text_color="#e0e0e0"
            )
            label.grid(row=0, column=0, padx=8, pady=4, sticky="w")

            def delete_item(_e, item_id=item["id"], lf=list_frame, t=tipo):
                self.repo.eliminar_lista_item(item_id)
                self._refresh_list(lf, t)

            del_btn = ctk.CTkButton(
                row_frame, text="X", width=28, height=24,
                fg_color="#c0392b", hover_color="#a93226",
                font=ctk.CTkFont(size=10, weight="bold"),
                command=delete_item
            )
            del_btn.grid(row=0, column=1, padx=5, pady=3)

        if not items:
            ctk.CTkLabel(
                list_frame, text="(vacío)",
                font=ctk.CTkFont(size=10), text_color="#888"
            ).pack(pady=10)

    def refresh_lists(self):
        if hasattr(self, "_solicitado_list_frame"):
            self._refresh_list(self._solicitado_list_frame, self._solicitado_tipo)
        if hasattr(self, "_ceco_list_frame"):
            self._refresh_list(self._ceco_list_frame, self._ceco_tipo)
