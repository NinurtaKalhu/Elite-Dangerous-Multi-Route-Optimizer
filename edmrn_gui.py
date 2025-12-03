import sys
import os
if getattr(sys, 'frozen', False):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
import pandas as pd
import numpy as np
import math
import glob
import tkinter as tk
import json
import threading
import tempfile
import time
import shutil
import importlib.util
import platform
import subprocess
import re
from PIL import Image
import webbrowser
import requests
import customtkinter as ctk
import zipfile
import psutil
import queue
import atexit
import concurrent.futures
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any, Tuple, Callable
from pathlib import Path
from datetime import datetime
from scipy.spatial.distance import cdist
from python_tsp.heuristics import solve_tsp_lin_kernighan
from tkinter import filedialog
from tqdm import tqdm

def load_external_module(module_name):
    try:
        if module_name == "overlay":
            from edmrn_overlay import start_overlay, stop_overlay, get_overlay_data_from_app
            return start_overlay, stop_overlay, get_overlay_data_from_app, True
        elif module_name == "backup":
            from edmrn_backup import BackupManager
            return BackupManager, True
        elif module_name == "autosave":
            from edmrn_autosave import AutoSaveManager
            return AutoSaveManager, True
        elif module_name == "platform":
            from edmrn_platform import PlatformDetector
            return PlatformDetector, True
    except ImportError:
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            module_path = os.path.join(base_path, f"edmrn_{module_name}.py")
            
            if os.path.exists(module_path):
                spec = importlib.util.spec_from_file_location(f"edmrn_{module_name}", module_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"edmrn_{module_name}"] = module
                spec.loader.exec_module(module)
                
                if module_name == "overlay":
                    return module.start_overlay, module.stop_overlay, module.get_overlay_data_from_app, True
                elif module_name == "backup":
                    return module.BackupManager, True
                elif module_name == "autosave":
                    return module.AutoSaveManager, True
                elif module_name == "platform":
                    return module.PlatformDetector, True
        except Exception:
            pass
    
    if module_name == "overlay":
        return None, None, None, False
    elif module_name == "backup":
        class FallbackBackupManager:
            def __init__(self, *args, **kwargs): pass
            def start(self): return False
            def stop(self): return False
            def backup_now(self): return None
            def get_backup_list(self): return []
            def get_status(self): return {}
        return FallbackBackupManager, True
    elif module_name == "autosave":
        class FallbackAutoSaveManager:
            def __init__(self, *args, **kwargs): pass
            def start(self): return False
            def stop(self): return False
            def save_now(self): return False
            def get_status(self): return {}
        return FallbackAutoSaveManager, True
    elif module_name == "platform":
        class FallbackPlatformDetector:
            def __init__(self): pass
            def is_windows(self): return platform.system() == "Windows"
            def is_macos(self): return platform.system() == "Darwin"
            def is_linux(self): return platform.system() == "Linux"
            def get_system_cores(self): return os.cpu_count() or 4
            def format_platform_string(self): return platform.platform()
            def get_temp_dir(self): return tempfile.gettempdir()
            def get_optimization_methods(self): return ["Standard"]
        return FallbackPlatformDetector, True


@dataclass
class AppConfig:
    appearance_mode: str = 'Dark'
    color_theme: str = 'green'
    overlay_opacity: int = 80
    overlay_size: str = 'Medium'
    journal_path: str = ''
    selected_commander: str = 'Auto'
    autosave_interval: str = '5 minutes'
    
    @classmethod
    def load(cls, path: str) -> 'AppConfig':
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception:
                pass
        return cls()
    
    def save(self, path: str) -> bool:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False


class ThreadSafeRouteManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._route: List[Dict[str, Any]] = []
        self._route_names: set = set()
    
    def __enter__(self):
        self._lock.acquire()
        return self._route
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
    
    def load_route(self, route_data: List[Dict[str, Any]]) -> None:
        with self._lock:
            self._route = route_data.copy()
            self._route_names = {item.get('name', '') for item in route_data}
    
    def get_route(self) -> List[Dict[str, Any]]:
        with self._lock:
            return self._route.copy()
    
    def update_system_status(self, system_name: str, status: str) -> bool:
        with self._lock:
            for item in self._route:
                if item.get('name') == system_name:
                    if item.get('status') != status:
                        item['status'] = status
                        return True
                    return False
            return False
    
    def contains_system(self, system_name: str) -> bool:
        with self._lock:
            return system_name in self._route_names
    
    def clear(self) -> None:
        with self._lock:
            self._route.clear()
            self._route_names.clear()


def get_app_data_path():
    try:
        home = os.path.expanduser("~")
        documents = os.path.join(home, "Documents")
        if not os.path.exists(documents):
            documents = home
        return os.path.join(documents, "EDMRN_Route_Data")
    except Exception:
        return os.path.abspath("EDMRN_Route_Data")


APP_DATA_DIR = get_app_data_path()
os.makedirs(APP_DATA_DIR, exist_ok=True)

SETTINGS_FILE = os.path.join(APP_DATA_DIR, 'settings.json')
ROUTE_STATUS_FILE = os.path.join(APP_DATA_DIR, 'route_status.json')
LAST_CSV_FILE = os.path.join(APP_DATA_DIR, 'last_output.txt')
BACKUP_FOLDER = os.path.join(APP_DATA_DIR, 'backups')
os.makedirs(BACKUP_FOLDER, exist_ok=True)

SYSTEM_NAME_COLUMN = 'System Name'
X_COORD_COLUMN = 'X'
Y_COORD_COLUMN = 'Y'
Z_COORD_COLUMN = 'Z'
DEFAULT_SHIP_JUMP_RANGE_LY = 70.0

COLOR_VISITED = '#4CAF50'
COLOR_SKIPPED = '#E53935'
COLOR_DEFAULT_TEXT = ('#DCE4EE', '#212121')
COLOR_VALID = '#4CAF50'
COLOR_MISSING = '#E53935'
COLOR_UNKNOWN = '#757575'

STATUS_VISITED = 'visited'
STATUS_SKIPPED = 'skipped'
STATUS_UNVISITED = 'unvisited'

APP_NAME_SHORT = "EDMRN"
APP_NAME_FULL = "ED Multi Route Navigation"
CURRENT_VERSION = "2.6.1"

GITHUB_LINK = "https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer"
DISCORD_LINK = "https://discord.gg/DWvCEXH7ae"
DONATION_LINK_KOFI = "https://ko-fi.com/ninurtakalhu"
DONATION_LINK_PATREON = "https://www.patreon.com/c/NinurtaKalhu"

GITHUB_OWNER = "NinurtaKalhu"
GITHUB_REPO = "Elite-Dangerous-Multi-Route-Optimizer"


