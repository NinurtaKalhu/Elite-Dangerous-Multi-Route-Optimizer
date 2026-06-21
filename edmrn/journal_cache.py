import os
import glob
import json
import hashlib
import threading
import logging
from collections import defaultdict
from edmrn.utils import get_ed_journal_dir

logger = logging.getLogger('JournalCache')


class JournalCache:
    def __init__(self, section):
        self.section = section
        self._journal_events = []
        self._journal_seen_hashes = set()
        self._journal_seen_order = []
        self._journal_cache_ready = False
        self._journal_cache_lock = threading.Lock()
        self._journal_latest_file = None
        self._journal_latest_size = 0
        self._journal_cache_thread = None
        self._journal_dir = get_ed_journal_dir() or os.path.join(os.path.expanduser('~'), 'Saved Games', 'Frontier Developments', 'Elite Dangerous')

    def prime_async(self):
        if self._journal_cache_thread and self._journal_cache_thread.is_alive():
            return
        self._journal_cache_thread = threading.Thread(target=self._prime, daemon=True)
        self._journal_cache_thread.start()

    def _track_seen_line(self, line):
        try:
            h = hashlib.md5(line.encode('utf-8', errors='ignore')).hexdigest()
        except Exception:
            return False
        if h in self._journal_seen_hashes:
            return False
        self._journal_seen_hashes.add(h)
        if len(self._journal_seen_order) >= 200000:
            old = self._journal_seen_order[0]
            try:
                self._journal_seen_hashes.discard(old)
            except Exception:
                pass
        self._journal_seen_order.append(h)
        return True

    def _prime(self):
        pattern = os.path.join(self._journal_dir, 'Journal.*.log')
        files = sorted(glob.glob(pattern), key=os.path.getmtime)
        events = []
        current_tracking_system = None
        try:
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '"event"' not in line:
                                continue
                            if not self._track_seen_line(line):
                                continue
                            try:
                                data = json.loads(line)
                                event_name = data.get('event')
                                if event_name in ('FSDJump', 'Location', 'CarrierJump'):
                                    current_tracking_system = data.get('StarSystem')
                                if not data.get('StarSystem') and current_tracking_system:
                                    data['StarSystem'] = current_tracking_system
                                events.append(data)
                            except Exception:
                                continue
                except Exception:
                    continue
        finally:
            try:
                if files:
                    newest = files[-1]
                    self._journal_latest_file = newest
                    try:
                        self._journal_latest_size = os.path.getsize(newest)
                    except Exception:
                        self._journal_latest_size = 0
                with self._journal_cache_lock:
                    self._journal_events = events
                    self._journal_cache_ready = True
            except Exception:
                pass

    def _tail_lines(self, file_path, n=10, chunk_size=4096):
        lines = []
        try:
            with open(file_path, 'rb') as f:
                f.seek(0, os.SEEK_END)
                end = f.tell()
                buf = b''
                while end > 0 and len(lines) <= n:
                    read_size = min(chunk_size, end)
                    end -= read_size
                    f.seek(end)
                    buf = f.read(read_size) + buf
                    lines = buf.splitlines()
                tail = lines[-n:]
            return [ln.decode('utf-8', errors='ignore') for ln in tail]
        except Exception:
            return []

    def refresh_tail(self):
        pattern = os.path.join(self._journal_dir, 'Journal.*.log')
        files = sorted(glob.glob(pattern), key=os.path.getmtime)
        if not files:
            return
        newest = files[-1]
        try:
            newest_size = os.path.getsize(newest)
        except Exception:
            newest_size = 0
        if newest != self._journal_latest_file or newest_size != self._journal_latest_size:
            tail_lines = self._tail_lines(newest, n=100)
            new_events = []
            current_tracking_system = None
            try:
                with self._journal_cache_lock:
                    for evt in reversed(self._journal_events):
                        if evt.get('event') in ('FSDJump', 'Location', 'CarrierJump'):
                            current_tracking_system = evt.get('StarSystem')
                            break
            except Exception:
                pass
            for line in tail_lines:
                if '"event"' not in line:
                    continue
                if not self._track_seen_line(line):
                    continue
                try:
                    data = json.loads(line)
                    event_name = data.get('event')
                    if event_name in ('FSDJump', 'Location', 'CarrierJump'):
                        current_tracking_system = data.get('StarSystem')
                    if not data.get('StarSystem') and current_tracking_system:
                        data['StarSystem'] = current_tracking_system
                    new_events.append(data)
                except Exception:
                    continue
            if new_events:
                try:
                    with self._journal_cache_lock:
                        self._journal_events.extend(new_events)
                except Exception:
                    pass
            self._journal_latest_file = newest
            self._journal_latest_size = newest_size

    def parse_log_files(self, current_system):
        if not self._journal_cache_ready:
            self.prime_async()
            all_keys = set()
            body_events = defaultdict(list)
            pattern = os.path.join(self._journal_dir, 'Journal.*.log')
            files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)[:10]
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '"event"' not in line:
                                continue
                            try:
                                data = json.loads(line)
                                all_keys.update(data.keys())
                                body_name = data.get('BodyName')
                                if body_name:
                                    if self._should_skip_body(body_name, current_system):
                                        continue
                                    ts = data.get('timestamp') or data.get('Timestamp') or data.get('Time') or data.get('time')
                                    data['Timestamp'] = ts
                                    body_events[body_name].append(data)
                            except Exception:
                                continue
                except Exception:
                    continue
            all_keys = sorted(list(all_keys | {'Timestamp', 'StarSystem', 'BodyName', 'Body'}))
            return all_keys, body_events
        try:
            self.refresh_tail()
        except Exception:
            pass
        try:
            with self._journal_cache_lock:
                events = list(self._journal_events)
        except Exception:
            events = []
        all_keys = set()
        body_events = defaultdict(list)
        for data in events:
            try:
                if not isinstance(data, dict):
                    continue
                data = dict(data)
                all_keys.update(data.keys())
                body_name = data.get('BodyName')
                if body_name:
                    if self._should_skip_body(body_name, current_system):
                        continue
                    ts = data.get('timestamp') or data.get('Timestamp') or data.get('Time') or data.get('time')
                    data['Timestamp'] = ts
                    body_events[body_name].append(data)
            except Exception:
                continue
        all_keys = sorted(list(all_keys | {'Timestamp', 'StarSystem', 'BodyName', 'Body'}))
        return all_keys, body_events

    def _should_skip_body(self, body_name, current_system):
        if not isinstance(body_name, str):
            return False
        body_lower = body_name.lower()
        if 'belt' in body_lower or 'cluster' in body_lower or 'ring' in body_lower:
            return True
        clean_name = body_name
        if current_system and isinstance(current_system, str) and body_name.startswith(current_system):
            clean_name = body_name[len(current_system):].strip()
        if clean_name:
            if len(clean_name) == 1:
                return True
            try:
                float(clean_name)
                return True
            except (ValueError, TypeError):
                pass
        return False
