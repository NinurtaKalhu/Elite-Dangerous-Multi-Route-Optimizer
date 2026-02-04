import threading
import pandas as pd
import tkinter as tk
from pathlib import Path
import customtkinter as ctk
from edmrn.config import Paths
from edmrn.tracker import STATUS_VISITED, STATUS_SKIPPED, STATUS_UNVISITED
from edmrn.gui import ProcessingDialog, InfoDialog, ErrorDialog
from edmrn.minimap import MiniMapFrame, MiniMapFrameFallback
from edmrn.logger import get_logger
from edmrn.visit_history import get_history_manager
from edmrn.visit_history_dialog import VisitedSystemsDialog
logger = get_logger('RouteManagement')

class StatusUpdateDialog(ctk.CTkToplevel):
    def __init__(self, parent, system_name):
        super().__init__(parent)
        self.result = None
        self.title("Status Update")
        self.resizable(False, False)
        try:
            from edmrn.utils import resource_path
            from pathlib import Path
            import ctypes
            import os
            from PIL import Image
            from tkinter import PhotoImage
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                self.iconbitmap(ico_path)
                if os.name == 'nt':
                    try:
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = ctypes.windll.user32.LoadImageW(0, str(ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    except Exception:
                        pass
        except Exception:
            pass
        self.transient(parent)
        self.grab_set()
        
        message = f"Have you visited '{system_name}'?"
        label = ctk.CTkLabel(
            self,
            text=message,
            font=("Segoe UI", 13, "bold"),
            wraplength=380
        )
        label.pack(pady=(15, 8))
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=6, padx=20, fill="x")
        
        visited_btn = ctk.CTkButton(
            button_frame,
            text="Visited",
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=("Segoe UI", 12, "bold"),
            height=28,
            command=lambda: self.set_result('visited')
        )
        visited_btn.pack(side="left", expand=True, fill="x", padx=4)

        skipped_btn = ctk.CTkButton(
            button_frame,
            text="Skipped",
            fg_color="#FF5D5D",
            hover_color="#D34242",
            font=("Segoe UI", 12, "bold"),
            height=28,
            command=lambda: self.set_result('skipped')
        )
        skipped_btn.pack(side="left", expand=True, fill="x", padx=4)

        clear_btn = ctk.CTkButton(
            button_frame,
            text="Clear Status",
            fg_color="#FF8C00",
            hover_color="#FFA500",
            font=("Segoe UI", 12, "bold"),
            height=28,
            command=lambda: self.set_result('clear')
        )
        clear_btn.pack(side="left", expand=True, fill="x", padx=4)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#666666",
            hover_color="#555555",
            font=("Segoe UI", 12, "bold"),
            height=28,
            command=lambda: self.set_result('cancel')
        )
        cancel_btn.pack(side="left", expand=True, fill="x", padx=4)
        
        desc_frame = ctk.CTkFrame(self, fg_color="transparent")
        desc_frame.pack(pady=(4, 8))
        
        desc_label = ctk.CTkLabel(
            desc_frame,
            text="Visited = Mark as visited (Green)  |  Skipped = Mark as skipped (Red)  |  Clear = Remove status  |  Cancel = No change",
            font=("Segoe UI", 9),
            text_color="#888888"
        )
        desc_label.pack()
        
        self.bind("<Escape>", lambda e: self.set_result('cancel'))
        
        button_frame.lift()
        visited_btn.lift()
        clear_btn.lift()
        cancel_btn.lift()
        
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        try:
            self.bind('<Map>', lambda e: self._schedule_reapply_icons())
            self.bind('<FocusIn>', lambda e: self._schedule_reapply_icons())
        except Exception:
            pass
    
    def set_result(self, value):
        self.result = value
        self.grab_release()
        self.destroy()
    
    def _schedule_reapply_icons(self):
        if getattr(self, '_reapply_pending', False):
            return
        self._reapply_pending = True
        try:
            self.after(100, lambda: self._do_reapply_icons())
        except Exception:
            self._do_reapply_icons()
    
    def _do_reapply_icons(self):
        try:
            from edmrn.utils import resource_path
            from pathlib import Path
            import ctypes
            import os
            
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.iconbitmap(ico_path)
                except Exception:
                    pass
                if os.name == 'nt':
                    try:
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = ctypes.windll.user32.LoadImageW(0, str(ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    except Exception:
                        pass
        except Exception:
            pass
        finally:
            self._reapply_pending = False
    
    def get_result(self):
        self.wait_window()
        return self.result


class RouteManagement:
    def __init__(self, app):
        self.app = app
    def run_optimization_threaded(self):
        if self.app._optimization_in_progress:
            self.app._log("Optimization already in progress")
            return
        self.app._optimization_in_progress = True
        self.app.run_button.configure(state='disabled', text="Optimizing...")
        cancel_event = threading.Event()
        dialog = ProcessingDialog(self.app, on_cancel=lambda: cancel_event.set())
        def progress_callback(stage: str, fraction: float = None):
            try:
                if fraction is None:
                    self.app.root.after(0, lambda: dialog.update(stage.replace('_', ' ').capitalize(), None))
                else:
                    self.app.root.after(0, lambda: dialog.update(stage.replace('_', ' ').capitalize(), fraction))
            except Exception:
                pass
        def optimization_wrapper():
            try:
                csv_path = self.app.csv_file_path.get()
                if not csv_path or not Path(csv_path).exists():
                    self.app.root.after(0, lambda: (dialog.close(), ErrorDialog(self.app, "Error", "Please select a valid CSV file.")))
                    return
                try:
                    jump_range = float(self.app.jump_range.get())
                    if jump_range <= 0:
                        self.app.root.after(0, lambda: (dialog.close(), ErrorDialog(self.app, "Error", "Ship jump range must be a positive number.")))
                        return
                    self.app.config.ship_jump_range = str(jump_range)
                    self.app.config.save()
                except ValueError:
                    self.app.root.after(0, lambda: (dialog.close(), ErrorDialog(self.app, "Error", "Enter a valid number for ship jump range.")))
                    return
                starting_system_name = self.app.starting_system.get().strip()
                existing_status = {}
                route_data = self.app.route_manager.get_route()
                for route in route_data:
                    existing_status[route['name']] = route['status']
                result = self.app.route_optimizer.optimize_route(csv_path, jump_range, starting_system_name, existing_status, progress_callback=progress_callback, cancel_event=cancel_event)
                def finish():
                    try:
                        dialog.close()
                    except Exception:
                        pass
                    self.app._optimization_in_progress = False
                    self.app.run_button.configure(state='normal', text="Optimize & Track")
                    if not result['success']:
                        ErrorDialog(self.app, "Error", result.get('error', 'Optimization failed'))
                        return
                    optimized_df = result['optimized_df']
                    output_file_name = f"Optimized_Route_{result['num_systems']}_J{result['total_jumps']}_M{jump_range:.1f}LY.csv"
                    output_file_path = Path(Paths.get_backup_folder()) / output_file_name
                    Path(Paths.get_backup_folder()).mkdir(exist_ok=True)
                    if result['success']:
                        self.app.current_backup_folder = result.get('backup_folder')
                    backup_folder = Path(result.get('backup_folder', ''))
                    if backup_folder.exists():
                        self.app._log(f"Route saved to backup: {backup_folder.name}")
                    else:
                        self.app._log(f"Route optimization complete")
                    
                    route_data = result['route_data']
                    route_data = self._check_visited_systems(route_data)
                    
                    self.app.route_tracker.load_route(route_data)
                    if 'backup_folder' in result:
                        try:
                            rows = []
                            for item in route_data:
                                rows.append({
                                    'System Name': item['name'],
                                    'X': item['coords'][0],
                                    'Y': item['coords'][1],
                                    'Z': item['coords'][2],
                                    'Status': item.get('status', STATUS_UNVISITED),
                                    'Bodies': str(item.get('bodies_to_scan', [])),
                                    'Body_Count': item.get('body_count', 0)
                                })
                            if rows:
                                csv_path = Path(result['backup_folder']) / 'current_route.csv'
                                df = pd.DataFrame(rows)
                                df.to_csv(csv_path, index=False)
                        except Exception as e:
                            logger.error(f"Failed to write filtered route CSV: {e}")
                        self.app.route_tracker.save_route_status(result['backup_folder'])
                    self.app.total_distance_ly = result['total_distance']
                    self.create_route_tracker_tab_content()
                    self.app.tabview.set("Route Tracking")
                    self.app._start_journal_monitor()
                    self.copy_next_system_to_clipboard()
                    self.app._ensure_overlay_started("Route Tracking")
                    self.app._log("OPTIMIZATION COMPLETE")
                    self.app._log(f"Total Distance: {result['total_distance']:.2f} LY")
                    self.app._log(f"Estimated Jumps: {result['total_jumps']} jumps")
                    self.app._log(f"Route successfully saved to: '{output_file_path}'")
                    self.app._log("Switched to Route Tracking tab (with 3D Map).")
                    self.app._log("Auto-Tracking STARTED (Monitoring Elite Dangerous Journal).")
                    InfoDialog(self.app, "Success", f"Route optimization complete and Auto-Tracking is ready.\nFile: {output_file_name}")
                self.app.root.after(0, finish)
            except RuntimeError as e:
                try:
                    dialog.close()
                except Exception:
                    pass
                self.app._optimization_in_progress = False
                self.app.root.after(0, lambda: (self.app.run_button.configure(state='normal', text="Optimize & Track"), InfoDialog(self.app, "Info", "Optimization cancelled.")))
            except Exception as e:
                try:
                    dialog.close()
                except Exception:
                    pass
                error_msg = f"Optimization failed: {str(e)[:100]}"
                self.app._optimization_in_progress = False
                self.app.root.after(0, lambda: (self.app._log(f"{error_msg}"), self.app.run_button.configure(state='normal', text="Optimize & Track")))
        threading.Thread(target=optimization_wrapper, daemon=True).start()
    
    def _check_visited_systems(self, route_data):
        try:
            history_manager = get_history_manager()
            system_names = [item.get('name') for item in route_data if item.get('name')]
            
            visited_systems = history_manager.find_visited_systems(system_names)
            
            if not visited_systems:
                return route_data
            
            dialog = VisitedSystemsDialog(self.app.root, visited_systems)
            result, systems_to_remove = dialog.get_result()
            
            if result == 'cancel':
                return route_data
            
            if result == 'keep_all':
                self.app._log(f"INFO: Keeping all {len(visited_systems)} previously visited systems in route")
                return route_data
            
            if result == 'remove_selected' and systems_to_remove:
                filtered_route = [
                    item for item in route_data 
                    if item.get('name') not in systems_to_remove
                ]
                removed_count = len(route_data) - len(filtered_route)
                self.app._log(f"INFO: Removed {removed_count} previously visited systems from route")
                self.app._log(f"New route: {len(filtered_route)} systems (was {len(route_data)})")
                return filtered_route
            
            return route_data
            
        except Exception as e:
            logger.error(f"Error checking visited systems: {e}")
            return route_data
    
    def create_route_tracker_tab_content(self):
        colors = self.app.theme_manager.get_theme_colors()
        if hasattr(self.app, 'system_labels'):
            for label in self.app.system_labels.values():
                try:
                    label.destroy()
                except Exception:
                    pass
            self.app.system_labels.clear()
        if hasattr(self.app, 'map_frame') and self.app.map_frame:
            try:
                if hasattr(self.app.map_frame, 'clear_plot'):
                    self.app.map_frame.clear_plot()
                self.app.map_frame.destroy()
            except Exception:
                pass
            self.app.map_frame = None
        for attr in ['progress_label', 'stats_total_label', 'stats_traveled_label',
                     'stats_avg_jump_label', 'scroll_frame']:
            if hasattr(self.app, attr):
                setattr(self.app, attr, None)
        for widget in self.app.tab_tracker.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass
        import gc
        gc.collect()
        self.app.root.update_idletasks()
        route_data = self.app.route_manager.get_route()
        if not route_data:
            ctk.CTkLabel(self.app.tab_tracker, text="Optimized Route Not Found.\\nPlease create a new route in the 'Route Optimization' tab.").pack(padx=20, pady=20)
            return
        main_container = ctk.CTkFrame(self.app.tab_tracker, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        main_container.columnconfigure(0, weight=60)
        main_container.columnconfigure(1, weight=40)
        main_container.rowconfigure(0, weight=1)
        left_frame = ctk.CTkFrame(main_container,
                                  fg_color=colors['frame'],
                                  border_color=colors['primary'],
                                  border_width=1,
                                  corner_radius=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=85)
        left_frame.rowconfigure(1, weight=15)
        try:
            self.app.map_frame = MiniMapFrame(left_frame, on_system_selected=self.handle_system_click, corner_radius=8)
        except Exception:
            self.app.map_frame = MiniMapFrameFallback(left_frame, on_system_selected=self.handle_system_click, corner_radius=8)
        self.app.map_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        button_frame = ctk.CTkFrame(left_frame,
                                    fg_color=colors['secondary'],
                                    border_color=colors['primary'],
                                    border_width=1,
                                    corner_radius=8)
        button_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        button_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)
        button_frame.rowconfigure(0, weight=1)
        button_frame.rowconfigure(1, weight=1)
        colors = self.app.theme_manager.get_theme_colors()
        copy_next_btn = ctk.CTkButton(button_frame, text="Copy Next", command=self.copy_next_system_to_clipboard,
                                     fg_color=colors['primary'], hover_color=colors['primary_hover'],
                                     text_color=colors['text'], border_color=colors['border'], border_width=1,
                                     height=22, font=ctk.CTkFont(size=11, weight="bold"))
        copy_next_btn.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        open_folder_btn = ctk.CTkButton(button_frame, text="Data Folder", command=self.app._open_app_data_folder,
                                       fg_color=colors['secondary'], hover_color=colors['secondary_hover'],
                                       text_color=colors['text'], border_color=colors['primary'], border_width=1,
                                       height=22, font=ctk.CTkFont(size=11))
        open_folder_btn.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        open_csv_btn = ctk.CTkButton(button_frame, text="Open Excel", command=self.app._open_output_csv,
                                    fg_color=colors['secondary'], hover_color=colors['secondary_hover'],
                                    text_color=colors['text'], border_color=colors['primary'], border_width=1,
                                    height=22, font=ctk.CTkFont(size=11))
        open_csv_btn.grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        backup_btn = ctk.CTkButton(button_frame, text="Load Backup", command=self.app._load_from_backup,
                                  fg_color=colors['secondary'], hover_color=colors['secondary_hover'],
                                  text_color=colors['text'], border_color=colors['primary'], border_width=1,
                                  height=22, font=ctk.CTkFont(size=11))
        backup_btn.grid(row=0, column=3, padx=3, pady=3, sticky="ew")
        quick_save_btn = ctk.CTkButton(button_frame, text="💾 Quick Save",
                                      command=self.app._quick_save_route,
                                      fg_color=colors['success'], hover_color=colors['success_hover'],
                                      text_color=colors['text'], border_width=0,
                                      height=22, font=ctk.CTkFont(size=11, weight="bold"))
        quick_save_btn.grid(row=0, column=4, padx=3, pady=3, sticky="ew")
        info_frame = ctk.CTkFrame(button_frame,
                                 fg_color=colors['frame'],
                                 border_color=colors['accent'],
                                 border_width=1,
                                 corner_radius=8)
        info_frame.grid(row=1, column=0, columnspan=5, padx=5, pady=(2, 5), sticky="nsew")
        info_frame.columnconfigure(0, weight=1)
        self.app.stats_label = ctk.CTkLabel(info_frame,
                                       text="📊 Route Statistics | Total: 0.00 LY | Traveled: 0.00 LY | Average: 0.0 LY",
                                       font=ctk.CTkFont(family="Consolas", size=12, weight="normal"),
                                       text_color=colors['accent'])
        self.app.stats_label.grid(row=0, column=0, padx=8, pady=(8, 2), sticky="w")
        self.app.progress_label = ctk.CTkLabel(info_frame,
                                          text="🎯 Progress Status | Loading...",
                                          font=ctk.CTkFont(family="Consolas", size=12, weight="normal"),
                                          text_color=colors['accent'])
        self.app.progress_label.grid(row=1, column=0, padx=8, pady=(2, 8), sticky="w")
        right_frame = ctk.CTkFrame(main_container,
                                   fg_color=colors['frame'],
                                   border_color=colors['primary'],
                                   border_width=1,
                                   corner_radius=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        ctk.CTkLabel(right_frame, text="Navigation:",
                    font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                    text_color=colors['accent']).pack(pady=(15, 10))
        self.app.scroll_frame = ctk.CTkScrollableFrame(right_frame, width=300,
                                                  fg_color=colors['secondary'],
                                                  border_color=colors['primary'],
                                                  border_width=1,
                                                  scrollbar_button_color=colors['primary'],
                                                  scrollbar_button_hover_color=colors['primary_hover'])
        self.app.scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.app.system_labels = {}
        for i, item in enumerate(route_data):
            system_name = item.get('name', f"Unknown-{i}")
            status = item.get('status', STATUS_UNVISITED)
            display_name = system_name
            bodies_to_scan = item.get('bodies_to_scan', [])
            if bodies_to_scan:
                formatted_bodies = []
                for body_name in bodies_to_scan:
                    if not isinstance(body_name, str):
                        body_name = str(body_name)
                    if body_name.startswith(system_name):
                        pattern = f"{system_name} "
                        if body_name.startswith(pattern):
                            body_display = body_name[len(pattern):]
                        else:
                            body_display = body_name.replace(system_name, "").strip()
                    else:
                        body_display = body_name
                    formatted_bodies.append(body_display)
                if formatted_bodies:
                    all_bodies = " > ".join(formatted_bodies)
                    max_display_length = 100
                    if len(all_bodies) > max_display_length:
                        all_bodies = all_bodies[:80] + "..."
                    display_name = f"{display_name} → {all_bodies}"
            label = ctk.CTkLabel(self.app.scroll_frame, text=f"{i+1}. {display_name}",
                                anchor="w", justify="left", cursor="hand2",
                                font=ctk.CTkFont(family="Segoe UI", size=13, underline=False),
                                fg_color="transparent",
                                text_color=colors['text'])
            label.pack(fill="x", padx=10, pady=2)
            label.bind("<Button-1>", lambda event, name=system_name: self.handle_system_click_manual(name))
            self.app.system_labels[system_name] = label
            self.update_label_color(system_name, status)
        has_coords = route_data and 'coords' in route_data[0]
        if has_coords:
            def plot_in_background():
                try:
                    self.app.map_frame.plot_route(route_data)
                except Exception as e:
                    logger.error(f"Map plot error: {e}")
            import threading
            threading.Thread(target=plot_in_background, daemon=True).start()
        self.update_route_statistics()
        self.update_progress_info()
    def handle_system_click_manual(self, system_name):
        if self.app.map_frame:
            self.app.map_frame.highlight_system(system_name)
        
        dialog = StatusUpdateDialog(self.app.root, system_name)
        result = dialog.get_result()
        
        if result == 'cancel' or result is None:
            return
        
        new_status = None
        if result == 'visited':
            new_status = STATUS_VISITED
        elif result == 'skipped':
            new_status = STATUS_SKIPPED
        elif result == 'clear':
            new_status = STATUS_UNVISITED

        if new_status is not None:
            status_changed = self.app.route_manager.update_system_status(system_name, new_status)
            if status_changed:
                self.update_label_color(system_name, new_status)
                if self.app.map_frame:
                    self.app.map_frame.update_system_status(system_name, new_status)
                self.update_progress_info()
                self.update_route_statistics()
            if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
                self.app.route_tracker.save_route_status(self.app.current_backup_folder)
                self.app._log(f"'{system_name}' status updated to: {new_status.upper()}")
    def handle_system_click(self, system_name):
        if self.app.map_frame:
            self.app.map_frame.highlight_system(system_name)
    def update_label_color(self, system_name, status):
        if system_name in self.app.system_labels:
            label = self.app.system_labels[system_name]
            if status == STATUS_VISITED:
                label.configure(fg_color="#32B837")
            elif status == STATUS_SKIPPED:
                label.configure(fg_color="#FF5D5D")
            else:
                label.configure(fg_color="transparent", text_color="#D1CFCF")
    def update_progress_info(self):
        route_data = self.app.route_manager.get_route()
        if not route_data or not hasattr(self.app, 'progress_label'):
            return
        visited_count = sum(1 for item in route_data if item.get('status') == STATUS_VISITED)
        skipped_count = sum(1 for item in route_data if item.get('status') == STATUS_SKIPPED)
        total_count = len(route_data)
        unvisited_count = total_count - visited_count - skipped_count
        if total_count > 0:
            progress_text = f"🎯 Progress Status | Total: {total_count} | Visited: {visited_count} | Skipped: {skipped_count} | Remaining: {unvisited_count}"
            self.app.progress_label.configure(text=progress_text)
    def update_route_statistics(self):
        try:
            ship_jump_range = float(self.app.jump_range.get() or "70.0")
        except ValueError:
            ship_jump_range = 70.0
        self.app.route_tracker.update_route_statistics(ship_jump_range)
        if hasattr(self.app, 'stats_label'):
            stats_text = f"📊 Route Statistics | Total: {self.app.route_tracker.total_distance_ly:.2f} LY | Traveled: {self.app.route_tracker.traveled_distance_ly:.2f} LY | Average: {self.app.route_tracker.average_jump_range:.1f} LY"
            self.app.stats_label.configure(text=stats_text)
    def update_system_status_from_monitor(self, system_name, new_status):
        if not self.app.route_manager.contains_system(system_name):
            self.app._log(f"Jumped to '{system_name}' (not on current route).")
            return
        status_changed = self.app.route_manager.update_system_status(system_name, new_status)
        if status_changed:
            self.update_label_color(system_name, new_status)
            if self.app.map_frame:
                self.app.map_frame.update_system_status(system_name, new_status)
            self.update_progress_info()
            self.update_route_statistics()
        if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
            self.app.route_tracker.save_route_status(self.app.current_backup_folder)
            self.copy_next_system_to_clipboard()
            self.app._log(f"Auto-Detected Jump to '{system_name}'. Status updated to {new_status.upper()}.")
    def copy_next_system_to_clipboard(self):
        next_system_name = self.app.route_tracker.get_next_unvisited_system()
        if next_system_name:
            try:
                temp_root = tk.Tk()
                temp_root.withdraw()
                temp_root.clipboard_clear()
                temp_root.clipboard_append(next_system_name)
                temp_root.update()
                temp_root.destroy()
                self.app._log(f"'{next_system_name}' (Next System) copied to clipboard.")
            except Exception:
                self.app._log("ERROR: Failed to copy system name to clipboard.")
        else:
            self.app._log("INFO: Route complete. Nothing to copy.")

    def copy_prev_system_to_clipboard(self):
        route_data = self.app.route_manager.get_route()
        if not route_data:
            self.app._log("INFO: No route loaded. Nothing to copy.")
            return

        next_index = next((i for i, item in enumerate(route_data)
                           if item.get('status') == STATUS_UNVISITED), len(route_data))

        if next_index == 0:
            self.app._log("INFO: No previous system to copy.")
            return

        prev_system_name = route_data[next_index - 1].get('name')
        if not prev_system_name:
            self.app._log("INFO: Previous system has no name. Nothing copied.")
            return

        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            temp_root.clipboard_clear()
            temp_root.clipboard_append(prev_system_name)
            temp_root.update()
            temp_root.destroy()
            self.app._log(f"'{prev_system_name}' (Previous System) copied to clipboard.")
        except Exception:
            self.app._log("ERROR: Failed to copy previous system to clipboard.")
