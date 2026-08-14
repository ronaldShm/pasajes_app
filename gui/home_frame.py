"""Panel principal de la aplicación - Procesamiento de pasajes."""
import threading
import customtkinter as ctk
from tkinter import messagebox
from config import SUPPORTED_EXTENSIONS
from core.processor import TicketProcessor, ProcessingResult
from utils.file_manager import FileManager


class HomeFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.file_manager = FileManager()
        self.folder_var = ctk.StringVar(value="")
        self.processing = False
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        folder_frame = ctk.CTkFrame(self)
        folder_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        folder_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            folder_frame, text="Carpeta de pasajes:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.entry_folder = ctk.CTkEntry(
            folder_frame, textvariable=self.folder_var,
            placeholder_text="Selecciona una carpeta...",
            height=35
        )
        self.entry_folder.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkButton(
            folder_frame, text="Seleccionar", width=110, height=35,
            command=self.app.select_folder,
            fg_color="#2E86AB", hover_color="#1a6d8a"
        ).grid(row=0, column=2, padx=10, pady=10)

        stats_frame = ctk.CTkFrame(self)
        stats_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        self.stat_files = self._create_stat_box(stats_frame, "Encontrados", "0", "#3498db")
        self.stat_files.grid(row=0, column=0, padx=8, pady=10, sticky="ew")

        self.stat_processed = self._create_stat_box(stats_frame, "Procesados", "0", "#27ae60")
        self.stat_processed.grid(row=0, column=1, padx=8, pady=10, sticky="ew")

        self.stat_duplicates = self._create_stat_box(stats_frame, "Duplicados", "0", "#f39c12")
        self.stat_duplicates.grid(row=0, column=2, padx=8, pady=10, sticky="ew")

        self.stat_errors = self._create_stat_box(stats_frame, "Errores", "0", "#c0392b")
        self.stat_errors.grid(row=0, column=3, padx=8, pady=10, sticky="ew")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        self.btn_process = ctk.CTkButton(
            btn_frame, text="PROCESAR PASAJES", height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start_processing,
            fg_color="#27ae60", hover_color="#219a52"
        )
        self.btn_process.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_export = ctk.CTkButton(
            btn_frame, text="Exportar Excel", height=45,
            font=ctk.CTkFont(size=13),
            command=self._export_excel,
            fg_color="#2E86AB", hover_color="#1a6d8a"
        )
        self.btn_export.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_records = ctk.CTkButton(
            btn_frame, text="Ver Registros", height=45,
            font=ctk.CTkFont(size=13),
            command=lambda: self.app._show_frame("records"),
            fg_color="#555555", hover_color="#444444"
        )
        self.btn_records.pack(side="left", padx=5, expand=True, fill="x")

        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(
            progress_frame, text="Listo para procesar",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=20)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.progress_bar.set(0)

        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(5, 10))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            log_frame, text="Log de actividad:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.log_text = ctk.CTkTextbox(
            log_frame, font=ctk.CTkFont(family="Consolas", size=11),
            state="disabled"
        )
        self.log_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def _create_stat_box(self, parent, title, value, color):
        frame = ctk.CTkFrame(parent, fg_color=color, corner_radius=10)
        ctk.CTkLabel(
            frame, text=title, font=ctk.CTkFont(size=11),
            text_color="white"
        ).pack(pady=(10, 0))
        label = ctk.CTkLabel(
            frame, text=value, font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        label.pack(pady=(0, 10))
        frame._value_label = label
        return frame

    def _update_stat(self, stat_frame, value):
        stat_frame._value_label.configure(text=str(value))

    def scan_folder(self):
        folder = self.folder_var.get()
        if not folder:
            return
        files = self.file_manager.scan_folder(folder, SUPPORTED_EXTENSIONS)
        self._update_stat(self.stat_files, len(files))

    def _log(self, message: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _start_processing(self):
        folder = self.folder_var.get()
        if not folder:
            messagebox.showwarning(
                "Sin carpeta",
                "Selecciona una carpeta de pasajes primero"
            )
            return
        if self.processing:
            return

        self.processing = True
        self.btn_process.configure(state="disabled", text="Procesando...")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._update_stat(self.stat_processed, 0)
        self._update_stat(self.stat_duplicates, 0)
        self._update_stat(self.stat_errors, 0)
        self.progress_bar.set(0)
        self.progress_label.configure(text="Iniciando procesamiento...")

        thread = threading.Thread(
            target=self._process_thread, args=(folder,), daemon=True
        )
        thread.start()

    def _process_thread(self, folder: str):
        def progress_callback(current, total, filename):
            self.after(0, lambda: self._update_progress(current, total, filename))

        processor = TicketProcessor(progress_callback=progress_callback)
        result = processor.process_folder(folder)
        self.after(0, lambda: self._on_processing_complete(result))

    def _update_progress(self, current: int, total: int, filename: str):
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        self.progress_label.configure(
            text=f"Procesando {current}/{total}: {filename}"
        )

    def _on_processing_complete(self, result: ProcessingResult):
        self.processing = False
        self.btn_process.configure(state="normal", text="PROCESAR PASAJES")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Procesamiento completado")

        self._update_stat(self.stat_processed, result.procesados)
        self._update_stat(self.stat_duplicates, result.duplicados)
        self._update_stat(self.stat_errors, result.errores)

        self._log(f"--- RESUMEN ---")
        self._log(f"Total archivos: {result.total_archivos}")
        self._log(f"Procesados: {result.procesados}")
        self._log(f"Duplicados: {result.duplicados}")
        self._log(f"Errores: {result.errores}")

        for detail in result.detalles:
            self._log(f"  {detail}")

        if result.procesados > 0:
            try:
                from excel.exporter import ExcelExporter
                from database.repository import PasajeRepository
                repo = PasajeRepository()
                excel = ExcelExporter()
                records = repo.obtener_todos()
                excel.export_from_records(records)
                self._log(f"Excel actualizado: {len(records)} registros totales")
            except Exception as e:
                self._log(f"Error al exportar Excel: {e}")

        if result.errores > 0:
            messagebox.showwarning(
                "Completado con errores",
                f"Se procesaron {result.procesados} archivos.\n"
                f"{result.duplicados} duplicados omitidos.\n"
                f"{result.errores} errores (ver Log.txt)"
            )
        else:
            messagebox.showinfo(
                "Completado",
                f"Procesamiento exitoso.\n"
                f"{result.procesados} registros nuevos.\n"
                f"{result.duplicados} duplicados omitidos.\n"
                f"Excel actualizado automáticamente."
            )

    def _export_excel(self):
        from excel.exporter import ExcelExporter
        from database.repository import PasajeRepository
        try:
            repo = PasajeRepository()
            excel = ExcelExporter()
            records = repo.obtener_todos()
            excel.export_from_records(records)
            messagebox.showinfo(
                "Exportar Excel",
                f"Archivo Excel exportado correctamente en:\n{excel.excel_path}\n"
                f"Total registros: {len(records)}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar Excel:\n{e}")
