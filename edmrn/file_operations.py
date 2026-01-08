import os
import sys
import json
import pandas as pd
import subprocess
import webbrowser
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox
from datetime import datetime
from edmrn.config import Paths
from edmrn.tracker import STATUS_VISITED, STATUS_UNVISITED
from edmrn.logger import get_logger
logger = get_logger('FileOperations')
class FileOperations:
    def __init__(self, app):
        self.app = app
    def browse_file(self):
        for widget in self.app.tab_tracker.winfo_children():
            widget.destroy()
        filename = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.app.csv_file_path.set(filename)
            self.app._log(f"File: {filename}")
    def autodetect_csv(self, initial_run=False):
        csv_path = self.app.csv_file_path.get()
        if not csv_path or not Path(csv_path).exists():
            if initial_run:
                csv_files = list(Path.cwd().glob('*.csv'))
                if csv_files:
                    self.app.csv_file_path.set(str(csv_files[0]))
                    self.app._log(f"Auto-Detected: '{csv_files[0].name}' file selected.")
                else:
                    if initial_run:
                        self.app._log("Warning: CSV file not found. Please use 'Browse' to select one.")
    def open_app_data_folder(self):
        try:
            path = Paths.get_app_data_dir()
            Path(path).mkdir(exist_ok=True)
            if os.name == 'nt':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', path])
            else:
                subprocess.call(['xdg-open', path])
            self.app._log(f"Opened data folder: '{path}'")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open data folder:\n{Paths.get_app_data_dir()}")
            self.app._log(f"ERROR opening data folder: {e}")
    def open_output_csv(self):
        try:
            if hasattr(self.app, 'current_backup_folder') and self.app.current_backup_folder:
                backup_path = Path(self.app.current_backup_folder)
                csv_files = list(backup_path.glob("*.csv"))
                if csv_files:
                    latest_file = csv_files[0]
                    self._open_file(latest_file)
                    return
            backup_dir = Path(Paths.get_backup_folder())
            if backup_dir.exists():
                all_csvs = []
                for item in backup_dir.rglob("*.csv"):
                    if item.is_file():
                        all_csvs.append(item)
                if all_csvs:
                    latest_file = max(all_csvs, key=lambda x: x.stat().st_mtime)
                    self._open_file(latest_file)
                    return
            old_files = list(Path(Paths.get_app_data_dir()).glob("Optimized_Route_*.csv"))
            if old_files:
                latest_old = max(old_files, key=lambda x: x.stat().st_mtime)
                self._open_file(latest_old)
                return
            messagebox.showinfo("Info",
                "No optimized route file found.\n\n"
                "Please optimize a route first, then try again.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open CSV file:\n{e}")
            self.app._log(f"ERROR opening CSV: {e}")
    def _open_file(self, file_path):
        try:
            if os.name == 'nt':
                os.startfile(str(file_path))
            elif sys.platform == 'darwin':
                subprocess.call(['open', str(file_path)])
            else:
                subprocess.call(['xdg-open', str(file_path)])
            self.app._log(f"Opened CSV file: '{file_path.name}'")
        except Exception as e:
            try:
                webbrowser.open(f"file://{file_path}")
            except Exception:
                messagebox.showinfo("Info",
                    f"File: {file_path.name}\n\n"
                    f"Could not open automatically.\n"
                    f"Please open manually from:\n{file_path}")
    def quick_save_route(self):
        try:
            route_data = self.app.route_manager.get_route()
            if not route_data:
                messagebox.showwarning("Warning", "No route to save!")
                return
            visited = sum(1 for r in route_data if r['status'] == STATUS_VISITED)
            total = len(route_data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            route_name = f"QuickSave_{visited}of{total}_{timestamp}"
            backup_folder = Path(Paths.get_backup_folder()) / route_name
            backup_folder.mkdir(parents=True, exist_ok=True)
            rows = []
            for item in route_data:
                rows.append({
                    'System Name': item['name'],
                    'X': item['coords'][0],
                    'Y': item['coords'][1],
                    'Z': item['coords'][2],
                    'Status': item['status'],
                    'Bodies': str(item.get('bodies_to_scan', [])),
                    'Body_Count': item.get('body_count', 0)
                })
            df = pd.DataFrame(rows)
            csv_path = backup_folder / "current_route.csv"
            df.to_csv(csv_path, index=False)
            status_data = [{'name': item['name'], 'status': item['status']}
                          for item in route_data]
            status_path = backup_folder / "route_status.json"
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
            self.app.current_backup_folder = str(backup_folder)
            self.app._log(f"Quick save created: {route_name}")
            messagebox.showinfo("Quick Save",
                f"Route saved!\n\n"
                f"Name: {route_name}\n"
                f"Progress: {visited}/{total} systems")
        except Exception as e:
            self.app._log(f"Quick save error: {e}")
            messagebox.showerror("Error", f"Quick save failed:\n{e}")
    def load_from_backup(self):
        try:
            backup_dir = Path(Paths.get_backup_folder())
            if not backup_dir.exists():
                messagebox.showinfo("Info", "No backup folder found.")
                return
            backup_folders = []
            for item in backup_dir.iterdir():
                if item.is_dir():
                    csv_files = list(item.glob("*.csv"))
                    if csv_files:
                        backup_folders.append(str(item))
            if not backup_folders:
                messagebox.showinfo("Info",
                    "No backup routes found.\n\n"
                    "Backup routes will be created automatically when you optimize a new route."
                )
                return
            from edmrn.gui import BackupSelectionWindow
            selection_window = BackupSelectionWindow(
                self.app,
                backup_folders,
                self.load_backup_file
            )
        except Exception as e:
            logger.error(f"Backup loading error: {e}")
            messagebox.showerror("Error", f"Error loading backups:\n{str(e)}")
    def load_backup_file(self, backup_folder_path):
        try:
            folder = Path(backup_folder_path)
            if not folder.is_dir():
                raise ValueError("Selected path is not a folder")
            csv_path = folder / "optimized_route.csv"
            status_path = folder / "route_status.json"
            if not csv_path.exists():
                csv_files = list(folder.glob("*.csv"))
                if not csv_files:
                    raise FileNotFoundError("No CSV file found in backup folder")
                csv_path = csv_files[0]
            self.app.current_backup_folder = backup_folder_path
            df = pd.read_csv(csv_path)
            system_col = None
            for col in ['System Name', 'system_name', 'System', 'Name']:
                if col in df.columns:
                    system_col = col
                    break
            if not system_col:
                raise ValueError("No system name column found in CSV")
            coord_cols = {}
            for coord, aliases in [('X', ['X', 'x', 'Coord_X']),
                                   ('Y', ['Y', 'y', 'Coord_Y']),
                                   ('Z', ['Z', 'z', 'Coord_Z'])]:
                for alias in aliases:
                    if alias in df.columns:
                        coord_cols[coord] = alias
                        break
            if len(coord_cols) != 3:
                raise ValueError("Missing coordinate columns in CSV")
            route_data = []
            for idx, row in df.iterrows():
                try:
                    coords = [
                        float(row[coord_cols['X']]),
                        float(row[coord_cols['Y']]),
                        float(row[coord_cols['Z']])
                    ]
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Skipping row {idx} due to invalid coordinates: {e}")
                    continue
                    
                bodies = []
                body_count = 0
                if 'Body_Names' in df.columns:
                    body_data = row.get('Body_Names', [])
                    if isinstance(body_data, str):
                        if body_data.startswith('[') and body_data.endswith(']'):
                            try:
                                import ast
                                bodies = ast.literal_eval(body_data)
                            except Exception:
                                body_data = body_data.strip("[]").replace("'", "").replace('"', '')
                                bodies = [b.strip() for b in body_data.split(',')] if body_data else []
                        else:
                            bodies = [body_data.strip()] if body_data.strip() else []
                    elif isinstance(body_data, list):
                        bodies = body_data
                if 'Body_Count' in df.columns:
                    try:
                        body_count = int(row.get('Body_Count', 0))
                    except Exception:
                        body_count = len(bodies)
                if body_count == 0:
                    body_count = len(bodies)
                if not bodies and 'Bodies_To_Scan_List' in df.columns:
                    bodies_str = row.get('Bodies_To_Scan_List', '[]')
                    if isinstance(bodies_str, str) and bodies_str.startswith('['):
                        try:
                            import ast
                            bodies = ast.literal_eval(bodies_str)
                        except Exception:
                            bodies = []
                route_data.append({
                    'name': str(row[system_col]),
                    'status': STATUS_UNVISITED,
                    'coords': coords,
                    'bodies_to_scan': bodies,
                    'body_count': body_count
                })
            if status_path.exists():
                with open(status_path, "r", encoding="utf-8") as f:
                    status_data = json.load(f)
                status_map = {item['name']: item['status'] for item in status_data
                             if 'name' in item and 'status' in item}
                for item in route_data:
                    if item['name'] in status_map:
                        item['status'] = status_map[item['name']]
            self.app.route_tracker.load_route(route_data)
            if self.app.neutron_router.load_neutron_route(backup_folder_path):
                self.app._update_neutron_navigation()
                self.app._update_neutron_statistics_from_loaded_route()
                self.app._log(f"Neutron route loaded from backup")
            self.app._create_route_tracker_tab_content()
            self.app._log(f"Backup loaded: {folder.name}")
            messagebox.showinfo("Success",
                f"Backup loaded successfully!\n\n"
                f"Route: {folder.name}\n"
                f"Systems: {len(route_data)}\n"
                f"Visited: {sum(1 for r in route_data if r['status'] == STATUS_VISITED)}")
            return {'success': True, 'message': f"Backup loaded: {folder.name}"}
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("Error", f"Error loading backup:\n{error_msg}")
            logger.error(f"Backup load error: {e}")
            return {'success': False, 'error': error_msg}
