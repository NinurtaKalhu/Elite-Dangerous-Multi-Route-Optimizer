import threading
import json
import math
from enum import Enum
from pathlib import Path

from edmrn.logger import get_logger
from edmrn.config import Paths
from edmrn.utils import atomic_write_json

logger = get_logger("Tracker")

# add Enum serialized

class VisitStatus(str, Enum):
    VISITED = "visited"
    SKIPPED = "skipped"
    UNVISITED = "unvisited"


COLOR_VISITED = "#4CAF50"
COLOR_SKIPPED = "#E53935"
COLOR_DEFAULT_TEXT = ("#DCE4EE", "#212121")

def euclidean(a, b):
    return math.sqrt(
        (b[0] - a[0]) ** 2 +
        (b[1] - a[1]) ** 2 +
        (b[2] - a[2]) ** 2
    )

# added thread-safe to Route Manager

class ThreadSafeRouteManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._route = []
        self._route_index = {}

    def __enter__(self):
        self._lock.acquire()
        return self._route

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()

    def load_route(self, route_data):
        with self._lock:
            self._route = route_data.copy()
            self._route_index = {
                item["name"]: item
                for item in self._route
                if "name" in item
            }

    def get_route(self):
        with self._lock:
            return self._route.copy()

    def update_system_status(self, system_name, status: VisitStatus):
        with self._lock:
            item = self._route_index.get(system_name)
            if not item:
                return False

            if item.get("status") != status.value:
                item["status"] = status.value
                return True
            return False

    def contains_system(self, system_name):
        with self._lock:
            return system_name in self._route_index

    def clear(self):
        with self._lock:
            self._route.clear()
            self._route_index.clear()


# Optimized Route Tracker 

class RouteTracker:
    def __init__(self, route_manager: ThreadSafeRouteManager):
        self.route_manager = route_manager
        self.total_distance_ly = 0.0
        self.traveled_distance_ly = 0.0
        self.average_jump_range = 70.0

    def load_route_status(self):
        route_status_file = Paths.get_route_status_file()
        if Path(route_status_file).exists():
            try:
                with open(route_status_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Route status JSON corrupted, ignoring.")
        return []

    def save_route_status(self, route_list):
        route_status_file = Paths.get_route_status_file()
        return atomic_write_json(route_status_file, route_list)

    def get_next_unvisited_system(self):
        with self.route_manager as route:
            for item in route:
                if item.get("status") == VisitStatus.UNVISITED.value:
                    return item.get("name")
        return None

    def update_route_statistics(self, ship_jump_range=70.0):
        route_data = self.route_manager.get_route()

        if len(route_data) < 2:
            self.total_distance_ly = 0.0
            self.traveled_distance_ly = 0.0
            self.average_jump_range = ship_jump_range
            return

# Segmentation
        
        segments = []
        for i in range(len(route_data) - 1):
            segments.append(
                euclidean(
                    route_data[i]["coords"],
                    route_data[i + 1]["coords"]
                )
            )

        self.total_distance_ly = sum(segments)

        last_visited_index = -1
        for i, item in enumerate(route_data):
            if item.get("status") == VisitStatus.VISITED.value:
                last_visited_index = i

        self.traveled_distance_ly = (
            sum(segments[:last_visited_index])
            if last_visited_index > 0 else 0.0
        )

        total_jumps = sum(
            math.ceil(d / ship_jump_range) for d in segments
        )

        self.average_jump_range = (
            self.total_distance_ly / total_jumps
            if total_jumps > 0 else ship_jump_range
        )
        
    def get_progress_info(self):
        route_data = self.route_manager.get_route()
        if not route_data:
            return "No route loaded"

        visited = sum(
            1 for i in route_data
            if i.get("status") == VisitStatus.VISITED.value
        )
        skipped = sum(
            1 for i in route_data
            if i.get("status") == VisitStatus.SKIPPED.value
        )

        total = len(route_data)
        remaining = total - visited - skipped

        return (
            f"Total: {total} | "
            f"Visited: {visited} | "
            f"Skipped: {skipped} | "
            f"Remaining: {remaining}"
        )

    def get_overlay_data(self, app_instance):
        if not app_instance:
            return None

        try:
            route_data = self.route_manager.get_route()

            if not route_data:
                return {
                    "current_system": "No Route",
                    "current_status": "READY",
                    "bodies_to_scan": ["Load route..."],
                    "next_system": "N/A",
                    "progress": "0/0 (0%)",
                    "total_distance": "0.00 LY",
                    "traveled_distance": "0.00 LY",
                }

            visited = [
                i for i in route_data
                if i.get("status") == VisitStatus.VISITED.value
            ]
            unvisited = [
                i for i in route_data
                if i.get("status") == VisitStatus.UNVISITED.value
            ]

            if visited:
                current_system = visited[-1]
                current_status = VisitStatus.VISITED.value
            elif unvisited:
                current_system = unvisited[0]
                current_status = VisitStatus.UNVISITED.value
            else:
                current_system = route_data[0]
                current_status = "unknown"

            idx = route_data.index(current_system)
            next_system = (
                route_data[idx + 1]["name"]
                if idx < len(route_data) - 1
                else "Complete"
            )

            total = len(route_data)
            visited_count = len(visited)
            pct = int((visited_count / total) * 100) if total else 0

            bodies = current_system.get("bodies_to_scan", [])
            prefix = f"{current_system['name']} "
            bodies = [
                b[len(prefix):] if isinstance(b, str) and b.startswith(prefix)
                else str(b)
                for b in bodies
            ] or ["No bodies to scan"]

            return {
                "current_system": current_system["name"],
                "current_status": current_status,
                "bodies_to_scan": bodies,
                "next_system": next_system,
                "progress": f"{visited_count}/{total} ({pct}%)",
                "total_distance": f"{self.total_distance_ly:.2f} LY",
                "traveled_distance": f"{self.traveled_distance_ly:.2f} LY",
            }

        except Exception as e:
            logger.error(f"Overlay data error: {e}")
            return None
