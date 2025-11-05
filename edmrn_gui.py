import pandas as pd
from scipy.spatial.distance import cdist
import numpy as np
from python_tsp.heuristics import solve_tsp_lin_kernighan
import math
import glob
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import sys
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


try:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        module_path = os.path.join(sys._MEIPASS, "edmrn_3d_minimap.py")
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location("edmrn_3d_minimap", module_path)
            edmrn_3d_minimap = importlib.util.module_from_spec(spec)
            sys.modules["edmrn_3d_minimap"] = edmrn_3d_minimap
            spec.loader.exec_module(edmrn_3d_minimap)
            MiniMapFrame = edmrn_3d_minimap.MiniMapFrame
        else:
            raise ImportError("Module not found in MEIPASS.")
    else:
        from edmrn_3d_minimap import MiniMapFrame

except ImportError:
    class MiniMapFrame(ctk.CTkFrame):
        def __init__(self, master, on_system_selected=None, **kwargs):
            super().__init__(master, **kwargs)
            ctk.CTkLabel(self, text="ERROR: 3D Map Module Not Found. Check pyinstaller --add-data path.").pack(padx=20, pady=20)
        def plot_route(self, *args):
            pass
        def highlight_system(self, *args):
            pass
def get_app_data_path():

    try:
        if platform.system() == "Windows":
            documents_path = os.path.join(os.path.expanduser('~'), 'Documents')
        else:
            documents_path = os.path.join(os.path.expanduser('~'), 'Documents') 
    except Exception:
        documents_path = os.path.abspath(".")
        
    return os.path.join(documents_path, "EDMRN_Route_Data")

APP_DATA_DIR = get_app_data_path()
SETTINGS_FILE = os.path.join(APP_DATA_DIR, 'settings.json')
ROUTE_STATUS_FILE = os.path.join(APP_DATA_DIR, 'route_status.json')
LAST_CSV_FILE = os.path.join(APP_DATA_DIR, 'last_output.txt')
BACKUP_FOLDER = os.path.join(APP_DATA_DIR, 'backups')

SYSTEM_NAME_COLUMN = 'System Name'
X_COORD_COLUMN = 'X'
Y_COORD_COLUMN = 'Y'
Z_COORD_COLUMN = 'Z'
DEFAULT_SHIP_JUMP_RANGE_LY = 70.0

COLOR_VISITED = '#4CAF50'
COLOR_SKIPPED = '#E53935'

COLOR_DEFAULT_TEXT = ('#DCE4EE', '#212121')

STATUS_VISITED = 'visited'
STATUS_SKIPPED = 'skipped'
STATUS_UNVISITED = 'unvisited'

APP_NAME_SHORT = "EDMRN"
APP_NAME_FULL = "ED Multi Route Navigation"

ALL_POSSIBLE_COLUMNS = [
    SYSTEM_NAME_COLUMN,
    X_COORD_COLUMN,
    Y_COORD_COLUMN,
    Z_COORD_COLUMN,
    'Body Name',
    'Gravity',
    'Atmosphere',
    'Subtype',
    'Surface Temperature (K)',
    'Distance to Arrival (LS)',
    'Last Updated At'
]

GITHUB_LINK = "https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer"
DISCORD_LINK = "https://discord.gg/jxVTyev8"
DONATION_LINK_KOFI = "https://ko-fi.com/ninurtakalhu"
DONATION_LINK_PATREON = "https://www.patreon.com/c/NinurtaKalhu"


APP_NAME_SHORT = "EDMRN"
CURRENT_VERSION = "2.1.0"  
GITHUB_OWNER = "NinurtaKalhu" 
GITHUB_REPO = "Elite-Dangerous-Multi-Route-Optimizer" 

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
            print(f"WARNING: Version conversion error after cleaning. Skipping update check.")
            return False, None, None

        is_update_available = latest_parts > current_parts

        if is_update_available:
            download_url = latest_release.get('html_url') 
            return True, latest_version, download_url
        else:
            return False, latest_version, None

    except requests.exceptions.RequestException as e:

        print(f"WARNING: Update check failed: {e}")
        return False, None, None
    except Exception as e:
        print(f"WARNING: Unexpected update check error: {e}")
        return False, None, None

def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_default_text_color():
    mode = ctk.get_appearance_mode()
    return COLOR_DEFAULT_TEXT[0] if mode == 'Dark' else COLOR_DEFAULT_TEXT[1]

def atomic_write_json(path, data):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    dirpath = os.path.dirname(path) or '.'
    fd, tmp = tempfile.mkstemp(dir=dirpath, prefix='.tmp_', suffix='.json')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

