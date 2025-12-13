import threading
import time
import os
import shutil
import zipfile
from datetime import datetime, timedelta
import atexit
from pathlib import Path
from edmrn.logger import get_logger

logger = get_logger('Backup')

class BackupManager:
    def __init__(self, backup_dir, source_dirs, log_callback=None):
        self.backup_dir = Path(backup_dir)
        self.source_dirs = [Path(d) for d in source_dirs]
        self.log_callback = log_callback
        self.frequency = 'daily'
        self.max_backups = 10
        self.running = False
        self.timer = None
        self._lock = threading.RLock()
        
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
    
    def set_frequency(self, frequency):
        valid_frequencies = ['daily', 'weekly', 'monthly', 'never']
        if frequency not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {valid_frequencies}")
        
        with self._lock:
            self.frequency = frequency
            
            if self.running and frequency != 'never':
                self.stop()
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
                except:
                    pass
                self.timer = None
            return True
    
    def _schedule_next_backup(self):
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
                self.running = False
                return
    
    def _get_interval_seconds(self):
        if self.frequency == 'daily':
            return 24 * 60 * 60
        elif self.frequency == 'weekly':
            return 7 * 24 * 60 * 60
        elif self.frequency == 'monthly':
            return 30 * 24 * 60 * 60
        else:
            return 0
    
    def _perform_backup(self):
        try:
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
                        logger.warning(f"Failed to backup {file_path}: {e}")
            
            self._cleanup_old_backups()
                
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            
        finally:
            with self._lock:
                if self.running:
                    self._schedule_next_backup()
    
    def backup_now(self):
        try:
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
                                        logger.warning(f"Failed to backup {file}: {e}")
            
            if files_backed > 0:
                return backup_file
            else:
                return None
                
        except Exception as e:
            logger.error(f"Manual backup failed: {e}")
            return None
    
    def _cleanup_old_backups(self):
        try:
            backup_files = list(self.backup_dir.glob("edmrn_*.zip"))
            if not backup_files:
                return
            
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            if len(backup_files) > self.max_backups:
                for old_file in backup_files[self.max_backups:]:
                    try:
                        old_file.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to remove {old_file.name}: {e}")
                        
        except Exception as e:
            logger.warning(f"Backup cleanup failed: {e}")
    
    def get_backup_list(self):
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
                    logger.warning(f"Failed to get stats for {file}: {e}")
            
            backups.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            logger.warning(f"Failed to list backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_path, extract_to=None):
        try:
            if not extract_to:
                extract_to = self.backup_dir.parent
                
            extract_path = Path(extract_to)
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(extract_path)
            
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
                'total_size_mb': total_size,
                'last_backup': backups[0]['modified'] if backups else None
            }