def atomic_write_json(path: str, data: Any) -> bool:
    try:
        temp_dir = os.path.dirname(path) or '.'
        os.makedirs(temp_dir, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=temp_dir,
            prefix='.tmp_',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as tmp:
            json.dump(data, tmp, indent=4, ensure_ascii=False)
            tmp_path = tmp.name
        
        if os.name == 'nt':
            try:
                os.replace(tmp_path, path)
            except (PermissionError, OSError):
                shutil.move(tmp_path, path)
        else:
            os.replace(tmp_path, path)
        
        return True
        
    except Exception:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        return False


def calculate_3d_distance_matrix_chunked(coords: np.ndarray, chunk_size: int = 500) -> np.ndarray:
    n = len(coords)
    dist = np.zeros((n, n), dtype=np.float32)
    np.fill_diagonal(dist, 0.0)

    print("Calculating distance matrix... (this may take a few seconds)")
    
    for i in tqdm(range(0, n, chunk_size), desc="Distance matrix", unit="chunk", leave=False):
        end_i = min(i + chunk_size, n)
        chunk_i = coords[i:end_i]

        for j in range(i, n, chunk_size):
            end_j = min(j + chunk_size, n)
            chunk_j = coords[j:end_j]

            diff = chunk_i[:, np.newaxis, :] - chunk_j[np.newaxis, :, :]
            block_dist = np.sqrt(np.sum(diff ** 2, axis=2))

            dist[i:end_i, j:end_j] = block_dist
            if i != j:
                dist[j:end_j, i:end_i] = block_dist.T

    return dist
    

def calculate_jumps(distances, jump_range):

    if not distances:
        return 0

    distances_array = np.array(distances, dtype=float)
    jumps_per_segment = np.ceil(distances_array / jump_range)
    total_jumps = int(np.sum(jumps_per_segment))
    
    return total_jumps

def load_route_status() -> List[Dict[str, Any]]:

    if os.path.exists(ROUTE_STATUS_FILE):
        try:
            with open(ROUTE_STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return []

def save_route_status(route_list: List[Dict[str, Any]]) -> bool:

    return atomic_write_json(ROUTE_STATUS_FILE, route_list)

def save_last_output_path(path: str) -> bool:

    try:
        with open(LAST_CSV_FILE, 'w', encoding='utf-8') as f:
            f.write(path)
        return True
    except Exception:
        return False

def load_last_output_path() -> Optional[str]:

    if os.path.exists(LAST_CSV_FILE):
        try:
            with open(LAST_CSV_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            pass
    return None


def check_for_updates(current_version, owner, repo):
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        latest_release = response.json()
        latest_version = latest_release.get('tag_name', '0.0.0').lstrip('v')

        version_pattern = re.compile(r'[^0-9\.]')
        latest_version_clean = version_pattern.sub('', latest_version).strip('.')

        try:
            current_parts = [int(x) for x in current_version.split('.')]
            latest_parts = [int(x) for x in latest_version_clean.split('.')]
        except ValueError:
            return False, None, None

        is_update_available = latest_parts > current_parts

        if is_update_available:
            download_url = latest_release.get('html_url')
            return True, latest_version, download_url
        else:
            return False, latest_version, None

    except requests.exceptions.RequestException:
        return False, None, None
    except Exception:
        return False, None, None


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class JournalMonitor(threading.Thread):
    def __init__(self, callback, log_func, manual_journal_path=None, selected_commander=None):
        super().__init__(daemon=True)
        self.callback = callback
        self.log = log_func
        self._stop_event = threading.Event()
        self.last_tell = 0
        self.current_journal_file = None
        self.journal_path = manual_journal_path if manual_journal_path else self._find_journal_dir()
        self.selected_commander = selected_commander
        self.monitor_interval = 2
        self.max_retries = 3
        self._file_lock = threading.Lock()

    def _find_journal_dir(self):
        system = platform.system()
        
        if system == "Windows":
            path = os.path.join(os.path.expanduser('~'), 
                               'Saved Games', 
                               'Frontier Developments', 
                               'Elite Dangerous')
        elif system == "Darwin":
            path = os.path.join(os.path.expanduser('~'),
                               'Library',
                               'Application Support',
                               'Frontier Developments',
                               'Elite Dangerous')
        else:
            path = os.path.join(os.path.expanduser('~'),
                               '.local',
                               'share',
                               'Frontier Developments',
                               'Elite Dangerous')
        
        if os.path.exists(path):
            return path
        else:
            self.log(f"WARNING: Default journal path not found: {path}")
            return None

    def _get_latest_journal_file(self):
        if not self.journal_path:
            return None
        
        try:
            if self.selected_commander and self.selected_commander != "Auto":
                pattern = os.path.join(self.journal_path, f'Journal.*{self.selected_commander}*.log')
            else:
                pattern = os.path.join(self.journal_path, 'Journal.*.log')
                
            list_of_files = glob.glob(pattern)
            if not list_of_files:
                return None
            return max(list_of_files, key=os.path.getmtime)
        except Exception as e:
            self.log(f"ERROR reading journal directory {self.journal_path}: {e}")
            return None

    def _process_line(self, line):
        try:
            if '"event":"FSDJump"' in line:
                data = json.loads(line)
                system_name = data.get('StarSystem')
                if system_name:
                    self.callback(system_name)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            self.log(f"Journal Line Processing Error: {e}")

    def _tail_file(self, filename):
        if self.current_journal_file != filename:
            self.current_journal_file = filename
            self.last_tell = 0
            self.log(f"New Journal File: {os.path.basename(filename)}. Starting from end.")
            
            with open(filename, 'r', encoding='utf-8') as f:
                f.seek(0, 2)
                self.last_tell = f.tell()

        retry_count = 0
        while not self._stop_event.is_set() and retry_count < self.max_retries:
            try:
                with self._file_lock:
                    current_size = os.path.getsize(filename)
                    
                    if current_size < self.last_tell:
                        self.log("Journal file size reset. Restarting tail.")
                        self.last_tell = 0
                        continue

                    if current_size > self.last_tell:
                        with open(filename, 'r', encoding='utf-8') as f:
                            f.seek(self.last_tell)
                            new_lines = f.readlines()
                            for line in new_lines:
                                self._process_line(line)
                            self.last_tell = f.tell()
                        retry_count = 0
                        time.sleep(0.1)

            except FileNotFoundError:
                self.log("Journal file not found during tailing. Re-checking latest file.")
                break
            except PermissionError:
                self.log("Permission denied reading journal file.")
                retry_count += 1
                time.sleep(1)
            except Exception as e:
                retry_count += 1
                self.log(f"Journal File Reading Error (attempt {retry_count}): {e}")
                time.sleep(1)
                
        self.current_journal_file = None
            
    def run(self):
        self.log("Journal Monitor STARTED - Auto-tracking active")
        
        while not self._stop_event.is_set():
            try:
                latest_file = self._get_latest_journal_file()
                
                if latest_file and os.path.exists(latest_file):
                    self._tail_file(latest_file)
                else:
                    if not self.journal_path:
                        self.log("Journal path not configured. Auto-tracking disabled.")
                    else:
                        self.log("No journal file found. Waiting...")
                    time.sleep(5)
                    
            except Exception as e:
                self.log(f"Journal monitor error: {e}")
                time.sleep(5)

    def stop(self):
        self._stop_event.set()


class BackupSelectionWindow(ctk.CTkToplevel):
    def __init__(self, master, backup_files, load_callback):
        super().__init__(master)
        self.title("Select Backup File")
        self.load_callback = load_callback
        self.geometry("600x400")
        self.resizable(True, True)
        
        try:
            master.update_idletasks()
            x = master.winfo_x() + (master.winfo_width() // 2) - (600 // 2)
            y = master.winfo_y() + (master.winfo_height() // 2) - (400 // 2)
            self.geometry(f'+{x}+{y}')
        except Exception:
            pass
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self, text="Select Backup File to Load", 
                    font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10))
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.selected_file = tk.StringVar()
        
        backup_files.sort(key=os.path.getmtime, reverse=True)
        
        for i, file_path in enumerate(backup_files):
            file_name = os.path.basename(file_path)
            file_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
            file_size = f"{os.path.getsize(file_path) / 1024:.1f} KB"
            
            has_status = False
            try:
                df = pd.read_csv(file_path, nrows=1)
                has_status = 'Status' in df.columns
            except Exception:
                pass
            
            status_info = "✓ Visit status saved" if has_status else "⚠ Old format"
            
            frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=5)
            frame.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            frame.grid_columnconfigure(0, weight=1)
            
            radio = ctk.CTkRadioButton(frame, text="", variable=self.selected_file, value=file_path,
                                     width=20, height=20)
            radio.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            info_frame = ctk.CTkFrame(frame, fg_color="transparent")
            info_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            info_frame.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(info_frame, text=file_name, font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(info_frame, text=f"Modified: {file_time} | Size: {file_size}", 
                        font=ctk.CTkFont(size=11), text_color=("gray50", "gray70")).grid(row=1, column=0, sticky="w")
            ctk.CTkLabel(info_frame, text=status_info, 
                        font=ctk.CTkFont(size=10), 
                        text_color=("#4CAF50" if has_status else "#FF9800")).grid(row=2, column=0, sticky="w")
        
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        manual_btn = ctk.CTkButton(button_frame, text="Manual Select", 
                                  command=self.manual_select, height=32)
        manual_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", 
                                  command=self.destroy, height=32,
                                  fg_color="#757575", hover_color="#616161")
        cancel_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        load_btn = ctk.CTkButton(button_frame, text="Load Selected", 
                                command=self.load_selected, height=32,
                                fg_color="#4CAF50", hover_color="#45a049")
        load_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        if backup_files:
            self.selected_file.set(backup_files[0])
        
        self.grab_set()
        self.transient(master)
    
    def manual_select(self):
        filename = filedialog.askopenfilename(
            title="Select Backup CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=APP_DATA_DIR
        )
        if filename:
            self.load_callback(filename)
            self.destroy()
    
    def load_selected(self):
        if self.selected_file.get():
            self.load_callback(self.selected_file.get())
            self.destroy()
        else:
            tk.messagebox.showwarning("Warning", "Please select a backup file.")


class ManualWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"{APP_NAME_SHORT} - User Manual")
        try:
            self.iconbitmap(resource_path('explorer_icon.ico'))
        except Exception:
            pass
        self.geometry("700x550")
        self.resizable(False, False)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        try:
            master.update_idletasks()
            x = master.winfo_x() + (master.winfo_width() // 2) - (700 // 2)
            y = master.winfo_y() + (master.winfo_height() // 2) - (550 // 2)
            self.geometry(f'+{x}+{y}')
        except Exception:
            pass
            
        ctk.CTkLabel(self, text="ED Multi Route Navigation (EDMRN) - User Manual", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.manual_textbox = ctk.CTkTextbox(self, width=650, height=450)
        self.manual_textbox.pack(padx=20, pady=10, fill="both", expand=True)
        
        self._insert_manual_content()
        
        self.grab_set()

    def _insert_manual_content(self):
        manual_text = """
        =========================================================
        ED Multi Route Navigation (EDMRN) v2.6.1 - User Manual
        =========================================================

        EDMRN optimizes your multi-system exploration/data collection routes in Elite Dangerous for shortest distance (TSP) and provides in-game tracking.

        ---------------------------------------------------------
        TAB 1: ROUTE OPTIMIZATION
        ---------------------------------------------------------
        1. Route Data File (CSV):
           - Source: Exported system list from Elite Dangerous (e.g., EDDiscovery, EDMC, or Spansh).
           - REQUIRED COLUMNS: 'System Name', 'X', 'Y', and 'Z' coordinate columns must be present.

        2. Ship Jump Range (LY):
           - Enter your current ship's FSD jump range.

        3. Starting System (Optional):
           - Enter a system name if you want to fix the starting point of the route.

        4. Select Output CSV Columns:
           - Select the columns you want to appear in the optimized output CSV file.

        5. Optimize Route and Start Tracking:
           - Starts the optimization process.

        ---------------------------------------------------------
        TAB 2: ROUTE TRACKING
        ---------------------------------------------------------
        AUTO-TRACKING:
           - The program monitors your Elite Dangerous journal files in the background.
           - When you perform an FSD jump, it automatically updates the system status.

        MANUAL TRACKING:
           - Click on system names in the list to manually update their status.

        3D MINI MAP:
           - Displays your route in 3D space.

        IN-GAME OVERLAY:
           - Transparent overlay shows current system, bodies to scan, and next system while playing.
           - Press Ctrl+O to toggle overlay visibility in game.
           - Drag the title bar to move the overlay anywhere on screen.
           - Always on top of your game window.

        ACTION BUTTONS:
           - Copy Next System: Copies the next system to clipboard.
           - Open Data Folder: Opens the data folder.
           - Open Route in Excel: Opens the CSV file.
           - Load from Backup: Load previous optimized routes from backup files.
           - Start Overlay: Launch in-game overlay (Settings tab).

        ---------------------------------------------------------
        TAB 3: SETTINGS
        ---------------------------------------------------------
        - In-Game Overlay: Start/stop the overlay and check status
        - Journal Settings: Configure Elite Dangerous journal monitoring
        - Multi-CMDR Select: Switch between different commanders automatically
        - Appearance: Change theme and color scheme
        - Auto-save: Configure automatic saving of route progress
        - Advanced: Additional application settings
        """
        self.manual_textbox.insert("end", manual_text)
        self.manual_textbox.configure(state="disabled", font=ctk.CTkFont(family="Consolas", size=11))


class AboutWindow(ctk.CTkToplevel):
    def __init__(self, master, open_link_callback, show_manual_callback):
        super().__init__(master)
        self.title(f"{APP_NAME_FULL} ({APP_NAME_SHORT})")
        self.open_link = open_link_callback
        self.show_manual = show_manual_callback
        
        try:
            self.iconbitmap(resource_path('explorer_icon.ico'))
        except Exception:
            pass
        
        window_width = 450
        window_height = 500
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(False, False)
        
        try:
            master.update_idletasks()
            x = master.winfo_x() + (master.winfo_width() // 2) - (window_width // 2)
            y = master.winfo_y() + (master.winfo_height() // 2) - (window_height // 2)
            self.geometry(f'+{x}+{y}')
        except Exception:
            pass
            
        self.grid_columnconfigure(0, weight=1)
        
        def open_url(url):
            self.open_link(url)

        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(20, 10), sticky="ew")
        logo_frame.columnconfigure(0, weight=1)

        try:
            logo_path = resource_path('explorer_icon.png')
            if os.path.exists(logo_path):
                original_image = Image.open(logo_path)
                resized_image = original_image.resize((60, 60), Image.LANCZOS)
                app_logo = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(60, 60))
                logo_label = ctk.CTkLabel(logo_frame, image=app_logo, text="")
                logo_label.grid(row=0, column=0, pady=5)
                logo_label.image = app_logo
        except Exception:
            pass

        ctk.CTkLabel(self, text=f"{APP_NAME_FULL} ({APP_NAME_SHORT})", font=ctk.CTkFont(size=16, weight="bold")).grid(row=1, column=0, pady=(0, 10))
        
        app_frame = ctk.CTkFrame(self, fg_color="transparent")
        app_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        app_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(app_frame, text="Software Version:", anchor="w").grid(row=0, column=0, sticky="w", pady=2)
        ctk.CTkLabel(app_frame, text=CURRENT_VERSION, anchor="e").grid(row=0, column=1, sticky="e", pady=2)
        
        ctk.CTkLabel(app_frame, text="Developer:", anchor="w").grid(row=1, column=0, sticky="w", pady=2)
        ctk.CTkLabel(app_frame, text="Ninurta Kalhu", anchor="e").grid(row=1, column=1, sticky="e", pady=2)

        ctk.CTkLabel(app_frame, text="Main Purpose:", anchor="w").grid(row=2, column=0, sticky="w", pady=2)
        ctk.CTkLabel(app_frame, text="Multi-Waypoint Optimization and Route Tracking", anchor="e").grid(row=2, column=1, sticky="e", pady=2)

        ctk.CTkLabel(app_frame, text="Discord & Mail", anchor="w").grid(row=3, column=0, sticky="w", pady=2)
        ctk.CTkLabel(app_frame, text="Ninurta Kalhu [ninurtakalhu@gmail.com]", anchor="e").grid(row=3, column=1, sticky="e", pady=2)

        manual_btn = ctk.CTkButton(self, text="Show User Manual", command=self.show_manual, fg_color="#1E88E5", hover_color="#1565C0")
        manual_btn.grid(row=3, column=0, padx=20, pady=(15, 10), sticky="ew")

        update_info_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        update_info_frame.grid(row=4, column=0, padx=20, pady=(5, 5), sticky="ew")
        update_info_frame.columnconfigure(0, weight=1)
        
        ctk.CTkLabel(update_info_frame, 
                     text="New Updates may be available!\nCheck Don't forget to follow Discord",
                     justify="center",
                     font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        about_link_frame = ctk.CTkFrame(self, fg_color="transparent")
        about_link_frame.grid(row=5, column=0, padx=20, pady=(15, 10), sticky="ew")
        about_link_frame.columnconfigure((0, 1, 2), weight=1)
        
        github_btn = ctk.CTkButton(about_link_frame, text="GitHub", command=lambda: open_url(GITHUB_LINK))
        github_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        discord_btn = ctk.CTkButton(about_link_frame, text="Discord", command=lambda: open_url(DISCORD_LINK))
        discord_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        donation_btn = ctk.CTkButton(about_link_frame, text="Donate", command=lambda: open_url(DONATION_LINK_KOFI), fg_color="#E91E63", hover_color="#C2185B")
        donation_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self, text="Ninurta Kalhu (S.C.) Copyright (C) 2025 | All Rights Reserved.", font=ctk.CTkFont(size=10)).grid(row=6, column=0, pady=(5, 15))
        
        self.grab_set()


class MiniMapFrameFallback(ctk.CTkFrame):
    def __init__(self, master, on_system_selected=None, **kwargs):
        super().__init__(master, **kwargs)
        ctk.CTkLabel(self, text="ERROR: 3D Map Module Not Found.", 
                    font=("Arial", 12), text_color="orange").pack(padx=20, pady=40)
    
    def plot_route(self, *args): 
        pass
    
    def highlight_system(self, *args): 
        pass


class RouteOptimizerApp:
    def __init__(self, master):
        self.master = master
        master.title(f"{APP_NAME_FULL} ({APP_NAME_SHORT}) - CMDR Terminal v{CURRENT_VERSION}")
        
        master.geometry("1100x800")
        master.minsize(1000, 700)

        try:
            self.master.iconbitmap(resource_path('explorer_icon.ico'))
        except Exception:
            pass

        start_overlay, stop_overlay, get_overlay_data_from_app, overlay_available = load_external_module("overlay")
        self.start_overlay_func = start_overlay
        self.stop_overlay_func = stop_overlay
        self.get_overlay_data_from_app_func = get_overlay_data_from_app
        self.OVERLAY_AVAILABLE = overlay_available
        
        AutoSaveManagerClass, _ = load_external_module("autosave")
        PlatformDetectorClass, _ = load_external_module("platform")
        
        try:
            from edmrn_3d_minimap import MiniMapFrame
            self.MiniMapFrameClass = MiniMapFrame
        except ImportError:
            self.MiniMapFrameClass = MiniMapFrameFallback

        self.config = AppConfig.load(SETTINGS_FILE)
        
        self.csv_file_path = ctk.StringVar()
        self.jump_range = ctk.StringVar(value=str(DEFAULT_SHIP_JUMP_RANGE_LY))
        self.starting_system = ctk.StringVar()
        self.cmdr_name = ctk.StringVar(value="[CMDR Name: Loading...]")
        self.cmdr_role = ctk.StringVar(value="(Role: Explorer/Astrobiologist)")
        self.cmdr_cash = ctk.StringVar(value="N/A Cr")
        self.theme_mode = ctk.StringVar(value=self.config.appearance_mode)
        self.theme_color = ctk.StringVar(value=self.config.color_theme)
        self.journal_path_var = ctk.StringVar(value=self.config.journal_path)
        self.selected_commander = ctk.StringVar(value=self.config.selected_commander)
        
        self.autosave_interval_var = tk.StringVar(value=self.config.autosave_interval)
        
        self.platform_detector = PlatformDetectorClass()
        
        self.route_manager = ThreadSafeRouteManager()
        
        self.system_labels = {}
        self.progress_label = None
        self.map_frame = None
        
        self.overlay_enabled = False
        self.overlay_instance = None
        
        self.journal_monitor = None
        
        self.total_distance_ly = 0.0
        self.traveled_distance_ly = 0.0
        self.average_jump_range = DEFAULT_SHIP_JUMP_RANGE_LY
        
        self.column_vars = {}
        self.available_columns = []
        self.column_checkboxes = {}
        self.column_frame = None
        self.optional_window = None       
        self._optimization_running = False

        self._optimization_lock = threading.Lock()
        self._optimization_in_progress = False
        self._optimization_thread = None 
        self._optimization_executor = None
        
        try:
            logo_path = resource_path('explorer_icon.png')
            original_image = Image.open(logo_path)
            resized_image = original_image.resize((40, 40), Image.LANCZOS)
            self.app_logo = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(40, 40))
        except Exception as e:
            self.app_logo = None

        self.output_text = None
        
        self.create_widgets()
        
        self.autosave_manager = AutoSaveManagerClass(
            save_callback=self._perform_autosave,
            log_callback=self.log
        )
        
        self.autodetect_csv(initial_run=True)

        route_data = load_route_status()
        self.route_manager.load_route(route_data)
        
        if route_data:
            self.master.after(0, self.create_route_tracker_tab_content)
            self._start_journal_monitor()
            
        threading.Thread(target=self._get_latest_cmdr_data, daemon=True).start()
        threading.Thread(target=self._check_and_notify_update, daemon=True).start()
        
        self._initialize_managers()
        
        atexit.register(self._cleanup)
    
    def check_csv_columns(self, file_path):
        try:
            df = pd.read_csv(file_path, nrows=1)
            
            columns_status = {
                'System Name': SYSTEM_NAME_COLUMN in df.columns,
                'Body Name': any(col in df.columns for col in ['Body Name', 'Name', 'BodyName', 'body_name']),
                'X Coord': X_COORD_COLUMN in df.columns,
                'Y Coord': Y_COORD_COLUMN in df.columns,
                'Z Coord': Z_COORD_COLUMN in df.columns
            }
            
            return columns_status, df.columns.tolist()
        except Exception as e:
            self.log(f"CSV column check error: {e}")
            return None, []
    
    def update_column_status_display(self):
        for widget in self.columns_container.winfo_children():
            widget.destroy()
        
        csv_path = self.csv_file_path.get()
        
        if not csv_path or not os.path.exists(csv_path):
            ctk.CTkLabel(
                self.columns_container, 
                text="Select a CSV file to check column status",
                text_color=("gray50", "gray70"),
                font=ctk.CTkFont(size=11)
            ).pack(expand=True)
            return
        
        try:
            columns_status, all_columns = self.check_csv_columns(csv_path)
            
            if not columns_status:
                ctk.CTkLabel(
                    self.columns_container, 
                    text="❌ Unable to read CSV file",
                    text_color=COLOR_MISSING,
                    font=ctk.CTkFont(size=11, weight="bold")
                ).pack(expand=True)
                return
            
            self.current_csv_columns = all_columns
            
            grid_frame = ctk.CTkFrame(self.columns_container, fg_color="transparent")
            grid_frame.pack(fill="both", expand=True)
            
            for i in range(5):
                grid_frame.columnconfigure(i, weight=1)
            
            required_columns = [
                ('System Name', 'System Name (Required)'),
                ('Body Name', 'Body Name (Required)'),
                ('X Coord', 'X Coordinate (Required)'),
                ('Y Coord', 'Y Coordinate (Required)'),
                ('Z Coord', 'Z Coordinate (Required)')
            ]
            
            for idx, (col_key, display_name) in enumerate(required_columns):
                frame = ctk.CTkFrame(grid_frame, fg_color=("gray90", "gray25"), height=32)
                frame.grid(row=0, column=idx, padx=2, pady=5, sticky="ew")
                frame.grid_propagate(False)
                frame.grid_columnconfigure(1, weight=1)
                
                is_available = columns_status.get(col_key, False)
                
                if col_key == 'Body Name':
                    status_color = COLOR_VALID if is_available else COLOR_MISSING
                    status_icon = "✓" if is_available else "✗"
                    status_text = "Found" if is_available else "MISSING"
                else:
                    status_color = COLOR_VALID if is_available else COLOR_MISSING
                    status_icon = "✓" if is_available else "✗"
                    status_text = "Found" if is_available else "MISSING"
                
                col_label = ctk.CTkLabel(
                    frame,
                    text=display_name,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    anchor="w"
                )
                col_label.grid(row=0, column=0, padx=(6, 3), pady=5, sticky="w")
                
                status_label = ctk.CTkLabel(
                    frame,
                    text=status_text,
                    text_color=status_color,
                    font=ctk.CTkFont(size=9),
                    anchor="e"
                )
                status_label.grid(row=0, column=1, padx=3, pady=5, sticky="ew")
                
                icon_label = ctk.CTkLabel(
                    frame,
                    text=status_icon,
                    text_color=status_color,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="e"
                )
                icon_label.grid(row=0, column=2, padx=(0, 6), pady=5, sticky="e")
                
                self.column_indicators[col_key] = {
                    'frame': frame,
                    'status_label': status_label,
                    'icon_label': icon_label,
                    'available': is_available
                }
            
            info_text = f"Total columns in CSV: {len(all_columns)}"
            if not all(columns_status[col] for col in ['System Name', 'X Coord', 'Y Coord', 'Z Coord']):
                info_text += " - ❌ Missing required columns!"
            
            info_label = ctk.CTkLabel(
                grid_frame,
                text=info_text,
                text_color="#2196F3",
                font=ctk.CTkFont(size=9),
                anchor="w"
            )
            info_label.grid(row=1, column=0, columnspan=5, padx=5, pady=(8, 0), sticky="w")
            
            all_required = all(columns_status[col] for col in ['System Name', 'Body Name', 'X Coord', 'Y Coord', 'Z Coord'])
            if all_required:
                self.run_button.configure(state='normal', text="5. Optimize Route and Start Tracking")
            else:
                self.run_button.configure(state='disabled', text="❌ Missing required columns")
                
        except Exception as e:
            self.log(f"Column status update error: {e}")
            ctk.CTkLabel(
                self.columns_container, 
                text=f"Error checking CSV: {str(e)[:50]}",
                text_color=COLOR_MISSING,
                font=ctk.CTkFont(size=11)
            ).pack(expand=True)
    
    def on_csv_path_changed(self, *args):
        self.master.after(100, self.update_column_status_display)
        self.master.after(200, self.update_column_selection)
    
    def _initialize_managers(self):
        interval = self.config.autosave_interval
        self._apply_autosave_interval(interval)
        self.update_autosave_status()
        self.log("Managers initialized successfully")
    
    def _cleanup(self):
        try:
            self.log("Shutting down EDMRN...")
            
            self._optimization_in_progress = False
            
            if hasattr(self, '_optimization_executor') and self._optimization_executor:
                try:
                    self._optimization_executor.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass
                self._optimization_executor = None
            
            if hasattr(self, '_optimization_thread') and self._optimization_thread:
                try:
                    if self._optimization_thread.is_alive():
                        pass
                    self._optimization_thread = None
                except Exception:
                    pass
            
            try:
                if self.overlay_enabled and self.stop_overlay_func:
                    self.stop_overlay_func()
            except Exception:
                pass
            
            try:
                if self.journal_monitor:
                    self.journal_monitor.stop()
            except Exception:
                pass
            
            try:
                if self.autosave_manager:
                    self.autosave_manager.stop()
            except Exception:
                pass
            
            try:
                if self.master and self.master.winfo_exists():
                    self.cleanup_all()
            except Exception:
                pass
            
            time.sleep(0.05)
            
        except Exception as e:
            try:
                print(f"Cleanup error (non-critical): {e}")
            except Exception:
                pass
    
    def _perform_autosave(self):
        try:
            route_data = self.route_manager.get_route()
            save_route_status(route_data)
            self.log("Route status auto-saved")
        except Exception as e:
            self.log(f"Auto-save failed: {e}")
    
    def update_overlay_opacity(self, value):
        opacity_value = int(value)
        alpha_value = opacity_value / 100.0
        
        if hasattr(self, 'opacity_label'):
            self.opacity_label.configure(text=f"{opacity_value}%")
        
        self.config.overlay_opacity = opacity_value
        self.config.save(SETTINGS_FILE)

        if self.overlay_enabled and self.overlay_instance:
            try:
                self.overlay_instance.set_opacity(alpha_value)
                self.log(f"Overlay Opacity set to {opacity_value}%")
            except Exception as e:
                self.log(f"Could not update overlay opacity: {e}")
    
    def update_overlay_size(self, size):
        self.config.overlay_size = size
        self.config.save(SETTINGS_FILE)
        
        if self.platform_detector.is_macos() and size != "Medium":
            self.log("Overlay size may be limited on macOS")
        elif self.platform_detector.is_linux() and size == "Large":
            self.log("Large overlay may affect performance on Linux")
        
        self.log(f"Overlay size set to: {size}")
    
    def toggle_overlay(self):
        if not self.OVERLAY_AVAILABLE:
            tk.messagebox.showwarning("Overlay Not Available", 
                                 "Overlay module could not be loaded.")
            return
        
        if not self.overlay_enabled:
            opacity = self.config.overlay_opacity / 100.0
            self.overlay_instance = self.start_overlay_func(self.get_overlay_data, opacity=opacity)
            self.overlay_enabled = True
            self.overlay_btn.configure(text="Stop Overlay")
            self.log("Cross-Platform Overlay started!")
            self.log("Make sure Elite Dangerous is in BORDERLESS WINDOW mode")
            
            tk.messagebox.showinfo("Overlay Started", 
                              "Cross-Platform Overlay Started!\n\n"
                              "IMPORTANT:\n"
                              "• Set Elite Dangerous to BORDERLESS WINDOW mode\n"
                              "• Drag the title bar to move overlay\n"
                              "• Toggle visibility from EDMRN Settings\n\n"
                              "Works on Windows, Linux, and macOS!")
        else:
            self.stop_overlay_func()
            self.overlay_enabled = False
            self.overlay_instance = None
            self.overlay_btn.configure(text="Start Overlay")
            self.log("Overlay stopped")
    
    def get_overlay_data(self):
        if self.get_overlay_data_from_app_func:
            return self.get_overlay_data_from_app_func(self)
        return None
    
    def _apply_autosave_interval(self, interval):
        self.config.autosave_interval = interval
        self.config.save(SETTINGS_FILE)
        
        if interval == "1 minute":
            minutes = 1
        elif interval == "5 minutes":
            minutes = 5
        elif interval == "10 minutes":
            minutes = 10
        else:
            minutes = 0
        
        if self.autosave_manager:
            self.autosave_manager.set_interval(minutes)
        
        self.log(f"Auto-save interval: {interval}")
    
    def update_autosave_interval(self, interval):
        self._apply_autosave_interval(interval)
        self.update_autosave_status()
    
    def start_autosave(self):
        if self.autosave_manager:
            if self.autosave_manager.start():
                self.update_autosave_status()
                tk.messagebox.showinfo("Auto-save", "Auto-save scheduler started successfully!")
            else:
                tk.messagebox.showwarning("Auto-save", "Auto-save scheduler is already running.")
    
    def stop_autosave(self):
        if self.autosave_manager:
            if self.autosave_manager.stop():
                self.update_autosave_status()
                tk.messagebox.showinfo("Auto-save", "Auto-save scheduler stopped.")
            else:
                tk.messagebox.showwarning("Auto-save", "Auto-save scheduler is not running.")
    
    def manual_save(self):
        if self.autosave_manager:
            if self.autosave_manager.save_now():
                self.update_autosave_status()
            else:
                tk.messagebox.showerror("Save Error", "Manual save failed!")
    
    def update_autosave_status(self):
        if self.autosave_manager:
            status = self.autosave_manager.get_status()
            if status['running']:
                next_save = status['next_save_in']
                if next_save:
                    mins = int(next_save / 60)
                    secs = int(next_save % 60)
                    self.autosave_status.configure(text=f"Running ({mins}m {secs}s)", 
                                                  text_color="#4CAF50")
                    self.autosave_start_btn.configure(text="Stop", 
                                                     command=self.stop_autosave,
                                                     fg_color="#f44336",
                                                     hover_color="#d32f2f")
                else:
                    self.autosave_status.configure(text="Running", text_color="#4CAF50")
            else:
                self.autosave_status.configure(text="Stopped", text_color="#757575")
                self.autosave_start_btn.configure(text="Start", 
                                                 command=self.start_autosave,
                                                 fg_color="#4CAF50",
                                                 hover_color="#45a049")
    
    def change_appearance_mode_event(self, new_mode):
        ctk.set_appearance_mode(new_mode)
        self.config.appearance_mode = new_mode
        self.config.save(SETTINGS_FILE)
        if self.map_frame:
            self.map_frame.plot_route(self.route_manager.get_route())

    def change_color_theme_event(self, new_theme):
        ctk.set_default_color_theme(new_theme)
        self.config.color_theme = new_theme
        self.config.save(SETTINGS_FILE)
        self.theme_color.set(new_theme)
        self.log(f"Theme changed to: {new_theme}")
    
    def _check_and_notify_update(self):
        def run_check():
            update_available, latest_version, download_url = check_for_updates(
                CURRENT_VERSION, GITHUB_OWNER, GITHUB_REPO
            )

            if update_available:
                self.master.after(0, lambda: self._show_update_dialog(latest_version, download_url))

        threading.Thread(target=run_check, daemon=True).start()

    def _show_update_dialog(self, latest_version, download_url):
        title = "New Update Available!"
        message = (
            f"A new version of {APP_NAME_SHORT} (v{latest_version}) has been released.\n"
            f"Current Version: v{CURRENT_VERSION}\n\n"
            "Press 'Yes' to download the update now."
        )
        
        response = tk.messagebox.askyesno(
            title, 
            message, 
            icon='info', 
            detail="Would you like to be redirected to the GitHub Release page?"
        )
        
        if response and download_url:
            webbrowser.open(download_url)
    
    def open_link(self, url):
        try:
            webbrowser.open(url)
        except Exception as e:
            self.log(f"ERROR: Failed to open link {url}: {e}")

    def show_manual(self):
        if hasattr(self, 'manual_window') and self.manual_window.winfo_exists():
            self.manual_window.focus()
        else:
            self.manual_window = ManualWindow(self.master)
            try:
                self.manual_window.iconbitmap(resource_path('explorer_icon.ico'))
            except Exception:
                pass

    def show_about_info(self):
        if hasattr(self, 'about_window') and self.about_window.winfo_exists():
            self.about_window.focus()
        else:
            self.about_window = AboutWindow(self.master, self.open_link, self.show_manual)
            try:
                self.about_window.iconbitmap(resource_path('explorer_icon.ico'))
            except Exception:
                pass
    
    def format_cash(self, amount):
        try:
            cash_int = int(amount)
            return f"{cash_int:,}".replace(",", ".") + " Cr"
        except Exception:
            return f"{amount} Cr"
    
    def _get_auto_journal_path(self):
        temp_monitor = JournalMonitor(None, lambda x: None)
        return temp_monitor._find_journal_dir()

    def _browse_journal_path(self):
        folder = tk.filedialog.askdirectory(title="Select Elite Dangerous Journal Folder")
        if folder:
            self.journal_path_var.set(folder)
            self.config.journal_path = folder
            self.config.save(SETTINGS_FILE)

    def _test_journal_path(self):
        test_path = self.journal_path_var.get().strip()
        if not test_path:
            test_path = self._get_auto_journal_path()
        
        if not test_path:
            tk.messagebox.showerror("Error", "No journal path specified and auto-detection failed.")
            return
        
        if not os.path.exists(test_path):
            tk.messagebox.showerror("Error", f"Path does not exist:\n{test_path}")
            return

        journal_files = glob.glob(os.path.join(test_path, 'Journal.*.log'))
        if journal_files:
            latest = max(journal_files, key=os.path.getmtime)
            tk.messagebox.showinfo("Success", 
                              f"Journal path is valid!\n\n"
                              f"Found {len(journal_files)} journal files\n"
                              f"Latest: {os.path.basename(latest)}")
        else:
            tk.messagebox.showwarning("Warning", 
                                 f"Path exists but no journal files found.\n\n"
                                 f"Make sure:\n"
                                 f"1. Elite Dangerous is running\n"
                                 f"2. Journal logging is enabled\n"
                                 f"3. You're in the correct folder")

    def _apply_journal_settings(self):
        manual_path = self.journal_path_var.get().strip() or None
        
        self.config.journal_path = manual_path if manual_path else ''
        self.config.save(SETTINGS_FILE)
        
        if self.journal_monitor:
            self.journal_monitor.stop()
            self.journal_monitor = None

        self.journal_monitor = JournalMonitor(
            callback=self.handle_system_jump,
            log_func=self.log,
            manual_journal_path=manual_path,
            selected_commander=self.selected_commander.get()
        )
        self.journal_monitor.start()
        
        path_used = manual_path if manual_path else "Auto-detected path"
        self.log(f"Journal Monitor restarted with: {path_used}")
        tk.messagebox.showinfo("Success", "Journal monitor restarted with new settings!")
    
    def _start_journal_monitor(self):
        if self.journal_monitor:
            self.journal_monitor.stop()

        manual_path = self.journal_path_var.get().strip() or None
        
        self.journal_monitor = JournalMonitor(
            callback=self.handle_system_jump,
            log_func=self.log,
            manual_journal_path=manual_path,
            selected_commander=self.selected_commander.get()
        )
        self.journal_monitor.start()
        
        path_info = manual_path if manual_path else "auto-detected path"
        self.log(f"Started Journal Monitor with {path_info}")

    def handle_system_jump(self, system_name):
        self.master.after(0, lambda: self._update_system_status_from_monitor(system_name, STATUS_VISITED))

    def _get_latest_cmdr_data(self):
        cmdr_name_default = "CMDR NoName"
        cmdr_cash = 0
        
        selected_cmdr = getattr(self.config, 'selected_commander', "Auto")
        
        journal_monitor = JournalMonitor(None, self.log, selected_commander=selected_cmdr)
        latest_file = journal_monitor._get_latest_journal_file()

        if not latest_file:
            try:
                self.master.after(0, lambda: self.cmdr_name.set(f"CMDR Not Found ({cmdr_name_default})"))
                self.master.after(0, lambda: self.cmdr_cash.set("Where is the bank? (Saved Data)"))
            except RuntimeError:
                pass
            return

        self.log(f"Checking Journal file: {os.path.basename(latest_file)}")

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
                    except json.JSONDecodeError:
                        continue
                            
        except Exception as e:
            self.log(f"ERROR reading CMDR data from Journal: {e}")

        final_cmdr_name = cmdr_name_default
        final_cmdr_cash = self.format_cash(cmdr_cash)
        
        try:
            self.master.after(0, lambda: self.cmdr_name.set(final_cmdr_name))
            self.master.after(0, lambda: self.cmdr_cash.set(final_cmdr_cash))
        except RuntimeError:
            return
        
        self.log(f"CMDR Status Loaded: {final_cmdr_name}, {final_cmdr_cash}")
    
    def detect_all_commanders(self):
        commanders = set()
        journal_path = self.journal_path_var.get().strip() or self._get_auto_journal_path()
        
        if not journal_path or not os.path.exists(journal_path):
            return ["Auto"]
        
        try:
            journal_files = glob.glob(os.path.join(journal_path, 'Journal.*.log'))
            
            for file_path in journal_files:
                filename = os.path.basename(file_path)
                parts = filename.split('.')
                if len(parts) >= 3:
                    commander_name = parts[1]
                    if commander_name and commander_name not in ['beta', 'live', 'tmp']:
                        commanders.add(commander_name)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                data = json.loads(line)
                                if data.get('event') in ['Commander', 'LoadGame']:
                                    cmdr_name = data.get('Name')
                                    if cmdr_name:
                                        commanders.add(cmdr_name)
                            except Exception:
                                continue
                except Exception:
                    continue
            
            commander_list = sorted(list(commanders))
            return ["Auto"] + commander_list
            
        except Exception as e:
            self.log(f"Error detecting commanders: {e}")
            return ["Auto"]

    def get_commander_activity(self, commander_name):
        if commander_name == "Auto":
            return "Latest activity"
            
        journal_path = self.journal_path_var.get().strip() or self._get_auto_journal_path()
        if not journal_path:
            return "No journal path"
        
        try:
            pattern = os.path.join(journal_path, f'Journal.*{commander_name}*.log')
            journal_files = glob.glob(pattern)
            if journal_files:
                latest_file = max(journal_files, key=os.path.getmtime)
                file_time = time.localtime(os.path.getmtime(latest_file))
                return time.strftime('%Y-%m-%d %H:%M', file_time)
            return "No activity"
        except Exception:
            return "Error"

    def switch_commander(self, selected):
        if selected:
            self.config.selected_commander = selected
            self.config.save(SETTINGS_FILE)
            self.log(f"Switching to commander: {selected}")
            self._start_journal_monitor()
            tk.messagebox.showinfo("Success", f"Journal monitor restarted for commander: {selected}")

    def refresh_commanders_list(self):
        commanders = self.detect_all_commanders()
        if hasattr(self, 'cmdr_dropdown'):
            self.cmdr_dropdown.configure(values=commanders)
        
        if commanders:
            current = self.selected_commander.get()
            if current not in commanders:
                self.selected_commander.set(commanders[0])
        
        self.log(f"Refreshed commanders list: {len(commanders)} found")
    
    def _update_system_status_from_monitor(self, system_name, new_status):
        if not self.route_manager.contains_system(system_name):
            self.log(f"Jumped to '{system_name}' (not on current route).")
            return

        status_changed = self.route_manager.update_system_status(system_name, new_status)

        if status_changed:
            self.master.after(0, lambda: self._update_ui_after_status_change(system_name, new_status))
            
            threading.Thread(target=lambda: save_route_status(self.route_manager.get_route()), daemon=True).start()
            
            self.copy_next_system_to_clipboard()

            if self.map_frame:
                self.master.after(0, lambda: self._update_map(system_name))

            self.log(f"Auto-Detected Jump to '{system_name}'. Status updated to {new_status.upper()}.")
    
    def _update_ui_after_status_change(self, system_name, new_status):
        try:
            self.master.after(0, lambda: self.update_label_color(system_name, new_status))
            self.master.after(0, self.update_progress_info)
            self.master.after(0, self.update_route_statistics)
            
            if self.map_frame:
                self.master.after(100, lambda: self._update_map(system_name))
                
        except Exception as e:
            self.log(f"UI update error: {e}")
    
    def _update_map(self, system_name):
        if self.map_frame and self.route_manager.get_route():
            self.map_frame.plot_route(self.route_manager.get_route())
            self.map_frame.highlight_system(system_name)
    
    def _set_clipboard_text_non_disruptive(self, text):
        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            temp_root.clipboard_clear()
            temp_root.clipboard_append(text)
            temp_root.update()
            temp_root.destroy()
            return True
        except Exception:
            try:
                self.master.clipboard_clear()
                self.master.clipboard_append(text)
                return True
            except Exception:
                return False

    def get_next_unvisited_system(self) -> Optional[str]:
        with self.route_manager as route:
            for item in route:
                if item.get('status') == STATUS_UNVISITED:
                    return item.get('name')
            return None
        
    def copy_next_system_to_clipboard(self):
        next_system_name = self.get_next_unvisited_system()
        
        if next_system_name:
            if self._set_clipboard_text_non_disruptive(next_system_name):
                 self.log(f"'{next_system_name}' (Next System) copied to clipboard.")
            else:
                 tk.messagebox.showerror("Error", "Could not copy to clipboard.")
                 self.log("ERROR: Failed to copy system name to clipboard.")
        else:
            self.log("INFO: Route complete. Nothing to copy.")

    def open_output_csv(self):
        last_path = load_last_output_path()
        if not last_path or not os.path.exists(last_path):
            tk.messagebox.showerror("Error", "The optimized route file was not found. Please run optimization first.")
            self.log("ERROR: Route file not found for opening.")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(last_path)
            elif platform.system() == "Darwin":
                subprocess.call(('open', last_path))
            else:
                subprocess.call(('xdg-open', last_path))
            self.log(f"Opened CSV file: '{last_path}'")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Could not open the file automatically. Please open it manually.\nError: {e}")
            self.log(f"ERROR: Failed to open CSV file: {e}")

    def open_app_data_folder(self):
        try:
            os.makedirs(APP_DATA_DIR, exist_ok=True)
            path = APP_DATA_DIR
            
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.call(('open', path))
            else:
                subprocess.call(('xdg-open', path))
            self.log(f"Opened data folder: '{path}'")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Could not open the data folder automatically. Please navigate to:\n{APP_DATA_DIR}")
            self.log(f"ERROR: Failed to open data folder: {e}")

    def _load_backup_file(self, file_path):
        try:
            df = pd.read_csv(file_path)
            
            required_cols = ['System Name', 'X', 'Y', 'Z']
            if not all(col in df.columns for col in required_cols):
                tk.messagebox.showerror("Error", f"CSV file missing required columns: {', '.join(required_cols)}")
                return False
            
            has_status = 'Status' in df.columns
            
            route_data = []
            for _, row in df.iterrows():
                bodies_data = []
                if 'Bodies_To_Scan_List' in row:
                    bodies_str = row['Bodies_To_Scan_List']
                    if isinstance(bodies_str, str) and bodies_str.startswith('['):
                        try:
                            import ast
                            bodies_data = ast.literal_eval(bodies_str)
                        except Exception:
                            bodies_str = bodies_str.strip("[]").replace("'", "")
                            bodies_data = [body.strip() for body in bodies_str.split(",") if body.strip()]
                    elif isinstance(bodies_str, list):
                        bodies_data = bodies_str
                
                status = row['Status'] if has_status else STATUS_UNVISITED
                
                route_data.append({
                    'name': row['System Name'],
                    'status': status,
                    'coords': [float(row['X']), float(row['Y']), float(row['Z'])],
                    'bodies_to_scan': bodies_data,
                    'body_count': len(bodies_data)
                })
            
            self.route_manager.load_route(route_data)
            save_route_status(route_data)
            
            self.create_route_tracker_tab_content()
            self.log(f"Backup loaded: {os.path.basename(file_path)}")
            
            if has_status:
                visited_count = sum(1 for item in route_data if item.get('status') == STATUS_VISITED)
                skipped_count = sum(1 for item in route_data if item.get('status') == STATUS_SKIPPED)
                tk.messagebox.showinfo("Success", 
                                  f"Backup successfully loaded:\n{os.path.basename(file_path)}\n\n"
                                  f"Visit status preserved:\n"
                                  f"• Visited: {visited_count} systems\n"
                                  f"• Skipped: {skipped_count} systems")
            else:
                tk.messagebox.showinfo("Success", 
                                  f"Backup successfully loaded:\n{os.path.basename(file_path)}\n\n"
                                  f"Note: Old format - all systems marked as 'unvisited'.")
            
            self.update_route_statistics()
            return True
            
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error loading backup: {str(e)}")
            self.log(f"Backup loading error: {e}")
            return False

    def load_from_backup(self):
        try:
            backup_files = []
            
            if os.path.exists(BACKUP_FOLDER):
                backup_files.extend(glob.glob(os.path.join(BACKUP_FOLDER, "*.csv")))
            
            main_dir_files = glob.glob(os.path.join(APP_DATA_DIR, "Optimized_Route_*.csv"))
            backup_files.extend(main_dir_files)
            
            if not backup_files:
                response = tk.messagebox.askyesno(
                    "No Backups Found", 
                    "No backup files found in the usual locations.\n\nWould you like to manually select a CSV file?",
                    icon='question'
                )
                if response:
                    self._manual_backup_select()
                return
            
            if len(backup_files) > 1:
                if hasattr(self, 'backup_window') and self.backup_window.winfo_exists():
                    self.backup_window.focus()
                else:
                    self.backup_window = BackupSelectionWindow(self.master, backup_files, self._load_backup_file)
            else:
                self._load_backup_file(backup_files[0])
                
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error searching for backup files: {str(e)}")
            self.log(f"Backup search error: {e}")

    def _manual_backup_select(self):
        filename = tk.filedialog.askopenfilename(
            title="Select Backup CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=APP_DATA_DIR
        )
        if filename:
            self._load_backup_file(filename)

    def update_route_statistics(self):
        route_data = self.route_manager.get_route()
        
        if not route_data or len(route_data) < 2:
            self.total_distance_ly = 0.0
            self.traveled_distance_ly = 0.0
            self.average_jump_range = float(self.jump_range.get() or DEFAULT_SHIP_JUMP_RANGE_LY)
            return

        total_distance = 0.0
        for i in range(len(route_data) - 1):
            coords1 = route_data[i]['coords']
            coords2 = route_data[i + 1]['coords']
            distance = math.sqrt(
                (coords2[0] - coords1[0])**2 + 
                (coords2[1] - coords1[1])**2 + 
                (coords2[2] - coords1[2])**2
            )
            total_distance += distance
        
        self.total_distance_ly = total_distance

        traveled_distance = 0.0
        last_visited_index = -1
        
        for i, item in enumerate(route_data):
            if item.get('status') == STATUS_VISITED:
                last_visited_index = i
        
        if last_visited_index < 0:
            self.traveled_distance_ly = 0.0
        else:
            for i in range(last_visited_index):
                coords1 = route_data[i]['coords']
                coords2 = route_data[i + 1]['coords']
                distance = math.sqrt(
                    (coords2[0] - coords1[0])**2 + 
                    (coords2[1] - coords1[1])**2 + 
                    (coords2[2] - coords1[2])**2
                )
                traveled_distance += distance
            
            self.traveled_distance_ly = traveled_distance

        try:
            ship_jump_range = float(self.jump_range.get() or DEFAULT_SHIP_JUMP_RANGE_LY)
            if ship_jump_range <= 0:
                ship_jump_range = DEFAULT_SHIP_JUMP_RANGE_LY
        except ValueError:
            ship_jump_range = DEFAULT_SHIP_JUMP_RANGE_LY
        
        total_jumps = 0
        for i in range(len(route_data) - 1):
            coords1 = route_data[i]['coords']
            coords2 = route_data[i + 1]['coords']
            distance = math.sqrt(
                (coords2[0] - coords1[0])**2 + 
                (coords2[1] - coords1[1])**2 + 
                (coords2[2] - coords1[2])**2
            )
            jumps_for_segment = math.ceil(distance / ship_jump_range)
            total_jumps += jumps_for_segment
        
        if total_jumps > 0:
            self.average_jump_range = total_distance / total_jumps
        else:
            self.average_jump_range = ship_jump_range

        if hasattr(self, 'stats_total_label'):
            self.stats_total_label.configure(text=f"Total Distance: {self.total_distance_ly:.2f} LY")
        if hasattr(self, 'stats_traveled_label'):
            self.stats_traveled_label.configure(text=f"Traveled Distance: {self.traveled_distance_ly:.2f} LY")
        if hasattr(self, 'stats_avg_jump_label'):
            self.stats_avg_jump_label.configure(text=f"Average Jump Range: {self.average_jump_range:.1f} LY")
    

    def create_widgets(self):
        
        self.tabview = ctk.CTkTabview(self.master)
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)

        self.tab_optimizer = self.tabview.add("1. Route Optimization")
        self.tab_tracker = self.tabview.add("2. Route Tracking")
        self.tab_settings = self.tabview.add("3. Settings")

        self.tabview.set("1. Route Optimization")

        header_frame = ctk.CTkFrame(self.master, fg_color=("gray85", "gray15"), height=50)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=0)
        header_frame.grid_propagate(False)
        
        cmdr_info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        cmdr_info_frame.grid(row=0, column=0, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(cmdr_info_frame, text="CMDR:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.cmdr_name, font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", padx=(5, 15), pady=2)
        
        ctk.CTkLabel(cmdr_info_frame, text="CR:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.cmdr_cash, font=ctk.CTkFont(size=12)).grid(row=0, column=3, sticky="w", padx=(5, 0), pady=2)

        if self.app_logo:
            self.logo_label = ctk.CTkLabel(header_frame, image=self.app_logo, text="")
            self.logo_label.grid(row=0, column=1, sticky="e", padx=15, pady=5)

        self.create_optimizer_tab_content()
        self.create_settings_tab_content()
        self.create_bottom_buttons()

    def create_bottom_buttons(self):
        bottom_frame = ctk.CTkFrame(self.master, fg_color="transparent", height=40)
        bottom_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        bottom_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        github_btn = ctk.CTkButton(bottom_frame, text="GitHub", command=lambda: self.open_link(GITHUB_LINK), height=28)
        github_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        discord_btn = ctk.CTkButton(bottom_frame, text="Discord", command=lambda: self.open_link(DISCORD_LINK), height=28)
        discord_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        kofi_btn = ctk.CTkButton(bottom_frame, text="Ko-fi", command=lambda: self.open_link(DONATION_LINK_KOFI), height=28, fg_color="#FF5E5B", hover_color="#E04E4B")
        kofi_btn.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        patreon_btn = ctk.CTkButton(bottom_frame, text="Patreon", command=lambda: self.open_link(DONATION_LINK_PATREON), height=28, fg_color="#FF424D", hover_color="#E03A45")
        patreon_btn.grid(row=0, column=3, padx=2, pady=2, sticky="ew")

        about_btn = ctk.CTkButton(bottom_frame, text="About", command=self.show_about_info, height=28, fg_color="#1E88E5", hover_color="#1565C0")
        about_btn.grid(row=0, column=4, padx=2, pady=2, sticky="ew")

    def create_optimizer_tab_content(self):
        main_frame = ctk.CTkFrame(self.tab_optimizer, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        row1_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        row1_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        row1_frame.columnconfigure(0, weight=3)
        row1_frame.columnconfigure(1, weight=1)
        row1_frame.columnconfigure(2, weight=2)
    
        ctk.CTkLabel(row1_frame, text="1. Route Data File (CSV):", 
                    font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        file_frame = ctk.CTkFrame(row1_frame, fg_color="transparent")
        file_frame.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        self.file_entry = ctk.CTkEntry(file_frame, textvariable=self.csv_file_path)
        self.file_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.file_button = ctk.CTkButton(file_frame, text="Browse / Reset", command=self.browse_file, width=80)
        self.file_button.grid(row=0, column=1, padx=5, sticky="e")
    
        ctk.CTkLabel(row1_frame, text="2. Ship Jump Range (LY):", 
                    font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", pady=(0, 5))
        self.range_entry = ctk.CTkEntry(row1_frame, textvariable=self.jump_range, width=120)
        self.range_entry.grid(row=1, column=1, padx=10, sticky="w")
    
        ctk.CTkLabel(row1_frame, text="3. Starting System (Optional):", 
                    font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w", pady=(0, 5))
        self.start_entry = ctk.CTkEntry(row1_frame, textvariable=self.starting_system)
        self.start_entry.grid(row=1, column=2, sticky="ew")

        ctk.CTkLabel(main_frame, text="4. Required CSV Columns Status:", 
                    font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", pady=(10, 5))
        
        self.required_columns_frame = ctk.CTkFrame(main_frame, corner_radius=8, height=100)
        self.required_columns_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.required_columns_frame.grid_propagate(False)
        
        self.columns_container = ctk.CTkFrame(self.required_columns_frame, fg_color="transparent")
        self.columns_container.pack(fill="both", expand=True, padx=10, pady=8)
        
        self.column_status_label = ctk.CTkLabel(
            self.columns_container, 
            text="Please select a CSV file to check column status",
            text_color=("gray50", "gray70"),
            font=ctk.CTkFont(size=11)
        )
        self.column_status_label.pack(expand=True)
        
        self.column_indicators = {}
        self.current_csv_columns = []
        
        self.csv_file_path.trace_add('write', self.on_csv_path_changed)
    
        self.optional_toggle_btn = ctk.CTkButton(main_frame, 
                                               text="Optional Columns", 
                                               command=self.toggle_optional_columns,
                                               width=140, height=28,
                                               fg_color="#2196F3", hover_color="#1976D2")
        self.optional_toggle_btn.grid(row=3, column=0, pady=(0, 15), sticky="w")

        button_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_container.grid(row=5, column=0, pady=15, sticky="ew")
        button_container.grid_columnconfigure(0, weight=1)

        self.run_button = ctk.CTkButton(button_container, text="5. Optimize Route and Start Tracking", 
                                       command=self.run_optimization_threaded, 
                                       height=32,
                                       width=100,
                                       font=ctk.CTkFont(size=13, weight="bold"))
        self.run_button.grid(row=0, column=0)

        ctk.CTkLabel(main_frame, text="Status/Output Console:", 
                    font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, sticky="w", pady=(10, 2))
        self.output_text = ctk.CTkTextbox(main_frame, height=350)
        self.output_text.grid(row=6, column=0, padx=5, pady=(0, 10), sticky="nsew")

    def create_settings_tab_content(self):
        main_frame = ctk.CTkFrame(self.tab_settings, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text="Application Settings", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 20))

        row1_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        row1_frame.pack(fill="x", padx=5, pady=(0, 15))
        row1_frame.columnconfigure(0, weight=1)
        row1_frame.columnconfigure(1, weight=1)

        overlay_frame = ctk.CTkFrame(row1_frame, corner_radius=8)
        overlay_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        ctk.CTkLabel(overlay_frame, text="Overlay", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 10))

        self.overlay_btn = ctk.CTkButton(overlay_frame, 
                                       text="Start Overlay" if not self.overlay_enabled else "Stop Overlay", 
                                       command=self.toggle_overlay,
                                       fg_color="#9C27B0", hover_color="#7B1FA2", height=32,
                                       font=ctk.CTkFont(size=12, weight="bold"))
        self.overlay_btn.pack(pady=(0, 10), padx=12, fill="x")

        opacity_frame = ctk.CTkFrame(overlay_frame, fg_color="transparent")
        opacity_frame.pack(fill="x", padx=12, pady=(0, 5))
        ctk.CTkLabel(opacity_frame, text="Opacity:", width=50).pack(side="left")
        self.overlay_opacity = ctk.CTkSlider(opacity_frame, 
                                           from_=50, to=100, 
                                           number_of_steps=10,
                                           width=120, height=20,
                                           command=self.update_overlay_opacity)
        self.overlay_opacity.set(self.config.overlay_opacity)
        self.overlay_opacity.pack(side="right")
        
        opacity_value_frame = ctk.CTkFrame(overlay_frame, fg_color="transparent")
        opacity_value_frame.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(opacity_value_frame, text="", width=50).pack(side="left")
        self.opacity_label = ctk.CTkLabel(opacity_value_frame, 
                                        text=f"{self.config.overlay_opacity}%", 
                                        font=ctk.CTkFont(size=11))
        self.opacity_label.pack(side="right")
        
        size_frame = ctk.CTkFrame(overlay_frame, fg_color="transparent")
        size_frame.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(size_frame, text="Size:", width=50).pack(side="left")
        self.overlay_size = ctk.CTkOptionMenu(size_frame, 
                                            values=["Small", "Medium", "Large"],
                                            width=120, height=28,
                                            command=self.update_overlay_size)
        self.overlay_size.set(self.config.overlay_size)
        self.overlay_size.pack(side="right")
        
        autosave_frame = ctk.CTkFrame(row1_frame, corner_radius=8)
        autosave_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        ctk.CTkLabel(autosave_frame, text="Auto-save", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 10))

        interval_frame = ctk.CTkFrame(autosave_frame, fg_color="transparent")
        interval_frame.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(interval_frame, text="Interval:", width=60).grid(row=0, column=0, sticky="w")
        self.autosave_interval = ctk.CTkOptionMenu(interval_frame, 
                                                 values=["1 minute", "5 minutes", "10 minutes", "Never"],
                                                 width=120, height=28,
                                                 command=self.update_autosave_interval)
        self.autosave_interval.set(self.config.autosave_interval)
        self.autosave_interval.grid(row=0, column=1, sticky="e")
        interval_frame.columnconfigure(1, weight=1)

        status_frame = ctk.CTkFrame(autosave_frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(status_frame, text="Status:", width=60).grid(row=0, column=0, sticky="w")
        self.autosave_status = ctk.CTkLabel(status_frame, text="Stopped",
                                          font=ctk.CTkFont(size=10))
        self.autosave_status.grid(row=0, column=1, sticky="e")
        status_frame.columnconfigure(1, weight=1)

        autosave_btn_frame = ctk.CTkFrame(autosave_frame, fg_color="transparent")
        autosave_btn_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.autosave_start_btn = ctk.CTkButton(autosave_btn_frame, text="Start", 
                                              command=self.start_autosave,
                                              fg_color="#4CAF50", hover_color="#45a049",
                                              height=28, width=70)
        self.autosave_start_btn.pack(side="left", padx=(0, 8))
        self.autosave_save_btn = ctk.CTkButton(autosave_btn_frame, text="Save Now", 
                                             command=self.manual_save,
                                             height=28, width=80)
        self.autosave_save_btn.pack(side="left")

        separator1 = ctk.CTkFrame(main_frame, height=1, fg_color=("gray70", "gray30"))
        separator1.pack(fill="x", padx=10, pady=(15, 15))

        row2_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        row2_frame.pack(fill="x", padx=5, pady=(0, 0))
        row2_frame.columnconfigure(0, weight=1)
        row2_frame.columnconfigure(1, weight=1)

        journal_frame = ctk.CTkFrame(row2_frame, corner_radius=8)
        journal_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        ctk.CTkLabel(journal_frame, text="Journal", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 10))

        path_frame = ctk.CTkFrame(journal_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(path_frame, text="Path:", width=40).grid(row=0, column=0, sticky="w")
        self.journal_entry = ctk.CTkEntry(path_frame, textvariable=self.journal_path_var, 
                                        placeholder_text="Auto-detected path")
        self.journal_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.journal_browse_btn = ctk.CTkButton(path_frame, text="Browse", 
                                              command=self._browse_journal_path, 
                                              width=70, height=28)
        self.journal_browse_btn.grid(row=0, column=2, padx=(0, 0))
        path_frame.columnconfigure(1, weight=1)

        commanders = self.detect_all_commanders()
        cmdr_frame = ctk.CTkFrame(journal_frame, fg_color="transparent")
        cmdr_frame.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(cmdr_frame, text="CMDR:", width=40).grid(row=0, column=0, sticky="w")
        self.cmdr_dropdown = ctk.CTkOptionMenu(cmdr_frame, 
                                             values=commanders,
                                             variable=self.selected_commander,
                                             width=140, height=28,
                                             command=self.switch_commander)
        self.cmdr_dropdown.grid(row=0, column=1, sticky="e")
        cmdr_frame.columnconfigure(1, weight=1)

        journal_btn_frame = ctk.CTkFrame(journal_frame, fg_color="transparent")
        journal_btn_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.journal_test_btn = ctk.CTkButton(journal_btn_frame, text="Test", 
                                            command=self._test_journal_path, 
                                            height=28, width=70)
        self.journal_test_btn.pack(side="left", padx=(0, 8))
        self.journal_apply_btn = ctk.CTkButton(journal_btn_frame, text="Apply", 
                                             command=self._apply_journal_settings,
                                             fg_color="#4CAF50", hover_color="#45a049",
                                             height=28, width=70)
        self.journal_apply_btn.pack(side="left")
        self.refresh_cmdr_btn = ctk.CTkButton(journal_btn_frame, text="Refresh", 
                                            command=self.refresh_commanders_list,
                                            height=28, width=70)
        self.refresh_cmdr_btn.pack(side="right")

        theme_frame = ctk.CTkFrame(row2_frame, corner_radius=8)
        theme_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        ctk.CTkLabel(theme_frame, text="Theme", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 10))

        mode_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
        mode_frame.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(mode_frame, text="Mode:", width=60).grid(row=0, column=0, sticky="w")
        self.theme_mode_menu = ctk.CTkOptionMenu(mode_frame, 
                                               values=["Dark", "Light", "System"],
                                               command=self.change_appearance_mode_event,
                                               variable=self.theme_mode,
                                               width=120, height=28)
        self.theme_mode_menu.grid(row=0, column=1, sticky="e")
        mode_frame.columnconfigure(1, weight=1)

        color_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
        color_frame.pack(fill="x", padx=12, pady=(0, 15))
        ctk.CTkLabel(color_frame, text="Color:", width=60).grid(row=0, column=0, sticky="w")
        self.theme_color_menu = ctk.CTkOptionMenu(color_frame, 
                                                values=["green", "blue", "dark-blue"],
                                                command=self.change_color_theme_event,
                                                variable=self.theme_color,
                                                width=120, height=28)
        self.theme_color_menu.grid(row=0, column=1, sticky="e")
        color_frame.columnconfigure(1, weight=1)

    def create_route_tracker_tab_content(self):
        for widget in self.tab_tracker.winfo_children():
            widget.destroy()

        route_data = self.route_manager.get_route()
        if not route_data:
            ctk.CTkLabel(self.tab_tracker, text="Optimized Route Not Found.\nPlease create a new route in the 'Route Optimization' tab.").pack(padx=20, pady=20)
            return

        main_container = ctk.CTkFrame(self.tab_tracker, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        main_container.columnconfigure(0, weight=60)
        main_container.columnconfigure(1, weight=40)
        main_container.rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(main_container, corner_radius=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=85)
        left_frame.rowconfigure(1, weight=15)

        self.map_frame = self.MiniMapFrameClass(left_frame,
                                    on_system_selected=self.handle_system_click,
                                    corner_radius=8)
        self.map_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        button_frame = ctk.CTkFrame(left_frame, corner_radius=8)
        button_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        button_frame.columnconfigure((0, 1, 2, 3), weight=1)
        button_frame.rowconfigure(0, weight=1)
        button_frame.rowconfigure(1, weight=1)

        copy_next_btn = ctk.CTkButton(button_frame, text="Copy Next", 
                                    command=self.copy_next_system_to_clipboard, 
                                    fg_color="#FF9800", hover_color="#F57C00",
                                    height=22, font=ctk.CTkFont(size=11))
        copy_next_btn.grid(row=0, column=0, padx=3, pady=3, sticky="ew")

        open_folder_btn = ctk.CTkButton(button_frame, text="Data Folder", 
                                      command=self.open_app_data_folder,
                                      height=22, font=ctk.CTkFont(size=11))
        open_folder_btn.grid(row=0, column=1, padx=3, pady=3, sticky="ew")

        open_csv_btn = ctk.CTkButton(button_frame, text="Open Excel", 
                                   command=self.open_output_csv,
                                   height=22, font=ctk.CTkFont(size=11))
        open_csv_btn.grid(row=0, column=2, padx=3, pady=3, sticky="ew")

        backup_btn = ctk.CTkButton(button_frame, text="Load Backup", 
                                  command=self.load_from_backup,
                                  height=22, font=ctk.CTkFont(size=11), 
                                  fg_color="#9C27B0", hover_color="#7B1FA2")
        backup_btn.grid(row=0, column=3, padx=3, pady=3, sticky="ew")

        stats_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=(2, 5), sticky="nsew")
        stats_frame.columnconfigure(0, weight=1)

        self.stats_total_label = ctk.CTkLabel(stats_frame, 
                                            text="Total Rota: 0.00 LY",
                                            font=ctk.CTkFont(size=11, weight="bold"))
        self.stats_total_label.grid(row=0, column=0, pady=(2, 0))

        self.stats_traveled_label = ctk.CTkLabel(stats_frame,
                                               text="Kat Edilen: 0.00 LY",
                                               font=ctk.CTkFont(size=11))
        self.stats_traveled_label.grid(row=1, column=0, pady=(1, 0))

        self.stats_avg_jump_label = ctk.CTkLabel(stats_frame,
                                               text=f"Ort. Jump: {self.average_jump_range:.1f} LY",
                                               font=ctk.CTkFont(size=11))
        self.stats_avg_jump_label.grid(row=2, column=0, pady=(1, 0))

        self.update_route_statistics()

        right_frame = ctk.CTkFrame(main_container, corner_radius=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(right_frame, text="Loading route status...", 
                                         font=ctk.CTkFont(weight="bold"))
        self.progress_label.pack(pady=(15, 10))

        ctk.CTkLabel(right_frame, text="Route Details:", 
                    font=ctk.CTkFont(weight="bold")).pack(pady=(0, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(right_frame, width=300)
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.system_labels = {}

        for i, item in enumerate(route_data):
            system_name = item.get('name', f"Unknown-{i}")
            status = item.get('status', STATUS_UNVISITED)

            display_name = system_name
            bodies_to_scan = item.get('bodies_to_scan', [])
            
            if bodies_to_scan:
                body_identifiers = []
                prefix = f"{system_name} " 
                
                for full_body_name in bodies_to_scan:
                    if full_body_name.startswith(prefix):
                        identifier = full_body_name[len(prefix):].strip()
                        body_identifiers.append(identifier)
                    else:
                        body_identifiers.append(full_body_name.strip())
                        
                body_list_str = ", ".join(body_identifiers)
                display_name = f"{display_name} ({body_list_str})"
            
            body_count = item.get('body_count', 0)
            if body_count > 0:
                display_name = f"{display_name} [{body_count} bodies]"

            label = ctk.CTkLabel(self.scroll_frame, text=f"{i+1}. {display_name}", anchor="w", justify="left", cursor="hand2", font=ctk.CTkFont(size=14, underline=True), fg_color="transparent")
            label.pack(fill="x", padx=10, pady=2)

            label.bind("<Button-1>", lambda event, name=system_name: self.handle_system_click(name))

            self.system_labels[system_name] = label
            self.update_label_color(system_name, status)

        has_coords = route_data and 'coords' in route_data[0]
        if has_coords:
            self.map_frame.plot_route(route_data)
        else:
            self.log("WARNING: Loaded route has no coordinates. 3D Map not plotted.")
            self.map_frame.plot_route([])

        self.update_progress_info()

    def update_progress_info(self):
        route_data = self.route_manager.get_route()
        if not route_data or self.progress_label is None:
            return

        visited_count = sum(1 for item in route_data if item.get('status') == STATUS_VISITED)
        skipped_count = sum(1 for item in route_data if item.get('status') == STATUS_SKIPPED)
        total_count = len(route_data)
        unvisited_count = total_count - visited_count - skipped_count

        if total_count > 0:
            progress_text = f"Total: {total_count} | Visited: {visited_count} | Skipped: {skipped_count} | Remaining: {unvisited_count}"
            self.progress_label.configure(text=progress_text)

    def update_label_color(self, system_name, status):
        if system_name in self.system_labels:
            label = self.system_labels[system_name]

            text_color = ('#DCE4EE' if ctk.get_appearance_mode() == 'Dark' else '#212121')
            fg_color = "transparent"

            if status == STATUS_VISITED:
                fg_color = COLOR_VISITED
                text_color = 'white'
            elif status == STATUS_SKIPPED:
                fg_color = COLOR_SKIPPED
                text_color = 'white'
            elif status == STATUS_UNVISITED:
                fg_color = "transparent"
                text_color = text_color

            try:
                label.configure(fg_color=fg_color, text_color=text_color)
            except Exception as e:
                self.log(f"Label color update error: {e}")

    def handle_system_click(self, system_name):
        if self.map_frame:
            self.map_frame.highlight_system(system_name)

        response = tk.messagebox.askyesnocancel(
            "Status Update",
            f"Have you visited the system '{system_name}'?\n\n'Yes' = Visited (Green)\n'No' = Skipped (Red)\n'Cancel' = Do not change status",
            icon="question"
        )

        if response is None:
            return

        new_status = None
        current_status = None
        
        with self.route_manager as route:
            current_item = next((item for item in route if item.get('name') == system_name), None)
            if current_item:
                current_status = current_item.get('status', STATUS_UNVISITED)
                
                if response:
                    if current_status == STATUS_VISITED:
                        new_status = STATUS_UNVISITED
                    else:
                        new_status = STATUS_VISITED
                else:
                    if current_status == STATUS_SKIPPED:
                        new_status = STATUS_UNVISITED
                    else:
                        new_status = STATUS_SKIPPED
                
                current_item['status'] = new_status
        
        if new_status:
            self._update_ui_after_manual_change(system_name, new_status)
            
            threading.Thread(target=lambda: save_route_status(self.route_manager.get_route()), daemon=True).start()
            
            self.log(f"'{system_name}' status updated to: {new_status.upper()}")

    def _update_ui_after_manual_change(self, system_name, new_status):
        try:
            self.update_label_color(system_name, new_status)
            self.update_progress_info()
            self.update_route_statistics()
            
            self.copy_next_system_to_clipboard()

            if self.map_frame and self.route_manager.get_route():
                self.master.after(50, lambda: self.map_frame.plot_route(self.route_manager.get_route()))
                self.master.after(100, lambda: self.map_frame.highlight_system(system_name))
                
        except Exception as e:
            self.log(f"Manual UI update error: {e}")
            self.master.after(100, lambda: self._retry_ui_update(system_name, new_status))

    def _retry_ui_update(self, system_name, new_status):
        try:
            self.update_label_color(system_name, new_status)
        except Exception:
            pass

    def log(self, message):
        try:
            self.output_text.configure(state='normal')
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.output_text.configure(state='disabled')
        except Exception:
            print(message)

    def autodetect_csv(self, initial_run=False):
        csv_path = self.csv_file_path.get()
        if not csv_path or not os.path.exists(csv_path):
            if initial_run:
                csv_files = glob.glob('*.csv')
                if csv_files:
                    self.csv_file_path.set(csv_files[0])
                    self.log(f"Auto-Detected: '{csv_files[0]}' file selected.")
                    csv_path = csv_files[0]
                    self.update_column_status_display()
                else:
                    if initial_run:
                        self.log("Warning: CSV file not found. Please use 'Browse' to select one.")
                    return
            else:
                return

        try:
            df = pd.read_csv(csv_path, nrows=5)
            self.available_columns = df.columns.tolist()
            
            if initial_run:
                self.log(f"CSV columns detected: {', '.join(self.available_columns)}")
                self.update_column_status_display()
                
        except Exception as e:
            self.log(f"ERROR: Could not read CSV file for column detection: {e}")

    def cleanup_all(self):
        try:
            self.log("Performing cleanup...")
            
            self._optimization_in_progress = False
            
            if hasattr(self, '_optimization_executor') and self._optimization_executor:
                try:
                    self._optimization_executor.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass
                self._optimization_executor = None
            
            try:
                import numpy as np
                large_arrays = ['_distance_matrix', '_coords_array', '_optimized_route']
                for array_name in large_arrays:
                    if hasattr(self, array_name):
                        delattr(self, array_name)
            except Exception:
                pass
            
            import gc
            gc.collect()
            
            self.log("Cleanup complete")
            
        except Exception as e:
            self.log(f"Cleanup error: {e}")

    def reset_for_new_optimization(self):
        try:
            self.log("Preparing for new optimization...")
            
            self._optimization_in_progress = False
            
            if hasattr(self, '_optimization_executor') and self._optimization_executor:
                try:
                    self._optimization_executor.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass
                self._optimization_executor = None
            
            if hasattr(self, '_optimization_thread') and self._optimization_thread:
                self._optimization_thread = None
            
            try:
                if hasattr(self, 'output_text'):
                    self.output_text.configure(state='normal')
                    self.output_text.delete(1.0, tk.END)
                    self.output_text.configure(state='disabled')
            except Exception:
                pass
            
            if hasattr(self, 'map_frame') and self.map_frame:
                try:
                    self.map_frame.clear()
                except Exception:
                    pass
            
            import gc
            gc.collect()
            
            self.log("Ready for new optimization")
            
        except Exception as e:
            self.log(f"Reset error: {e}")
            
    def cleanup_optimization_only(self):
        try:
            self._optimization_in_progress = False
            
            if hasattr(self, '_optimization_executor') and self._optimization_executor:
                try:
                    self._optimization_executor.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass
                self._optimization_executor = None
            
            try:
                import numpy as np
                large_vars = []
                for var_name in dir(self):
                    if var_name.startswith('_') and not var_name.startswith('__'):
                        var = getattr(self, var_name)
                        if isinstance(var, np.ndarray) and var.size > 1000:
                            large_vars.append(var_name)
                
                for var_name in large_vars:
                    delattr(self, var_name)
            except Exception:
                pass
            
        except Exception as e:
            self.log(f"Optimization cleanup error: {e}")


    def browse_file(self):
        
        self.reset_for_new_optimization()
        
        filename = filedialog.askopenfilename(
            defaultextension=".csv", 
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            self.csv_file_path.set(filename)
            self.log(f"File Selected: {filename}")
            
            self.update_column_status_display()
            self.update_column_selection(silent=False)

    def toggle_optional_columns(self):
        if self.optional_window and self.optional_window.winfo_exists():
            self.optional_window.destroy()
            self.optional_window = None
            return

        self.update_column_selection(silent=True)

        self.optional_window = ctk.CTkToplevel(self.master)
        self.optional_window.title("Optional Columns Selection")
        self.optional_window.geometry("500x400")
        self.optional_window.resizable(True, True)
        self.optional_window.transient(self.master)
        self.optional_window.grab_set()
        
        try:
            self.master.update_idletasks()
            x = self.master.winfo_x() + self.master.winfo_width() + 10
            y = self.master.winfo_y()
            self.optional_window.geometry(f"+{x}+{y}")
        except Exception:
            pass

        main_container = ctk.CTkFrame(self.optional_window)
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)

        ctk.CTkLabel(main_container, text="Select Optional Columns", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        scroll_frame = ctk.CTkScrollableFrame(main_container)
        scroll_frame.pack(fill="both", expand=True, pady=5)
        
        grid_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        grid_container.pack(fill="both", expand=True)

        required_columns = [SYSTEM_NAME_COLUMN, X_COORD_COLUMN, Y_COORD_COLUMN, Z_COORD_COLUMN]
        optional_columns = [col for col in self.available_columns if col not in required_columns]
        
        if not optional_columns:
            ctk.CTkLabel(scroll_frame, text="No optional columns detected in CSV", 
                        text_color=("gray50", "gray70")).pack(pady=20)
            return

        sorted_columns = sorted(optional_columns)
        
        for col in sorted_columns:
            if col not in self.column_vars:
                self.column_vars[col] = tk.BooleanVar(value=False)
        
        for i, col in enumerate(sorted_columns):
            row = i // 2
            col_pos = i % 2
            
            checkbox_frame = ctk.CTkFrame(grid_container, fg_color="transparent", height=26)
            checkbox_frame.grid(row=row, column=col_pos, sticky="w", padx=8, pady=2)
            checkbox_frame.grid_propagate(False)
            
            chk = ctk.CTkCheckBox(checkbox_frame, text=col, variable=self.column_vars[col],
                                 font=ctk.CTkFont(size=12),
                                 checkbox_width=16, checkbox_height=16)
            chk.pack(side="left")
            self.column_checkboxes[col] = chk

        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        select_all_btn = ctk.CTkButton(button_frame, text="Select All", 
                                      command=self.select_all_optional,
                                      width=100, height=28)
        select_all_btn.pack(side="left", padx=(0, 10))
        
        deselect_all_btn = ctk.CTkButton(button_frame, text="Deselect All", 
                                        command=self.deselect_all_optional,
                                        width=100, height=28)
        deselect_all_btn.pack(side="left", padx=(0, 10))
        
        close_btn = ctk.CTkButton(button_frame, text="Close", 
                                 command=lambda: self.optional_window.destroy(),
                                 width=100, height=28,
                                 fg_color="#757575", hover_color="#616161")
        close_btn.pack(side="right")

    def select_all_optional(self):
        for var in self.column_vars.values():
            var.set(True)

    def deselect_all_optional(self):
        for var in self.column_vars.values():
            var.set(False)
            
    def update_column_selection(self, silent=False):
        csv_path = self.csv_file_path.get()
        if not csv_path or not os.path.exists(csv_path):
            return

        try:
            df = pd.read_csv(csv_path, nrows=5)
            self.available_columns = df.columns.tolist()
            
            if not silent:
                self.log(f"CSV columns detected: {', '.join(self.available_columns)}")
                
        except Exception as e:
            if not silent:
                self.log(f"ERROR: Could not read CSV file for column detection: {e}")
    
    def run_optimization_threaded(self):
        if self._optimization_in_progress:
            self.log("Optimization already in progress")
            return
        
        self._optimization_in_progress = True
        
        self.cleanup_optimization_only()
        
        self.run_button.configure(state='disabled', text="Optimizing...")
        self.master.update_idletasks()
        
        def optimization_wrapper():
            try:
                self.run_optimization()
            except Exception as e:
                import traceback
                error_msg = f"Optimization failed: {str(e)[:100]}"
                self.master.after(0, lambda: self.log(f"{error_msg}"))
            finally:
                self._optimization_in_progress = False
                self.master.after(0, lambda: self.run_button.configure(
                    state='normal',
                    text="5. Optimize Route and Start Tracking"
                ))
        
        thread = threading.Thread(
            target=optimization_wrapper,
            daemon=True,
            name="OptimizationThread"
        )
        thread.start()
        self._optimization_thread = thread
    
    def _optimization_complete_callback(self, future):
        try:
            future.result()
        except Exception as e:
            self.log(f"Optimization thread error: {e}")
        finally:
            self._optimization_running = False
    
    def _handle_optimization_error(self, message):
        self.run_button.configure(state='normal')
        self.log(f"ERROR: {message}")
        tk.messagebox.showerror("Error", message.splitlines()[0])
        
    def _complete_optimization_on_main_thread(self, optimized_route_length, total_jumps, output_file_path, output_file_name, success=True, error_message=None):
        self.run_button.configure(state='normal')

        if not success:
            if error_message:
                self.log(f"CRITICAL ERROR: {error_message}")
                tk.messagebox.showerror("Critical Error", error_message.splitlines()[0])
            return

        self.total_distance_ly = optimized_route_length
        
        self.create_route_tracker_tab_content()
        self.tabview.set("2. Route Tracking")
        
        self._start_journal_monitor()
        self.copy_next_system_to_clipboard()

        self.log("\nOPTIMIZATION COMPLETE")
        self.log(f"Total Distance: {optimized_route_length:.2f} LY")
        self.log(f"Estimated Jumps: {total_jumps} jumps")
        self.log(f"Route successfully saved to: '{output_file_path}'")
        self.log("Switched to Route Tracking tab (with 3D Map).")
        self.log("Auto-Tracking STARTED (Monitoring Elite Dangerous Journal).")

        tk.messagebox.showinfo("Success", f"Route optimization complete and Auto-Tracking is ready.\nFile: {output_file_name}")

    def run_optimization(self):
        csv_path = self.csv_file_path.get()
        if csv_path and os.path.exists(csv_path):
            try:
                file_size = os.path.getsize(csv_path) / (1024*1024)
                if file_size > 100:
                    self.log(f"Large CSV file detected: {file_size:.1f}MB")
                    self.log("This may cause memory issues. Consider splitting the file.")
            except Exception:
                pass
        
        import gc
        for i in range(2):
            gc.collect()
        
        self.run_button.configure(state='disabled')
        
        try:
            self.log('--- STARTING OPTIMIZATION ---')
            if not csv_path or not os.path.exists(csv_path) or not csv_path.endswith('.csv'):
                self.master.after(0, self._handle_optimization_error, "Please select a valid CSV file.")
                return
            try:
                jump_range = float(self.jump_range.get())
                if jump_range <= 0:
                    self.master.after(0, self._handle_optimization_error, "Ship jump range must be a positive number.")
                    return
            except ValueError:
                self.master.after(0, self._handle_optimization_error, "Enter a valid number for ship jump range.")
                return
            starting_system_name = self.starting_system.get().strip()
            self.log(f"Starting System: '{starting_system_name}'")
            existing_status = {}
            route_data = self.route_manager.get_route()
            for route in route_data:
                existing_status[route['name']] = route['status']
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                self.master.after(0, self._handle_optimization_error, f"Failed to read CSV: {e}")
                return
            required_cols = {SYSTEM_NAME_COLUMN, X_COORD_COLUMN, Y_COORD_COLUMN, Z_COORD_COLUMN}
            if not required_cols.issubset(set(df.columns)):
                missing = required_cols - set(df.columns)
                self.master.after(0, self._handle_optimization_error, f"CSV missing required columns: {', '.join(missing)}")
                return
            df_grouped = self._group_systems_and_bodies(df)
            points = df_grouped[[SYSTEM_NAME_COLUMN, X_COORD_COLUMN, Y_COORD_COLUMN, Z_COORD_COLUMN]].copy()
            N_all = len(points)
            if N_all < 2:
                self.master.after(0, self._handle_optimization_error, "At least two unique waypoints are required for routing.")
                return
            self.log(f"Ship Range: {jump_range:.1f} LY | System Count: {N_all}")
            start_system_data = None
            optimization_points = points.copy()
            if starting_system_name:
                starting_system_name_clean = starting_system_name.lower().strip()
                mask = optimization_points[SYSTEM_NAME_COLUMN].str.lower().str.strip() == starting_system_name_clean
                matching_systems = optimization_points[mask]
                if len(matching_systems) > 0:
                    start_system_data = matching_systems.iloc[0]
                    optimization_points = optimization_points[~mask].reset_index(drop=True)
                    self.log(f"Starting system FIXED: '{start_system_data[SYSTEM_NAME_COLUMN]}'")
                    self.log(f"Remaining systems for optimization: {len(optimization_points)}")
                else:
                    self.log(f"WARNING: Starting system '{starting_system_name}' not found in CSV.")
                    self.log(f"Available systems: {len(optimization_points)}")
                    self.log(f"First few systems: {optimization_points[SYSTEM_NAME_COLUMN].head(5).tolist()}")
                    starting_system_name = None
            self.log("Starting TSP (Lin-Kernighan) optimization...")
            if len(optimization_points) == 0:
                self.log("ERROR: No systems left to optimize after removing starting system.")
                self.master.after(0, self._handle_optimization_error, "No systems left to optimize after removing starting system.")
                return
            coords_array = optimization_points[[X_COORD_COLUMN, Y_COORD_COLUMN, Z_COORD_COLUMN]].astype(np.float32).values
            distance_matrix_opt = calculate_3d_distance_matrix_chunked(coords_array, chunk_size=500)
            if len(distance_matrix_opt) > 1:
                permutation_opt, _ = solve_tsp_lin_kernighan(distance_matrix_opt, x0=None)
                optimized_names = optimization_points.iloc[permutation_opt][SYSTEM_NAME_COLUMN].tolist()
            else:
                optimized_names = optimization_points[SYSTEM_NAME_COLUMN].tolist()
            if start_system_data is not None:
                optimized_names.insert(0, start_system_data[SYSTEM_NAME_COLUMN])
                self.log(f"Final route order: Starting with '{start_system_data[SYSTEM_NAME_COLUMN]}'")
                self.log(f"Route length: {len(optimized_names)} systems")
            optimized_points_full = df[df[SYSTEM_NAME_COLUMN].isin(optimized_names)]
            system_bodies = df.groupby('System Name')['Name'].apply(list).to_dict()
            optimized_points_full = optimized_points_full.drop_duplicates('System Name').copy()
            optimized_points_full['Body_Names'] = optimized_points_full['System Name'].map(system_bodies)
            optimized_points_full = optimized_points_full.set_index(SYSTEM_NAME_COLUMN).loc[optimized_names].reset_index()
            route_distances = np.sqrt(
                np.sum(np.diff(optimized_points_full[[X_COORD_COLUMN, Y_COORD_COLUMN, Z_COORD_COLUMN]].values, axis=0) ** 2, axis=1)
            ).tolist()
            optimized_route_length = float(np.sum(route_distances))
            total_jumps = calculate_jumps(route_distances, jump_range)
            selected_columns = []
            required_columns = [SYSTEM_NAME_COLUMN, X_COORD_COLUMN, Y_COORD_COLUMN, Z_COORD_COLUMN]
            for col in required_columns:
                if col not in selected_columns:
                    selected_columns.append(col)
            for col, var in self.column_vars.items():
                if var.get() and col not in selected_columns:
                    selected_columns.append(col)
            final_output_columns = [col for col in selected_columns if col in optimized_points_full.columns]
            if 'Body_Names' in optimized_points_full.columns and 'Body_Names' not in final_output_columns:
                final_output_columns.append('Body_Names')
            if 'Body_Count' in optimized_points_full.columns and 'Body_Count' not in final_output_columns:
                final_output_columns.append('Body_Count')
            self.log(f"Selected columns for output: {', '.join(final_output_columns)}")
            output_df = optimized_points_full[final_output_columns]
            if 'Body_Names' in output_df.columns:
                output_df = output_df.rename(columns={'Body_Names': 'Bodies_To_Scan_List'})
                output_df['Bodies_To_Scan_List'] = output_df['Bodies_To_Scan_List'].apply(
                    lambda x: str(x) if isinstance(x, list) else x
                )
            output_df['Status'] = output_df['System Name'].map(
                lambda x: existing_status.get(x, STATUS_UNVISITED)
            )
            if not output_df.columns.tolist():
                self.master.after(0, self._handle_optimization_error, "Please select at least one valid column for output.")
                return
            safe_jump = int(total_jumps)
            output_file_name = f"Optimized_Route_{len(optimized_names)}_J{safe_jump}_M{jump_range:.1f}LY.csv"
            output_file_path = os.path.join(BACKUP_FOLDER, output_file_name)
            os.makedirs(BACKUP_FOLDER, exist_ok=True)
            output_df.to_csv(output_file_path, index=False)
            save_last_output_path(output_file_path)
            route_data = []
            records = optimized_points_full.to_dict('records')
            for rec in records:
                route_data.append({
                    'name': rec[SYSTEM_NAME_COLUMN],
                    'status': existing_status.get(rec[SYSTEM_NAME_COLUMN], STATUS_UNVISITED),
                    'coords': [
                        float(rec.get(X_COORD_COLUMN, 0) or 0),
                        float(rec.get(Y_COORD_COLUMN, 0) or 0),
                        float(rec.get(Z_COORD_COLUMN, 0) or 0)
                    ],
                    'bodies_to_scan': rec.get('Body_Names', []),
                    'body_count': int(rec.get('Body_Count', 0) or 0)
                })
            self.route_manager.load_route(route_data)
            save_route_status(route_data)
            self.master.after(0, 
                              self._complete_optimization_on_main_thread, 
                              optimized_route_length, 
                              total_jumps, 
                              output_file_path, 
                              output_file_name, 
                              True, 
                              None)
        except Exception as e:
            import traceback
            error_message = f"Critical error in optimization: {e}\n{traceback.format_exc()}"
            self.master.after(0, 
                              self._complete_optimization_on_main_thread, 
                              0, 0, "", "", False, error_message)

    def _group_systems_and_bodies(self, df):
        if 'System Name' not in df.columns:
            self.log("ERROR: CSV must contain a 'System Name' column for grouping.")
            return None

        body_columns = ['Body Name', 'Name', 'BodyName', 'body_name']
        body_column = next((col for col in body_columns if col in df.columns), None)
        
        group_cols = {'X': 'first', 'Y': 'first', 'Z': 'first'}
        
        if body_column:
            group_cols[body_column] = lambda x: [i for i in x if pd.notna(i)]
        
        grouped_df = df.groupby('System Name', sort=False).agg(group_cols).reset_index()
        
        if body_column:
            grouped_df['Body_Names'] = grouped_df[body_column]
            grouped_df['Body_Count'] = grouped_df['Body_Names'].apply(len)
            grouped_df = grouped_df.drop(columns=[body_column])
        else:
            grouped_df['Body_Names'] = [[] for _ in range(len(grouped_df))]
            grouped_df['Body_Count'] = 0

        self.log(f"INFO: Systems grouped. Total unique systems: {len(grouped_df)}")
        return grouped_df


if __name__ == '__main__':
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    initial_config = AppConfig.load(SETTINGS_FILE)
    ctk.set_appearance_mode(initial_config.appearance_mode)
    ctk.set_default_color_theme(initial_config.color_theme)

    root = ctk.CTk()
    root.title(f"{APP_NAME_FULL} v{CURRENT_VERSION}")
    app = RouteOptimizerApp(root)
    
    def on_closing():
        app._cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