def calculate_3d_distance_matrix(points_df):
    coords = points_df[[X_COORD_COLUMN, Y_COORD_COLUMN, Z_COORD_COLUMN]].astype(float).values
    diff = coords[:, None, :] - coords[None, :, :]
    distances = np.sqrt(np.sum(diff * diff, axis=2))
    return distances

def calculate_jumps(distances, jump_range):
    total_jumps = int(np.sum(np.ceil(np.array(distances) / jump_range)))
    return total_jumps

os.makedirs(APP_DATA_DIR, exist_ok=True)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {'appearance_mode': 'Dark', 'color_theme': 'green'}

def save_settings(mode, theme):
    settings = {'appearance_mode': mode, 'color_theme': theme}
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass

def load_route_status():
    if os.path.exists(ROUTE_STATUS_FILE):
        try:
            with open(ROUTE_STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return []

def save_route_status(route_list):
    try:
        atomic_write_json(ROUTE_STATUS_FILE, route_list)
    except Exception:
        pass

def save_last_output_path(path):
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    try:
        with open(LAST_CSV_FILE, 'w') as f:
            f.write(path)
    except Exception:
        pass

def load_last_output_path():
    if os.path.exists(LAST_CSV_FILE):
        try:
            with open(LAST_CSV_FILE, 'r') as f:
                return f.read().strip()
        except Exception:
            pass
    return None


class JournalMonitor(threading.Thread):
    def __init__(self, callback, log_func):
        super().__init__(daemon=True)
        self.callback = callback
        self.log = log_func
        self._stop_event = threading.Event()
        self.last_tell = 0
        self.current_journal_file = None
        self.journal_path = self._find_journal_dir()
        self.monitor_interval = 2

    def _find_journal_dir(self):
        if platform.system() == "Windows":
            path = os.path.join(os.path.expanduser('~'), 'Saved Games', 'Frontier Developments', 'Elite Dangerous')
            if os.path.exists(path):
                return path
        return None

    def _get_latest_journal_file(self):
        if not self.journal_path:
            return None
        
        list_of_files = glob.glob(os.path.join(self.journal_path, 'Journal.*.log'))
        
        if not list_of_files:
            return None
            
        latest_file = max(list_of_files, key=os.path.getmtime)
        return latest_file

    def _process_line(self, line):
        try:
            if '"event":"FSDJump"' in line:
                data = json.loads(line)
                system_name = data.get('StarSystem')
                if system_name:
                    self.callback(system_name)
                    
            elif '"event":"Commander"' in line or '"event":"LoadGame"' in line:
                pass
                
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

        while not self._stop_event.is_set():
            time.sleep(self.monitor_interval)
            
            try:
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

            except FileNotFoundError:
                self.log("Journal file not found during tailing. Re-checking latest file.")
                break
            except Exception as e:
                self.log(f"Journal File Reading Error: {e}")
                time.sleep(5)
                
        self.current_journal_file = None
            
    def run(self):
        
        self.log("Journal Monitor STARTED - Auto-tracking active")
        
        while not self._stop_event.is_set():
            try:
                latest_file = self._get_latest_journal_file()
                
                if latest_file and os.path.exists(latest_file):
                    self._tail_file(latest_file)
                else:
                    self.log("No journal file found. Waiting...")
                    time.sleep(5)
                    
            except Exception as e:
                self.log(f"Journal monitor error: {e}")
                time.sleep(5)

    def stop(self):
        self._stop_event.set()
    def stop(self):
        self._stop_event.set()

class ManualWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"{APP_NAME_SHORT} - User Manual")
        try:
            self.iconbitmap(resource_path('explorer_icon.ico'))
        except Exception as e:
            print(f"Manual window icon error: {e}")
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
        ED Multi Route Navigation (EDMRN) - User Manual
        =========================================================

        EDMRN optimizes your multi-system exploration/data collection routes in Elite Dangerous for shortest distance (TSP) and provides in-game tracking.

        YOUR ROLE: Explorer/Astrobiologist (CMDR Ninurta Kalhu)

        ---------------------------------------------------------
        TAB 1: ROUTE OPTIMIZATION
        ---------------------------------------------------------
        1. Route Data File (CSV):
           - **Source:** Exported system list from Elite Dangerous (e.g., EDDiscovery, EDMC, or Spansh).
           - **REQUIRED COLUMNS:** 'System Name', 'X', 'Y', and 'Z' coordinate columns must be present.

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

        ACTION BUTTONS:
           - **Copy Next System:** Copies the next system to clipboard.
           - **Open Data Folder:** Opens the data folder.
           - **Open Route in Excel:** Opens the CSV file.
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
        except Exception as e:
            print(f"About window icon error: {e}")
        
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
            else:
                self.master.log(f"WARNING: Logo file not found at {logo_path}")
        except Exception as e:
            self.master.log(f"WARNING: Error loading logo in AboutWindow: {e}")

        ctk.CTkLabel(self, text=f"{APP_NAME_FULL} ({APP_NAME_SHORT})", font=ctk.CTkFont(size=16, weight="bold")).grid(row=1, column=0, pady=(0, 10))
        
        app_frame = ctk.CTkFrame(self, fg_color="transparent")
        app_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        app_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(app_frame, text="Software Version:", anchor="w").grid(row=0, column=0, sticky="w", pady=2)
        ctk.CTkLabel(app_frame, text="2.0 (Lin–Kernighan algorithm + Auto-Tracking)", anchor="e").grid(row=0, column=1, sticky="e", pady=2)
        
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


