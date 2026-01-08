import requests
import threading
import time
import json
from typing import Dict, List, Optional, Callable
from edmrn.logger import get_logger
from edmrn.icons import Icons
logger = get_logger('Neutron')
class NeutronRouter:
    def __init__(self):
        self.route_api_url = "https://spansh.co.uk/api/route"
        self.results_api_url = "https://spansh.co.uk/api/results"
        self.last_route = []
        self.is_calculating = False
        self.current_waypoint_index = 0
    def calculate_route(self, from_system: str, to_system: str, jump_range: float,
                       fsd_boost: str = "x4", progress_callback: Callable = None) -> Dict:
        if self.is_calculating:
            return {"success": False, "error": "Route calculation already in progress"}
        if from_system.strip().lower() == to_system.strip().lower():
            return {"success": False, "error": "Source and destination cannot be the same system"}
        self.is_calculating = True
        try:
            boost_multiplier = 6.0 if fsd_boost == "x6" else 4.0
            neutron_range = jump_range * boost_multiplier
            supercharge_multiplier = 6 if fsd_boost == "x6" else 4
            if progress_callback:
                progress_callback("Connecting to Spansh API...")
            response = requests.post(
                self.route_api_url,
                params={
                    "efficiency": 60,
                    "range": jump_range,
                    "from": from_system,
                    "to": to_system,
                    "supercharge_multiplier": supercharge_multiplier
                },
                headers={'User-Agent': "EDMRN_NeutronRouter 1.0"},
                timeout=30
            )
            if response.status_code != 202:
                return {"success": False, "error": f"API Error: {response.status_code}"}
            data = response.json()
            job_id = data.get("job")
            if not job_id:
                return {"success": False, "error": "No job ID received"}
            if progress_callback:
                progress_callback("Waiting for route calculation...")
            result_data = self._wait_for_result(job_id, progress_callback)
            if not result_data["success"]:
                return result_data
            route_data = self._process_route_data(result_data["data"], from_system, to_system)
            self.last_route = route_data["waypoints"]
            self.current_waypoint_index = 0
            return {
                "success": True,
                "waypoints": route_data["waypoints"],
                "total_distance": route_data["total_distance"],
                "total_jumps": route_data["total_jumps"],
                "neutron_jumps": route_data["neutron_jumps"],
                "normal_jumps": route_data["normal_jumps"]
            }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout - Spansh API not responding"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection error - Check internet connection"}
        except Exception as e:
            logger.error(f"Neutron route calculation error: {e}")
            return {"success": False, "error": f"Calculation error: {str(e)}"}
        finally:
            self.is_calculating = False
    def _wait_for_result(self, job_id: str, progress_callback: Callable = None) -> Dict:
        max_attempts = 20
        attempt = 0
        while attempt < max_attempts:
            try:
                response = requests.get(f"{self.results_api_url}/{job_id}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return {"success": True, "data": data}
                elif response.status_code != 202:
                    return {"success": False, "error": f"Result API Error: {response.status_code}"}
                if progress_callback:
                    progress_callback(f"Calculating... ({attempt + 1}/20)")
                time.sleep(1)
                attempt += 1
            except Exception as e:
                return {"success": False, "error": f"Result check error: {str(e)}"}
        return {"success": False, "error": "Calculation timeout"}
    def _process_route_data(self, data: Dict, from_system: str, to_system: str) -> Dict:
        waypoints = []
        total_distance = 0.0
        neutron_jumps = 0
        normal_jumps = 0
        result = data.get("result", {})
        system_jumps = result.get("system_jumps", [])
        for jump in system_jumps:
            system_name = jump.get("system", "Unknown")
            distance_jumped = jump.get("distance_jumped", 0.0)
            jumps_count = jump.get("jumps", 1)
            neutron_star = jump.get("neutron_star", False)
            waypoints.append({
                "system": system_name,
                "type": "Neutron" if neutron_star else "Normal",
                "distance": distance_jumped,
                "jumps": jumps_count
            })
            total_distance += distance_jumped
            if neutron_star:
                neutron_jumps += 1
            normal_jumps += jumps_count
        total_jumps = normal_jumps
        return {
            "waypoints": waypoints,
            "total_distance": round(total_distance, 2),
            "total_jumps": total_jumps,
            "neutron_jumps": neutron_jumps,
            "normal_jumps": normal_jumps - neutron_jumps
        }
    def get_current_waypoint(self) -> str:
        if not self.last_route or self.current_waypoint_index >= len(self.last_route):
            return "No route calculated"
        return self.last_route[self.current_waypoint_index]["system"]
    def next_waypoint(self) -> bool:
        if not self.last_route:
            return False
        if self.current_waypoint_index < len(self.last_route) - 1:
            self.current_waypoint_index += 1
            return True
        return False
    def prev_waypoint(self) -> bool:
        if not self.last_route:
            return False
        if self.current_waypoint_index > 0:
            self.current_waypoint_index -= 1
            return True
        return False
    def get_next_waypoint(self) -> str:
        if not self.last_route:
            return ""
        if len(self.last_route) > 0:
            return self.last_route[0]["system"]
        return ""
    def get_route_text(self) -> str:
        if not self.last_route:
            return "No route calculated"
        route_text = []
        for i, waypoint in enumerate(self.last_route):
            system = waypoint["system"]
            wp_type = waypoint["type"]
            jumps = waypoint.get("jumps", 1)
            prefix = ">>> " if i == self.current_waypoint_index else "    "
            if wp_type == "Neutron":
                route_text.append(f"{prefix}{system}")
            else:
                if jumps > 1:
                    route_text.append(f"{prefix}{system} ({jumps} jumps)")
                else:
                    route_text.append(f"{prefix}{system}")
        return "\n".join(route_text)
    def save_neutron_route(self, backup_folder):
        try:
            from pathlib import Path
            import json
            if not self.last_route:
                return False
            backup_path = Path(backup_folder)
            neutron_file = backup_path / "neutron_route.json"
            neutron_data = {
                "waypoints": self.last_route,
                "current_index": self.current_waypoint_index
            }
            with open(neutron_file, 'w', encoding='utf-8') as f:
                json.dump(neutron_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save neutron route: {e}")
            return False
    def load_neutron_route(self, backup_folder):
        try:
            from pathlib import Path
            import json
            backup_path = Path(backup_folder)
            neutron_file = backup_path / "neutron_route.json"
            if not neutron_file.exists():
                return False
            with open(neutron_file, 'r', encoding='utf-8') as f:
                neutron_data = json.load(f)
            self.last_route = neutron_data.get("waypoints", [])
            self.current_waypoint_index = neutron_data.get("current_index", 0)
            return True
        except Exception as e:
            logger.error(f"Failed to load neutron route: {e}")
            return False
    def calculate_route_async(self, from_system: str, to_system: str, jump_range: float,
                            fsd_boost: str, callback: Callable, progress_callback: Callable = None):
        def worker():
            result = self.calculate_route(from_system, to_system, jump_range, fsd_boost, progress_callback)
            callback(result)
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    def get_overlay_data(self) -> Dict:
        current_system = self.get_current_waypoint()
        if current_system == "No route calculated":
            return {
                'current_system': 'No neutron route',
                'current_status': 'NEUTRON',
                'next_system': 'Calculate route first',
                'progress': '0/0',
                'distance': '0.00 LY',
                'bodies_to_scan': ['Calculate neutron route']
            }
        total_waypoints = len(self.last_route)
        current_index = self.current_waypoint_index
        next_system = "End of route"
        if current_index < total_waypoints - 1:
            next_system = self.last_route[current_index + 1]["system"]
        total_distance = sum(wp.get('distance', 0) for wp in self.last_route)
        total_jumps = sum(wp.get('jumps', 1) for wp in self.last_route)
        traveled_distance = sum(wp.get('distance', 0) for wp in self.last_route[:current_index])
        traveled_jumps = sum(wp.get('jumps', 1) for wp in self.last_route[:current_index])
        neutron_progress = f'{Icons.LIGHTNING} {current_index + 1}/{total_waypoints} neutrons'
        jump_progress = f'{Icons.ROCKET} {traveled_jumps}/{total_jumps} jumps'
        return {
            'current_system': current_system,
            'current_status': 'NEUTRON',
            'next_system': next_system,
            'progress': f'{neutron_progress}\n{jump_progress}',
            'distance': f'{traveled_distance:.2f}/{total_distance:.2f} LY',
            'bodies_to_scan': []
        }
