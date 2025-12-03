import threading
import time
import json
import logging
import atexit
from typing import Callable, Optional, Dict, Any
from pathlib import Path


class AutoSaveManager:
    def __init__(self, save_callback: Callable, log_callback: Optional[Callable] = None):
        self.save_callback = save_callback
        self.log_callback = log_callback
        self.interval = 300
        self.running = False
        self.timer: Optional[threading.Timer] = None
        self.last_save_time = 0
        self._lock = threading.RLock()
        
        self.logger = logging.getLogger('EDMRN.AutoSave')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
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
    
    def set_interval(self, minutes: int) -> None:
        with self._lock:
            if minutes <= 0:
                self.interval = 0
                self._log("Auto-save disabled")
            else:
                self.interval = minutes * 60
                self._log(f"Auto-save interval set to {minutes} minutes")
            
            if self.running:
                self.stop()
                if self.interval > 0:
                    self.start()
    
    def start(self) -> bool:
        with self._lock:
            if self.interval <= 0:
                self._log("Auto-save disabled (interval is 0)")
                return False
                
            if self.running:
                self._log("Auto-save already running")
                return False
            
            self.running = True
            self._schedule_next_save()
            self._log(f"Auto-save started (every {self.interval//60} minutes)")
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
            self._log("Auto-save stopped")
            return True
    
    def _schedule_next_save(self) -> None:
        with self._lock:
            if not self.running or self.interval <= 0:
                return
            
            self.timer = threading.Timer(self.interval, self._perform_save)
            self.timer.daemon = True
            try:
                self.timer.start()
            except Exception as e:
                self._log(f"Failed to schedule next save: {e}", level='ERROR')
                self.running = False
    
    def _perform_save(self) -> None:
        try:
            if not self.running:
                return
                
            self._log("Auto-saving...")
            self.save_callback()
            self.last_save_time = time.time()
            self._log("Auto-save completed successfully")
            
        except Exception as e:
            self._log(f"Auto-save failed: {e}", level='ERROR')
            self.logger.error(f"Auto-save error: {e}")
            
        finally:
            with self._lock:
                if self.running:
                    self._schedule_next_save()
    
    def save_now(self) -> bool:
        try:
            self._log("Manual save triggered")
            self.save_callback()
            self.last_save_time = time.time()
            self._log("Manual save completed successfully")
            return True
            
        except Exception as e:
            self._log(f"Manual save failed: {e}", level='ERROR')
            return False
    
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            next_save_in = None
            if self.running and self.last_save_time > 0:
                elapsed = time.time() - self.last_save_time
                next_save_in = max(0, self.interval - elapsed)
            
            return {
                'running': self.running,
                'interval_minutes': self.interval // 60 if self.interval > 0 else 0,
                'last_save_time': self.last_save_time,
                'last_save_formatted': time.strftime('%Y-%m-%d %H:%M:%S', 
                                                   time.localtime(self.last_save_time)) if self.last_save_time > 0 else None,
                'next_save_in': next_save_in,
                'next_save_formatted': time.strftime('%Y-%m-%d %H:%M:%S', 
                                                   time.localtime(self.last_save_time + self.interval)) if self.last_save_time > 0 and self.interval > 0 else None
            }
    
    def _log(self, message: str, level: str = 'INFO') -> None:
        if self.log_callback:
            self.log_callback(f"[AutoSave] {message}")
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)


def create_autosave_manager(save_callback: Callable, log_callback: Optional[Callable] = None) -> AutoSaveManager:
    return AutoSaveManager(save_callback, log_callback)
