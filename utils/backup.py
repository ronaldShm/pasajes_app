"""Sistema de respaldo automático y manual de la base de datos."""
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from config import DB_PATH, BACKUP_DIR
from utils.logger import AppLogger


def backup_db() -> Path:
    BACKUP_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    dest = BACKUP_DIR / f"pasajes_{today}.db"
    shutil.copy2(DB_PATH, dest)
    logger = AppLogger()
    logger.log_info(f"Backup creado: {dest.name}")
    return dest


def restore_db(backup_path: Path) -> None:
    shutil.copy2(backup_path, DB_PATH)
    logger = AppLogger()
    logger.log_info(f"Backup restaurado: {backup_path.name}")


def list_backups() -> list[Path]:
    if not BACKUP_DIR.exists():
        return []
    return sorted(BACKUP_DIR.glob("pasajes_*.db"), reverse=True)


class BackupScheduler:
    def __init__(self):
        self._running = False
        self._thread = None
        self._last_backup_date = None
        self.logger = AppLogger()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.logger.log_info("Backup scheduler iniciado (L-V 16:00)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.logger.log_info("Backup scheduler detenido")

    def _loop(self):
        while self._running:
            now = datetime.now()
            if (now.weekday() < 5
                    and now.hour == 16
                    and now.minute == 0
                    and self._last_backup_date != now.date()):
                try:
                    backup_db()
                    self._last_backup_date = now.date()
                except Exception as e:
                    self.logger.log_error("backup_auto", str(e))
            time.sleep(60)
