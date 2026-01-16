import json
import threading
import glob
import os
from pathlib import Path
from tkinter import filedialog
from edmrn.journal import JournalMonitor
from edmrn.logger import get_logger
from edmrn.gui import ErrorDialog, InfoDialog, WarningDialog
logger = get_logger('JournalOperations')
class JournalOperations:
    def __init__(self, app):
        self.app = app
    def start_journal_monitor(self):
        if self.app.journal_monitor:
            self.app.journal_monitor.stop()
        manual_path = self.app.journal_path_var.get().strip() or None
        self.app.journal_monitor = JournalMonitor(callback=self.app._handle_system_jump, manual_journal_path=manual_path, selected_commander=self.app.selected_commander.get())
        self.app.journal_monitor.start()
        self.app._log(f"Journal monitor started with path: {manual_path or 'auto-detected'}")
    def handle_system_jump(self, system_name):
        current_tab = self.app.tabview.get()
        if current_tab == "Neutron Highway":
            self.app.neutron_manager.handle_neutron_system_jump(system_name)
        elif current_tab == "Galaxy Plotter":
            if self.app.galaxy_route_waypoints:
                self.app._handle_galaxy_system_jump(system_name)
        else:
            self.app.root.after(0, lambda: self.app._update_system_status_from_monitor(system_name, 'visited'))
    def get_latest_cmdr_data(self):
        cmdr_name_default = "CMDR NoName"
        cmdr_cash = 0
        current_system = "Unknown"
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
        final_cmdr_cash = self._format_cash(cmdr_cash)
        final_location = current_system or "Unknown"
        try:
            self.app.root.after(0, lambda: self.app.cmdr_name.set(final_cmdr_name))
            self.app.root.after(0, lambda: self.app.cmdr_cash.set(final_cmdr_cash))
            self.app.root.after(0, lambda: self.app.cmdr_location.set(final_location))
        except RuntimeError:
            return
        self.app._log(f"CMDR Status Loaded: {final_cmdr_name}, {final_cmdr_cash}, Location: {final_location}")
    def _format_cash(self, amount):
        try:
            cash_int = int(amount)
            return f"{cash_int:,}".replace(",", ".") + " Cr"
        except Exception:
            return f"{amount} Cr"
    def detect_all_commanders(self):
        try:
            journal_path = self.app.journal_path_var.get().strip() or self._get_auto_journal_path()
            if not journal_path or not Path(journal_path).exists():
                return ["Auto"]
            jm = JournalMonitor(None, manual_journal_path=journal_path)
            commanders = jm.detect_commanders()
            current = jm.detect_current_commander()
            values = ["Auto"] + commanders
            if current and current not in values:
                values.insert(1, f"Auto (Current: {current})")
            return values
        except Exception as e:
            self.app._log(f"Error detecting commanders: {e}")
            return ["Auto"]
    def _get_auto_journal_path(self):
        temp_monitor = JournalMonitor(None)
        return temp_monitor._find_journal_dir()
    def test_journal_path(self):
        test_path = self.app.journal_path_var.get().strip()
        if not test_path:
            test_path = self._get_auto_journal_path()
        if not test_path:
            ErrorDialog(self.app, "Error", "No journal path found")
            return
        if not Path(test_path).exists():
            ErrorDialog(self.app, "Error", f"Path does not exist:\n{test_path}")
            return
        pattern = Path(test_path) / 'Journal.*.log'
        journal_files = glob.glob(str(pattern))
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
            self.app._log(f"Switching to commander: {selected}")
            if self.app.journal_monitor:
                self.app.journal_monitor.stop()
            manual_path = self.app.journal_path_var.get().strip() or None
            self.app.journal_monitor = JournalMonitor(
                callback=self.app._handle_system_jump,
                manual_journal_path=manual_path,
                selected_commander=selected
            )
            self.app.journal_monitor.start()
            threading.Thread(target=self.get_latest_cmdr_data, daemon=True).start()
            InfoDialog(self.app, "Success", f"Journal monitor restarted for commander: {selected}")
    def refresh_commanders_list(self):
        commanders = self.detect_all_commanders()
        if hasattr(self.app, 'cmdr_dropdown'):
            self.app.cmdr_dropdown.configure(values=commanders)
        current = self.app.selected_commander.get()
        if current not in commanders and commanders:
            self.app.selected_commander.set(commanders[0])
        self.app._log(f"Refreshed commanders list: {len(commanders)} found")
        return commanders
