import json
from pathlib import Path
from datetime import datetime
from edmrn.config import Paths
from edmrn.logger import get_logger

logger = get_logger('VisitHistory')

class VisitHistoryManager:
    
    def __init__(self):
        self.history_file = Path(Paths.get_app_data_dir()) / "visited_systems_history.json"
        self.history = self._load_history()
    
    def _load_history(self):
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load visit history: {e}")
            return {}
    
    def _save_history(self):
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            logger.debug(f"Visit history saved: {len(self.history)} systems")
        except Exception as e:
            logger.error(f"Failed to save visit history: {e}")
    
    def mark_visited(self, system_name, source_file=None):
        if not system_name:
            return
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if system_name not in self.history:
            self.history[system_name] = {
                'first_visit': now,
                'last_visit': now,
                'visit_count': 1,
                'source_files': [source_file] if source_file else []
            }
        else:
            self.history[system_name]['last_visit'] = now
            self.history[system_name]['visit_count'] += 1
            if source_file and source_file not in self.history[system_name]['source_files']:
                self.history[system_name]['source_files'].append(source_file)
        
        self._save_history()
    
    def is_visited(self, system_name):
        return system_name in self.history
    
    def get_visit_info(self, system_name):
        return self.history.get(system_name, None)
    
    def find_visited_systems(self, system_list):
        visited = []
        for system_name in system_list:
            if self.is_visited(system_name):
                info = self.get_visit_info(system_name)
                visited.append({
                    'name': system_name,
                    'first_visit': info['first_visit'],
                    'last_visit': info['last_visit'],
                    'visit_count': info['visit_count']
                })
        return visited
    
    def clear_system(self, system_name):
        if system_name in self.history:
            del self.history[system_name]
            self._save_history()
    
    def clear_all(self):
        self.history = {}
        self._save_history()
        logger.info("Visit history cleared")
    
    def get_total_visited(self):
        return len(self.history)

_history_manager = None

def get_history_manager():
    global _history_manager
    if _history_manager is None:
        _history_manager = VisitHistoryManager()
    return _history_manager
