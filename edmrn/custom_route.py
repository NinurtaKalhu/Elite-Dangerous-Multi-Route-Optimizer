import json
import os
import time
import math
import threading
import numpy as np
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from typing import List, Dict, Optional, Callable
from edmrn.logger import get_logger
from edmrn.autocomplete_entry import AutocompleteEntry
from edmrn.minimap import MiniMapFrame
from edmrn.gui import InfoDialog, WarningDialog, ErrorDialog

logger = get_logger('CustomRoute')

STATUS_CURRENT = 'current'
STATUS_VISITED = 'visited'
STATUS_PENDING = 'pending'


class CustomRouteManager:
    def __init__(self, app):
        self.app = app
        self.systems = []
        self.optimized_route = []
        self.current_index = 0
        self.is_optimized = False
        self.starting_system = None
        self.ending_system = None
        self._optimize_lock = threading.Lock()

    def detect_current_system(self) -> Optional[str]:
        try:
            if hasattr(self.app, 'journal_monitor') and self.app.journal_monitor:
                system = self.app.journal_monitor.get_current_system()
                if system:
                    return system
        except Exception:
            pass
        try:
            if hasattr(self.app, 'cmdr_location'):
                loc = self.app.cmdr_location.get()
                if loc and loc != "[Location: Unknown]":
                    return loc
        except Exception:
            pass
        return None

    def set_starting_system(self, name: str):
        self.starting_system = name

    def set_ending_system(self, name: str):
        self.ending_system = name

    def add_system(self, name: str) -> bool:
        for s in self.systems:
            if s['name'].lower() == name.lower():
                return False
        coords = self._fetch_coordinates(name)
        if coords is None:
            return False
        self.systems.append({
            'name': name,
            'x': coords[0],
            'y': coords[1],
            'z': coords[2],
            'added_order': len(self.systems)
        })
        self.is_optimized = False
        return True

    def add_system_direct(self, name: str, x: float, y: float, z: float) -> bool:
        for s in self.systems:
            if s['name'].lower() == name.lower():
                return False
        self.systems.append({
            'name': name,
            'x': x,
            'y': y,
            'z': z,
            'added_order': len(self.systems)
        })
        self.is_optimized = False
        return True

    def remove_system(self, index: int):
        if 0 <= index < len(self.systems):
            self.systems.pop(index)
            self.is_optimized = False
            if self.current_index >= len(self.systems):
                self.current_index = max(0, len(self.systems) - 1)

    def clear_systems(self):
        self.systems.clear()
        self.optimized_route.clear()
        self.current_index = 0
        self.is_optimized = False

    def move_system(self, from_idx: int, to_idx: int):
        if 0 <= from_idx < len(self.systems) and 0 <= to_idx < len(self.systems):
            system = self.systems.pop(from_idx)
            self.systems.insert(to_idx, system)
            self.is_optimized = False

    def optimize_route(self, mode: str = 'distance', boost_multiplier: float = 6.0) -> bool:
        if len(self.systems) < 1:
            return False
        acquired = self._optimize_lock.acquire(blocking=True, timeout=5)
        if not acquired:
            logger.error("Could not acquire optimization lock")
            return False
        try:
            logger.info(f"Starting optimization: {len(self.systems)} systems, mode={mode}")
            start_data = None
            end_data = None
            middle_systems = list(self.systems)

            if self.starting_system:
                for s in self.systems:
                    if s['name'].lower() == self.starting_system.lower():
                        start_data = s
                        middle_systems = [s for s in middle_systems if s['name'].lower() != self.starting_system.lower()]
                        break
                if not start_data:
                    coords = self._fetch_coordinates(self.starting_system)
                    if coords:
                        start_data = {
                            'name': self.starting_system,
                            'x': coords[0], 'y': coords[1], 'z': coords[2],
                            'added_order': -1
                        }

            if self.ending_system:
                for s in self.systems:
                    if s['name'].lower() == self.ending_system.lower():
                        end_data = s
                        middle_systems = [s for s in middle_systems if s['name'].lower() != self.ending_system.lower()]
                        break
                if not end_data:
                    coords = self._fetch_coordinates(self.ending_system)
                    if coords:
                        end_data = {
                            'name': self.ending_system,
                            'x': coords[0], 'y': coords[1], 'z': coords[2],
                            'added_order': 999999
                        }

            if middle_systems:
                logger.info(f"TSP optimization: {len(middle_systems)} middle systems")
                coords_arr = np.array([[s['x'], s['y'], s['z']] for s in middle_systems])
                from edmrn.optimizer import RouteOptimizer
                optimizer = RouteOptimizer()
                distance_matrix = optimizer.calculate_distance_matrix(coords_arr)
                permutation, _ = solve_tsp(distance_matrix)
                ordered_middle = [middle_systems[idx] for idx in permutation]
                logger.info("TSP optimization completed")
            else:
                ordered_middle = []

            all_systems = []
            if start_data:
                all_systems.append(start_data)
            all_systems.extend(ordered_middle)
            if end_data:
                all_systems.append(end_data)

            logger.info(f"Final route: {len(all_systems)} systems")
            if len(all_systems) < 2:
                self.optimized_route = all_systems.copy()
                if self.optimized_route:
                    self.optimized_route[0]['distance_from_prev'] = 0
                self.current_index = 0
                self.is_optimized = True
                self.optimization_mode = mode
                return True

            self.optimized_route = []
            logger.info("Calculating distances...")
            for i in range(len(all_systems)):
                system = all_systems[i].copy()
                if i == 0:
                    system['distance_from_prev'] = 0
                    system['normal_jumps'] = 0
                    system['neutron_jumps'] = 0
                    system['uses_neutron'] = False
                    self.optimized_route.append(system)
                else:
                    prev = all_systems[i - 1]
                    dx = all_systems[i]['x'] - prev['x']
                    dy = all_systems[i]['y'] - prev['y']
                    dz = all_systems[i]['z'] - prev['z']
                    dist = math.sqrt(dx**2 + dy**2 + dz**2)
                    system['distance_from_prev'] = round(dist, 2)

                    if mode == 'neutron':
                        jump_range = self.app.jump_range.get() if hasattr(self.app, 'jump_range') else '70'
                        try:
                            jr = float(jump_range)
                        except:
                            jr = 70.0

                        normal_jumps = max(1, math.ceil(dist / jr))
                        neutron_jumps = max(1, math.ceil(dist / (jr * boost_multiplier)))
                        system['normal_jumps'] = normal_jumps
                        system['neutron_jumps'] = neutron_jumps
                        system['uses_neutron'] = normal_jumps > neutron_jumps
                        system['segment_waypoints'] = [prev['name'], all_systems[i]['name']]

                    self.optimized_route.append(system)
            logger.info(f"Route calculation completed: {len(self.optimized_route)} systems in optimized_route")

            self.current_index = 0
            self.is_optimized = True
            self.optimization_mode = mode
            logger.info(f"optimize_route returning True: systems={len(self.systems)}, optimized_route={len(self.optimized_route)}")
            return True
        except Exception as e:
            logger.error(f"Route optimization failed: {e}")
            return False
        finally:
            self._optimize_lock.release()

    def get_route(self) -> List[Dict]:
        if self.is_optimized and self.optimized_route:
            logger.debug(f"get_route: returning optimized_route ({len(self.optimized_route)} systems)")
            return self.optimized_route
        logger.debug(f"get_route: returning systems ({len(self.systems)} systems)")
        return self.systems

    def get_statistics(self, jump_range: float = None) -> Dict:
        route = self.get_route()
        if len(route) < 2:
            return {'total_distance': 0, 'jumps': 0, 'systems': len(route), 'total_jumps': 0, 'neutron_jumps': 0}
        total_distance = 0
        segment_jumps = []
        neutron_segment_jumps = []
        for i in range(len(route) - 1):
            dx = route[i + 1]['x'] - route[i]['x']
            dy = route[i + 1]['y'] - route[i]['y']
            dz = route[i + 1]['z'] - route[i]['z']
            dist = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
            total_distance += dist
            if jump_range and jump_range > 0:
                segment_jumps.append(max(1, math.ceil(dist / jump_range)))
                neutron_range = jump_range * 6
                neutron_segment_jumps.append(max(1, math.ceil(dist / neutron_range)))
            else:
                segment_jumps.append(1)
                neutron_segment_jumps.append(1)
        total_jumps = sum(segment_jumps) if jump_range and jump_range > 0 else len(route) - 1
        total_neutron_jumps = sum(neutron_segment_jumps) if jump_range and jump_range > 0 else len(route) - 1
        return {
            'total_distance': round(total_distance, 2),
            'jumps': len(route) - 1,
            'systems': len(route),
            'total_jumps': total_jumps,
            'total_neutron_jumps': total_neutron_jumps,
            'segment_jumps': segment_jumps,
            'neutron_segment_jumps': neutron_segment_jumps
        }

    def get_next_waypoint(self) -> Optional[Dict]:
        route = self.get_route()
        if not route:
            return None
        if self.current_index < len(route) - 1:
            self.current_index += 1
            return route[self.current_index]
        return None

    def get_prev_waypoint(self) -> Optional[Dict]:
        route = self.get_route()
        if not route:
            return None
        if self.current_index > 0:
            self.current_index -= 1
            return route[self.current_index]
        return None

    def get_current_waypoint(self) -> Optional[Dict]:
        route = self.get_route()
        if route and 0 <= self.current_index < len(route):
            return route[self.current_index]
        return None

    def export_list(self, filepath: str):
        route = self.get_route()
        if filepath.endswith('.txt'):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Custom Route - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                if self.starting_system:
                    f.write(f"# Starting System: {self.starting_system}\n")
                f.write("# Format: SystemName X Y Z\n\n")
                for s in route:
                    f.write(f"{s['name']} {s['x']:.2f} {s['y']:.2f} {s['z']:.2f}\n")
        else:
            data = {
                'name': 'Custom Route',
                'created': time.strftime('%Y-%m-%d %H:%M:%S'),
                'starting_system': self.starting_system,
                'systems': [{'name': s['name'], 'x': s['x'], 'y': s['y'], 'z': s['z']} for s in route]
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def import_list(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.clear_systems()
            if filepath.endswith('.txt'):
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) >= 4:
                        name = parts[0]
                        try:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            self.add_system_direct(name, x, y, z)
                        except ValueError:
                            continue
            else:
                data = json.loads(content)
                systems = data.get('systems', [])
                for s in systems:
                    self.add_system_direct(s['name'], s['x'], s['y'], s['z'])
            return True
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return False

    def _fetch_coordinates(self, system_name: str) -> Optional[tuple]:
        try:
            import requests
            resp = requests.post(
                'https://spansh.co.uk/api/systems/search',
                json={'filters': {'name': {'value': [system_name]}}, 'size': 1},
                headers={'User-Agent': 'EDMRN 3.3'},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get('result', [])
                if results:
                    coords = results[0].get('coords', {})
                    return (coords.get('x', 0), coords.get('y', 0), coords.get('z', 0))
        except Exception:
            pass

        try:
            import requests
            resp = requests.get(
                f'https://edsm.net/api-v1/system?systemName={system_name}&showCoordinates=1',
                headers={'User-Agent': 'EDMRN 3.3'},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                coords = data.get('coords', {})
                if coords:
                    return (coords.get('x', 0), coords.get('y', 0), coords.get('z', 0))
        except Exception:
            pass

        return None


def solve_tsp(distance_matrix):
    n = len(distance_matrix)
    permutation = [0]
    total = 0
    current = 0
    visited = {0}
    for _ in range(n - 1):
        nearest = None
        nearest_dist = float('inf')
        for j in range(n):
            if j not in visited and distance_matrix[current][j] < nearest_dist:
                nearest = j
                nearest_dist = distance_matrix[current][j]
        if nearest is not None:
            permutation.append(nearest)
            total += nearest_dist
            visited.add(nearest)
            current = nearest
        else:
            break
    return permutation, total


class CustomRouteTab:
    def __init__(self, app):
        self.app = app
        self.manager = CustomRouteManager(app)
        self.tab = None
        self.scroll_frame = None
        self.minimap = None
        self.system_labels = []
        self.selected_indices = set()
        self._build_ui()
        self._detect_current_location()

    def _build_ui(self):
        self.tab = self.app.tab_custom_route
        colors = self.app.theme_manager.get_theme_colors()
        self.tab.configure(fg_color=colors['background'])

        top_frame = ctk.CTkFrame(self.tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            top_frame, text="Starting System:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=colors['text']
        ).pack(side="left", padx=(0, 8))

        self.starting_entry = AutocompleteEntry(
            top_frame,
            placeholder_text="Current location (auto-detected)",
            suggestion_provider=self._get_suggestions,
            on_suggestion_callback=self._on_suggestion_selected,
            fg_color=colors['frame'],
            text_color=colors['text'],
            width=200
        )
        self.starting_entry.pack(side="left", padx=(0, 8))

        set_start_btn = ctk.CTkButton(
            top_frame, text="Set", width=40,
            command=self._set_starting_system
        )
        self.app.theme_manager.apply_button_theme(set_start_btn, "secondary")
        set_start_btn.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            top_frame, text="Ending System:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=colors['text']
        ).pack(side="left", padx=(0, 8))

        self.ending_entry = AutocompleteEntry(
            top_frame,
            placeholder_text="Optional destination",
            suggestion_provider=self._get_suggestions,
            on_suggestion_callback=self._on_suggestion_selected,
            fg_color=colors['frame'],
            text_color=colors['text'],
            width=200
        )
        self.ending_entry.pack(side="left", padx=(0, 8))

        set_end_btn = ctk.CTkButton(
            top_frame, text="Set", width=40,
            command=self._set_ending_system
        )
        self.app.theme_manager.apply_button_theme(set_end_btn, "secondary")
        set_end_btn.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            top_frame, text="Add System:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=colors['text']
        ).pack(side="left", padx=(0, 8))

        self.system_entry = AutocompleteEntry(
            top_frame,
            placeholder_text="Enter system name (e.g., Sol, Achenar)",
            suggestion_provider=self._get_suggestions,
            on_suggestion_callback=self._on_suggestion_selected,
            fg_color=colors['frame'],
            text_color=colors['text'],
            width=300
        )
        self.system_entry.pack(side="left", padx=(0, 8))

        add_btn = ctk.CTkButton(
            top_frame, text="Add", width=60,
            command=self._add_system
        )
        self.app.theme_manager.apply_button_theme(add_btn, "primary")
        add_btn.pack(side="left", padx=(0, 8))

        coord_btn = ctk.CTkButton(
            top_frame, text="Add by Coords", width=100,
            command=self._add_by_coordinates
        )
        self.app.theme_manager.apply_button_theme(coord_btn, "secondary")
        coord_btn.pack(side="left", padx=(0, 8))

        main_frame = ctk.CTkFrame(self.tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(main_frame, fg_color=colors['background'], border_width=1, border_color=colors['border'])
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(0, weight=1)

        list_header = ctk.CTkFrame(left_frame, fg_color="transparent")
        list_header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            list_header, text="System List",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=colors['primary']
        ).pack(side="left")

        self.scroll_frame = ctk.CTkScrollableFrame(
            left_frame,
            fg_color=colors['background'],
            border_width=1,
            border_color=colors['border']
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))

        bottom_btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        bottom_btn_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))

        self.optimize_btn = ctk.CTkButton(
            bottom_btn_frame, text="Optimize Route", width=120,
            command=self._optimize_route
        )
        self.app.theme_manager.apply_button_theme(self.optimize_btn, "primary")
        self.optimize_btn.pack(side="left", padx=(0, 8))

        self.sort_var = ctk.StringVar(value="distance")
        ctk.CTkRadioButton(
            bottom_btn_frame, text="Shortest Distance",
            variable=self.sort_var, value="distance",
            text_color=colors['text']
        ).pack(side="left", padx=(0, 8))

        ctk.CTkRadioButton(
            bottom_btn_frame, text="Neutron Path",
            variable=self.sort_var, value="neutron",
            text_color=colors['text']
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            bottom_btn_frame, text="Boost:",
            font=ctk.CTkFont(size=11),
            text_color=colors['text']
        ).pack(side="left", padx=(8, 4))

        self.boost_var = ctk.StringVar(value="x4")
        ctk.CTkOptionMenu(
            bottom_btn_frame, values=["x4", "x6"],
            variable=self.boost_var, width=60
        ).pack(side="left", padx=(0, 8))

        export_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        export_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))

        self.remove_btn = ctk.CTkButton(
            export_frame, text="Remove", width=60,
            command=self._remove_selected
        )
        self.app.theme_manager.apply_button_theme(self.remove_btn, "secondary")
        self.remove_btn.pack(side="left", padx=(0, 4))

        self.clear_btn = ctk.CTkButton(
            export_frame, text="Clear All", width=70,
            command=self._clear_all
        )
        self.app.theme_manager.apply_button_theme(self.clear_btn, "secondary")
        self.clear_btn.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            export_frame, text="Export", width=60,
            command=self._export_list
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            export_frame, text="Import", width=60,
            command=self._import_list
        ).pack(side="left")

        right_frame = ctk.CTkFrame(main_frame, fg_color=colors['background'], border_width=1, border_color=colors['border'])
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)

        self.minimap = MiniMapFrame(
            right_frame,
            width=500,
            height=350,
            fg_color=colors['background']
        )
        self.minimap.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        waypoint_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        waypoint_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))

        self.stats_label = ctk.CTkLabel(
            waypoint_frame,
            text="Total: 0 LY | 0 jumps | 0 systems",
            font=ctk.CTkFont(size=12),
            text_color=colors['text']
        )
        self.stats_label.pack(anchor="w", padx=8, pady=(4, 0))

        self.progress_label = ctk.CTkLabel(
            waypoint_frame,
            text="Ready to plan",
            font=ctk.CTkFont(size=11),
            text_color=colors['text']
        )
        self.progress_label.pack(anchor="w", padx=8, pady=(0, 0))

        nav_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))

        self.prev_btn = ctk.CTkButton(
            nav_frame, text="< Previous", width=90,
            command=self._prev_waypoint
        )
        self.app.theme_manager.apply_button_theme(self.prev_btn, "secondary")
        self.prev_btn.pack(side="left", padx=(0, 8))

        self.current_label = ctk.CTkLabel(
            nav_frame, text="No route",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=colors['accent']
        )
        self.current_label.pack(side="left", padx=(0, 8))

        self.next_btn = ctk.CTkButton(
            nav_frame, text="Next >", width=90,
            command=self._next_waypoint
        )
        self.app.theme_manager.apply_button_theme(self.next_btn, "primary")
        self.next_btn.pack(side="left", padx=(0, 8))

        self.copy_btn = ctk.CTkButton(
            nav_frame, text="Copy System", width=90,
            command=self._copy_current_system
        )
        self.app.theme_manager.apply_button_theme(self.copy_btn, "secondary")
        self.copy_btn.pack(side="left")

    def _detect_current_location(self):
        def detect():
            system = self.manager.detect_current_system()
            if system:
                self.app.root.after(0, lambda: self.starting_entry.set(system))
                self.manager.set_starting_system(system)
        threading.Thread(target=detect, daemon=True).start()

    def _set_starting_system(self):
        name = self.starting_entry.get().strip()
        if name:
            self.manager.set_starting_system(name)
            if name.lower() not in [s['name'].lower() for s in self.manager.systems]:
                self._add_system_async(name)
            self.app._log(f"Starting system set to: {name}")

    def _set_ending_system(self):
        name = self.ending_entry.get().strip()
        if name:
            self.manager.set_ending_system(name)
            if name.lower() not in [s['name'].lower() for s in self.manager.systems]:
                self._add_system_async(name)
            self.app._log(f"Ending system set to: {name}")

    def _get_suggestions(self, query: str, callback: Callable):
        def fetch():
            try:
                from edmrn.system_autocomplete import SystemAutocompleter
                completer = SystemAutocompleter()
                suggestions = completer.get_suggestions(query, max_results=8)
                callback(suggestions)
            except Exception:
                callback([])
        threading.Thread(target=fetch, daemon=True).start()

    def _on_suggestion_selected(self, selected: str):
        pass

    def _add_system(self):
        name = self.system_entry.get().strip()
        if not name:
            return
        self.system_entry.set("")
        self._add_system_async(name)

    def _add_system_async(self, name: str):
        def add():
            success = self.manager.add_system(name)
            if success:
                self.app.root.after(0, lambda: self._refresh_ui())
            else:
                self.app.root.after(0, lambda: WarningDialog(
                    self.app, "System Not Found",
                    f"Could not find system: {name}\n\nCheck the spelling and try again."
                ))
        threading.Thread(target=add, daemon=True).start()

    def _add_by_coordinates(self):
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Add System by Coordinates")
        dialog.geometry("350x200")
        dialog.configure(bg="#222")
        dialog.transient(self.app.root)
        dialog.grab_set()

        colors = self.app.theme_manager.get_theme_colors()
        frame = tk.Frame(dialog, bg=colors['background'])
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(frame, text="System Name:", bg=colors['background'], fg=colors['text']).grid(row=0, column=0, sticky="w", pady=4)
        name_entry = tk.Entry(frame, bg=colors['frame'], fg=colors['text'], insertbackground=colors['text'])
        name_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        tk.Label(frame, text="X:", bg=colors['background'], fg=colors['text']).grid(row=1, column=0, sticky="w", pady=4)
        x_entry = tk.Entry(frame, bg=colors['frame'], fg=colors['text'], insertbackground=colors['text'])
        x_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)

        tk.Label(frame, text="Y:", bg=colors['background'], fg=colors['text']).grid(row=2, column=0, sticky="w", pady=4)
        y_entry = tk.Entry(frame, bg=colors['frame'], fg=colors['text'], insertbackground=colors['text'])
        y_entry.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=4)

        tk.Label(frame, text="Z:", bg=colors['background'], fg=colors['text']).grid(row=3, column=0, sticky="w", pady=4)
        z_entry = tk.Entry(frame, bg=colors['frame'], fg=colors['text'], insertbackground=colors['text'])
        z_entry.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=4)

        frame.columnconfigure(1, weight=1)

        def add():
            try:
                name = name_entry.get().strip()
                x = float(x_entry.get().strip())
                y = float(y_entry.get().strip())
                z = float(z_entry.get().strip())
                if name:
                    self.manager.add_system_direct(name, x, y, z)
                    self._refresh_ui()
                    dialog.destroy()
            except ValueError:
                WarningDialog(self.app, "Invalid Input", "Please enter valid numeric coordinates.")

        tk.Button(frame, text="Add", command=add, bg=colors['primary'], fg=colors['background'],
                 font=("Segoe UI", 10, "bold")).grid(row=4, column=0, columnspan=2, pady=(12, 0), sticky="ew")

    def _remove_selected(self):
        if not self.selected_indices:
            if self.manager.systems:
                self.manager.remove_system(len(self.manager.systems) - 1)
                self._refresh_ui()
            return
        for idx in sorted(self.selected_indices, reverse=True):
            self.manager.remove_system(idx)
        self.selected_indices.clear()
        self._refresh_ui()

    def _clear_all(self):
        self.manager.clear_systems()
        self.selected_indices.clear()
        self._refresh_ui()

    def _optimize_route(self):
        if len(self.manager.systems) < 2:
            WarningDialog(self.app, "Not Enough Systems",
                         "Please add at least 2 systems to optimize the route.")
            return
        mode = self.sort_var.get()
        boost_val = self.boost_var.get()
        boost_multiplier = 6.0 if boost_val == "x6" else 4.0
        self.optimize_btn.configure(state="disabled", text="Optimizing...")
        logger.info(f"Optimize clicked: mode={mode}, boost={boost_val}")
        
        def do_optimize():
            try:
                logger.info("Starting optimization thread...")
                success = self.manager.optimize_route(mode, boost_multiplier)
                logger.info(f"Optimization completed: success={success}")
                self.app.root.after(0, lambda: self._on_optimize_complete(success))
            except Exception as e:
                logger.error(f"Optimization error: {e}")
                self.app.root.after(0, lambda: self._on_optimize_complete(False))
        
        threading.Thread(target=do_optimize, daemon=True).start()

    def _on_optimize_complete(self, success):
        logger.info(f"BEFORE _refresh_ui: systems={len(self.manager.systems)}, optimized_route={len(self.manager.optimized_route)}")
        self.optimize_btn.configure(state="normal", text="Optimize Route")
        if success:
            self._refresh_ui()
            logger.info(f"AFTER _refresh_ui: systems={len(self.manager.systems)}, optimized_route={len(self.manager.optimized_route)}")
            stats = self.manager.get_statistics(self._get_jump_range())
            logger.info(f"AFTER get_statistics: systems={len(self.manager.systems)}, optimized_route={len(self.manager.optimized_route)}, stats_systems={stats['systems']}")
            self.app._log(f"Route optimized: {stats['systems']} systems, {stats['total_distance']:.0f} LY, {stats.get('total_jumps', stats['jumps'])} jumps")
            self._ensure_overlay_started()
        else:
            self.app._log("Route optimization failed")

    def _ensure_overlay_started(self):
        try:
            if hasattr(self.app, '_ensure_overlay_started'):
                self.app._ensure_overlay_started("Custom Route")
        except Exception as e:
            logger.debug(f"Overlay auto-start error: {e}")

    def _export_list(self):
        filepath = filedialog.asksaveasfilename(
            title="Export Route",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            self.manager.export_list(filepath)
            InfoDialog(self.app, "Export Successful", f"Route exported to:\n{filepath}")

    def _import_list(self):
        filepath = filedialog.askopenfilename(
            title="Import Route",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            success = self.manager.import_list(filepath)
            if success:
                self._refresh_ui()
                InfoDialog(self.app, "Import Successful", f"Imported {len(self.manager.systems)} systems.")
            else:
                ErrorDialog(self.app, "Import Failed", "Failed to import route file.")

    def _prev_waypoint(self):
        self.manager.get_prev_waypoint()
        try:
            if hasattr(self.app, 'root') and self.app.root:
                self.app.root.after(0, self._update_navigation)
                self.app.root.after(0, self._update_system_list_visual)
        except Exception:
            pass

    def _next_waypoint(self):
        self.manager.get_next_waypoint()
        try:
            if hasattr(self.app, 'root') and self.app.root:
                self.app.root.after(0, self._update_navigation)
                self.app.root.after(0, self._update_system_list_visual)
        except Exception:
            pass

    def _copy_current_system(self):
        current = self.manager.get_current_waypoint()
        if current:
            def do_copy():
                try:
                    import pyperclip
                    pyperclip.copy(current['name'])
                except ImportError:
                    try:
                        self.app.root.clipboard_clear()
                        self.app.root.clipboard_append(current['name'])
                    except Exception:
                        pass
                self.app._log(f"Copied system: {current['name']}")
            try:
                if hasattr(self.app, 'root') and self.app.root:
                    self.app.root.after(0, do_copy)
                else:
                    do_copy()
            except Exception:
                pass

    def _refresh_ui(self):
        self._update_system_list()
        jump_range = self._get_jump_range()
        stats = self.manager.get_statistics(jump_range)
        is_neutron_mode = getattr(self.manager, 'optimization_mode', 'distance') == 'neutron'
        
        if is_neutron_mode and jump_range and jump_range > 0:
            self.stats_label.configure(
                text=f"Total: {stats['total_distance']:.2f} LY | {stats['total_neutron_jumps']} jumps (neutron) vs {stats['total_jumps']} jumps (normal) | {stats['systems']} systems"
            )
        elif jump_range and jump_range > 0:
            self.stats_label.configure(
                text=f"Total: {stats['total_distance']:.2f} LY | {stats['total_jumps']} jumps ({jump_range:.0f} LY range) | {stats['systems']} systems"
            )
        else:
            self.stats_label.configure(
                text=f"Total: {stats['total_distance']:.2f} LY | {stats['jumps']} systems | {stats['systems']} systems"
            )
        self._update_minimap()
        self._update_navigation()

    def _get_jump_range(self) -> float:
        try:
            if hasattr(self.app, 'jump_range'):
                val = self.app.jump_range.get()
                if val:
                    return float(val)
        except Exception:
            pass
        return 0

    def _update_system_list(self):
        if not self.scroll_frame:
            return

        for widget in self.scroll_frame.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

        self.system_labels = []
        self.selected_indices.clear()
        route = self.manager.get_route()
        colors = self.app.theme_manager.get_theme_colors()
        jump_range = self._get_jump_range()
        is_neutron_mode = getattr(self.manager, 'optimization_mode', 'distance') == 'neutron'

        if not route:
            no_route_label = ctk.CTkLabel(
                self.scroll_frame,
                text="No systems added yet",
                font=ctk.CTkFont(size=12),
                text_color=colors['text']
            )
            no_route_label.pack(pady=20)
            return

        for i, system in enumerate(route):
            name = system.get('name', 'Unknown')
            dist = system.get('distance_from_prev', None)
            status = 'current' if i == self.manager.current_index else 'pending'

            if dist is not None and isinstance(dist, (int, float)) and dist > 0:
                if is_neutron_mode and jump_range and jump_range > 0:
                    normal_jumps = system.get('normal_jumps', max(1, math.ceil(dist / jump_range)))
                    neutron_jumps = system.get('neutron_jumps', max(1, math.ceil(dist / (jump_range * 6))))
                    if normal_jumps > neutron_jumps:
                        display_text = f"{i+1}. {name} | {dist:.1f} LY | ⚡ {neutron_jumps} jumps (was {normal_jumps})"
                    else:
                        display_text = f"{i+1}. {name} | {dist:.1f} LY | {normal_jumps} jumps"
                elif jump_range and jump_range > 0:
                    jumps = max(1, math.ceil(dist / jump_range))
                    display_text = f"{i+1}. {name} | {dist:.1f} LY | {jumps} jumps"
                else:
                    display_text = f"{i+1}. {name} | {dist:.1f} LY"
            else:
                display_text = f"{i+1}. {name}"

            label = ctk.CTkLabel(
                self.scroll_frame,
                text=display_text,
                anchor="w",
                justify="left",
                cursor="hand2",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                fg_color="transparent",
                text_color=colors['text']
            )
            label.pack(fill="x", padx=4, pady=2)

            idx = i
            label.bind("<Button-1>", lambda e, idx=idx: self._toggle_selection(idx))

            if status == 'current':
                label.configure(fg_color="#FF8C00", text_color="#0D0D0D")
            elif idx in self.selected_indices:
                label.configure(fg_color="#4A4A4A", text_color="#FFD700")
            else:
                label.configure(fg_color="transparent", text_color="#E0E0E0")

            self.system_labels.append(label)

    def _toggle_selection(self, idx):
        if idx in self.selected_indices:
            self.selected_indices.discard(idx)
        else:
            self.selected_indices.add(idx)
        self._update_system_list_visual()

    def _update_system_list_visual(self):
        if not self.system_labels:
            return
        colors = self.app.theme_manager.get_theme_colors()
        for i, label in enumerate(self.system_labels):
            try:
                if i == self.manager.current_index:
                    label.configure(fg_color="#FF8C00", text_color="#0D0D0D")
                elif i in self.selected_indices:
                    label.configure(fg_color="#4A4A4A", text_color="#FFD700")
                else:
                    label.configure(fg_color="transparent", text_color="#E0E0E0")
            except Exception:
                pass

    def _update_minimap(self):
        route = self.manager.get_route()
        if not route or not self.minimap:
            return
        try:
            if self.minimap.matplotlib_available and self.minimap.ax:
                self.minimap.ax.cla()
                self.minimap._setup_axes()

                xs = [s['x'] for s in route]
                ys = [s['y'] for s in route]
                zs = [s['z'] for s in route]

                colors_list = []
                for i, s in enumerate(route):
                    if i == self.manager.current_index:
                        colors_list.append('#FF8C00')
                    else:
                        colors_list.append('#4FC3F7')

                self.minimap._scatter = self.minimap.ax.scatter(
                    xs, ys, zs,
                    s=50,
                    c=colors_list,
                    marker='o',
                    picker=True,
                    pickradius=10,
                    zorder=5,
                    edgecolors='#000000',
                    linewidths=1.0
                )

                if len(xs) > 1:
                    self.minimap.ax.plot(xs, ys, zs, color='#FF8C00', linewidth=1.5, alpha=0.7)

                for i, s in enumerate(route):
                    self.minimap.ax.text(xs[i], ys[i], zs[i], s['name'], fontsize=7, color='#E0E0E0')

                self.minimap.ax.set_xlabel('X', color='#888888', fontsize=8)
                self.minimap.ax.set_ylabel('Y', color='#888888', fontsize=8)
                self.minimap.ax.set_zlabel('Z', color='#888888', fontsize=8)
                self.minimap.ax.tick_params(colors='#888888', labelsize=7)

                if self.minimap.canvas:
                    self.minimap.canvas.draw_idle()
        except Exception as e:
            logger.debug(f"Minimap update error: {e}")

    def _update_navigation(self):
        route = self.manager.get_route()
        current = self.manager.get_current_waypoint()
        if current:
            idx = self.manager.current_index + 1
            total = len(route)
            self.current_label.configure(
                text=f"{idx}/{total} - {current['name']}"
            )
            self.progress_label.configure(
                text=f"Progress: {idx}/{total} | {total - idx} remaining"
            )
        else:
            self.current_label.configure(text="No route")
            self.progress_label.configure(text="Ready to plan")

        self.prev_btn.configure(
            state="normal" if self.manager.current_index > 0 else "disabled"
        )
        self.next_btn.configure(
            state="normal" if self.manager.current_index < len(route) - 1 else "disabled"
        )
