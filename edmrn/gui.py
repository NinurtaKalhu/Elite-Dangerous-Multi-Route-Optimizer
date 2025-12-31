import time
import pandas as pd
import tkinter as tk
import customtkinter as ctk
import webbrowser
from PIL import Image
from pathlib import Path
from edmrn.logger import get_logger
from edmrn.utils import resource_path

logger = get_logger('GUI')

class ManualWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("EDMRN - User Manual")
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
        ED Multi Route Navigation (EDMRN) v2.3.1 - User Manual
        =========================================================

        EDMRN optimizes your multi-system exploration/data collection routes 
        in Elite Dangerous for shortest distance and provides 
        in-game tracking with overlay.

        -----------------------------------------------------------------------
        TAB 1: ROUTE OPTIMIZATION
        -----------------------------------------------------------------------
        1. ROUTE DATA FILE (CSV):
           • Source: Exported system list from Elite Dangerous tools:
             - Spansh.co.uk: Galaxy plotter exports
           
           • REQUIRED COLUMNS:
             - 'System Name' (case sensitive)
             - 'X', 'Y', 'Z' coordinate columns
           
           • OPTIONAL: 'Body Name', 'Planet Class', etc.

        2. SHIP JUMP RANGE (LY):
           • Enter your current ship's maximum FSD jump range
           • Default: 70.0 LY (suitable for exploration ships)
           • This affects jump calculations and route efficiency

        3. STARTING SYSTEM (OPTIONAL):
           • If you want to start from a specific system
           • Enter exact system name as in CSV
           • Leave blank for auto-optimized starting point

        4. CSV COLUMN STATUS:
           • Shows which required columns are found
           • Green checkmarks = Found
           • Red X = Missing
           • All required columns must be present

        5. OPTIONAL COLUMNS BUTTON:
           • Click to select additional columns for output CSV
           • Only affects exported file, not optimization

        6. OPTIMIZE ROUTE AND START TRACKING:
           • Click to begin optimization process
           • Progress shown in output console
           • Automatically switches to Tracking tab when complete

        -----------------------------------------------------------------------
        TAB 2: ROUTE TRACKING
        -----------------------------------------------------------------------
        AUTO-TRACKING (Journal Monitoring):
           • EDMRN automatically monitors Elite Dangerous journal files
           • When you perform an FSD jump, system status updates automatically
           • Journal path auto-detected (can be changed in Settings)

        MANUAL TRACKING:
           • Click on system names in the list to update status
           • Three options: Visited (Green), Skipped (Red), Unvisited (Default)
           • Systems can be marked manually if auto-tracking fails

        3D MINI MAP:
           • Interactive 3D visualization of your route
           • Left-click on points to select systems
           • Scroll to zoom in/out
           • Click-drag to rotate view
           • Color coding:
             - Green: Visited systems
             - Red: Skipped systems
             - White: Unvisited systems
             - Yellow: Highlighted/selected system

        IN-GAME OVERLAY:
           • Transparent overlay shows critical info while playing
           • FEATURES:
             - Current system and status
             - Bodies to scan in current system
             - Next system in route
             - Progress statistics
             - Distance traveled
           
           • CONTROLS:
             - Press Ctrl+O to toggle visibility
             - Drag header to move overlay
             - Click X to hide (Ctrl+O to show again)
           
           • CONFIGURATION (in Settings tab):
             - Opacity: 50-100%
             - Size: Small/Medium/Large

        ACTION BUTTONS (Bottom of 3D Map):
           • COPY NEXT SYSTEM: Copies next unvisited system to clipboard
           • DATA FOLDER: Opens EDMRN data directory
           • OPEN EXCEL: Opens latest optimized route in default CSV viewer
           • LOAD BACKUP: Load previously saved routes from backup files

        STATISTICS PANEL:
           • Total Route Distance: Complete route length in LY
           • Traveled Distance: Distance covered so far
           • Average Jump Range: Calculated based on ship jump range

        -----------------------------------------------------------------------
        TAB 3: SETTINGS
        -----------------------------------------------------------------------
        OVERLAY SETTINGS:
           • START/STOP OVERLAY: Toggle in-game overlay
           • OPACITY: Adjust transparency (50-100%)
           • SIZE: Change overlay window size

        AUTO-SAVE SETTINGS:
           • INTERVAL: 1/5/10 minutes or Never
           • STATUS: Shows if auto-save is running
           • START/STOP: Control auto-save
           • SAVE NOW: Manual save button

        JOURNAL SETTINGS:
           • JOURNAL PATH: Auto-detected or manually set
           • CMDR SELECTION: Choose between multiple commanders
           • TEST BUTTON: Verify journal path is working
           • APPLY BUTTON: Save and restart journal monitor
           • REFRESH: Reload commander list

        APPEARANCE SETTINGS:
           • MODE: Dark, Light, or System theme
           • COLOR THEME: Green, Blue, or Dark Blue
           • APPLY THEME: Apply selected theme

        -----------------------------------------------------------------------
        KEYBOARD SHORTCUTS
        -----------------------------------------------------------------------
        Global Shortcuts (anywhere in EDMRN):
           • Ctrl+D or F12: Open Debug Console
           • Ctrl+O: Toggle In-Game Overlay (when Elite Dangerous is active)

        In-Game Overlay Shortcuts (when Elite Dangerous is focused):
           • Ctrl+O: Show/Hide overlay
           • Drag Header: Move overlay position

        -----------------------------------------------------------------------
        TROUBLESHOOTING
        -----------------------------------------------------------------------
        COMMON ISSUES:

        1. CSV FILE NOT LOADING:
           • Ensure file has required columns
           • Check column names are exact
           • Try opening in Excel and re-saving as CSV

        2. JOURNAL NOT DETECTED:
           • Make sure Elite Dangerous is running
           • Verify journal path in Settings
           • Check if you have multiple Elite installations

        3. OVERLAY NOT VISIBLE:
           • Press Ctrl+O to toggle
           • Check overlay is started in Settings
           • Ensure Elite Dangerous is in Windowed or Borderless mode

        4. 3D MAP NOT DISPLAYING:
           • Install matplotlib: pip install matplotlib
           • Check system has 3D acceleration enabled
           • Try reducing route size if too many systems

        5. PERFORMANCE ISSUES:
           • For large routes (>1000 systems), disable 3D map
           • Close other applications
           • Reduce overlay update frequency

        DEBUG CONSOLE:
           • Press Ctrl+D or F12 anytime
           • Shows detailed error information
           • Export logs for technical support
           • Monitor application performance

        -----------------------------------------------------------------------
        DATA MANAGEMENT
        -----------------------------------------------------------------------
        AUTOMATIC BACKUPS:
           • Route status automatically backed up
           • Manual backups via Load Backup button
           • Backups stored in: Documents/EDMRN_Route_Data/backups/

        DATA LOCATIONS:
           • App Data: Documents/EDMRN_Route_Data/
           • Settings: settings.json
           • Route Status: route_status.json
           • Logs: logs/ folder with daily files

        EXPORTING DATA:
           • Optimized routes saved as CSV in backups folder
           • Debug data export via Debug Console
           • Log files for troubleshooting

        -----------------------------------------------------------------------
        MULTI-COMMANDER SUPPORT
        -----------------------------------------------------------------------
        • EDMRN automatically detects all commanders
        • Switch between commanders in Settings
        • Each commander maintains separate route progress
        • Commander selection affects journal monitoring

        -----------------------------------------------------------------------
        SUPPORT & COMMUNITY
        -----------------------------------------------------------------------
        • GitHub: https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer
        • Discord: https://discord.gg/DWvCEXH7ae
        • Email: ninurtakalhu@gmail.com
        • Ko-fi: https://ko-fi.com/ninurtakalhu

        -----------------------------------------------------------------------
        CREDITS
        -----------------------------------------------------------------------
        Developed by: Ninurta Kalhu (S.C.)
        Special Thanks: Elite Dangerous Community, Beta Testers
        Libraries: CustomTkinter, Matplotlib, NumPy, SciPy, Python-TSP

        -----------------------------------------------------------------------
        FLY SAFE, COMMANDER! o7
        -----------------------------------------------------------------------
        """
        self.manual_textbox.insert("end", manual_text)
        self.manual_textbox.configure(state="disabled", 
                                      font=ctk.CTkFont(family="Consolas", size=11))

class AboutWindow(ctk.CTkToplevel):
    def __init__(self, master, open_link_callback, show_manual_callback):
        super().__init__(master)
        self.title("ED Multi Route Navigation (EDMRN)")
        self.open_link = open_link_callback
        self.show_manual = show_manual_callback
        
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
        
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(20, 10), sticky="ew")
        logo_frame.columnconfigure(0, weight=1)

        try:
            logo_path = resource_path('assets/explorer_icon.png')
            if Path(logo_path).exists():
                original_image = Image.open(logo_path)
                resized_image = original_image.resize((60, 60), Image.LANCZOS)
                app_logo = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(60, 60))
                logo_label = ctk.CTkLabel(logo_frame, image=app_logo, text="")
                logo_label.grid(row=0, column=0, pady=5)
                logo_label.image = app_logo
        except Exception:
            pass

        ctk.CTkLabel(self, text="ED Multi Route Navigation (EDMRN)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=1, column=0, pady=(0, 10))
        
        app_frame = ctk.CTkFrame(self, fg_color="transparent")
        app_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        app_frame.columnconfigure(0, weight=1)

        manual_btn = ctk.CTkButton(self, text="Show User Manual", command=self.show_manual, fg_color="#1E88E5", hover_color="#1565C0")
        manual_btn.grid(row=3, column=0, padx=20, pady=(15, 10), sticky="ew")

        about_link_frame = ctk.CTkFrame(self, fg_color="transparent")
        about_link_frame.grid(row=4, column=0, padx=20, pady=(15, 10), sticky="ew")
        about_link_frame.columnconfigure((0, 1, 2), weight=1)
        
        github_btn = ctk.CTkButton(about_link_frame, text="GitHub", command=lambda: self.open_link("https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer"))
        github_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        discord_btn = ctk.CTkButton(about_link_frame, text="Discord", command=lambda: self.open_link("https://discord.gg/DWvCEXH7ae"))
        discord_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        donation_btn = ctk.CTkButton(about_link_frame, text="Donate", command=lambda: self.open_link("https://ko-fi.com/ninurtakalhu"), fg_color="#E91E63", hover_color="#C2185B")
        donation_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self, text="Ninurta Kalhu (S.C.) Copyright (C) 2025 | All Rights Reserved.", font=ctk.CTkFont(size=10)).grid(row=5, column=0, pady=(5, 15))
        
        self.grab_set()

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
        
        backup_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
        
        for i, file_path in enumerate(backup_files):
            file_name = Path(file_path).name
            file_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(file_path).stat().st_mtime))
            file_size = f"{Path(file_path).stat().st_size / 1024:.1f} KB"
            
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
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select Backup CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=Paths.get_app_data_dir()
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
