import os
import json
import tempfile
import shutil
import threading
import sys
from pathlib import Path
def atomic_write_json(path, data):
    try:
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=path_obj.parent,
            prefix='.tmp_',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as tmp:
            json.dump(data, tmp, indent=4, ensure_ascii=False)
            tmp_path = tmp.name
        if os.name == 'nt':
            try:
                os.replace(tmp_path, path)
            except (PermissionError, OSError):
                shutil.move(tmp_path, path)
        else:
            os.replace(tmp_path, path)
        return True
    except Exception:
        if 'tmp_path' in locals() and Path(tmp_path).exists():
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
        return False
class ThreadSafeList:
    def __init__(self):
        self._list = []
        self._lock = threading.RLock()
    def append(self, item):
        with self._lock:
            self._list.append(item)
    def remove(self, item):
        with self._lock:
            if item in self._list:
                self._list.remove(item)
    def clear(self):
        with self._lock:
            self._list.clear()
    def get_all(self):
        with self._lock:
            return self._list.copy()
    def __len__(self):
        with self._lock:
            return len(self._list)
    def __contains__(self, item):
        with self._lock:
            return item in self._list
def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
        if relative_path.startswith('../assets/'):
            relative_path = relative_path[3:]
    else:
        base_path = Path(__file__).resolve().parent
    try:
        candidate = base_path / relative_path
        resolved = candidate.resolve()
        return str(resolved)
    except Exception as e:
        from edmrn.logger import get_logger
        logger = get_logger('resource_path')
        logger.error(f"resource_path: Exception for {relative_path}: {e}")
        fallback = base_path / relative_path
        return str(fallback)
