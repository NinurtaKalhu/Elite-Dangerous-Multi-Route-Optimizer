import os
import json
import logging
import threading
import customtkinter as ctk
import tkinter as tk
from pathlib import Path
from edmrn.journal import JournalMonitor
from edmrn.gui import InfoDialog, WarningDialog, ErrorDialog

logger = logging.getLogger('JournalHandler')


class JournalHandler:
    def __init__(self, app):
        self.app = app

    def start_journal_monitor(self):
        if self.app.journal_monitor:
            self.app.journal_monitor.stop()
        manual_path = self.app.journal_path_var.get().strip() or None
        self.app.journal_monitor = JournalMonitor(
            callback=self.app._journal_callback,
            manual_journal_path=manual_path,
            selected_commander=self.app.selected_commander.get()
        )
        self.app.journal_monitor.start()
        self.app._log(f"Journal monitor started with path: {manual_path or 'auto-detected'}")

    def handle_system_jump(self, system_name, event_data=None):
        if not system_name and event_data is not None:
            if event_data.get('event') in ('Exobiology', 'ScanOrganic'):
                self.app.handle_onfoot_bio_event(None, event_data)
                return

        if not system_name:
            system_name = getattr(self.app, 'last_known_system', None)
            if not system_name and hasattr(self.app, 'cmdr_location'):
                try:
                    system_name = self.app.cmdr_location.get()
                except Exception:
                    system_name = None

        if not system_name:
            logger.warning("[handle_system_jump] No system_name could be determined, aborting jump handling.")
            return

        if not hasattr(self.app, '_last_handled_system'):
            self.app._last_handled_system = None
        is_new_system = (system_name != self.app._last_handled_system)

        if not is_new_system:
            logger.info(f"[handle_system_jump] System already processed: {system_name}, skipping")
            if event_data is not None:
                self.app.handle_onfoot_bio_event(system_name, event_data)
            return

        self.app.last_known_system = system_name
        logger.info(f"[handle_system_jump] Processing NEW system: {system_name}")
        current_tab = self.app.tabview.get()

        overlay_manager = None
        try:
            from edmrn.overlay import get_overlay_manager
            overlay_manager = get_overlay_manager()
        except Exception:
            pass
        if overlay_manager and getattr(overlay_manager, '_instance', None):
            try:
                overlay_manager._instance.current_data['exobio_species'] = []
                overlay_manager._instance.current_data['bodies_to_scan'] = []
                overlay_manager._instance.update_display()
            except Exception:
                pass
        self.app._overlay_exobio_species = []
        if hasattr(self.app, 'system_info_section') and self.app.system_info_section:
            try:
                if hasattr(self.app.system_info_section, '_enqueue_bio_update'):
                    self.app.system_info_section._enqueue_bio_update([], system=system_name)
                else:
                    self.app.system_info_section.update_bio_summary([], system=system_name)
            except Exception:
                pass
            try:
                if hasattr(self.app.system_info_section, '_last_body'):
                    self.app.system_info_section._last_body = None
                if hasattr(self.app.system_info_section, '_onfoot_bio_samples'):
                    self.app.system_info_section._onfoot_bio_samples = []
                if hasattr(self.app.system_info_section, '_incomplete_exobio'):
                    self.app.system_info_section._incomplete_exobio = []
            except Exception:
                pass

        try:
            self.app.root.after(0, lambda: self.app.cmdr_location.set(system_name))
            entry = getattr(self.app.system_info_section, 'system_info_entry', None)
            if entry:
                real_entry = getattr(entry, 'entry', entry)
                if hasattr(real_entry, 'delete') and hasattr(real_entry, 'insert'):
                    real_entry.delete(0, tk.END)
                    real_entry.insert(0, system_name)
        except Exception:
            pass

        if current_tab == "Neutron Highway":
            if getattr(self.app.neutron_router, 'last_route', None):
                self.app.neutron_manager.handle_neutron_system_jump(system_name)
        elif current_tab == "Galaxy Plotter":
            if getattr(self.app, 'galaxy_route_waypoints', None):
                self.app.galaxy_handler.handle_galaxy_system_jump(system_name)

        if not hasattr(self.app, 'system_info_section') or self.app.system_info_section is None:
            self.app._lazy_load_tab("System Info")
        if hasattr(self.app, 'system_info_section') and self.app.system_info_section:
            if not hasattr(self.app, 'system_info_section') or self.app.system_info_section is None:
                self.app._pending_system_info_fetch = system_name
                try:
                    self.app.root.after(0, lambda: self.app._lazy_load_tab("System Info"))
                except Exception:
                    pass
            else:
                logger.info("[handle_system_jump] Triggering _system_info_fetch_callback() for System Info tab")
                self.app._system_info_fetch_callback(system_name)

        if hasattr(self.app, 'system_info_section') and self.app.system_info_section:
            try:
                if hasattr(self.app, 'root') and self.app.root:
                    self.app.root.after(0, lambda: self.app.system_info_section.update_log({'name': system_name}))
                else:
                    self.app.system_info_section.update_log({'name': system_name})
                logger.info(f"[handle_system_jump] Log updated for system: {system_name}")
            except Exception as ex:
                logger.warning(f"[handle_system_jump] Failed to update log: {ex}")

        self.app._last_handled_system = system_name

        if event_data is not None:
            self.app.handle_onfoot_bio_event(system_name, event_data)

        if current_tab not in ("System Info", "Neutron Highway", "Galaxy Plotter"):
            self.app.root.after(0, lambda: self.app._update_system_status_from_monitor(system_name, 'visited'))

    def get_latest_cmdr_data(self):
        cmdr_name_default = "CMDR NoName"
        cmdr_cash = 0
        selected_cmdr = self.app.config.selected_commander
        journal_monitor = JournalMonitor(None, selected_commander=selected_cmdr)
        latest_file = journal_monitor._get_latest_journal_file()
        if not latest_file:
            try:
                self.app.root.after(0, lambda: self.app.cmdr_name.set(f"CMDR Not Found ({cmdr_name_default})"))
                self.app.root.after(0, lambda: self.app.cmdr_cash.set("Where is the bank? (Saved Data)"))
            except RuntimeError:
                pass
            return
        self.app._log(f"Checking Journal file: {Path(latest_file).name}")
        current_system = "Unknown"
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        event = data.get('event')
                        if event == 'Commander':
                            cmdr_name_default = data.get('Name', cmdr_name_default)
                        elif event == 'LoadGame':
                            cmdr_cash = data.get('Credits', cmdr_cash)
                        elif event in ['FSDJump', 'Location']:
                            current_system = data.get('StarSystem', current_system)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.app._log(f"ERROR reading CMDR data from Journal: {e}")

        final_cmdr_name = cmdr_name_default
        try:
            self.app.root.after(0, lambda: self.app.cmdr_name.set(f"CMDR {final_cmdr_name}"))
            self.app.root.after(0, lambda: self.app.cmdr_cash.set(f"{cmdr_cash:,} Cr"))
            self.app.root.after(0, lambda: self.app.cmdr_location.set(current_system))
            self.app._log(f"CMDR Status Loaded: {final_cmdr_name}, {cmdr_cash:,} Cr, Location: {current_system}")
        except RuntimeError:
            pass

    def format_cash(self, amount):
        try:
            return f"{int(amount):,} Cr"
        except (ValueError, TypeError):
            return "N/A Cr"

    def detect_all_commanders(self):
        journal_dir = self.app._get_auto_journal_path()
        if not journal_dir or not os.path.exists(journal_dir):
            return []
        commanders = set()
        try:
            import glob
            pattern = os.path.join(journal_dir, 'Journal.*.log')
            files = glob.glob(pattern)
            for f in files:
                try:
                    with open(f, 'r', encoding='utf-8') as fh:
                        for line in fh:
                            if '"Commander"' in line or '"LoadGame"' in line:
                                data = json.loads(line)
                                if data.get('event') == 'Commander':
                                    name = data.get('Name')
                                    if name:
                                        commanders.add(name)
                                elif data.get('event') == 'LoadGame':
                                    name = data.get('Commander')
                                    if name and name != '$ức_default_name':
                                        commanders.add(name)
                except Exception:
                    continue
        except Exception:
            pass
        return sorted(list(commanders))

    def get_auto_journal_path(self):
        base = os.path.join(os.path.expanduser('~'), 'Saved Games', 'Frontier Developments', 'Elite Dangerous')
        if os.path.exists(base):
            return base
        return None

    def browse_journal_path(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Select Elite Dangerous Journal Directory")
        if path:
            self.app.journal_path_var.set(path)

    def test_journal_path(self):
        path = self.app.journal_path_var.get().strip()
        if not path:
            WarningDialog(self.app, "No Path", "Please enter or browse for a journal path first.")
            return
        if not os.path.exists(path):
            ErrorDialog(self.app, "Invalid Path", f"Path does not exist:\n{path}")
            return
        import glob
        pattern = os.path.join(path, 'Journal.*.log')
        journal_files = glob.glob(pattern)
        if journal_files:
            latest = max(journal_files, key=os.path.getmtime)
            InfoDialog(self.app, "Success", f"Journal path is valid!\n\nFound {len(journal_files)} files\nLatest: {Path(latest).name}")
        else:
            WarningDialog(self.app, "Warning", "Path exists but no journal files found")

    def apply_journal_settings(self):
        manual_path = self.app.journal_path_var.get().strip() or None
        self.app.config.journal_path = manual_path if manual_path else ''
        self.app.config.save()
        if self.app.journal_monitor:
            self.app.journal_monitor.stop()
            self.app.journal_monitor = None
        self.app.journal_monitor = JournalMonitor(
            callback=self.app._handle_system_jump,
            manual_journal_path=manual_path,
            selected_commander=self.app.selected_commander.get()
        )
        self.app.journal_monitor.start()
        path_used = manual_path if manual_path else "Auto-detected path"
        self.app._log(f"Journal Monitor restarted with: {path_used}")
        InfoDialog(self.app, "Success", "Journal monitor restarted with new settings!")
        threading.Thread(target=self.get_latest_cmdr_data, daemon=True).start()

    def switch_commander(self, selected):
        if selected:
            self.app.config.selected_commander = selected
            self.app.config.save()
            self.app.selected_commander.set(selected)
            self.apply_journal_settings()

    def use_current_location(self):
        try:
            if hasattr(self.app, 'journal_monitor') and self.app.journal_monitor:
                current_system = self.app.journal_monitor.get_current_system()
                if current_system:
                    self.app.starting_system.set(current_system)
                    self.app._log(f"Starting system set to current location: {current_system}")
                    InfoDialog(self.app, "Location Set", f"Starting system set to:\n{current_system}")
                else:
                    WarningDialog(self.app, "No Location",
                                         "Could not detect current system.\n\n"
                                         "Make sure:\n"
                                         "- Elite Dangerous is running\n"
                                         "- You've jumped to a system recently\n"
                                         "- Journal monitoring is configured")
            else:
                WarningDialog(self.app, "Journal Not Ready",
                                     "Journal monitoring not initialized.\n"
                                     "Please configure journal path in Settings first.")
        except Exception as e:
            logger.error(f"Error getting current location: {e}")
            ErrorDialog(self.app, "Error", f"Could not get current location:\n{e}")

    def find_nearest_system_by_coordinates(self):
        import numpy as np
        try:
            starting = self.app.starting_system.get().strip()
            if not starting:
                WarningDialog(self.app, "No Starting System", "Please enter a starting system name.")
                return
            try:
                import requests
                resp = requests.get(
                    f"https://spansh.co.uk/api/systems/search",
                    json={"filters": {"name": {"value": [starting]}}, "size": 1},
                    headers={"User-Agent": "EDMRN_AutoComplete/1.0"},
                    timeout=10
                )
                if resp.status_code != 200:
                    WarningDialog(self.app, "API Error", f"Spansh API returned status {resp.status_code}")
                    return
                data = resp.json()
                systems = data.get('result', [])
                if not systems:
                    WarningDialog(self.app, "System Not Found", f"Could not find system: {starting}")
                    return
                coords = systems[0].get('coords', {})
                x = coords.get('x', 0)
                y = coords.get('y', 0)
                z = coords.get('z', 0)
            except Exception as e:
                WarningDialog(self.app, "API Error", f"Failed to look up system coordinates:\n{e}")
                return

            if not hasattr(self.app, 'csv_systems_data') or self.app.csv_systems_data is None:
                WarningDialog(self.app, "No CSV Data", "Please load a CSV file first.")
                return

            csv_data = self.app.csv_systems_data
            names = csv_data['names'].copy()
            coords_array = np.array(csv_data['coords'])
            player_coords = np.array([x, y, z])
            distances = np.linalg.norm(coords_array - player_coords, axis=1)
            sorted_indices = np.argsort(distances)
            nearest_count = min(20, len(sorted_indices))
            nearest_indices = sorted_indices[:nearest_count]

            self.app._show_nearest_results({
                'names': [names[i] for i in nearest_indices],
                'distances': [float(distances[i]) for i in nearest_indices]
            }, x, y, z)
        except Exception as e:
            logger.error(f"Error finding nearest system: {e}")
            ErrorDialog(self.app, "Error", f"Failed to find nearest system:\n{e}")

    def show_nearest_results(self, data, x, y, z):
        if not data or not data.get('names'):
            WarningDialog(self.app, "No Results", "No nearby systems found.")
            return
        popup = tk.Toplevel(self.app.root)
        popup.title("Nearest Systems")
        popup.geometry("500x400")
        popup.configure(bg="#222")
        popup.transient(self.app.root)
        popup.grab_set()
        frame = tk.Frame(popup, bg="#222")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(frame, text=f"Systems near ({x:.1f}, {y:.1f}, {z:.1f}):",
                 font=("Segoe UI", 11, "bold"), bg="#222", fg="#FFD700").pack(anchor="w", pady=(0, 5))
        listbox = tk.Listbox(frame, font=("Consolas", 10), bg="#333", fg="#FFF",
                            selectbackground="#FFD700", selectforeground="#000")
        listbox.pack(fill="both", expand=True)
        for name, dist in zip(data['names'], data['distances']):
            listbox.insert(tk.END, f"{name} ({dist:.2f} LY)")
        def copy_selected():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                name = data['names'][idx]
                try:
                    import pyperclip
                    pyperclip.copy(name)
                except ImportError:
                    self.app.root.clipboard_clear()
                    self.app.root.clipboard_append(name)
                self.app._log(f"Copied nearest system: {name}")
                popup.destroy()
        btn_frame = tk.Frame(frame, bg="#222")
        btn_frame.pack(fill="x", pady=(5, 0))
        tk.Button(btn_frame, text="Copy Selected", command=copy_selected,
                 bg="#FFD700", fg="#000", font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Button(btn_frame, text="Close", command=popup.destroy,
                 bg="#666", fg="#FFF", font=("Segoe UI", 10)).pack(side="right")

    def find_nearest_system(self, auto=False):
        try:
            if not hasattr(self.app, 'csv_systems_data') or self.app.csv_systems_data is None:
                if not auto:
                    WarningDialog(self.app, "No CSV Data",
                                         "Please load a CSV file first.\n\n"
                                         "The CSV must contain System Name, X, Y, Z columns.")
                return

            if not hasattr(self.app, 'journal_monitor') or not self.app.journal_monitor:
                if not auto:
                    WarningDialog(self.app, "Journal Not Ready",
                                         "Journal monitoring not initialized.\n"
                                         "Configure journal path in Settings first.")
                return

            current_system = self.app.journal_monitor.get_current_system()
            if not current_system:
                if not auto:
                    WarningDialog(self.app, "No Location",
                                         "Could not detect current system.\n"
                                         "Make sure Elite Dangerous is running.")
                return

            import requests
            resp = requests.get(
                f"https://spansh.co.uk/api/systems/search",
                json={"filters": {"name": {"value": [current_system]}}, "size": 1},
                headers={"User-Agent": "EDMRN_AutoComplete/1.0"},
                timeout=10
            )
            if resp.status_code != 200:
                if not auto:
                    WarningDialog(self.app, "API Error", f"Spansh API returned status {resp.status_code}")
                return
            data = resp.json()
            systems = data.get('result', [])
            if not systems:
                if not auto:
                    WarningDialog(self.app, "System Not Found", f"Could not find system: {current_system}")
                return
            coords = systems[0].get('coords', {})
            x = coords.get('x', 0)
            y = coords.get('y', 0)
            z = coords.get('z', 0)

            import numpy as np
            csv_data = self.app.csv_systems_data
            names = csv_data['names'].copy()
            coords_array = np.array(csv_data['coords'])
            player_coords = np.array([x, y, z])
            distances = np.linalg.norm(coords_array - player_coords, axis=1)
            nearest_idx = int(np.argmin(distances))
            nearest_name = names[nearest_idx]
            nearest_dist = float(distances[nearest_idx])

            self.app.starting_system.set(nearest_name)
            self.app._log(f"Nearest system to {current_system}: {nearest_name} ({nearest_dist:.2f} LY)")
            if not auto:
                InfoDialog(self.app, "Nearest System Found",
                                  f"Nearest system to your location:\n\n"
                                  f"{nearest_name}\n"
                                  f"Distance: {nearest_dist:.2f} LY\n\n"
                                  f"This has been set as the starting system.")
        except Exception as e:
            logger.error(f"Error finding nearest system: {e}")
            if not auto:
                ErrorDialog(self.app, "Error", f"Failed to find nearest system:\n{e}")

    def get_current_system_from_journal(self):
        if hasattr(self.app, 'journal_monitor') and self.app.journal_monitor:
            return self.app.journal_monitor.get_current_system()
        return None
