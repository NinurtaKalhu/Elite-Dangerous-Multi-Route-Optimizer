import threading
import time
import json
import glob
import os
import platform
from edmrn.logger import get_logger

logger = get_logger('Journal')

class JournalMonitor(threading.Thread):
    def __init__(self, callback, manual_journal_path=None, selected_commander=None):
        super().__init__(daemon=True)
        self.callback = callback
        self._stop_event = threading.Event()
        self.last_tell = 0
        self.current_journal_file = None
        self.journal_path = manual_journal_path if manual_journal_path else self._find_journal_dir()
        self.selected_commander = selected_commander
        self.monitor_interval = 2
        self.max_retries = 3
        self._file_lock = threading.Lock()

    def _find_journal_dir(self):
        system = platform.system()
        
        if system == "Windows":
            path = os.path.join(os.path.expanduser('~'), 
                               'Saved Games', 
                               'Frontier Developments', 
                               'Elite Dangerous')
        elif system == "Darwin":
            path = os.path.join(os.path.expanduser('~'),
                               'Library',
                               'Application Support',
                               'Frontier Developments',
                               'Elite Dangerous')
        else:
            path = os.path.join(os.path.expanduser('~'),
                               '.local',
                               'share',
                               'Frontier Developments',
                               'Elite Dangerous')
        
        if os.path.exists(path):
            return path
        else:
            logger.warning(f"Default journal path not found: {path}")
            return None

    def _get_latest_journal_file(self):
        if not self.journal_path:
            return None
        
        try:
            if self.selected_commander and self.selected_commander != "Auto":
                pattern = os.path.join(self.journal_path, f'Journal.*{self.selected_commander}*.log')
            else:
                pattern = os.path.join(self.journal_path, 'Journal.*.log')
                
            list_of_files = glob.glob(pattern)
            if not list_of_files:
                return None
            return max(list_of_files, key=os.path.getmtime)
        except Exception as e:
            logger.error(f"Reading journal directory {self.journal_path}: {e}")
            return None

    def _process_line(self, line):
        try:
            if '"event":"FSDJump"' in line:
                data = json.loads(line)
                system_name = data.get('StarSystem')
                if system_name:
                    self.callback(system_name)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"Journal line processing error: {e}")

    def _tail_file(self, filename):
        if self.current_journal_file != filename:
            self.current_journal_file = filename
            self.last_tell = 0
            logger.info(f"New journal file: {os.path.basename(filename)}")
            
            with open(filename, 'r', encoding='utf-8') as f:
                f.seek(0, 2)
                self.last_tell = f.tell()

        retry_count = 0
        while not self._stop_event.is_set() and retry_count < self.max_retries:
            try:
                with self._file_lock:
                    current_size = os.path.getsize(filename)
                    
                    if current_size < self.last_tell:
                        logger.info("Journal file size reset")
                        self.last_tell = 0
                        continue

                    if current_size > self.last_tell:
                        with open(filename, 'r', encoding='utf-8') as f:
                            f.seek(self.last_tell)
                            new_lines = f.readlines()
                            for line in new_lines:
                                self._process_line(line)
                            self.last_tell = f.tell()
                        retry_count = 0
                        time.sleep(0.1)

            except FileNotFoundError:
                logger.warning("Journal file not found during tailing")
                break
            except PermissionError:
                logger.error("Permission denied reading journal file")
                retry_count += 1
                time.sleep(1)
            except Exception as e:
                retry_count += 1
                logger.error(f"Journal file reading error (attempt {retry_count}): {e}")
                time.sleep(1)
                
        self.current_journal_file = None
            
    def run(self):
        logger.info("Journal monitor started")
        
        while not self._stop_event.is_set():
            try:
                latest_file = self._get_latest_journal_file()
                
                if latest_file and os.path.exists(latest_file):
                    self._tail_file(latest_file)
                else:
                    if not self.journal_path:
                        logger.warning("Journal path not configured")
                    else:
                        logger.info("No journal file found")
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"Journal monitor error: {e}")
                time.sleep(5)

    def stop(self):
        self._stop_event.set()
        logger.info("Journal monitor stopped")