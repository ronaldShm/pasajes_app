"""Sistema de respaldo automático y manual de la base de datos."""
import shutil
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from config import DB_PATH, DB_NAME, BACKUP_DIR
from utils.logger import AppLogger


def _wal_checkpoint(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA wal_checkpoint(FULL)")
    conn.close()


def backup_db() -> Path:
    _wal_checkpoint(DB_PATH)
    BACKUP_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    dest = BACKUP_DIR / f"pasajes_{today}.db"
    shutil.copy2(DB_PATH, dest)
    for ext in ("-wal", "-shm"):
        src = DB_PATH.parent / f"{DB_NAME}{ext}"
        if src.exists():
            shutil.copy2(src, BACKUP_DIR / f"pasajes_{today}.db{ext}")
    logger = AppLogger()
    logger.log_info(f"Backup creado: {dest.name}")
    return dest


def restore_db(backup_path: Path) -> None:
    for conn_attempt in range(3):
        try:
            shutil.copy2(backup_path, DB_PATH)
            break
        except PermissionError:
            time.sleep(0.5)
    for ext in ("-wal", "-shm"):
        src_wal = backup_path.parent / f"{backup_path.name}{ext}"
        dst_wal = DB_PATH.parent / f"{DB_PATH.name}{ext}"
        if src_wal.exists():
            shutil.copy2(src_wal, dst_wal)
        elif dst_wal.exists():
            dst_wal.unlink()
    _wal_checkpoint(DB_PATH)
    logger = AppLogger()
    logger.log_info(f"Backup restaurado: {backup_path.name}")


def list_backups() -> list[Path]:
    if not BACKUP_DIR.exists():
        return []
    seen = set()
    result = []
    for p in sorted(BACKUP_DIR.glob("pasajes_*.db"), reverse=True):
        stem = p.stem
        if stem not in seen:
            seen.add(stem)
            result.append(p)
    return result


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
