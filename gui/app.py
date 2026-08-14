"""Ventana principal de la aplicación."""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from config import APP_NAME, APP_VERSION, load_config, save_config, SUPPORTED_EXTENSIONS
from gui.home_frame import HomeFrame
from gui.records_frame import RecordsFrame
from utils.file_manager import FileManager


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1000x700")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.file_manager = FileManager()
        self.config_data = load_config()
        self.selected_folder = self.config_data.get("last_folder", "")
        self._setup_ui()
        if self.selected_folder:
            self.home_frame.folder_var.set(self.selected_folder)

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, height=60, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        title_label = ctk.CTkLabel(
            header,
            text=f"  {APP_NAME}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#2E86AB",
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        nav_frame = ctk.CTkFrame(header, fg_color="transparent")
        nav_frame.grid(row=0, column=1, padx=20, pady=15, sticky="e")

        self.btn_home = ctk.CTkButton(
            nav_frame, text="Inicio", width=100,
            command=lambda: self._show_frame("home"),
            fg_color="#2E86AB", hover_color="#1a6d8a"
        )
        self.btn_home.pack(side="left", padx=5)

        self.btn_records = ctk.CTkButton(
            nav_frame, text="Registros", width=100,
            command=lambda: self._show_frame("records"),
            fg_color="#555555", hover_color="#444444"
        )
        self.btn_records.pack(side="left", padx=5)

        self.btn_exit = ctk.CTkButton(
            nav_frame, text="Salir", width=80,
            command=self._on_exit,
            fg_color="#c0392b", hover_color="#a93226"
        )
        self.btn_exit.pack(side="left", padx=5)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.home_frame = HomeFrame(self.container, self)
        self.frames["home"] = self.home_frame
        self.records_frame = RecordsFrame(self.container, self)
        self.frames["records"] = self.records_frame

        self._show_frame("home")

    def _show_frame(self, name: str):
        for frame in self.frames.values():
            frame.grid_forget()
        frame = self.frames[name]
        frame.grid(row=0, column=0, sticky="nsew")
        if name == "home":
            self.btn_home.configure(fg_color="#2E86AB")
            self.btn_records.configure(fg_color="#555555")
        elif name == "records":
            self.btn_home.configure(fg_color="#555555")
            self.btn_records.configure(fg_color="#2E86AB")
            self.records_frame.refresh_data()

    def select_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta de pasajes")
        if folder:
            self.selected_folder = folder
            self.home_frame.folder_var.set(folder)
            self.config_data["last_folder"] = folder
            save_config(self.config_data)
            self.home_frame.scan_folder()

    def _on_exit(self):
        if messagebox.askyesno("Salir", "¿Estás seguro que deseas salir?"):
            self.destroy()
