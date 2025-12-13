import os
import json
import tempfile
import shutil
import threading
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

def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path.cwd()
    return str(base_path / relative_path)