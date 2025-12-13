import threading
import time
import atexit
from edmrn.logger import get_logger

logger = get_logger('AutoSave')

class AutoSaveManager:
    def __init__(self, save_callback, log_callback=None):
        self.save_callback = save_callback
        self.log_callback = log_callback
        self.interval = 300
        self.running = False
        self.timer = None
        self.last_save_time = 0
        self._lock = threading.RLock()
        
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
    
    def set_interval(self, minutes):
        with self._lock:
            if minutes <= 0:
                self.interval = 0
            else:
                self.interval = minutes * 60
            
            if self.running:
                self.stop()
                if self.interval > 0:
                    self.start()
    
    def start(self):
        with self._lock:
            if self.interval <= 0:
                return False
                
            if self.running:
                return False
            
            self.running = True
            self._schedule_next_save()
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
    
    def _schedule_next_save(self):
        with self._lock:
            if not self.running or self.interval <= 0:
                return
            
            self.timer = threading.Timer(self.interval, self._perform_save)
            self.timer.daemon = True
            try:
                self.timer.start()
            except Exception as e:
                self.running = False
    
    def _perform_save(self):
        try:
            if not self.running:
                return
                
            self.save_callback()
            self.last_save_time = time.time()
            
        except Exception as e:
            logger.error(f"Auto-save error: {e}")
            
        finally:
            with self._lock:
                if self.running:
                    self._schedule_next_save()
    
    def save_now(self):
        try:
            self.save_callback()
            self.last_save_time = time.time()
            return True
            
        except Exception as e:
            logger.error(f"Manual save failed: {e}")
            return False
    
    def get_status(self):
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