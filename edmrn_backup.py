import threading
import time
import os
import shutil
import zipfile
from datetime import datetime, timedelta
import logging
import tempfile
import atexit
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path


class BackupManager:
    def __init__(self, 
                 backup_dir: str,
                 source_dirs: List[str],
                 log_callback: Optional[Callable] = None):
        self.backup_dir = Path(backup_dir)
        self.source_dirs = [Path(d) for d in source_dirs]
        self.log_callback = log_callback
        self.frequency = 'daily'
        self.max_backups = 10
        self.running = False
        self.timer: Optional[threading.Timer] = None
        self._lock = threading.RLock()
        
        self.logger = logging.getLogger('EDMRN.Backup')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        atexit.register(self._cleanup)
    
    def _cleanup(self):
        with self._lock:
            if self.timer:
                try:
                    self.timer.cancel()
                except:
                    pass
                self.timer = None
            self.running = False
    
    def set_frequency(self, frequency: str) -> None:
        valid_frequencies = ['daily', 'weekly', 'monthly', 'never']
        if frequency not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {valid_frequencies}")
        
        with self._lock:
            self.frequency = frequency
            self._log(f"Backup frequency set to: {frequency}")
            
            if self.running and frequency != 'never':
                self.stop()
                self.start()
            elif frequency == 'never':
                self.stop()
    
    def start(self) -> bool:
        with self._lock:
            if self.frequency == 'never':
                self._log("Backup scheduler disabled (frequency is 'never')")
                return False
                
            if self.running:
                self._log("Backup scheduler already running")
                return False
            
            self.running = True
            self._schedule_next_backup()
            self._log(f"Backup scheduler started ({self.frequency})")
            return True
    
    def stop(self) -> bool:
        with self._lock:
            if not self.running:
                return False
            
            self.running = False
            if self.timer:
                try:
                    self.timer.cancel()
                except:
                    pass
                self.timer = None
            self._log("Backup scheduler stopped")
            return True
    
    def _schedule_next_backup(self) -> None:
        with self._lock:
            if not self.running or self.frequency == 'never':
                return
            
            interval = self._get_interval_seconds()
            if interval <= 0:
                return
            
            self.timer = threading.Timer(interval, self._perform_backup)
            self.timer.daemon = True
            try:
                self.timer.start()
            except Exception as e:
                self._log(f"Failed to schedule next backup: {e}", level='ERROR')
                self.running = False
                return
            
            next_time = datetime.now() + timedelta(seconds=interval)
            self._log(f"Next backup scheduled for: {next_time.strftime('%Y-%m-%d %H:%M')}")
    
    def _get_interval_seconds(self) -> int:
        if self.frequency == 'daily':
            return 24 * 60 * 60
        elif self.frequency == 'weekly':
            return 7 * 24 * 60 * 60
        elif self.frequency == 'monthly':
            return 30 * 24 * 60 * 60
        else:
            return 0
    
    def _perform_backup(self) -> None:
        try:
            self._log("Starting automated backup...")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"edmrn_backup_{timestamp}.zip"
            
            files_to_backup = []
            for source_dir in self.source_dirs:
                if source_dir.exists():
                    for root, dirs, files in os.walk(source_dir):
                        for file in files:
                            if file.endswith(('.csv', '.json', '.txt', '.log', '.png', '.ico', '.eddb', '.dll', '.edpro')):
                                file_path = Path(root) / file
                                files_to_backup.append(file_path)
            
            if not files_to_backup:
                self._log("No files to backup", level='WARNING')
                return
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_backup:
                    try:
                        for source_dir in self.source_dirs:
                            source_path = Path(source_dir)
                            file_path_obj = Path(file_path)
                            try:
                                if file_path_obj.is_relative_to(source_path):
                                    rel_path = file_path_obj.relative_to(source_path)
                                    arcname = source_path.name / rel_path
                                    zipf.write(file_path_obj, arcname)
                                    break
                            except ValueError:
                                continue
                    except Exception as e:
                        self._log(f"Failed to backup {file_path}: {e}", level='WARNING')
            
            self._log(f"Backup created: {backup_file.name} ({len(files_to_backup)} files)")
            
            self._cleanup_old_backups()
                
        except Exception as e:
            self._log(f"Backup failed: {e}", level='ERROR')
            self.logger.error(f"Backup error: {e}")
            
        finally:
            with self._lock:
                if self.running:
                    self._schedule_next_backup()
    
    def backup_now(self) -> Optional[Path]:
        try:
            self._log("Creating manual backup...")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"edmrn_manual_{timestamp}.zip"
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                files_backed = 0
                for source_dir in self.source_dirs:
                    source_path = Path(source_dir)
                    if source_path.exists():
                        for root, dirs, files in os.walk(source_path):
                            for file in files:
                                if file.endswith(('.csv', '.json', '.txt', '.log', '.png', '.ico', '.eddb', '.dll', '.edpro')):
                                    file_path = Path(root) / file
                                    try:
                                        rel_path = file_path.relative_to(source_path)
                                        arcname = source_path.name / rel_path
                                        zipf.write(file_path, arcname)
                                        files_backed += 1
                                    except Exception as e:
                                        self._log(f"Failed to backup {file}: {e}", level='WARNING')
            
            if files_backed > 0:
                self._log(f"Manual backup created: {backup_file.name} ({files_backed} files)")
                return backup_file
            else:
                self._log("No files backed up", level='WARNING')
                return None
                
        except Exception as e:
            self._log(f"Manual backup failed: {e}", level='ERROR')
            return None
    
    def _cleanup_old_backups(self) -> None:
        try:
            backup_files = list(self.backup_dir.glob("edmrn_*.zip"))
            if not backup_files:
                return
            
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            if len(backup_files) > self.max_backups:
                for old_file in backup_files[self.max_backups:]:
                    try:
                        old_file.unlink()
                        self._log(f"Removed old backup: {old_file.name}")
                    except Exception as e:
                        self._log(f"Failed to remove {old_file.name}: {e}", level='WARNING')
                        
        except Exception as e:
            self._log(f"Backup cleanup failed: {e}", level='WARNING')
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        backups = []
        try:
            backup_files = list(self.backup_dir.glob("*.zip"))
            for file in backup_files:
                try:
                    stats = file.stat()
                    backups.append({
                        'name': file.name,
                        'path': str(file),
                        'size_mb': stats.st_size / (1024 * 1024),
                        'modified': datetime.fromtimestamp(stats.st_mtime),
                        'created': datetime.fromtimestamp(stats.st_ctime)
                    })
                except Exception as e:
                    self._log(f"Failed to get stats for {file}: {e}", level='WARNING')
            
            backups.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            self._log(f"Failed to list backups: {e}", level='WARNING')
        
        return backups
    
    def restore_backup(self, backup_path: str, extract_to: Optional[str] = None) -> bool:
        try:
            if not extract_to:
                extract_to = self.backup_dir.parent
                
            extract_path = Path(extract_to)
            self._log(f"Restoring backup: {os.path.basename(backup_path)}")
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(extract_path)
            
            self._log("Backup restored successfully")
            return True
            
        except Exception as e:
            self._log(f"Restore failed: {e}", level='ERROR')
            return False
    
    def get_status(self) -> Dict[str, Any]:
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
                'total_size_mb': total_size,
                'last_backup': backups[0]['modified'] if backups else None
            }
    
    def cleanup_old_backups(self, keep_count: Optional[int] = None) -> int:
        if keep_count is None:
            keep_count = self.max_backups
        
        try:
            backup_files = list(self.backup_dir.glob("edmrn_*.zip"))
            if len(backup_files) <= keep_count:
                return 0
            
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            removed_count = 0
            for old_file in backup_files[keep_count:]:
                try:
                    old_file.unlink()
                    removed_count += 1
                    self._log(f"Removed old backup: {old_file.name}")
                except Exception as e:
                    self._log(f"Failed to remove {old_file.name}: {e}", level='WARNING')
            
            return removed_count
            
        except Exception as e:
            self._log(f"Backup cleanup failed: {e}", level='WARNING')
            return 0
    
    def _log(self, message: str, level: str = 'INFO') -> None:
        if self.log_callback:
            self.log_callback(f"[Backup] {message}")
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)


def create_backup_manager(backup_dir: str, source_dirs: List[str], log_callback: Optional[Callable] = None) -> BackupManager:
    return BackupManager(backup_dir, source_dirs, log_callback)
