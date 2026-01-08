import threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import customtkinter as ctk
from edmrn.config import Paths
from edmrn.tracker import STATUS_VISITED, STATUS_SKIPPED, STATUS_UNVISITED
from edmrn.gui import ProcessingDialog
from edmrn.minimap import MiniMapFrame, MiniMapFrameFallback
from edmrn.logger import get_logger
logger = get_logger('RouteManagement')
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
                    self.app.root.after(0, lambda: (dialog.close(), messagebox.showerror("Error", "Please select a valid CSV file.")))
                    return
                try:
                    jump_range = float(self.app.jump_range.get())
                    if jump_range <= 0:
                        self.app.root.after(0, lambda: (dialog.close(), messagebox.showerror("Error", "Ship jump range must be a positive number.")))
                        return
                    self.app.config.ship_jump_range = str(jump_range)
                    self.app.config.save()
                except ValueError:
                    self.app.root.after(0, lambda: (dialog.close(), messagebox.showerror("Error", "Enter a valid number for ship jump range.")))
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
                    self.app.run_button.configure(state='normal', text="Optimize Route and Start Tracking")
                    if not result['success']:
                        messagebox.showerror("Error", result.get('error', 'Optimization failed'))
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
                    self.app.route_tracker.load_route(result['route_data'])
                    if 'backup_folder' in result:
                        self.app.route_tracker.save_route_status(result['backup_folder'])
                    self.app.total_distance_ly = result['total_distance']
                    self.create_route_tracker_tab_content()
                    self.app.tabview.set("Route Tracking")
                    self.app._start_journal_monitor()
                    self.copy_next_system_to_clipboard()
                    self.app._log("\\nOPTIMIZATION COMPLETE")
                    self.app._log(f"Total Distance: {result['total_distance']:.2f} LY")
                    self.app._log(f"Estimated Jumps: {result['total_jumps']} jumps")
                    self.app._log(f"Route successfully saved to: '{output_file_path}'")
                    self.app._log("Switched to Route Tracking tab (with 3D Map).")
                    self.app._log("Auto-Tracking STARTED (Monitoring Elite Dangerous Journal).")
                    messagebox.showinfo("Success", f"Route optimization complete and Auto-Tracking is ready.\\nFile: {output_file_name}")
                self.app.root.after(0, finish)
            except RuntimeError as e:
                try:
                    dialog.close()
                except Exception:
                    pass
                self.app._optimization_in_progress = False
                self.app.root.after(0, lambda: (self.app.run_button.configure(state='normal', text="Optimize Route and Start Tracking"), messagebox.showinfo("Info", "Optimization cancelled.")))
            except Exception as e:
                try:
                    dialog.close()
                except Exception:
                    pass
                error_msg = f"Optimization failed: {str(e)[:100]}"
                self.app._optimization_in_progress = False
                self.app.root.after(0, lambda: (self.app._log(f"{error_msg}"), self.app.run_button.configure(state='normal', text="Optimize Route and Start Tracking")))
        threading.Thread(target=optimization_wrapper, daemon=True).start()
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
            self.app.map_frame.plot_route(route_data)
        self.update_route_statistics()
        self.update_progress_info()
    def handle_system_click_manual(self, system_name):
        if self.app.map_frame:
            self.app.map_frame.highlight_system(system_name)
        response = messagebox.askyesnocancel(
            "Status Update",
            f"Have you visited the system '{system_name}'?\\n\\n'Yes' = Visited (Green)\\n'No' = Skipped (Red)\\n'Cancel' = Do not change status",
            icon="question"
        )
        if response is None:
            return
        new_status = None
        if response:
            new_status = STATUS_VISITED
        else:
            new_status = STATUS_SKIPPED
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
                label.configure(fg_color="#4CAF50")
            elif status == STATUS_SKIPPED:
                label.configure(fg_color="#FFA500")
            else:
                label.configure(fg_color="transparent", text_color="#E0E0E0")
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
