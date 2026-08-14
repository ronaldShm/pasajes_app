"""Gestión de archivos y carpetas."""
import shutil
import time
from pathlib import Path
from config import PROCESADOS_DIR, ERRORES_DIR


class FileManager:
    def create_folder(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)

    def move_to_processed(self, file_path: Path, base_folder: Path):
        dest = base_folder / PROCESADOS_DIR / file_path.name
        dest = self._get_unique_path(dest)
        self._safe_move(file_path, dest)

    def move_to_errors(self, file_path: Path, base_folder: Path):
        dest = base_folder / ERRORES_DIR / file_path.name
        dest = self._get_unique_path(dest)
        self._safe_move(file_path, dest)

    def _safe_move(self, src: Path, dest: Path, retries: int = 3, delay: float = 0.5):
        for attempt in range(retries):
            try:
                shutil.move(str(src), str(dest))
                return
            except PermissionError:
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    shutil.copy2(str(src), str(dest))
                    src.unlink()

    def _get_unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def scan_folder(self, folder_path: str, extensions: set) -> list[Path]:
        folder = Path(folder_path)
        if not folder.exists():
            return []
        return [
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        ]
