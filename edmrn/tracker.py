import threading
import json
import math
from pathlib import Path
import customtkinter as ctk
from edmrn.logger import get_logger
from edmrn.config import AppConfig
from edmrn.icons import Icons
logger = get_logger('Tracker')
STATUS_VISITED = 'visited'
STATUS_SKIPPED = 'skipped'
STATUS_UNVISITED = 'unvisited'
COLOR_VISITED = '#4CAF50'
COLOR_SKIPPED = '#FFA500'
COLOR_DEFAULT_TEXT = ('#E0E0E0', '#E0E0E0')
class ThreadSafeRouteManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._route = []
        self._route_names = set()
    def __enter__(self):
        self._lock.acquire()
        return self._route
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
    def load_route(self, route_data):
        with self._lock:
            self._route = route_data.copy()
            self._route_names = {item.get('name', '') for item in route_data}
    def get_route(self):
        with self._lock:
            return self._route.copy()
    def update_system_status(self, system_name, status):
        with self._lock:
            for item in self._route:
                if item.get('name') == system_name:
                    if item.get('status') != status:
                        item['status'] = status
                        return True
                    return False
            return False
    def contains_system(self, system_name):
        with self._lock:
            return system_name in self._route_names
    def clear(self):
        with self._lock:
            self._route.clear()
            self._route_names.clear()
