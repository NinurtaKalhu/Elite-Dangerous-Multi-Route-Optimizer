import sys
import traceback
import threading
import time
import queue
from datetime import datetime
from pathlib import Path
from edmrn.logger import get_logger
from edmrn.config import AppConfig

logger = get_logger('Debug')

class DebugSystem:
    def __init__(self):
        self.error_queue = queue.Queue(maxsize=100)
        self.warning_queue = queue.Queue(maxsize=100)
        self.info_queue = queue.Queue(maxsize=100)
        self.error_count = 0
        self.warning_count = 0
        self.start_time = time.time()
        self._lock = threading.RLock()
        self.subscribers = []
        self.log_level = 'INFO'
        
        self.error_stats = {
            'total': 0,
            'unhandled': 0,
            'gui': 0,
            'thread': 0,
            'io': 0,
            'network': 0,
            'other': 0
        }
        
        self._setup_exception_hook()
        
    def _setup_exception_hook(self):
        def custom_exception_hook(exc_type, exc_value, exc_traceback):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            
            error_msg = f"Unhandled Exception: {exc_type.__name__}: {exc_value}"
            stack_trace = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            logger.error(f"UNHANDLED EXCEPTION:\n{error_msg}\nStack trace:\n{stack_trace}")
            
            self.record_error(
                error_type=exc_type.__name__,
                error_message=str(exc_value),
                stack_trace=stack_trace,
                is_unhandled=True
            )
           
            self._notify_subscribers('error', {
                'type': 'unhandled_exception',
                'message': error_msg,
                'timestamp': datetime.now(),
                'stack_trace': stack_trace
            })
        
        sys.excepthook = custom_exception_hook
    
    def record_error(self, error_type, error_message, stack_trace=None, 
                    module=None, function=None, is_unhandled=False):
        with self._lock:
            self.error_count += 1
            self.error_stats['total'] += 1
            
            if is_unhandled:
                self.error_stats['unhandled'] += 1
            
            if 'gui' in error_type.lower() or 'tkinter' in str(error_message).lower():
                self.error_stats['gui'] += 1
                category = 'GUI'
            elif 'thread' in error_type.lower():
                self.error_stats['thread'] += 1
                category = 'Thread'
            elif any(keyword in str(error_message).lower() for keyword in ['file', 'io', 'read', 'write']):
                self.error_stats['io'] += 1
                category = 'I/O'
            elif any(keyword in str(error_message).lower() for keyword in ['network', 'http', 'socket', 'connection']):
                self.error_stats['network'] += 1
                category = 'Network'
            else:
                self.error_stats['other'] += 1
                category = 'Other'
            
            error_record = {
                'id': self.error_count,
                'timestamp': datetime.now(),
                'type': error_type,
                'category': category,
                'message': error_message,
                'module': module or self._get_calling_module(),
                'function': function or self._get_calling_function(),
                'stack_trace': stack_trace or self._get_current_stack_trace(limit=10),
                'is_unhandled': is_unhandled,
                'thread': threading.current_thread().name
            }
            
            try:
                self.error_queue.put(error_record, timeout=0.1, block=False)
            except queue.Full:
                try:
                    self.error_queue.get_nowait()
                    self.error_queue.put(error_record, timeout=0.1, block=False)
                except:
                    pass
            
            self._notify_subscribers('error', error_record)
            
            return error_record
    
    def record_warning(self, warning_type, warning_message, module=None, function=None):
        with self._lock:
            self.warning_count += 1
            
            warning_record = {
                'id': self.warning_count,
                'timestamp': datetime.now(),
                'type': warning_type,
                'message': warning_message,
                'module': module or self._get_calling_module(),
                'function': function or self._get_calling_function(),
                'thread': threading.current_thread().name
            }
            
            try:
                self.warning_queue.put(warning_record, timeout=0.1, block=False)
            except queue.Full:
                try:
                    self.warning_queue.get_nowait()
                    self.warning_queue.put(warning_record, timeout=0.1, block=False)
                except:
                    pass
            
            self._notify_subscribers('warning', warning_record)
            
            return warning_record
    
    def record_info(self, info_type, info_message, module=None, function=None):
        info_record = {
            'id': self.info_queue.qsize() + 1,
            'timestamp': datetime.now(),
            'type': info_type,
            'message': info_message,
            'module': module or self._get_calling_module(),
            'function': function or self._get_calling_function(),
            'thread': threading.current_thread().name
        }
        
        try:
            self.info_queue.put(info_record, timeout=0.1, block=False)
        except queue.Full:
            try:
                self.info_queue.get_nowait()
                self.info_queue.put(info_record, timeout=0.1, block=False)
            except:
                pass
        
        self._notify_subscribers('info', info_record)
        
        return info_record
    
    def _get_calling_module(self):
        try:
            stack = traceback.extract_stack()
            for frame in reversed(stack[:-2]):
                if 'edmrn' in frame.filename:
                    module_name = Path(frame.filename).stem
                    return module_name
        except:
            pass
        return 'unknown'
    
    def _get_calling_function(self):
        try:
            stack = traceback.extract_stack()
            return stack[-3].name if len(stack) >= 3 else 'unknown'
        except:
            return 'unknown'
    
    def _get_current_stack_trace(self, limit=5):
        try:
            stack = traceback.extract_stack(limit=limit)
            return ''.join(traceback.format_list(stack[:-1]))
        except:
            return "Stack trace unavailable"
    
    def subscribe(self, callback, event_types=None):
        if event_types is None:
            event_types = ['error', 'warning', 'info']
        
        subscriber = {
            'callback': callback,
            'event_types': event_types
        }
        self.subscribers.append(subscriber)
        return subscriber
    
    def unsubscribe(self, subscriber):
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
    
    def _notify_subscribers(self, event_type, data):
        for subscriber in self.subscribers[:]:
            if event_type in subscriber['event_types']:
                try:
                    subscriber['callback'](event_type, data)
                except Exception as e:
                    logger.error(f"Debug subscriber callback error: {e}")
    
    def get_all_errors(self, limit=None):
        errors = list(self.error_queue.queue)
        if limit:
            return errors[:limit]
        return errors
    
    def get_all_warnings(self, limit=None):
        warnings = list(self.warning_queue.queue)
        if limit:
            return warnings[:limit]
        return warnings
    
    def get_all_info(self, limit=None):
        infos = list(self.info_queue.queue)
        if limit:
            return infos[:limit]
        return infos
    
    def get_stats(self):
        with self._lock:
            uptime = time.time() - self.start_time
            hours, remainder = divmod(uptime, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return {
                'uptime': f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
                'error_count': self.error_count,
                'warning_count': self.warning_count,
                'error_stats': self.error_stats.copy(),
                'queue_sizes': {
                    'error_queue': self.error_queue.qsize(),
                    'warning_queue': self.warning_queue.qsize(),
                    'info_queue': self.info_queue.qsize()
                },
                'thread_count': threading.active_count(),
                'log_level': self.log_level,
                'start_time': datetime.fromtimestamp(self.start_time)
            }
    
    def clear_all(self):
        with self._lock:
            while not self.error_queue.empty():
                self.error_queue.get_nowait()
            while not self.warning_queue.empty():
                self.warning_queue.get_nowait()
            while not self.info_queue.empty():
                self.info_queue.get_nowait()
            
            self.error_count = 0
            self.warning_count = 0
    
    def set_log_level(self, level):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        if level.upper() in valid_levels:
            self.log_level = level.upper()
            self.record_info('debug', f"Log level changed to {level}")
            return True
        return False
    
    def export_to_file(self, filename=None):
        if filename is None:
            app_data_dir = Path(AppConfig.get_app_data_path())
            logs_dir = app_data_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            filename = logs_dir / f"debug_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("EDMRN DEBUG EXPORT\n")
                f.write(f"Export Time: {datetime.now()}\n")
                f.write("=" * 80 + "\n\n")
                
                stats = self.get_stats()
                f.write("STATISTICS:\n")
                f.write("-" * 40 + "\n")
                for key, value in stats.items():
                    if key == 'error_stats':
                        f.write(f"Error Statistics:\n")
                        for stat_key, stat_value in value.items():
                            f.write(f"  {stat_key}: {stat_value}\n")
                    elif key == 'queue_sizes':
                        f.write(f"Queue Sizes:\n")
                        for q_key, q_value in value.items():
                            f.write(f"  {q_key}: {q_value}\n")
                    else:
                        f.write(f"{key}: {value}\n")
                f.write("\n")
                
                f.write("ERRORS:\n")
                f.write("=" * 40 + "\n")
                for error in self.get_all_errors():
                    f.write(f"ID: {error['id']}\n")
                    f.write(f"Time: {error['timestamp']}\n")
                    f.write(f"Type: {error['type']}\n")
                    f.write(f"Category: {error['category']}\n")
                    f.write(f"Module: {error['module']}\n")
                    f.write(f"Function: {error['function']}\n")
                    f.write(f"Thread: {error['thread']}\n")
                    f.write(f"Message: {error['message']}\n")
                    if error.get('stack_trace'):
                        f.write(f"Stack Trace:\n{error['stack_trace']}\n")
                    f.write("-" * 40 + "\n")
                f.write("\n")
                
                f.write("WARNINGS:\n")
                f.write("=" * 40 + "\n")
                for warning in self.get_all_warnings():
                    f.write(f"ID: {warning['id']}\n")
                    f.write(f"Time: {warning['timestamp']}\n")
                    f.write(f"Type: {warning['type']}\n")
                    f.write(f"Module: {warning['module']}\n")
                    f.write(f"Function: {warning['function']}\n")
                    f.write(f"Message: {warning['message']}\n")
                    f.write("-" * 40 + "\n")
                
                f.write("\nINFO MESSAGES:\n")
                f.write("=" * 40 + "\n")
                for info in self.get_all_info()[:50]:
                    f.write(f"ID: {info['id']}\n")
                    f.write(f"Time: {info['timestamp']}\n")
                    f.write(f"Type: {info['type']}\n")
                    f.write(f"Message: {info['message']}\n")
                    f.write("-" * 40 + "\n")
            
            self.record_info('debug', f"Debug data exported to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Debug export failed: {e}")
            return None

_debug_system = None

def get_debug_system():
    global _debug_system
    if _debug_system is None:
        _debug_system = DebugSystem()
    return _debug_system

def catch_and_record_errors(func):
    def wrapper(*args, **kwargs):
        debug_system = get_debug_system()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            
            debug_system.record_error(
                error_type=error_type,
                error_message=error_msg,
                stack_trace=stack_trace,
                module=func.__module__,
                function=func.__name__
            )
            
            raise
    
    return wrapper

def log_execution_time(func):
    def wrapper(*args, **kwargs):
        debug_system = get_debug_system()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:
                debug_system.record_warning(
                    warning_type='slow_execution',
                    warning_message=f"Function '{func.__name__}' took {execution_time:.2f} seconds",
                    module=func.__module__,
                    function=func.__name__
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            debug_system.record_info(
                info_type='execution_failed',
                info_message=f"Function '{func.__name__}' failed after {execution_time:.2f} seconds: {e}",
                module=func.__module__,
                function=func.__name__
            )
            raise
    
    return wrapper