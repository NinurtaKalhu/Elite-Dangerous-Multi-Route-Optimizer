import requests
import json
import time
from typing import Optional, Dict, Any, Callable, List
from edmrn.logger import get_logger

logger = get_logger('GalaxyPlotter')

STATUS_VISITED = 'visited'
STATUS_UNVISITED = 'unvisited'


class GalaxyPlotter:
    
    def __init__(self):
        self.route_api = "https://spansh.co.uk/api/route"
        self.results_api = "https://spansh.co.uk/api/results"
        
    def submit_route_job(self,
                        source_system: str,
                        destination_system: str,
                        range_ly: float = 50.0,
                        efficiency: int = 60,
                        supercharge: bool = True,
                        progress_callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        try:
            if progress_callback:
                progress_callback(f"Submitting route calculation to Spansh API...")
            
            supercharge_multiplier = 6 if supercharge else 4
            
            params = {
                "from": source_system,
                "to": destination_system,
                "range": range_ly,
                "efficiency": efficiency,
                "supercharge_multiplier": supercharge_multiplier,
            }
            
            logger.debug(f"Submitting route params: {params}")
            
            response = requests.post(
                self.route_api,
                params=params,
                timeout=30,
                headers={'User-Agent': "EDMRN 3.0"}
            )
            
            if response.status_code != 202:
                error_msg = response.text
                logger.error(f"Failed to submit route job: {response.status_code} - {error_msg}")
                if progress_callback:
                    progress_callback(f"Error: {error_msg}")
                return None
            
            data = response.json()
            job_id = data.get("job")
            
            if not job_id:
                logger.error(f"No job ID in response: {data}")
                if progress_callback:
                    progress_callback("Error: No job ID received from Spansh")
                return None
            
            logger.info(f"Route job submitted: {job_id}")
            return job_id
            
        except requests.RequestException as e:
            logger.error(f"Network error submitting route: {e}")
            if progress_callback:
                progress_callback(f"Network error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error submitting route: {e}")
            if progress_callback:
                progress_callback(f"Error: {e}")
            return None
    
    def poll_route_results(self,
                          job_id: str,
                          max_wait: int = 300,
                          progress_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        try:
            if progress_callback:
                progress_callback(f"Waiting for route calculation...\nJob ID: {job_id}")
            
            results_url = f"{self.results_api}/{job_id}"
            elapsed = 0
            poll_interval = 1
            
            while elapsed < max_wait:
                try:
                    response = requests.get(results_url, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Route calculation complete")
                        return data
                    
                    elif response.status_code == 202:
                        elapsed += poll_interval
                        if progress_callback:
                            progress_callback(f"Calculating route...\nElapsed: {elapsed}s")
                        time.sleep(poll_interval)
                        poll_interval = min(5, poll_interval + 0.5)
                        continue
                    
                    else:
                        error_msg = response.text
                        logger.error(f"Error polling route: {response.status_code} - {error_msg}")
                        if progress_callback:
                            progress_callback(f"Error: {error_msg}")
                        return None
                
                except requests.RequestException as e:
                    logger.error(f"Network error polling route: {e}")
                    if progress_callback:
                        progress_callback(f"Network error: {e}")
                    return None
            
            logger.error(f"Route calculation timeout after {max_wait}s")
            if progress_callback:
                progress_callback(f"Timeout: Route calculation took too long")
            return None
            
        except Exception as e:
            logger.error(f"Error polling route: {e}")
            if progress_callback:
                progress_callback(f"Error: {e}")
            return None
    
    def plot_route(self,
                   source_system: str,
                   destination_system: str,
                   ship_build: str,
                   cargo: int = 0,
                   reserve_fuel: float = 0.0,
                   already_supercharged: bool = False,
                   use_supercharge: bool = True,
                   use_injections: bool = False,
                   exclude_secondary: bool = True,
                   refuel_every_scoopable: bool = True,
                   routing_algorithm: str = "optimistic",
                   progress_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        try:
            efficiency = 60 if routing_algorithm == "optimistic" else 80
            
            job_id = self.submit_route_job(
                source_system, destination_system,
                range_ly=50.0,
                efficiency=efficiency,
                supercharge=use_supercharge,
                progress_callback=progress_callback
            )
            
            if not job_id:
                return None
            
            route_data = self.poll_route_results(job_id, max_wait=300, progress_callback=progress_callback)
            
            return route_data
            
        except Exception as e:
            logger.error(f"Error plotting route: {e}")
            if progress_callback:
                progress_callback(f"Error: {e}")
            return None
    
    def extract_system_jumps(self, route_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not route_data:
            return []
        
        try:
            jumps = route_data.get("result", {}).get("system_jumps", [])
            for jump in jumps:
                if 'status' not in jump:
                    jump['status'] = STATUS_UNVISITED
            return jumps
        except:
            return []
    
    def format_route_summary(self, route_data: Dict[str, Any]) -> str:
        if not route_data or "result" not in route_data:
            return "No route data available"
        
        result = route_data["result"]
        system_jumps = result.get("system_jumps", [])
        
        summary = []
        summary.append(f"Total jumps: {len(system_jumps)}")
        summary.append(f"Total distance: {result.get('distance', 0):.2f} LY")
        
        neutron_count = sum(1 for jump in system_jumps if jump.get("neutron_star", False))
        summary.append(f"Neutron boosts: {neutron_count}")
        
        refuel_count = sum(1 for jump in system_jumps if jump.get("refuel", False))
        summary.append(f"Refuel stops: {refuel_count}")
        
        return "\n".join(summary)
    
    def export_route_to_csv(self, route_data: Dict[str, Any], filename: str) -> bool:
        try:
            if not route_data or "result" not in route_data:
                return False
            
            system_jumps = route_data["result"].get("system_jumps", [])
            
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["System", "Distance", "Jumps", "Neutron", "Refuel", "Coordinates"])
                
                for jump in system_jumps:
                    system_name = jump.get("system", "")
                    distance = jump.get("distance_jumped", 0)
                    jumps = jump.get("jumps", 0)
                    neutron = "Yes" if jump.get("neutron_star", False) else "No"
                    refuel = "Yes" if jump.get("refuel", False) else "No"
                    coords = jump.get("coords", {})
                    coord_str = f"{coords.get('x', 0):.2f}, {coords.get('y', 0):.2f}, {coords.get('z', 0):.2f}"
                    
                    writer.writerow([system_name, f"{distance:.2f}", jumps, neutron, refuel, coord_str])
            
            logger.info(f"Route exported to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export route to CSV: {e}")
            return False
    
    def save_galaxy_route(self, backup_folder: str, waypoints: List[Dict[str, Any]], current_index: int) -> bool:
        try:
            from pathlib import Path
            
            if not waypoints:
                return False
            
            backup_path = Path(backup_folder)
            galaxy_file = backup_path / "galaxy_route.json"
            
            galaxy_data = {
                "waypoints": waypoints,
                "current_index": current_index
            }
            
            with open(galaxy_file, 'w', encoding='utf-8') as f:
                json.dump(galaxy_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Galaxy route saved to {galaxy_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save galaxy route: {e}")
            return False
    
    def load_galaxy_route(self, backup_folder: str) -> Optional[Dict[str, Any]]:
        try:
            from pathlib import Path
            
            backup_path = Path(backup_folder)
            galaxy_file = backup_path / "galaxy_route.json"
            
            if not galaxy_file.exists():
                return None
            
            with open(galaxy_file, 'r', encoding='utf-8') as f:
                galaxy_data = json.load(f)
            
            logger.info(f"Galaxy route loaded from {galaxy_file}")
            return galaxy_data
            
        except Exception as e:
            logger.error(f"Failed to load galaxy route: {e}")
            return None
    
    def mark_waypoint_as_visited(self, waypoints: List[Dict[str, Any]], index: int) -> bool:
        if not waypoints or index < 0 or index >= len(waypoints):
            return False
        waypoints[index]['status'] = STATUS_VISITED
        return True
    
    def update_waypoint_status(self, waypoints: List[Dict[str, Any]], system_name: str, status: str) -> bool:
        for waypoint in waypoints:
            if waypoint.get('system') == system_name:
                waypoint['status'] = status
                return True
        return False

    def get_overlay_data(self, waypoints: List[Dict[str, Any]], current_index: int, route_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not waypoints:
            return {
                'current_system': 'No galaxy route',
                'current_status': 'GALAXY',
                'next_system': 'Calculate route first',
                'progress': '0/0',
                'distance': '0.00 LY',
                'bodies_to_scan': ['Calculate galaxy route']
            }
        
        total_waypoints = len(waypoints)
        current_system = waypoints[current_index].get('system', 'Unknown')
        
        next_system = "End of route"
        if current_index < total_waypoints - 1:
            next_system = waypoints[current_index + 1].get('system', 'Unknown')
        
        total_distance = 0
        traveled_distance = 0
        neutron_count = 0
        refuel_count = 0
        
        for i, wp in enumerate(waypoints):
            dist = wp.get('distance_jumped', 0)
            total_distance += dist
            if i < current_index:
                traveled_distance += dist
            if wp.get('neutron_star', False):
                neutron_count += 1
            if wp.get('refuel', False):
                refuel_count += 1
        
        from edmrn.icons import Icons
        waypoint_progress = f'{Icons.TARGET} {current_index + 1}/{total_waypoints} waypoints'
        neutron_progress = f'{Icons.LIGHTNING} {neutron_count} neutron boosts'
        
        return {
            'current_system': current_system,
            'current_status': 'GALAXY',
            'next_system': next_system,
            'progress': f'{waypoint_progress}\n{neutron_progress}',
            'distance': f'{traveled_distance:.2f}/{total_distance:.2f} LY',
            'bodies_to_scan': []
        }