class RouteTracker:
    def __init__(self, route_manager):
        self.route_manager = route_manager
        self.total_distance_ly = 0.0
        self.traveled_distance_ly = 0.0
        self.average_jump_range = 70.0
    def load_route(self, route_data):
        self.route_manager.load_route(route_data)
        return route_data
    def load_route_status(self, custom_path: str = None):
        try:
            if custom_path is None:
                temp_path = Path(AppConfig.get_app_data_path()) / "temp_route_status.json"
                if temp_path.exists():
                    custom_path = str(temp_path)
            if custom_path is None or not Path(custom_path).exists():
                return []
            with open(custom_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                logger.warning(f"Route status data is not a list: {type(data)}")
                return []
            for item in data:
                name = item.get("name")
                status = item.get("status")
                if name and status:
                    self.route_manager.update_system_status(name, status)
            logger.info(f"Route status loaded from backup for {len(data)} systems")
            try:
                if "temp_route_status.json" in custom_path:
                    Path(custom_path).unlink()
            except Exception:
                pass
            return data
        except Exception as e:
            logger.error(f"Failed to load route status: {e}")
            return []
    def update_system_status(self, system_name, status):
        return self.route_manager.update_system_status(system_name, status)
    def save_route_status(self, backup_folder=None):
        route_data = self.route_manager.get_route()
        if not route_data:
            logger.warning("No route data to save")
            return False
        if backup_folder is None:
            logger.debug("No backup folder specified, skipping main directory save")
            return False
        try:
            backup_path = Path(backup_folder)
            if not backup_path.exists():
                backup_path.mkdir(parents=True, exist_ok=True)
            status_path = backup_path / "route_status.json"
            save_data = []
            for item in route_data:
                save_data.append({
                    'name': item.get('name', ''),
                    'status': item.get('status', STATUS_UNVISITED)
                })
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Route status saved to backup: {backup_path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save route status: {e}")
            return False
    def get_next_unvisited_system(self):
        with self.route_manager as route:
            for item in route:
                if item.get('status') == STATUS_UNVISITED:
                    return item.get('name')
            return None
    def update_route_statistics(self, ship_jump_range=70.0):
        route_data = self.route_manager.get_route()
        if not route_data or len(route_data) < 2:
            self.total_distance_ly = 0.0
            self.traveled_distance_ly = 0.0
            self.average_jump_range = ship_jump_range
            return
        total_distance = 0.0
        for i in range(len(route_data) - 1):
            coords1 = route_data[i]['coords']
            coords2 = route_data[i + 1]['coords']
            distance = math.sqrt(
                (coords2[0] - coords1[0])**2 +
                (coords2[1] - coords1[1])**2 +
                (coords2[2] - coords1[2])**2
            )
            total_distance += distance
        self.total_distance_ly = total_distance
        traveled_distance = 0.0
        last_visited_index = -1
        for i, item in enumerate(route_data):
            if item.get('status') == STATUS_VISITED:
                last_visited_index = i
        if last_visited_index < 0:
            self.traveled_distance_ly = 0.0
        else:
            for i in range(last_visited_index):
                coords1 = route_data[i]['coords']
                coords2 = route_data[i + 1]['coords']
                distance = math.sqrt(
                    (coords2[0] - coords1[0])**2 +
                    (coords2[1] - coords1[1])**2 +
                    (coords2[2] - coords1[2])**2
                )
                traveled_distance += distance
            self.traveled_distance_ly = traveled_distance
        total_jumps = 0
        for i in range(len(route_data) - 1):
            coords1 = route_data[i]['coords']
            coords2 = route_data[i + 1]['coords']
            distance = math.sqrt(
                (coords2[0] - coords1[0])**2 +
                (coords2[1] - coords1[1])**2 +
                (coords2[2] - coords1[2])**2
            )
            jumps_for_segment = math.ceil(distance / ship_jump_range)
            total_jumps += jumps_for_segment
        if total_jumps > 0:
            self.average_jump_range = total_distance / total_jumps
        else:
            self.average_jump_range = ship_jump_range
    def get_progress_info(self):
        route_data = self.route_manager.get_route()
        if not route_data:
            return "No route loaded"
        visited_count = sum(1 for item in route_data if item.get('status') == STATUS_VISITED)
        skipped_count = sum(1 for item in route_data if item.get('status') == STATUS_SKIPPED)
        total_count = len(route_data)
        unvisited_count = total_count - visited_count - skipped_count
        return f"Total: {total_count} | Visited: {visited_count} | Skipped: {skipped_count} | Remaining: {unvisited_count}"
    def get_overlay_data(self, app_instance):
        if not app_instance:
            return None
        try:
            route_data = self.route_manager.get_route()
            if not route_data:
                return {
                    'current_system': 'No Route',
                    'current_status': 'READY',
                    'bodies_to_scan': ['Load route...'],
                    'next_system': 'N/A',
                    'progress': '0/0 (0%)',
                    'total_distance': '0.00 LY',
                    'traveled_distance': '0.00 LY'
                }
            current_system = None
            current_status = 'unvisited'
            visited = [item for item in route_data if item.get('status') == STATUS_VISITED]
            unvisited = [item for item in route_data if item.get('status') == STATUS_UNVISITED]
            if visited:
                current_system = visited[-1]
                current_status = 'visited'
            elif unvisited:
                current_system = unvisited[0]
            else:
                current_system = route_data[0] if route_data else None
            next_system = "Complete"
            if current_system and route_data:
                current_index = next((i for i, item in enumerate(route_data)
                                   if item['name'] == current_system['name']), -1)
                if current_index < len(route_data) - 1:
                    next_system = route_data[current_index + 1]['name']
            total = len(route_data)
            visited_count = len(visited)
            progress_pct = int((visited_count / total) * 100) if total > 0 else 0
            progress_text = f"{visited_count}/{total} ({progress_pct}%)"
            ship_jump_range = float(getattr(app_instance, 'jump_range', ctk.StringVar(value="70.0")).get() or "70.0")
            total_jumps = 0
            traveled_jumps = 0
            last_visited_index = -1
            for i, item in enumerate(route_data):
                if item.get('status') == STATUS_VISITED:
                    last_visited_index = i
            for i in range(len(route_data) - 1):
                coords1 = route_data[i]['coords']
                coords2 = route_data[i + 1]['coords']
                distance = math.sqrt(
                    (coords2[0] - coords1[0])**2 +
                    (coords2[1] - coords1[1])**2 +
                    (coords2[2] - coords1[2])**2
                )
                segment_jumps = math.ceil(distance / ship_jump_range)
                total_jumps += segment_jumps
                if i <= last_visited_index:
                    traveled_jumps += segment_jumps
            progress_text += f"\n{Icons.ROCKET} {traveled_jumps}/{total_jumps} jumps"
            bodies = []
            if current_system:
                bodies = current_system.get('bodies_to_scan', [])
                simplified = []
                prefix = f"{current_system['name']} "
                for body in bodies:
                    if isinstance(body, str) and body.startswith(prefix):
                        simplified.append(body[len(prefix):])
                    else:
                        simplified.append(str(body))
                bodies = simplified
            return {
                'current_system': current_system['name'] if current_system else 'Unknown',
                'current_status': current_status,
                'bodies_to_scan': bodies if bodies else ['No bodies to scan'],
                'next_system': next_system,
                'progress': progress_text,
                'total_distance': f"{self.total_distance_ly:.2f} LY",
                'traveled_distance': f"{self.traveled_distance_ly:.2f} LY",
                'distance': f"{self.traveled_distance_ly:.2f}/{self.total_distance_ly:.2f} LY"
            }
        except Exception as e:
            logger.error(f"Overlay data error: {e}")
            return None
