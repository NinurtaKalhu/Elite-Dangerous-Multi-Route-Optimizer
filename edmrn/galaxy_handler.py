import logging
import threading
import customtkinter as ctk
import tkinter as tk
from edmrn.gui import ErrorDialog, InfoDialog, WarningDialog

logger = logging.getLogger('GalaxyHandler')


class GalaxyHandler:
    def __init__(self, app):
        self.app = app

    def reverse_galaxy_route(self):
        source = self.app.galaxy_source_autocomplete.get()
        dest = self.app.galaxy_dest_autocomplete.get()
        self.app.galaxy_source_autocomplete.set(dest)
        self.app.galaxy_dest_autocomplete.set(source)
        self.app._log("Galaxy Plotter: Route reversed")

    def calculate_galaxy_route(self):
        source = self.app.galaxy_source_autocomplete.get().strip()
        dest = self.app.galaxy_dest_autocomplete.get().strip()
        jump_range_str = self.app.galaxy_jump_range_var.get().strip()

        if not source:
            if hasattr(self.app, 'journal_monitor') and self.app.journal_monitor:
                current_system = self.app.journal_monitor.get_current_system()
                if current_system:
                    source = current_system
                    self.app.galaxy_source_autocomplete.set(current_system)
        if not dest:
            if hasattr(self.app, 'journal_monitor') and self.app.journal_monitor:
                last_system = getattr(self.app, 'last_known_system', None)
                if last_system:
                    dest = last_system
                    self.app.galaxy_dest_autocomplete.set(last_system)
        if not jump_range_str:
            default_jump_range = self.app.jump_range.get().strip() if hasattr(self.app, 'jump_range') else "50.0"
            jump_range_str = default_jump_range
            self.app.galaxy_jump_range_var.set(jump_range_str)

        ship_build = self.app.galaxy_ship_build.get("1.0", "end").strip()
        if not ship_build:
            ship_build = ""
        try:
            jump_range = float(jump_range_str)
        except Exception:
            jump_range = 50.0
        boost_val = self.app.galaxy_boost_var.get() if hasattr(self.app, 'galaxy_boost_var') else "x6 (Caspian)"
        use_supercharge = True if "x6" in boost_val else False

        if not source or not dest:
            WarningDialog(self.app, "Missing Input", "Please enter both source and destination systems.")
            return
        try:
            cargo = int(self.app.galaxy_cargo_var.get() or 0)
            reserve_fuel = float(self.app.galaxy_reserve_fuel_var.get() or 0.0)
        except ValueError:
            WarningDialog(self.app, "Invalid Input", "Cargo and Reserve Fuel must be numeric values.")
            return
        self.app.galaxy_output.configure(state="normal")
        self.app.galaxy_output.delete("1.0", "end")
        self.app.galaxy_output.insert("1.0", "Submitting route to Spansh API...\n\n")
        self.app.galaxy_output.insert("end", "Calculating route...\n\n")
        self.app.galaxy_output.configure(state="disabled")

        def progress_callback(message: str):
            self.app.galaxy_output.configure(state="normal")
            self.app.galaxy_output.insert("end", f"{message}\n")
            self.app.galaxy_output.see("end")
            self.app.galaxy_output.configure(state="disabled")

        def calculate_thread():
            try:
                result = self.app.galaxy_plotter.plot_route(
                    source_system=source,
                    destination_system=dest,
                    ship_build=ship_build,
                    cargo=cargo,
                    reserve_fuel=reserve_fuel,
                    already_supercharged=self.app.galaxy_already_supercharged.get(),
                    use_supercharge=use_supercharge,
                    use_injections=self.app.galaxy_use_injections.get(),
                    exclude_secondary=self.app.galaxy_exclude_secondary.get(),
                    refuel_every_scoopable=self.app.galaxy_refuel_every.get(),
                    routing_algorithm=self.app.galaxy_algorithm_var.get(),
                    progress_callback=lambda msg: self.app.root.after(0, lambda: progress_callback(msg)),
                    range_ly=jump_range
                )
                self.app.root.after(0, lambda: self.display_galaxy_route_result(result))
            except Exception as e:
                error_msg = f"Error: {e}"
                logger.error(error_msg)
                self.app.root.after(0, lambda: self.display_galaxy_route_error(error_msg))

        threading.Thread(target=calculate_thread, daemon=True).start()
        self.app._log(f"Galaxy Plotter: Calculating route via Spansh API for {source} -> {dest}")

    def display_galaxy_route_result(self, result):
        self.app.galaxy_output.configure(state="normal")
        self.app.galaxy_output.delete("1.0", "end")

        if not result or "result" not in result:
            self.app.galaxy_output.insert("1.0", "No route data returned.\n")
            self.app.galaxy_output.configure(state="disabled")
            self.app.galaxy_current_btn.configure(text="No route calculated")
            self.app.galaxy_prev_btn.configure(state="disabled")
            self.app.galaxy_next_btn.configure(state="disabled")
            self.update_galaxy_systems_list()
            self.update_galaxy_statistics()
            return

        self.app.galaxy_plotter_route_data = result
        self.app.galaxy_export_btn.configure(state="normal")

        summary = self.app.galaxy_plotter.format_route_summary(result)
        self.app.galaxy_output.insert("1.0", "=== ROUTE SUMMARY ===\n")
        self.app.galaxy_output.insert("end", summary + "\n\n")

        self.app.galaxy_route_waypoints = self.app.galaxy_plotter.extract_system_jumps(result)
        self.app.galaxy_current_waypoint_index = 0
        self.update_galaxy_systems_list()
        self.update_galaxy_navigation()
        self.update_galaxy_statistics()
        self.copy_current_galaxy_system(auto=True)

        if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
            self.app.galaxy_plotter.save_galaxy_route(self.app.current_backup_folder, self.app.galaxy_route_waypoints, self.app.galaxy_current_waypoint_index)

        if not self.app.journal_monitor:
            self.app._start_journal_monitor()
        self.app._ensure_overlay_started("Galaxy Plotter")

        self.app.galaxy_output.configure(state="disabled")

    def display_galaxy_route_error(self, error_msg: str):
        self.app.galaxy_calculate_btn.configure(state="normal", text="Calculate Exact Route")
        self.app.galaxy_output.configure(state="normal")
        self.app.galaxy_output.insert("end", f"\n{error_msg}\n")
        self.app.galaxy_output.configure(state="disabled")
        self.app._log(f"Galaxy Plotter: {error_msg}")

    def export_galaxy_route(self):
        if not self.app.galaxy_plotter_route_data:
            WarningDialog(self.app, "No Route", "Please calculate a route first before exporting.")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            title="Export Galaxy Route",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            success = self.app.galaxy_plotter.export_route_to_csv(self.app.galaxy_plotter_route_data, filename)
            if success:
                InfoDialog(self.app, "Export Successful", f"Route exported to:\n{filename}")
                self.app._log(f"Galaxy Plotter: Route exported to {filename}")
            else:
                ErrorDialog(self.app, "Export Failed", "Failed to export route to CSV.")
                self.app._log("Galaxy Plotter: Route export failed")

    def galaxy_prev_waypoint(self):
        if not self.app.galaxy_route_waypoints:
            return
        if self.app.galaxy_current_waypoint_index > 0:
            self.app.galaxy_current_waypoint_index -= 1
            self.update_galaxy_navigation()
            if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
                self.app.galaxy_plotter.save_galaxy_route(
                    self.app.current_backup_folder,
                    self.app.galaxy_route_waypoints,
                    self.app.galaxy_current_waypoint_index
                )

    def galaxy_next_waypoint(self):
        if not self.app.galaxy_route_waypoints:
            return
        if self.app.galaxy_current_waypoint_index < len(self.app.galaxy_route_waypoints) - 1:
            self.app.galaxy_plotter.mark_waypoint_as_visited(
                self.app.galaxy_route_waypoints,
                self.app.galaxy_current_waypoint_index
            )
            self.app.galaxy_current_waypoint_index += 1
            self.update_galaxy_navigation()
            self.update_galaxy_statistics()
            self.copy_current_galaxy_system(auto=True)
            if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
                self.app.galaxy_plotter.save_galaxy_route(
                    self.app.current_backup_folder,
                    self.app.galaxy_route_waypoints,
                    self.app.galaxy_current_waypoint_index
                )

    def copy_current_galaxy_system(self, auto: bool = False):
        if not self.app.galaxy_route_waypoints:
            if not auto:
                WarningDialog(self.app, "Warning", "No galaxy route calculated.")
            return
        current = self.app.galaxy_route_waypoints[self.app.galaxy_current_waypoint_index]
        current_system = current.get('system', 'Unknown')
        try:
            import pyperclip
            pyperclip.copy(current_system)
            if auto:
                self.app._log(f"Auto-copied galaxy waypoint: {current_system}")
            else:
                self.app._log(f"Copied galaxy waypoint: {current_system}")
        except ImportError:
            try:
                temp_root = tk.Tk()
                temp_root.withdraw()
                temp_root.clipboard_clear()
                temp_root.clipboard_append(current_system)
                temp_root.update()
                temp_root.destroy()
                self.app._log(f"Galaxy system copied: {current_system}")
            except Exception as e:
                if not auto:
                    ErrorDialog(self.app, "Error", f"Failed to copy to clipboard:\n{e}")
                self.app._log(f"Clipboard copy error (galaxy): {e}")

    def update_galaxy_navigation(self):
        if not self.app.galaxy_route_waypoints:
            self.app.galaxy_current_btn.configure(text="No route calculated")
            self.app.galaxy_prev_btn.configure(state="disabled")
            self.app.galaxy_next_btn.configure(state="disabled")
            if hasattr(self.app, 'galaxy_scroll_frame'):
                for widget in self.app.galaxy_scroll_frame.winfo_children():
                    widget.destroy()
                no_route_label = ctk.CTkLabel(
                    self.app.galaxy_scroll_frame,
                    text="No route calculated",
                    font=ctk.CTkFont(size=12)
                )
                no_route_label.pack(pady=20)
            return

        idx = self.app.galaxy_current_waypoint_index
        total = len(self.app.galaxy_route_waypoints)
        current = self.app.galaxy_route_waypoints[idx]
        current_name = current.get('system', 'Unknown')
        self.app.galaxy_current_btn.configure(text=current_name)

        if idx < total - 1:
            next_system = self.app.galaxy_route_waypoints[idx + 1].get('system', 'Unknown')
            try:
                import pyperclip
                pyperclip.copy(next_system)
                self.app._log(f"Auto-copied next galaxy waypoint: {next_system}")
            except ImportError:
                try:
                    temp_root = tk.Tk()
                    temp_root.withdraw()
                    temp_root.clipboard_clear()
                    temp_root.clipboard_append(next_system)
                    temp_root.update()
                    temp_root.destroy()
                    self.app._log(f"Auto-copied next galaxy waypoint: {next_system}")
                except Exception as e:
                    self.app._log(f"Clipboard copy error (galaxy next): {e}")

        has_prev = idx > 0
        has_next = idx < total - 1
        self.app.galaxy_prev_btn.configure(state=("normal" if has_prev else "disabled"))
        self.app.galaxy_next_btn.configure(state=("normal" if has_next else "disabled"))

        self.update_galaxy_systems_list()

        if hasattr(self.app, 'galaxy_progress_label'):
            remaining = total - idx - 1
            progress_text = f"Progress Status | Current: {idx + 1}/{total} | Remaining: {remaining} waypoints"
            self.app.galaxy_progress_label.configure(text=progress_text)

        if self.app.overlay_enabled and self.app.tabview.get() == "Galaxy Plotter":
            try:
                self.app.overlay_manager.update_data()
            except Exception:
                pass

    def update_galaxy_statistics(self):
        if not self.app.galaxy_route_waypoints or not self.app.galaxy_plotter_route_data:
            if hasattr(self.app, 'galaxy_stats_label'):
                self.app.galaxy_stats_label.configure(text="Galaxy Statistics | No route calculated")
            if hasattr(self.app, 'galaxy_progress_label'):
                self.app.galaxy_progress_label.configure(text="Progress Status | Ready to calculate")
            return

        result = self.app.galaxy_plotter_route_data.get("result", {})
        total_distance = result.get("distance", 0)
        total_jumps = len(self.app.galaxy_route_waypoints)
        neutron_count = sum(1 for wp in self.app.galaxy_route_waypoints if wp.get("neutron_star", False))
        refuel_count = sum(1 for wp in self.app.galaxy_route_waypoints if wp.get("refuel", False))

        stats_text = f"Galaxy Statistics | Distance: {total_distance:.2f} LY | Jumps: {total_jumps} | Neutrons: {neutron_count} | Refuels: {refuel_count}"

        if hasattr(self.app, 'galaxy_stats_label'):
            self.app.galaxy_stats_label.configure(text=stats_text)

        idx = self.app.galaxy_current_waypoint_index
        remaining = total_jumps - idx - 1
        progress_text = f"Progress Status | Current: {idx + 1}/{total_jumps} | Remaining: {remaining} waypoints"

        if hasattr(self.app, 'galaxy_progress_label'):
            self.app.galaxy_progress_label.configure(text=progress_text)

    def update_galaxy_systems_list(self):
        if not hasattr(self.app, 'galaxy_scroll_frame'):
            return
        for widget in self.app.galaxy_scroll_frame.winfo_children():
            widget.destroy()

        if not self.app.galaxy_route_waypoints:
            no_route_label = ctk.CTkLabel(
                self.app.galaxy_scroll_frame,
                text="No route calculated",
                font=ctk.CTkFont(size=12)
            )
            no_route_label.pack(pady=20)
            return

        colors = self.app.theme_manager.get_theme_colors()
        for i, waypoint in enumerate(self.app.galaxy_route_waypoints):
            system_name = waypoint.get('system', 'Unknown')
            status = waypoint.get('status', 'pending')

            if status == 'visited':
                bg_color = colors.get('success', '#4CAF50')
                text_color = '#FFFFFF'
                prefix = "[Visited] "
            elif i == self.app.galaxy_current_waypoint_index:
                bg_color = colors.get('accent', '#FFD700')
                text_color = colors.get('background', '#1a1a1a')
                prefix = "[Current] "
            else:
                bg_color = colors.get('frame', '#2E2E2E')
                text_color = colors.get('text', '#FFFFFF')
                prefix = ""

            frame = ctk.CTkFrame(self.app.galaxy_scroll_frame, fg_color=bg_color, corner_radius=5)
            frame.pack(fill="x", padx=5, pady=2)

            label = ctk.CTkLabel(
                frame,
                text=f"{prefix}{i + 1}. {system_name}",
                font=ctk.CTkFont(size=11),
                text_color=text_color
            )
            label.pack(padx=8, pady=4, anchor="w")

    def handle_galaxy_system_jump(self, system_name: str):
        if not self.app.galaxy_route_waypoints:
            return

        def normalize(name):
            return name.replace(' ', '').replace('-', '').replace('_', '').lower() if name else ''

        target = normalize(system_name)
        for i, waypoint in enumerate(self.app.galaxy_route_waypoints):
            wp_name = normalize(waypoint.get('system', ''))
            if wp_name == target:
                self.app.galaxy_plotter.update_waypoint_status(self.app.galaxy_route_waypoints, waypoint.get('system', ''), 'visited')
                self.app.galaxy_current_waypoint_index = i
                self.update_galaxy_navigation()
                self.update_galaxy_statistics()
                self.app._log(f"Galaxy Plotter: Auto-detected jump to '{system_name}' (marked visited)")
                if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
                    self.app.galaxy_plotter.save_galaxy_route(
                        self.app.current_backup_folder,
                        self.app.galaxy_route_waypoints,
                        self.app.galaxy_current_waypoint_index
                    )
                next_idx = None
                for j in range(i + 1, len(self.app.galaxy_route_waypoints)):
                    if self.app.galaxy_route_waypoints[j].get('status') != 'visited':
                        next_idx = j
                        break
                if next_idx is not None:
                    next_system = self.app.galaxy_route_waypoints[next_idx].get('system', 'Unknown')
                    try:
                        import pyperclip
                        pyperclip.copy(next_system)
                        self.app._log(f"Auto-copied next galaxy waypoint: {next_system}")
                    except ImportError:
                        try:
                            temp_root = tk.Tk()
                            temp_root.withdraw()
                            temp_root.clipboard_clear()
                            temp_root.clipboard_append(next_system)
                            temp_root.update()
                            temp_root.destroy()
                            self.app._log(f"Auto-copied next galaxy waypoint: {next_system}")
                        except Exception as e:
                            self.app._log(f"Clipboard copy error (galaxy next): {e}")
                return
