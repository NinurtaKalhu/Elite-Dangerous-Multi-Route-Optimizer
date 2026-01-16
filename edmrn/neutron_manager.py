import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from edmrn.logger import get_logger
from edmrn.gui import ErrorDialog, InfoDialog, WarningDialog
logger = get_logger('NeutronManager')
class NeutronManager:
    def __init__(self, app):
        self.app = app
    def calculate_neutron_route(self):
        from_system = self.app.neutron_from_autocomplete.get().strip()
        to_system = self.app.neutron_to_autocomplete.get().strip()
        
        if not from_system:
            current_system = self.get_current_system_from_journal()
            if current_system:
                from_system = current_system
                self.app.neutron_from_autocomplete.set(from_system)
            else:
                route_data = self.app.route_manager.get_route()
                if route_data:
                    visited = [r for r in route_data if r['status'] == 'visited']
                    if visited:
                        from_system = visited[-1]['name']
                        self.app.neutron_from_autocomplete.set(from_system)
                else:
                    unvisited = [r for r in route_data if r['status'] == 'unvisited']
                    if unvisited:
                        from_system = unvisited[0]['name']
                        self.app.neutron_from_autocomplete.set(from_system)
        if not to_system:
            route_data = self.app.route_manager.get_route()
            if route_data:
                unvisited = [r for r in route_data if r['status'] == 'unvisited']
                if unvisited:
                    to_system = unvisited[0]['name']
                    self.app.neutron_to_autocomplete.set(to_system)
        if not from_system or not to_system:
            ErrorDialog(self.app, "Error", "Please enter both From and To systems")
            return
        try:
            jump_range = float(self.app.neutron_range_var.get())
            if jump_range <= 0:
                raise ValueError("Jump range must be positive")
        except ValueError:
            ErrorDialog(self.app, "Error", "Please enter a valid jump range")
            return
        boost_text = self.app.neutron_boost_var.get()
        fsd_boost = "x6" if "x6" in boost_text else "x4"
        self.app.neutron_calculate_btn.configure(state="disabled", text="Calculating...")
        self.app.neutron_info_label.configure(text="🔄 Connecting to Spansh API...")
        def progress_update(message):
            self.app.root.after(0, lambda: self.app.neutron_info_label.configure(text=f"🔄 {message}"))
        def calculation_done(result):
            self.app.neutron_calculate_btn.configure(state="normal", text="🚀 Calculate Neutron Route")
            if result['success']:
                waypoints = result['waypoints']
                total_distance = result['total_distance']
                total_jumps = result['total_jumps']
                neutron_jumps = result['neutron_jumps']
                route_text = f"Neutron Highway Route: {from_system} → {to_system}\n"
                route_text += f"Total Distance: {total_distance} LY\n"
                route_text += f"Total Jumps: {total_jumps} ({neutron_jumps} neutron)\n"
                route_text += f"FSD Boost: {fsd_boost}\n\n"
                route_text += "Route Waypoints:\n"
                route_text += "=" * 40 + "\n"
                for i, waypoint in enumerate(waypoints, 1):
                    system = waypoint['system']
                    wp_type = waypoint['type']
                    if wp_type == "Neutron":
                        route_text += f"{i:2d}. {system} (Neutron Star)\n"
                    else:
                        route_text += f"{i:2d}. {system}\n"
                self.app.neutron_info_label.configure(
                    text=f"✅ Route calculated: {total_jumps} jumps ({neutron_jumps} neutron), {total_distance} LY"
                )
                self.update_neutron_statistics(result)
                self.update_neutron_navigation()
                self.copy_current_neutron_system(auto=True)
                if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
                    self.app.neutron_router.save_neutron_route(self.app.current_backup_folder)
                if not self.app.journal_monitor:
                    self.app._start_journal_monitor()
                try:
                    self.app._ensure_overlay_started("Neutron Highway")
                except Exception:
                    pass
                self.app._log(f"Neutron route calculated: {from_system} → {to_system}")
            else:
                error_msg = result.get('error', 'Unknown error')
                self.app.neutron_info_label.configure(text=f"❌ Error: {error_msg}")
                ErrorDialog(self.app, "Neutron Route Error", f"Failed to calculate route:\n{error_msg}")
        self.app.neutron_router.calculate_route_async(
            from_system, to_system, jump_range, fsd_boost,
            calculation_done, progress_update
        )
    def neutron_prev_waypoint(self):
        if self.app.neutron_router.prev_waypoint():
            self.update_neutron_navigation()
    
    def neutron_next_waypoint(self):
        if self.app.neutron_router.mark_current_as_visited():
            self.update_neutron_navigation()
            self.copy_current_neutron_system(auto=True)
            if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
                self.app.neutron_router.save_neutron_route(self.app.current_backup_folder)
    def copy_current_neutron_system(self, auto=False):
        current_system = self.app.neutron_router.get_current_waypoint()
        if current_system == "No route calculated":
            if not auto:
                WarningDialog(self.app, "Warning", "No neutron route calculated.")
            return
        try:
            import pyperclip
            pyperclip.copy(current_system)
            if auto:
                self.app.neutron_info_label.configure(text=f"📋 Auto-copied: {current_system}")
                self.app._log(f"Auto-copied neutron waypoint: {current_system}")
            else:
                self.app.neutron_info_label.configure(text=f"📋 Copied: {current_system}")
                self.app._log(f"Copied neutron waypoint: {current_system}")
        except ImportError:
            try:
                temp_root = tk.Tk()
                temp_root.withdraw()
                temp_root.clipboard_clear()
                temp_root.clipboard_append(current_system)
                temp_root.update()
                temp_root.destroy()
                if auto:
                    self.app.neutron_info_label.configure(text=f"📋 Auto-copied: {current_system}")
                    self.app._log(f"Auto-copied neutron waypoint: {current_system}")
                else:
                    self.app.neutron_info_label.configure(text=f"📋 Copied: {current_system}")
                    self.app._log(f"Copied neutron waypoint: {current_system}")
            except Exception as e:
                if not auto:
                    ErrorDialog(self.app, "Error", f"Failed to copy to clipboard:\n{e}")
                self.app._log(f"Clipboard copy error: {e}")
    def update_neutron_navigation(self):
        current_system = self.app.neutron_router.get_current_waypoint()
        self.app.neutron_current_btn.configure(text=current_system)
        has_prev = self.app.neutron_router.current_waypoint_index > 0
        has_next = (self.app.neutron_router.current_waypoint_index <
                   len(self.app.neutron_router.last_route) - 1 if self.app.neutron_router.last_route else False)
        self.app.neutron_prev_btn.configure(state="normal" if has_prev else "disabled")
        self.app.neutron_next_btn.configure(state="normal" if has_next else "disabled")
        
        self.update_neutron_systems_list()
        
        if has_next:
            next_system = self.app.neutron_router.last_route[self.app.neutron_router.current_waypoint_index + 1]["system"]
            try:
                import pyperclip
                pyperclip.copy(next_system)
                self.app._log(f"Next neutron system copied: {next_system}")
            except ImportError:
                try:
                    temp_root = tk.Tk()
                    temp_root.withdraw()
                    temp_root.clipboard_clear()
                    temp_root.clipboard_append(next_system)
                    temp_root.update()
                    temp_root.destroy()
                    self.app._log(f"Next neutron system copied: {next_system}")
                except Exception:
                    self.app._log(f"Failed to copy: {next_system}")
        if self.app.overlay_enabled and self.app.tabview.get() == "Neutron Highway":
            try:
                self.app.overlay_manager.update_data()
            except Exception:
                pass
        if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
            self.app.neutron_router.save_neutron_route(self.app.current_backup_folder)
        if hasattr(self.app, 'neutron_progress_label') and self.app.neutron_router.last_route:
            current_index = self.app.neutron_router.current_waypoint_index
            total_waypoints = len(self.app.neutron_router.last_route)
            progress_text = f"🎯 Progress Status | Current: {current_index + 1}/{total_waypoints} | Remaining: {total_waypoints - current_index - 1} waypoints"
            self.app.neutron_progress_label.configure(text=progress_text)
    def update_neutron_statistics(self, result):
        if not result or not result.get('success'):
            return
        waypoints = result.get('waypoints', [])
        total_distance = result.get('total_distance', 0)
        total_jumps = result.get('total_jumps', 0)
        neutron_jumps = result.get('neutron_jumps', 0)
        normal_jumps = result.get('normal_jumps', 0)
        stats_text = f"📊 Neutron Statistics | Distance: {total_distance} LY | Jumps: {total_jumps} | Neutrons: {neutron_jumps} | Waypoints: {len(waypoints)}"
        self.app.neutron_stats_label.configure(text=stats_text)
        current_index = self.app.neutron_router.current_waypoint_index
        progress_text = f"🎯 Progress Status | Current: {current_index + 1}/{len(waypoints)} | Remaining: {len(waypoints) - current_index - 1} waypoints"
        self.app.neutron_progress_label.configure(text=progress_text)
    def update_neutron_statistics_from_loaded_route(self):
        if not self.app.neutron_router.last_route:
            return
        waypoints = self.app.neutron_router.last_route
        total_distance = sum(wp.get('distance', 0) for wp in waypoints)
        neutron_jumps = sum(1 for wp in waypoints if wp.get('type') == 'Neutron')
        normal_jumps = sum(wp.get('jumps', 1) for wp in waypoints)
        fake_result = {
            'success': True,
            'waypoints': waypoints,
            'total_distance': total_distance,
            'total_jumps': normal_jumps,
            'neutron_jumps': neutron_jumps,
            'normal_jumps': normal_jumps - neutron_jumps
        }
        self.update_neutron_statistics(fake_result)
    def handle_neutron_system_jump(self, system_name):
        if not self.app.neutron_router.last_route:
            return
        for i, waypoint in enumerate(self.app.neutron_router.last_route):
            if waypoint['system'].lower() == system_name.lower():
                self.app.neutron_router.update_waypoint_status(system_name, 'visited')
                self.app.neutron_router.current_waypoint_index = i
                self.update_neutron_navigation()
                self.app._log(f"Auto-detected neutron jump to '{system_name}' (marked visited)")
                if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
                    self.app.neutron_router.save_neutron_route(self.app.current_backup_folder)
                return
    def get_current_system_from_journal(self):
        try:
            if self.app.journal_monitor:
                return self.app.journal_monitor.get_current_system()
            selected_cmdr = self.app.config.selected_commander
            from edmrn.journal import JournalMonitor
            import json
            temp_monitor = JournalMonitor(None, selected_commander=selected_cmdr)
            latest_file = temp_monitor._get_latest_journal_file()
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
            logger.error(f"Error getting current system: {e}")
            return None
    
    def update_neutron_systems_list(self):
        if not hasattr(self.app, 'neutron_scroll_frame'):
            return
        
        for widget in self.app.neutron_scroll_frame.winfo_children():
            widget.destroy()
        
        if not self.app.neutron_router.last_route:
            no_route_label = ctk.CTkLabel(
                self.app.neutron_scroll_frame,
                text="No neutron route calculated",
                font=ctk.CTkFont(size=12)
            )
            no_route_label.pack(pady=20)
            return
        
        colors = self.app.theme_manager.get_theme_colors()
        
        for i, waypoint in enumerate(self.app.neutron_router.last_route):
            system_name = waypoint.get('system', 'Unknown')
            status = waypoint.get('status', 'unvisited')
            wp_type = waypoint.get('type', 'Normal')
            jumps = waypoint.get('jumps', 1)
            
            if wp_type == "Neutron":
                display_text = f"{i+1}. ⚡ {system_name}"
            else:
                if jumps > 1:
                    display_text = f"{i+1}. {system_name} ({jumps} jumps)"
                else:
                    display_text = f"{i+1}. {system_name}"
            
            label = ctk.CTkLabel(
                self.app.neutron_scroll_frame,
                text=display_text,
                anchor="w",
                justify="left",
                cursor="hand2",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                fg_color="transparent",
                text_color=colors['text']
            )
            label.pack(fill="x", padx=10, pady=2)
            
            if status == 'visited':
                label.configure(fg_color="#4CAF50")
            elif status == 'skipped':
                label.configure(fg_color="#FFA500")
            else:
                label.configure(fg_color="transparent", text_color="#E0E0E0")
