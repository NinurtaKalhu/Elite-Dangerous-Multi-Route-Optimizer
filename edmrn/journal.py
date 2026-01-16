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
        self.current_commander = None
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
            pattern = os.path.join(self.journal_path, 'Journal.*.log')
            list_of_files = glob.glob(pattern)
            if not list_of_files:
                return None
            return max(list_of_files, key=os.path.getmtime)
        except Exception as e:
            logger.error(f"Reading journal directory {self.journal_path}: {e}")
            return None
    def _extract_commander_from_data(self, data: dict):
        for k, v in data.items():
            if 'commander' in str(k).lower():
                return v
        for k in ['Commander', 'CommanderName', 'Cmdr', 'Pilot']:
            if k in data:
                return data[k]
        return None
    def _process_line(self, line):
        try:
            if '"event"' not in line:
                return
            data = json.loads(line)
            event = data.get('event')
            if event in ('LoadGame', 'StartUp'):
                commander = self._extract_commander_from_data(data)
                if commander:
                    self.current_commander = commander
                    logger.debug(f"Detected commander from journal: {commander}")
                return
            if event == 'FSDJump':
                system_name = data.get('StarSystem')
                if self.selected_commander and self.selected_commander != 'Auto' and self.current_commander and self.current_commander != self.selected_commander:
                    return
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
    def detect_commanders(self, max_files: int = 200) -> list:
        commanders = set()
        if not self.journal_path or not os.path.exists(self.journal_path):
            return []
        try:
            pattern = os.path.join(self.journal_path, 'Journal.*.log')
            files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)[:max_files]
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '"event"' in line:
                                try:
                                    data = json.loads(line)
                                    event = data.get('event')
                                    if event in ('LoadGame', 'StartUp'):
                                        cmd = self._extract_commander_from_data(data)
                                        if cmd:
                                            commanders.add(cmd)
                                            break
                                except Exception:
                                    continue
                except Exception:
                    continue
            return sorted(list(commanders))
        except Exception as e:
            logger.error(f"Error detecting commanders: {e}")
            return []
    def detect_current_commander(self, max_files: int = 20) -> str:
        if not self.journal_path or not os.path.exists(self.journal_path):
            return None
        try:
            pattern = os.path.join(self.journal_path, 'Journal.*.log')
            files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)[:max_files]
            best_key = (-1, "")
            best_cmd = None
            for fpath in files:
                try:
                    size = os.path.getsize(fpath)
                    with open(fpath, 'r', encoding='utf-8') as f:
                        f.seek(max(0, size - 8192))
                        lines = f.readlines()
                        for line in reversed(lines):
                            if '"event"' not in line:
                                continue
                            try:
                                data = json.loads(line)
                                event = data.get('event')
                                if event in ('LoadGame', 'StartUp'):
                                    cmd = self._extract_commander_from_data(data)
                                    if cmd:
                                        try:
                                            mtime = os.path.getmtime(fpath)
                                        except Exception:
                                            mtime = 0
                                        key = (mtime, fpath)
                                        if key > best_key:
                                            best_key = key
                                            best_cmd = cmd
                                    break
                            except Exception:
                                continue
                except Exception:
                    continue
            return best_cmd
        except Exception as e:
            logger.error(f"Error reading latest journal files for commander detection: {e}")
            return None
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
    def get_current_system(self):
        try:
            latest_file = self._get_latest_journal_file()
            if not latest_file:
                return None
            current_system = None
            with open(latest_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        event = data.get('event')
                        if event in ['FSDJump', 'Location']:
                            current_system = data.get('StarSystem')
                    except json.JSONDecodeError:
                        continue
            return current_system
        except Exception as e:
            logger.error(f"Error getting current system from journal: {e}")
            return None
    
    def get_current_coordinates(self):
        try:
            latest_file = self._get_latest_journal_file()
            if not latest_file:
                return None
            
            coords = None
            with open(latest_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        event = data.get('event')
                        if event in ['FSDJump', 'Location']:
                            star_pos = data.get('StarPos')
                            if star_pos and isinstance(star_pos, list) and len(star_pos) == 3:
                                coords = tuple(star_pos)
                    except json.JSONDecodeError:
                        continue
            return coords
        except Exception as e:
            logger.error(f"Error getting current coordinates from journal: {e}")
            return None
    
    def stop(self):
        self._stop_event.set()
        logger.info("Journal monitor stopped")