class RouteOptimizerApp:
    def __init__(self, master):
        self.master = master
        master.title(f"{APP_NAME_FULL} ({APP_NAME_SHORT}) - CMDR Terminal")
        
        master.geometry("1100x800")
        master.minsize(1000, 700)

        try:
            self.master.iconbitmap(resource_path('explorer_icon.ico'))
        except Exception:
            pass
        self.csv_file_path = ctk.StringVar()
        self.jump_range = ctk.StringVar(value=str(DEFAULT_SHIP_JUMP_RANGE_LY))
        self.starting_system = ctk.StringVar()
        self.cmdr_name = ctk.StringVar(value="[CMDR Name: Loading...]")
        self.cmdr_role = ctk.StringVar(value="(Role: Explorer/Astrobiologist)")
        self.cmdr_cash = ctk.StringVar(value="N/A Cr") 
        current_settings = load_settings()
        self.theme_mode = ctk.StringVar(value=current_settings['appearance_mode'])
        self.theme_color = ctk.StringVar(value=current_settings['color_theme'])
        self.route_lock = threading.Lock() 
        self.current_route = load_route_status()
        self.system_labels = {}
        self.progress_label = None
        self.map_frame = None
        self.route_names = set(item['name'] for item in self.current_route)
        self.journal_monitor = None
        self.app_logo = None
        try:
            logo_path = resource_path('explorer_icon.png')
            original_image = Image.open(logo_path)
            resized_image = original_image.resize((40, 40), Image.LANCZOS) 
            self.app_logo = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(40, 40))
        except Exception as e:
            self.log(f"WARNING: Error loading logo: {e}")
        
        self.column_vars = {}
        self.available_columns = ALL_POSSIBLE_COLUMNS 
        default_selected = [SYSTEM_NAME_COLUMN, X_COORD_COLUMN, Y_COORD_COLUMN, Z_COORD_COLUMN]
        for col in ALL_POSSIBLE_COLUMNS:
            default_state = tk.BooleanVar(value=(col in default_selected))
            self.column_vars[col] = default_state

        self.create_widgets() 
        self.autodetect_csv(initial_run=True) 

        if self.current_route:
            self.master.after(0, self.create_route_tracker_tab_content)
            self._start_journal_monitor()
            
        threading.Thread(target=self._get_latest_cmdr_data, daemon=True).start()

        self._check_and_notify_update()
        
    def change_appearance_mode_event(self, new_mode):
        ctk.set_appearance_mode(new_mode)
        save_settings(new_mode, self.theme_color.get())
        if self.map_frame:
             self.map_frame.plot_route(self.current_route)

    def change_color_theme_event(self, new_theme):
        ctk.set_default_color_theme(new_theme)
        save_settings(self.theme_mode.get(), new_theme)
        self.theme_color.set(new_theme)
        self.log(f"Theme changed to: {new_theme}")
    
    def format_cash(self, amount):
        return f"{amount:,}".replace(",", ".") + " Cr"
   
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
        
        response = messagebox.askyesno(
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

    def create_widgets(self):
        self.tabview = ctk.CTkTabview(self.master)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.tab_optimizer = self.tabview.add("1. Route Optimization")
        self.tab_tracker = self.tabview.add("2. Route Tracking")
        self.tab_settings = self.tabview.add("3. Settings")

        self.tabview.set("1. Route Optimization")

        self.create_optimizer_tab_content()
        self.create_settings_tab_content()
        self.create_bottom_buttons()
        self.logo_label = None
        if self.app_logo:
            self.logo_label = ctk.CTkLabel(self.master, image=self.app_logo, text="")
            self.logo_label.place(relx=0.98, rely=0.02, anchor="ne")

    def create_bottom_buttons(self):
        bottom_frame = ctk.CTkFrame(self.master, fg_color="transparent", height=40)
        bottom_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
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

    def create_settings_tab_content(self):
        main_frame = ctk.CTkFrame(self.tab_settings, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text="Application Settings", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 20))

        appearance_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        appearance_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(appearance_frame, text="Appearance Settings", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 8))


        mode_frame = ctk.CTkFrame(appearance_frame, fg_color="transparent")
        mode_frame.pack(fill="x", padx=15, pady=4)

        ctk.CTkLabel(mode_frame, text="Appearance Mode:", width=120).grid(row=0, column=0, sticky="w", padx=5)
        mode_menu = ctk.CTkOptionMenu(mode_frame, values=["Dark", "Light", "System"], 
                                    command=self.change_appearance_mode_event, 
                                    variable=self.theme_mode, height=28)
        mode_menu.grid(row=0, column=1, sticky="ew", padx=5)
        mode_frame.columnconfigure(1, weight=1)

        theme_frame = ctk.CTkFrame(appearance_frame, fg_color="transparent")
        theme_frame.pack(fill="x", padx=15, pady=4)

        ctk.CTkLabel(theme_frame, text="Color Theme:", width=120).grid(row=0, column=0, sticky="w", padx=5)
        color_menu = ctk.CTkOptionMenu(theme_frame, values=["green", "blue", "dark-blue"], 
                                    command=self.change_color_theme_event, 
                                    variable=self.theme_color, height=28)
        color_menu.grid(row=0, column=1, sticky="ew", padx=5)
        theme_frame.columnconfigure(1, weight=1)

        donation_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        donation_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(donation_frame, text="Buy me coffee <3", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5))

        donation_buttons_frame = ctk.CTkFrame(donation_frame, fg_color="transparent")
        donation_buttons_frame.pack(fill="x", pady=5)
        donation_buttons_frame.columnconfigure((0, 1), weight=1)

        kofi_btn = ctk.CTkButton(donation_buttons_frame, text="Ko-fi", 
                                command=lambda: self.open_link(DONATION_LINK_KOFI),
                                fg_color="#FF5E5B", hover_color="#E04E4B", height=28)
        kofi_btn.grid(row=0, column=0, padx=5, pady=3, sticky="ew")

        patreon_btn = ctk.CTkButton(donation_buttons_frame, text="Patreon", 
                                   command=lambda: self.open_link(DONATION_LINK_PATREON),
                                   fg_color="#FF424D", hover_color="#E03A45", height=28)
        patreon_btn.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
    
    def _start_journal_monitor(self):
        if self.journal_monitor:
            self.journal_monitor.stop()
        
        self.route_names = set(item['name'] for item in self.current_route) 
        
        self.journal_monitor = JournalMonitor(
            callback=self.handle_system_jump,
            log_func=self.log
        )
        self.journal_monitor.start()
        self.log("INFO: Started Elite Dangerous Journal Monitor for auto-tracking.")

    def handle_system_jump(self, system_name):
        self.master.after(0, lambda: self._update_system_status_from_monitor(system_name, STATUS_VISITED))

    def _get_latest_cmdr_data(self):
        cmdr_name_default = self.cmdr_name.get().replace("[CMDR Name: Loading...]", "CMDR NoName")
        
        cmdr_cash = 0
        journal_monitor = JournalMonitor(None, self.log)
        latest_file = journal_monitor._get_latest_journal_file()

        if not latest_file:
            self.log("WARNING: Elite Dangerous Journal path not found. CMDR status not loaded.")
            self.master.after(0, self.cmdr_name.set, f"CMDR Not Found ({cmdr_name_default})")
            if "N/A" in self.cmdr_cash.get():
                self.master.after(0, self.cmdr_cash.set, "Where is the bank? (Saved Data)")
            return

        self.log(f"INFO: Checking Journal file: {os.path.basename(latest_file)}")

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    event = data.get('event')

                    if event == 'Commander':
                        cmdr_name_default = data.get('Name', cmdr_name_default)
                    elif event == 'LoadGame':
                        cmdr_cash = data.get('Credits', cmdr_cash)
                        
        except Exception as e:
            self.log(f"ERROR reading CMDR data from Journal: {e}")

        final_cmdr_name = cmdr_name_default
        final_cmdr_cash = self.format_cash(cmdr_cash)
        
        self.master.after(0, self.cmdr_name.set, final_cmdr_name)
        self.master.after(0, self.cmdr_cash.set, final_cmdr_cash)
        
        self.log(f"CMDR Status Loaded: {final_cmdr_name}, {final_cmdr_cash}")
        
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

    def get_next_unvisited_system(self):
        with self.route_lock: 
            for item in self.current_route:
                if item.get('status') == STATUS_UNVISITED:
                    return item.get('name')
            return None
        
    def copy_next_system_to_clipboard(self):
        next_system_name = self.get_next_unvisited_system()
        
        if next_system_name:
            if self._set_clipboard_text_non_disruptive(next_system_name):
                 self.log(f"'{next_system_name}' (Next System) copied to clipboard (Non-disruptive mode). Ready for Ctrl+V.")
            else:
                 messagebox.showerror("Error", "Could not copy to clipboard. Please try clicking the system name in the list below.")
                 self.log("ERROR: Failed to copy system name to clipboard.")
        else:
            self.log("INFO: Route complete. Nothing to copy.")

    def _update_system_status_from_monitor(self, system_name, new_status):
        if system_name not in self.route_names:
            self.log(f"Jumped to '{system_name}' (Explorer/Astrobiologist Role: New system found, but not on current route).")
            return

        status_changed = False
        current_item = None
        
        with self.route_lock: 
            current_item = next((item for item in self.current_route if item.get('name') == system_name), None)
            
            if current_item and current_item.get('status') == STATUS_UNVISITED:
                current_item['status'] = new_status
                save_route_status(self.current_route)
                status_changed = True

        if status_changed:
            self.update_label_color(system_name, new_status)
            self.update_progress_info()
            
            self.copy_next_system_to_clipboard() 

            if self.map_frame and self.current_route and 'coords' in self.current_route[0]:
                self.map_frame.plot_route(self.current_route)
                self.map_frame.highlight_system(system_name)

            self.log(f"Auto-Detected Jump to '{system_name}'. Status updated to {new_status.upper()}.")
        elif current_item and current_item.get('status') == STATUS_VISITED:
            self.log(f"Jumped to '{system_name}' (Already Visited).")
        
    def open_output_csv(self):
        last_path = load_last_output_path()
        if not last_path or not os.path.exists(last_path):
            messagebox.showerror("Error", "The optimized route file was not found. Please run optimization first.")
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
            messagebox.showerror("Error", f"Could not open the file automatically. Please open it manually.\nError: {e}")
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
            messagebox.showerror("Error", f"Could not open the data folder automatically. Please navigate to:\n{APP_DATA_DIR}")
            self.log(f"ERROR: Failed to open data folder: {e}")

    def create_route_tracker_tab_content(self):
        for widget in self.tab_tracker.winfo_children():
            widget.destroy()

        if not self.current_route:
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


        self.map_frame = MiniMapFrame(left_frame,
                                    on_system_selected=self.handle_system_click,
                                    corner_radius=8)
        self.map_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)


        button_frame = ctk.CTkFrame(left_frame, corner_radius=8)
        button_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        button_frame.columnconfigure(0, weight=1)

        copy_next_btn = ctk.CTkButton(button_frame, text="Copy Next System (Ctrl+V Ready)", 
                                    command=self.copy_next_system_to_clipboard, 
                                    fg_color="#FF9800", hover_color="#F57C00",
                                    height=32)
        copy_next_btn.grid(row=0, column=0, padx=10, pady=4, sticky="ew")

        open_folder_btn = ctk.CTkButton(button_frame, text="Open Data Folder", 
                                      command=self.open_app_data_folder,
                                      height=32)
        open_folder_btn.grid(row=1, column=0, padx=10, pady=4, sticky="ew")

        open_csv_btn = ctk.CTkButton(button_frame, text="Open Route in Excel", 
                                   command=self.open_output_csv,
                                   height=32)
        open_csv_btn.grid(row=2, column=0, padx=10, pady=4, sticky="ew")


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

        for i, item in enumerate(self.current_route):
            system_name = item.get('name', f"Unknown-{i}")
            status = item.get('status', STATUS_UNVISITED)

            display_name = system_name
            bodies_to_scan = item.get('bodies_to_scan', [])
            
            if len(bodies_to_scan) > 1:
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

            label = ctk.CTkLabel(self.scroll_frame, text=f"{i+1}. {display_name}", anchor="w", justify="left", cursor="hand2", font=ctk.CTkFont(size=14, underline=True), fg_color="transparent")
            label.pack(fill="x", padx=10, pady=2)

            label.bind("<Button-1>", lambda event, name=system_name: self.handle_system_click(name))

            self.system_labels[system_name] = label
            self.update_label_color(system_name, status)

        has_coords = self.current_route and 'coords' in self.current_route[0]
        if has_coords:
            self.map_frame.plot_route(self.current_route)
        else:
            self.log("WARNING: Loaded route has no coordinates. 3D Map not plotted.")
            self.map_frame.plot_route([])

        self.update_progress_info()

    def update_progress_info(self):
        if not self.current_route or self.progress_label is None:
            return

        visited_count = sum(1 for item in self.current_route if item.get('status') == STATUS_VISITED)
        skipped_count = sum(1 for item in self.current_route if item.get('status') == STATUS_SKIPPED)
        total_count = len(self.current_route)
        unvisited_count = total_count - visited_count - skipped_count

        if total_count > 0:
            progress_text = f"Total: {total_count} | Visited: {visited_count} | Skipped: {skipped_count} | Remaining: {unvisited_count}"
            self.progress_label.configure(text=progress_text)

    def update_label_color(self, system_name, status):
        if system_name in self.system_labels:
            label = self.system_labels[system_name]

            text_color = get_default_text_color()
            fg_color = "transparent"

            if status == STATUS_VISITED:
                fg_color = COLOR_VISITED
                text_color = 'white'
            elif status == STATUS_SKIPPED:
                fg_color = COLOR_SKIPPED
                text_color = 'white'
            elif status == STATUS_UNVISITED:
                fg_color = "transparent"
                text_color = get_default_text_color()

            try:
                label.configure(fg_color=fg_color, text_color=text_color)
            except Exception as e:
                self.log(f"WARNING: Label color update error: {e}")

    def handle_system_click(self, system_name):
        if self.map_frame:
            self.map_frame.highlight_system(system_name)

        response = messagebox.askyesnocancel(
            "Status Update",
            f"Have you visited the system '{system_name}'?\n\n'Yes' = Visited (Green)\n'No' = Skipped (Red)\n'Cancel' = Do not change status",
            icon="question"
        )

        if response is None:
            return

        new_status = None
        current_item = None

        with self.route_lock:
            current_item = next((item for item in self.current_route if item.get('name') == system_name), None)

            if current_item:
                current_status = current_item.get('status', STATUS_UNVISITED)
                new_status = current_status

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
                save_route_status(self.current_route)

        if current_item:
            self.update_label_color(system_name, new_status)
            self.update_progress_info()
            
            self.copy_next_system_to_clipboard() 

            if self.map_frame and self.current_route and 'coords' in self.current_route[0]:
                self.map_frame.plot_route(self.current_route)
                self.map_frame.highlight_system(system_name)

            self.log(f"'{system_name}' status updated to: {new_status.upper()}")

    def log(self, message):
        try:
            self.output_text.configure(state='normal')
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.output_text.configure(state='disabled')
        except Exception:
            print(message)

    def browse_file(self):
        filename = filedialog.askopenfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if filename:
            self.csv_file_path.set(filename)
            self.log(f"File Selected: {filename}")
            self.autodetect_csv(initial_run=False)

    def autodetect_csv(self, initial_run=False):
        csv_path = self.csv_file_path.get()
        if not csv_path or not os.path.exists(csv_path):
            if initial_run:
                csv_files = glob.glob('*.csv')
                if csv_files:
                    self.csv_file_path.set(csv_files[0])
                    self.log(f"Auto-Detected: '{csv_files[0]}' file selected.")
                    csv_path = csv_files[0]
                else:
                    self.log("Warning: CSV file not found. Please use 'Browse' to select one.")
                    return
            else:
                return

        try:
            df = pd.read_csv(csv_path, nrows=5)
            self.available_columns = df.columns.tolist()
            self.log(f"CSV columns detected: {', '.join(self.available_columns)}")
        except Exception:
            self.log("ERROR: Could not read CSV file for column detection.")

    def create_optimizer_tab_content(self):
        main_frame = ctk.CTkFrame(self.tab_optimizer, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)

        cmdr_frame = ctk.CTkFrame(main_frame, fg_color=("gray85", "gray15"))
        cmdr_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 15))
        cmdr_frame.columnconfigure(1, weight=1)
        
        cmdr_info_frame = ctk.CTkFrame(cmdr_frame, fg_color="transparent")
        cmdr_info_frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        ctk.CTkLabel(cmdr_info_frame, text="CMDR:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.cmdr_name, font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", padx=(5, 15), pady=2)
        
        ctk.CTkLabel(cmdr_info_frame, text="CR:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.cmdr_cash, font=ctk.CTkFont(size=12)).grid(row=0, column=3, sticky="w", padx=(5, 0), pady=2)

        ctk.CTkLabel(main_frame, text="1. Route Data File (CSV):", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky=tk.W, pady=(5, 5))
        
        file_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        file_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        self.file_entry = ctk.CTkEntry(file_frame, textvariable=self.csv_file_path)
        self.file_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.file_button = ctk.CTkButton(file_frame, text="Browse...", command=self.browse_file, width=80)
        self.file_button.grid(row=0, column=1, padx=5, sticky="e")

        range_system_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        range_system_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        range_system_frame.columnconfigure(0, weight=1)
        range_system_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(range_system_frame, text="2. Ship Jump Range (LY):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.range_entry = ctk.CTkEntry(range_system_frame, textvariable=self.jump_range, width=120)
        self.range_entry.grid(row=1, column=0, padx=(0, 10), sticky="w")
        
        ctk.CTkLabel(range_system_frame, text="3. Starting System (Optional):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        self.start_entry = ctk.CTkEntry(range_system_frame, textvariable=self.starting_system)
        self.start_entry.grid(row=1, column=1, sticky="ew")

        col_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        col_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        ctk.CTkLabel(col_frame, text="4. Select Output CSV Columns:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(8, 5))
        
        for i, col in enumerate(ALL_POSSIBLE_COLUMNS[:9]):
            row_pos = (i // 3) + 1
            col_pos = i % 3
            chk = ctk.CTkCheckBox(col_frame, text=col, variable=self.column_vars[col])
            chk.grid(row=row_pos, column=col_pos, sticky=tk.W, padx=12, pady=2)

        self.run_button = ctk.CTkButton(main_frame, text="5. Optimize Route and Start Tracking", 
                                       command=self.run_optimization_threaded, 
                                       height=32, 
                                       font=ctk.CTkFont(size=13, weight="bold"))
        self.run_button.grid(row=5, column=0, columnspan=2, pady=15, sticky="ew")

        ctk.CTkLabel(main_frame, text="Status/Output Console:", font=ctk.CTkFont(weight="bold")).grid(row=6, column=0, sticky=tk.W, pady=(10, 2))
        self.output_text = ctk.CTkTextbox(main_frame, height=350)
        self.output_text.grid(row=7, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="nsew")

    def run_optimization_threaded(self):
        t = threading.Thread(target=self.run_optimization, daemon=True)
        t.start()
    
    def _handle_optimization_error(self, message):
        self.run_button.configure(state='normal')
        self.log(f"ERROR: {message}")
        messagebox.showerror("Error", message.splitlines()[0])
        
    def _complete_optimization_on_main_thread(self, optimized_route_length, total_jumps, output_file_path, output_file_name, success=True, error_message=None):
        self.run_button.configure(state='normal')

        if not success:
            if error_message:
                self.log(f"CRITICAL ERROR: {error_message}")
                messagebox.showerror("Critical Error", error_message.splitlines()[0]) 
            return

        self.create_route_tracker_tab_content() 
        self.tabview.set("2. Route Tracking")
        
        self._start_journal_monitor()
        self.copy_next_system_to_clipboard()

        self.log("\nOPTIMIZATION COMPLETE")
        self.log(f"Total Distance: {optimized_route_length:.2f} LY")
        self.log(f"Estimated Jumps: {total_jumps} jumps")
        self.log(f"Route successfully saved to: '{output_file_path}' (In {APP_DATA_DIR})")
        self.log("Switched to Route Tracking tab (with 3D Map).")
        self.log("Auto-Tracking STARTED (Monitoring Elite Dangerous Journal).")

        messagebox.showinfo("Success", f"Route optimization complete and Auto-Tracking is ready.\nFile: {output_file_name}")

    def run_optimization(self):
        self.run_button.configure(state='disabled') 
        
        csv_path = self.csv_file_path.get()
        jump_range = None
        
        try:
            self.log('\n--- STARTING OPTIMIZATION ---')

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
                mask = optimization_points[SYSTEM_NAME_COLUMN].str.lower() == starting_system_name.lower()
                if mask.any():
                    start_system_data = optimization_points[mask].iloc[0]
                    optimization_points = optimization_points[~mask].reset_index(drop=True)
                    self.log(f"Starting system fixed: {starting_system_name}")
                else:
                    self.log(f"WARNING: Starting system '{starting_system_name}' not found. Full loop will be optimized.")
                    starting_system_name = None

            self.log("Starting TSP (Lin-Kernighan) optimization...")
            distance_matrix_opt = calculate_3d_distance_matrix(optimization_points)
            
            if len(distance_matrix_opt) > 1:
                permutation_opt, _ = solve_tsp_lin_kernighan(distance_matrix_opt, x0=None)
                optimized_names = optimization_points.iloc[permutation_opt][SYSTEM_NAME_COLUMN].tolist()
            else:
                optimized_names = optimization_points[SYSTEM_NAME_COLUMN].tolist()

            if start_system_data is not None:
                optimized_names.insert(0, start_system_data[SYSTEM_NAME_COLUMN])

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

            selected_columns = [col for col, var in self.column_vars.items() if var.get()]
            if SYSTEM_NAME_COLUMN not in selected_columns:
                selected_columns.insert(0, SYSTEM_NAME_COLUMN)
            
            if 'Body Name' in selected_columns:
                selected_columns.remove('Body Name')

            final_output_columns = [col for col in selected_columns if col in optimized_points_full.columns]
            
            if 'Body_Names' in optimized_points_full.columns and 'Body_Names' not in final_output_columns:
                final_output_columns.append('Body_Names')
            
            if 'Body_Count' in optimized_points_full.columns and 'Body_Count' not in final_output_columns:
                final_output_columns.append('Body_Count')

            output_df = optimized_points_full[final_output_columns]

            if 'Body_Names' in output_df.columns:
                output_df = output_df.rename(columns={'Body_Names': 'Bodies_To_Scan_List'})

            if not output_df.columns.tolist():
                self.master.after(0, self._handle_optimization_error, "Please select at least one valid column for output.")
                return

            safe_jump = int(total_jumps)
            output_file_name = f"Optimized_Route_{len(optimized_names)}_J{safe_jump}_M{jump_range:.1f}LY.csv"
            
            output_file_path = os.path.join(APP_DATA_DIR, output_file_name)
            os.makedirs(APP_DATA_DIR, exist_ok=True)
            output_df.to_csv(output_file_path, index=False)
            
            save_last_output_path(output_file_path)

            with self.route_lock:
                self.current_route = [
                    {
                        'name': row[SYSTEM_NAME_COLUMN],
                        'status': STATUS_UNVISITED,
                        'coords': [float(row[X_COORD_COLUMN]), float(row[Y_COORD_COLUMN]), float(row[Z_COORD_COLUMN])],
                        'bodies_to_scan': row['Body_Names'] if 'Body_Names' in row else [],
                        'body_count': row['Body_Count'] if 'Body_Count' in row else 0
                    }
                    for _, row in optimized_points_full.iterrows()
                ]

                os.makedirs(BACKUP_FOLDER, exist_ok=True)
                if os.path.exists(ROUTE_STATUS_FILE):
                    try:
                        shutil.copy2(ROUTE_STATUS_FILE, os.path.join(BACKUP_FOLDER, f"route_status_backup_{int(time.time())}.json"))
                    except Exception:
                        pass
                save_route_status(self.current_route)
            
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
            error_message = f"An unexpected critical error occurred: {e}\nTraceback:\n{traceback.format_exc()}"
            self.master.after(0, 
                              self._complete_optimization_on_main_thread, 
                              0, 
                              0, 
                              "", 
                              "", 
                              False, 
                              error_message)

    def _group_systems_and_bodies(self, df):
        if 'System Name' not in df.columns:
            self.log("ERROR: CSV must contain a 'System Name' column for grouping.")
            return None

        body_column = None
        if 'Body Name' in df.columns:
            body_column = 'Body Name'
        elif 'Name' in df.columns:
            body_column = 'Name'
        
        if body_column:
            grouped_df = df.groupby('System Name').agg({
                'X': 'first',
                'Y': 'first',
                'Z': 'first',
                body_column: lambda x: list(x) if len(x) > 1 else []
            }).reset_index()
            
            grouped_df['Body_Count'] = grouped_df[body_column].apply(len)
            grouped_df = grouped_df.rename(columns={body_column: 'Body_Names'})
        else:
            grouped_df = df.groupby('System Name').agg({
                'X': 'first',
                'Y': 'first',
                'Z': 'first'
            }).reset_index()
            grouped_df['Body_Names'] = [[] for _ in range(len(grouped_df))]
            grouped_df['Body_Count'] = 0

        self.log(f"INFO: Systems grouped. Total unique systems for routing: {len(grouped_df)}")
        return grouped_df

if __name__ == '__main__':
    initial_settings = load_settings()
    ctk.set_appearance_mode(initial_settings.get('appearance_mode', 'Dark'))
    ctk.set_default_color_theme(initial_settings.get('color_theme', 'green'))

    root = ctk.CTk()
    app = RouteOptimizerApp(root)
    
    def on_closing():
        if app.journal_monitor:
            app.journal_monitor.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
