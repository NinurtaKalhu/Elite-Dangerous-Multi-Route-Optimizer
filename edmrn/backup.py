import threading
import shutil
from datetime import datetime
import atexit
from pathlib import Path
from edmrn.logger import get_logger
from edmrn.config import Paths
from edmrn.utils import atomic_write_json
logger = get_logger('Backup')
class BackupManager:
    def __init__(self, backup_dir, source_dirs, log_callback=None, route_tracker=None):
        self.backup_dir = Path(backup_dir)
        self.source_dirs = [Path(d) for d in source_dirs]
        self.log_callback = log_callback
        self.route_tracker = route_tracker
        self.frequency = 'daily'
        self.max_backups = 10
        self.running = False
        self.timer = None
        self._lock = threading.RLock()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        atexit.register(self._cleanup)
    def _log(self, message):
        logger.info(message)
        if self.log_callback:
            self.log_callback(message)
    def _cleanup(self):
        with self._lock:
            if self.timer:
                try:
                    self.timer.cancel()
                except Exception:
                    pass
                self.timer = None
            self.running = False
    def set_frequency(self, frequency):
        valid_frequencies = ['daily', 'weekly', 'monthly', 'never']
        if frequency not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {valid_frequencies}")
        with self._lock:
            self.frequency = frequency
            if self.running and frequency != 'never':
                self.stop()
                if frequency != 'never':
                    self.start()
            elif frequency == 'never':
                self.stop()
    def start(self):
        with self._lock:
            if self.frequency == 'never':
                return False
            if self.running:
                return False
            self.running = True
            self._schedule_next_backup()
            return True
    def stop(self):
        with self._lock:
            if not self.running:
                return False
            self.running = False
            if self.timer:
                try:
                    self.timer.cancel()
                except Exception:
                    pass
                self.timer = None
            return True
    def _schedule_next_backup(self):
        with self._lock:
            if not self.running or self.frequency == 'never':
                return
            interval = 86400 if self.frequency == 'daily' else \
                       604800 if self.frequency == 'weekly' else \
                       2592000
            self.timer = threading.Timer(interval, self.create_backup)
            self.timer.daemon = True
            self.timer.start()
    def create_backup(self, timestamp_str=None, force_create=False):
        if not force_create and self.route_tracker:
            route_data = self.route_tracker.route_manager.get_route()
            if not route_data:
                logger.debug("No route data, skipping empty backup")
                return None
        if timestamp_str is None:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = Path(Paths.get_backup_subfolder(f"Manual_Backup_{timestamp_str}"))
        try:
            if self.route_tracker:
                route_data = self.route_tracker.route_manager.get_route()
                if route_data:
                    csv_path = backup_folder / "current_route.csv"
                    import pandas as pd
                    rows = []
                    for item in route_data:
                        rows.append({
                            'System Name': item['name'],
                            'X': item['coords'][0],
                            'Y': item['coords'][1],
                            'Z': item['coords'][2],
                            'Status': item['status'],
                            'Bodies': str(item.get('bodies_to_scan', []))
                        })
                    if rows:
                        df = pd.DataFrame(rows)
                        df.to_csv(csv_path, index=False)
                    status_path = backup_folder / "route_status.json"
                    status_data = [{'name': item['name'], 'status': item['status']}
                                  for item in route_data]
                    atomic_write_json(str(status_path), status_data)
            self._log(f"Manual backup created: {backup_folder.name}")
            return str(backup_folder)
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None
    def _cleanup_old_backups(self):
        try:
            backups = sorted(self.backup_dir.iterdir(), key=lambda p: p.stat().st_mtime)
            while len(backups) > self.max_backups:
                old = backups.pop(0)
                if old.is_dir():
                    shutil.rmtree(old)
                else:
                    old.unlink()
        except Exception as e:
            logger.warning(f"Backup cleanup failed: {e}")
    def get_backup_list(self):
        backups = []
        try:
            for folder in sorted(Path(self.backup_dir).iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if folder.is_dir():
                    stats = folder.stat()
                    csv_file = folder / "optimized_route.csv"
                    status_file = folder / "route_status.json"
                    total_size = sum(f.stat().st_size for f in folder.rglob('*') if f.is_file())
                    backups.append({
                        'name': folder.name,
                        'path': str(folder),
                        'csv_path': str(csv_file) if csv_file.exists() else None,
                        'status_path': str(status_file) if status_file.exists() else None,
                        'size_mb': round(total_size / (1024 * 1024), 2),
                        'modified': datetime.fromtimestamp(stats.st_mtime)
                    })
        except Exception as e:
            logger.warning(f"Failed to list backups: {e}")
        return backups
    def restore_backup(self, backup_path):
        try:
            source = Path(backup_path)
            csv_src = source / "optimized_route.csv"
            if csv_src.exists():
                shutil.copy(csv_src, Paths.get_last_csv_file())
            status_src = source / "route_status.json"
            if status_src.exists():
                temp_status = Path(Paths.get_app_data_dir()) / "temp_route_status.json"
                shutil.copy(status_src, temp_status)
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    def get_status(self):
        with self._lock:
            backups = self.get_backup_list()
            total_size = sum(b['size_mb'] for b in backups)
            return {
                'running': self.running,
                'frequency': self.frequency,
                'backup_dir': str(self.backup_dir),
                'source_dirs': [str(d) for d in self.source_dirs],
                'max_backups': self.max_backups,
                'available_backups': len(backups),
                'total_size_mb': round(total_size, 2),
                'last_backup': backups[0]['modified'] if backups else None
            }
