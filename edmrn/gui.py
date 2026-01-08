import json
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from datetime import datetime
from pathlib import Path
import os
import ctypes
_hicon_cache = {}
def _load_hicon(path):
    try:
        p = str(path)
        if p in _hicon_cache:
            return _hicon_cache[p]
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        hicon = ctypes.windll.user32.LoadImageW(0, p, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
        _hicon_cache[p] = hicon
        return hicon
    except Exception:
        return None
from edmrn.logger import get_logger
from edmrn.utils import resource_path
logger = get_logger('GUI')
class ProcessingDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_cancel=None):
        if hasattr(parent, 'root'):
            parent_window = parent.root
            self.app = parent
        else:
            parent_window = parent
            self.app = None
        super().__init__(parent_window)
        self.title("Processing")
        self.resizable(False, False)
        self.transient(parent_window)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self._on_cancel = on_cancel
        self._cancelled = False
        self._dot_state = 0
        if self.app and hasattr(self.app, 'theme_manager'):
            theme_colors = self.app.theme_manager.get_theme_colors()
        else:
            theme_colors = {
                'frame': '#2b2b2b',
                'primary': '#0078d7',
                'secondary': '#1e1e1e',
                'text': '#ffffff'
            }
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        frame = ctk.CTkFrame(self, fg_color=theme_colors['frame'], border_color=theme_colors['primary'], border_width=1)
        frame.pack(padx=20, pady=20, fill='both', expand=True)
        self.status_label = ctk.CTkLabel(frame, text="Processing...", anchor='w', text_color=theme_colors['text'], font=ctk.CTkFont(family="Segoe UI", size=12))
        self.status_label.pack(fill='x', pady=(0, 10))
        self.progress_bar = ctk.CTkProgressBar(frame, width=360, progress_color=theme_colors['primary'], fg_color=theme_colors['secondary'])
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.set(0.0)
        self._indeterminate = True
        self._animate_id = None
        self.cancel_button = ctk.CTkButton(frame, text="Cancel", fg_color="#FF6B6B", hover_color="#CC5555", command=self._do_cancel, height=32)
        self.cancel_button.pack(pady=(5, 0))
        try:
            parent_window.update_idletasks()
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (400 // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (150 // 2)
            self.geometry(f'400x150+{x}+{y}')
        except Exception:
            pass
        self._start_spinner()
    def _do_cancel(self):
        self._cancelled = True
        if callable(self._on_cancel):
            try:
                self._on_cancel()
            except Exception:
                pass
        self.status_label.configure(text="Cancelling...")
        self.cancel_button.configure(state='disabled')
    def update(self, status_text: str = None, fraction: float = None):
        if status_text is not None:
            self.status_label.configure(text=status_text)
        if fraction is None:
            if not self._indeterminate:
                self._indeterminate = True
                self.progress_bar.set(0.0)
                self._start_spinner()
        else:
            if self._indeterminate:
                self._indeterminate = False
                self._stop_spinner()
            try:
                self.progress_bar.set(max(0.0, min(1.0, float(fraction))))
            except Exception:
                pass
    def _start_spinner(self):
        def spin():
            self._dot_state = (self._dot_state + 1) % 4
            dots = '.' * self._dot_state
            try:
                self.status_label.configure(text=self.status_label.cget('text').split('...')[0] + dots)
            except Exception:
                pass
            self._animate_id = self.after(400, spin)
        spin()
    def _stop_spinner(self):
        if self._animate_id:
            try:
                self.after_cancel(self._animate_id)
            except Exception:
                pass
            self._animate_id = None
    def close(self):
        try:
            self._stop_spinner()
            self.grab_release()
            self.destroy()
        except Exception:
            pass
class ManualWindow(ctk.CTkToplevel):
    def __init__(self, master):
        if hasattr(master, 'root'):
            parent_window = master.root
            self.app = master
        else:
            parent_window = master
            self.app = None
        super().__init__(parent_window)
        self.title("EDMRN - User Manual")
        if self.app and hasattr(self.app, 'theme_manager'):
            self.theme_colors = self.app.theme_manager.get_theme_colors()
        else:
            self.theme_colors = {
                'frame': '#2E2E2E',
                'primary': '#FF8C00',
                'secondary': '#666666',
                'text': '#E0E0E0',
                'background': '#212121'
            }
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                self.iconbitmap(ico_path)
                logger.info(f"ManualWindow: iconbitmap set -> {ico_path}")
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
                            logger.info("ManualWindow: WM_SETICON applied for ICO")
                    except Exception as e:
                        logger.debug(f"ManualWindow: WM_SETICON failed: {e}")
        except Exception as e:
            logger.debug(f"ManualWindow: iconbitmap failed: {e}")
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                self._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.wm_iconphoto(True, self._title_icon)
                except Exception:
                    self.iconphoto(False, self._title_icon)
                logger.info(f"ManualWindow: iconphoto set -> {logo_path}")
                if os.name == 'nt':
                    try:
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = ctypes.windll.user32.LoadImageW(0, str(logo_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            logger.info("ManualWindow: WM_SETICON applied for PNG")
                    except Exception as e:
                        logger.debug(f"ManualWindow: WM_SETICON PNG failed: {e}")
        except Exception as e:
            logger.debug(f"ManualWindow: iconphoto failed: {e}")
        self.geometry("700x550")
        self.resizable(False, False)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        try:
            parent_window.update_idletasks()
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (700 // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (550 // 2)
            self.geometry(f'+{x}+{y}')
        except Exception:
            pass
        header = ctk.CTkFrame(self, fg_color=self.theme_colors['background'])
        header.pack(fill="x", padx=20, pady=(15, 10))
        header.columnconfigure(1, weight=1)
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                original_image = Image.open(logo_path)
                resized_image = original_image.resize((40, 40), Image.LANCZOS)
                app_logo = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(40, 40))
                logo_label = ctk.CTkLabel(header, image=app_logo, text="")
                logo_label.grid(row=0, column=0, padx=(0, 10), pady=5)
                logo_label.image = app_logo
        except Exception:
            pass
        ctk.CTkLabel(header, text="ED Multi Route Navigation (EDMRN) - User Manual",
                     font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color=self.theme_colors['primary']).grid(row=0, column=1, sticky="w")
        self.manual_textbox = ctk.CTkTextbox(self, width=650, height=450, fg_color=self.theme_colors['frame'], text_color=self.theme_colors['text'], border_color=self.theme_colors['primary'], border_width=1)
        self.manual_textbox.pack(padx=20, pady=10, fill="both", expand=True)
        self._insert_manual_content()
        self.grab_set()
        try:
            self.bind('<Map>', lambda e: self._schedule_reapply_icons())
            self.bind('<FocusIn>', lambda e: self._schedule_reapply_icons())
        except Exception:
            pass
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
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.iconbitmap(ico_path)
                except Exception:
                    pass
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon(ico_path)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            if not getattr(self, '_icon_set_logged', False):
                                logger.info("ManualWindow: WM_SETICON re-applied for ICO")
                                self._icon_set_logged = True
                            else:
                                logger.debug("ManualWindow: WM_SETICON re-applied for ICO (suppressed info)")
                    except Exception as e:
                        logger.debug(f"ManualWindow: WM_SETICON reapply failed: {e}")
        except Exception:
            pass
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                self._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.wm_iconphoto(True, self._title_icon)
                except Exception:
                    self.iconphoto(False, self._title_icon)
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon(logo_path)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            if not getattr(self, '_icon_set_logged', False):
                                logger.info("ManualWindow: WM_SETICON re-applied for PNG")
                                self._icon_set_logged = True
                            else:
                                logger.debug("ManualWindow: WM_SETICON re-applied for PNG (suppressed info)")
                    except Exception as e:
                        logger.debug(f"ManualWindow: WM_SETICON PNG reapply failed: {e}")
        except Exception:
            pass
        finally:
            self._reapply_pending = False
    def _reapply_icons(self, event=None):
        return self._schedule_reapply_icons()
    def _insert_manual_content(self):
        manual_text = """
        =========================================================
        ED Multi Route Navigation (EDMRN) v3.0 - User Manual
        =========================================================
        EDMRN v3.0 optimizes multi-system exploration/exobiology routes
        in Elite Dangerous using advanced TSP algorithms with complete
        modular architecture and 11 Powerplay faction themes.
        -----------------------------------------------------------------------
        TAB 1: ROUTE OPTIMIZATION
        -----------------------------------------------------------------------
        1. ROUTE DATA FILE (CSV):
           • Source: Exported system list from:
             - Spansh.co.uk: Galaxy plotter (recommended)
             - EDSM, EDDB, EDDiscovery exports
           • REQUIRED COLUMNS:
             - 'System Name' (destination system)
             - 'X', 'Y', 'Z' (galactic coordinates)
           • OPTIONAL:
             - 'Body Name' for biological/geological signals
        2. SHIP JUMP RANGE (LY):
           • Current ship's maximum FSD jump range
           • Critical for accurate route optimization
           • Updated in real-time for Neutron Highway sync
        3. STARTING SYSTEM (OPTIONAL):
           • Begin route from specific system
           • Leave blank for automatic optimization
        4. CSV COLUMN STATUS:
           • Real-time validation of CSV structure
           • ✓ Green = Column found and valid
           • ✗ Red = Column missing or invalid
           • All 5 required columns must be present!
        5. OPTIONAL COLUMNS (NEW v3.0):
           • Select additional CSV columns for export
           • Expandable list for custom data preservation
        6. OPTIMIZE ROUTE AND START TRACKING:
           • Triggers TSP optimization engine
           • Auto-creates timestamped backup folder
           • Automatically starts journal monitoring
           • Auto-switches to Route Tracking tab
        -----------------------------------------------------------------------
        TAB 2: NEUTRON HIGHWAY (New v3.0 Architecture)
        -----------------------------------------------------------------------
        🌟 ADVANCED NEUTRON ROUTING:
           • Calculate optimized neutron star jump routes
           • Enter source and destination systems
           • Supports x4 and x6 (Caspian) FSD boost
           • Real-time waypoint navigation with clipboard integration
        
        CONTROLS:
           • From/To System: Your current location and destination
           • Jump Range: Your ship's FSD range
           • FSD Boost: Select boost type for calculations
           • Navigation: < > buttons for step-by-step waypoint following
           
        STATISTICS:
           • Distance calculated
           • Jump efficiency metrics
           • Progress tracking with waypoint numbers
           • Real-time neutron route output
           
        AUTO-TRACKING:
           • Journal monitor detects neutron jumps automatically
           • Current waypoint updates as you jump
           • Distance-to-destination counter in real-time
        -----------------------------------------------------------------------
        TAB 3: ROUTE TRACKING
        -----------------------------------------------------------------------
        AUTO-TRACKING (Journal Monitoring):
           • EDMRN monitors Elite Dangerous journal automatically
           • System status updates in real-time as you jump
           • Multi-commander support (auto-detected)
           • Path auto-detected (configurable in Settings)
           
        MANUAL TRACKING:
           • Click systems to manually update status
           • Status options: Visited (Green), Skipped (Orange), Unvisited
           • Useful if auto-tracking misses a jump
           
        3D INTERACTIVE MAP:
           • Real-time 3D route visualization
           • Controls:
             - Mouse Wheel: Zoom in/out
             - Click+Drag: Rotate view
             - Left-Click: Select system for details
           • Color Coding:
             - Green: Visited (successfully scanned)
             - Orange: Skipped (passed over)
             - Gray: Unvisited (pending)
             
        ROUTE STATISTICS PANEL:
           • Total Route Distance: Complete LY distance
           • Traveled Distance: Current progress
           • Remaining Distance: Distance left
           • Systems Visited/Skipped/Remaining: Progress breakdown
           • Real-time progress percentage
           
        IN-GAME OVERLAY (Ctrl+O):
           • Transparent overlay in Elite Dangerous window
           • Features:
             - Current system + status
             - Next target system (highlighted)
             - Biological/geological signals to scan
             - Progress: X of Y visited
             - Distance: Traveled / Remaining
             - Refresh rate: ~500ms updates
           • Configuration in Settings:
             - Opacity: 50-100%
             - Size: Small (800x400), Medium (1000x500), Large (1200x600)
           • Auto-hides when Elite unfocused
           
        ACTION BUTTONS:
           • COPY NEXT: Copies next unvisited system name to clipboard
           • DATA FOLDER: Opens Documents/EDMRN_Route_Data/
           • OPEN EXCEL: Launch optimized route in default viewer
           • LOAD BACKUP: Restore previous route+progress from backup
           • QUICK SAVE: One-click backup of current progress
        -----------------------------------------------------------------------
        TAB 4: SETTINGS (Enhanced v3.0)
        -----------------------------------------------------------------------
        🎨 THEME SETTINGS (New v3.0):
           • 11 Elite Dangerous Powerplay faction themes
           • Each theme fully themed - NO gray areas!
           • Themes include:
             - Elite Dangerous (Orange) - Default
             - Aisling Duval (Blue)
             - Archon Delaine (Lime Green)
             - Arissa Lavigny-Duval (Purple)
             - Denton Patreus (Gold)
             - Edmund Mahon (Cyan)
             - Felicia Winters (Light Blue)
             - Li Yong Rui (Red)
             - Pranav Antal (Gold)
             - Zachary Hudson (Lime)
             - Zemina Torval (Indigo)
           • Smart Restart: Auto-restarts app to apply theme
           • All UI elements adapt to faction colors
           • Window geometry preserved across restarts
           
        ⚙️ OVERLAY SETTINGS:
           • START/STOP OVERLAY: Toggle in-game display
           • OPACITY SLIDER: 50-100% transparency control
           • SIZE OPTIONS: Small/Medium/Large overlays
           • Auto-minimize when unfocused
           
        💾 AUTO-SAVE SETTINGS:
           • INTERVAL: 1/5/10 minutes or Never
           • RUNNING STATUS: Shows auto-save state
           • START/STOP: Manual control
           • SAVE NOW: Immediate backup creation
           • Next Save Timer: Countdown display
           
        📝 JOURNAL MONITORING:
           • AUTO-DETECT: Scans for Elite journal folder
           • MANUAL PATH: Set custom journal location
           • CMDR SELECTOR: Switch between commanders
           • TEST PATH: Verify journal access
           • Path Status: Shows detected/configured path
           
        -----------------------------------------------------------------------
        BACKUP SYSTEM (Rebuilt v3.0)
        -----------------------------------------------------------------------
        AUTOMATIC BACKUPS:
           • Every optimization creates timestamped folder:
             Documents/EDMRN_Route_Data/backups/Route_[systems]_[timestamp]/
           • Contains:
             - optimized_route.csv (your TSP-optimized route)
             - route_status.json (visited/skipped status snapshot)
             
        LOAD BACKUP:
           • Restore previous route + progress instantly
           • No data loss between app sessions
           • Perfect for multi-phase expeditions
           • Backup folder automatically detected/managed
           
        QUICK SAVE (New v3.0):
           • One-click progress checkpoint creation
           • Folder: backups/QuickSave_[X]of[Y]_[timestamp]/
           • Use before:
             - Closing application
             - Switching to different route
             - Testing alternate optimization
             - Long expedition checkpoints
             
        -----------------------------------------------------------------------
        DEBUG SYSTEM (Professional v3.0)
        -----------------------------------------------------------------------
        OPEN DEBUG CONSOLE:
           • Press Ctrl+D or F12 anywhere in EDMRN
           • Real-time error tracking and diagnostics
           • Error categories: GUI, Thread, I/O, Network
           • Export debug data for support
           • Stack traces for troubleshooting
        -----------------------------------------------------------------------
        KEYBOARD SHORTCUTS
        -----------------------------------------------------------------------
        Global Shortcuts:
           • Ctrl+D or F12: Open Debug Console
           • Ctrl+O: Toggle In-Game Overlay (when Elite Dangerous active)
           
        3D Map Controls:
           • Mouse Wheel: Zoom in/out
           • Click+Drag: Rotate visualization
           • Left-Click: Select system
           
        -----------------------------------------------------------------------
        TROUBLESHOOTING (v3.0 Updates)
        -----------------------------------------------------------------------
        1. CSV NOT LOADING:
           • Verify: System Name, X/Y/Z columns exist
           • Ensure no duplicate column names
           • Re-save CSV in Excel before importing
           
        2. JOURNAL NOT DETECTED:
           • Check Settings → Journal → Test Path
           • Ensure Elite Dangerous uses Windowed/Borderless
           • Verify journal files exist in detected folder
           
        3. OVERLAY NOT SHOWING:
           • Press Ctrl+O to toggle (must be in Elite window)
           • Check Settings → Overlay → Start Overlay is enabled
           • Verify Elite is in Windowed or Borderless mode
           
        4. THEME CHANGE NOT APPLYING:
           • EDMRN automatically restarts on theme change
           • Wait for app to restart (5-10 seconds)
           • Check Settings for new theme name
           
        5. BACKUP LOADING ERRORS:
           • Verify backup folder contains both files:
             - optimized_route.csv
             - route_status.json
           • If missing, recreate with Quick Save
           
        6. PERFORMANCE ON LARGE ROUTES:
           • Routes >1000 systems: Disable 3D map view
           • Close overlay during active play
           • Reduce auto-save interval
           
        -----------------------------------------------------------------------
        DATA LOCATIONS (v3.0)
        -----------------------------------------------------------------------
        • Main Data: Documents/EDMRN_Route_Data/
        • Backups: Documents/EDMRN_Route_Data/backups/
        • Settings: Documents/EDMRN_Route_Data/config.json
        • Logs: EDMRN_Route_Data/logs/ (daily files)
        • Themes: edmrn/themes/ (11 JSON theme files)
        
        -----------------------------------------------------------------------
        MULTI-COMMANDER SUPPORT
        -----------------------------------------------------------------------
        • Auto-detects all Elite Dangerous commanders
        • Switch in Settings → Journal → Commander Selector
        • Each commander has separate route progress
        • Journal monitoring respects commander selection
        
        -----------------------------------------------------------------------
        v3.0 NEW FEATURES SUMMARY
        -----------------------------------------------------------------------
        
        ✨ Complete modular architecture (extracted modules)
        ✨ 11 Powerplay faction-themed color schemes
        ✨ Redesigned Neutron Highway with advanced routing
        ✨ Completely restructured backup system
        ✨ Enhanced overlay system with better detection
        ✨ Numerous performance optimizations and bug fixes
        
        -----------------------------------------------------------------------
        SUPPORT & COMMUNITY
        -----------------------------------------------------------------------
        • GitHub: https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer
        • Discord: https://discord.gg/DWvCEXH7ae
        • Email: ninurtakalhu@gmail.com
        • Ko-fi: https://ko-fi.com/ninurtakalhu
        
        -----------------------------------------------------------------------
        DEVELOPED BY
        -----------------------------------------------------------------------
        Ninurta Kalhu (S.C.) - Solo Developer

        ### 🙏 Contributors

        - Ozgur KARATAS (Ta2ozg) - Contributor
        - Aydin AKYUZ - Contributor / Beta Tester https://www.youtube.com/@drizzydnt
        
        Thanks to Elite Dangerous community, Frontier Developments,
        and all beta testers!
        
        -----------------------------------------------------------------------
        FLY SAFE, COMMANDER! o7
        "In the black, every lightyear counts."
        -----------------------------------------------------------------------
        """
        self.manual_textbox.insert("end", manual_text)
        self.manual_textbox.configure(state="disabled",
                                      font=ctk.CTkFont(family="Consolas", size=12), text_color=self.theme_colors['text'])
class AboutWindow(ctk.CTkToplevel):
    def __init__(self, master, open_link_callback, show_manual_callback):
        if hasattr(master, 'root'):
            parent_window = master.root
            self.app = master
        else:
            parent_window = master
            self.app = None
        super().__init__(parent_window)
        self.title("ED Multi Route Navigation (EDMRN)")
        if self.app and hasattr(self.app, 'theme_manager'):
            self.theme_colors = self.app.theme_manager.get_theme_colors()
        else:
            self.theme_colors = {
                'frame': '#2E2E2E',
                'primary': '#FF8C00',
                'secondary': '#666666',
                'text': '#E0E0E0',
                'background': '#212121'
            }
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                self.iconbitmap(ico_path)
                logger.info(f"AboutWindow: iconbitmap set -> {ico_path}")
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
                            logger.info("AboutWindow: WM_SETICON applied for ICO")
                    except Exception as e:
                        logger.debug(f"AboutWindow: WM_SETICON failed: {e}")
        except Exception as e:
            logger.debug(f"AboutWindow: iconbitmap failed: {e}")
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                self._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.wm_iconphoto(True, self._title_icon)
                except Exception:
                    self.iconphoto(False, self._title_icon)
                logger.info(f"AboutWindow: iconphoto set -> {logo_path}")
                if os.name == 'nt':
                    try:
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = ctypes.windll.user32.LoadImageW(0, str(logo_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            logger.info("AboutWindow: WM_SETICON applied for PNG")
                    except Exception as e:
                        logger.debug(f"AboutWindow: WM_SETICON PNG failed: {e}")
        except Exception as e:
            logger.debug(f"AboutWindow: iconphoto failed: {e}")
        self.open_link = open_link_callback
        self.show_manual = show_manual_callback
        window_width = 500
        window_height = 600
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(False, False)
        try:
            parent_window.update_idletasks()
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (window_width // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (window_height // 2)
            self.geometry(f'+{x}+{y}')
        except Exception:
            pass
        self.grid_columnconfigure(0, weight=1)
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                original_image = Image.open(logo_path)
                resized_image = original_image.resize((80, 80), Image.LANCZOS)
                app_logo = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(80, 80))
                logo_label = ctk.CTkLabel(self, image=app_logo, text="", fg_color="transparent")
                logo_label.grid(row=0, column=0, pady=(30, 15))
                logo_label.image = app_logo
        except Exception:
            pass
        ctk.CTkLabel(
            self,
            text="Elite Dangerous Multi-Route Navigation",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme_colors['text'],
            justify="center"
        ).grid(row=1, column=0, pady=(0, 5))
        ctk.CTkLabel(
            self,
            text="EDMRN",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=self.theme_colors['primary'],
            justify="center"
        ).grid(row=2, column=0, pady=(0, 20))
        info_text = """
    Version 3.0 - GPL3 Licensed
January 2026
Developed by CMDR Ninurta Kalhu
Elite Dangerous © Frontier Developments plc.
*This tool is not affiliated with, endorsed by, 
or connected to Frontier Developments plc.*
Thank you to all contributors and the Elite Dangerous exploration community!
Fly safe, Commander! o7
        """.strip()
        info_frame = ctk.CTkFrame(self, fg_color=self.theme_colors['frame'], border_color=self.theme_colors['primary'], border_width=1)
        info_frame.grid(row=3, column=0, padx=30, pady=10, sticky="nsew")
        info_frame.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            justify="center",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme_colors['text'],
            wraplength=440
        ).grid(row=0, column=0, pady=10)
        manual_btn = ctk.CTkButton(
            self,
            text="Show User Manual",
            command=self.show_manual,
            fg_color=self.theme_colors['primary'],
            hover_color=self.theme_colors.get('primary_hover', self.theme_colors['primary']),
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=40
        )
        manual_btn.grid(row=4, column=0, padx=50, pady=(20, 10), sticky="ew")
        link_frame = ctk.CTkFrame(self, fg_color="transparent")
        link_frame.grid(row=5, column=0, padx=50, pady=10, sticky="ew")
        link_frame.columnconfigure((0, 1, 2), weight=1)
        github_btn = ctk.CTkButton(
            link_frame,
            text="GitHub",
            command=lambda: self.open_link("https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer"),
            fg_color=self.theme_colors['secondary'],
            hover_color=self.theme_colors.get('secondary_hover', self.theme_colors['secondary']),
            border_color=self.theme_colors['primary'],
            border_width=1,
            text_color=self.theme_colors['primary'],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=35
        )
        github_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        discord_btn = ctk.CTkButton(
            link_frame,
            text="Discord",
            command=lambda: self.open_link("https://discord.gg/DWvCEXH7ae"),
            fg_color=self.theme_colors['secondary'],
            hover_color=self.theme_colors.get('secondary_hover', self.theme_colors['secondary']),
            border_color=self.theme_colors['primary'],
            border_width=1,
            text_color=self.theme_colors['primary'],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=35
        )
        discord_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        donation_btn = ctk.CTkButton(
            link_frame,
            text="Donate",
            command=lambda: self.open_link("https://ko-fi.com/ninurtakalhu"),
            fg_color="#FF5E5B",
            hover_color="#E04E4B",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=35
        )
        donation_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(
            self,
            text="© 2025-2026 Ninurta Kalhu (S.C.) | All Rights Reserved (Licence AGPL-3)",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme_colors['primary'],
        ).grid(row=6, column=0, pady=(20, 15))
        try:
            self.bind('<Map>', lambda e: self._schedule_reapply_icons())
            self.bind('<FocusIn>', lambda e: self._schedule_reapply_icons())
        except Exception:
            pass
        self.grab_set()
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
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.iconbitmap(ico_path)
                except Exception:
                    pass
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon(ico_path)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            if not getattr(self, '_icon_set_logged', False):
                                logger.info("AboutWindow: WM_SETICON re-applied for ICO")
                                self._icon_set_logged = True
                            else:
                                logger.debug("AboutWindow: WM_SETICON re-applied for ICO (suppressed info)")
                    except Exception as e:
                        logger.debug(f"AboutWindow: WM_SETICON reapply failed: {e}")
        except Exception:
            pass
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                self._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.wm_iconphoto(True, self._title_icon)
                except Exception:
                    self.iconphoto(False, self._title_icon)
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon(logo_path)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            if not getattr(self, '_icon_set_logged', False):
                                logger.info("AboutWindow: WM_SETICON re-applied for PNG")
                                self._icon_set_logged = True
                            else:
                                logger.debug("AboutWindow: WM_SETICON re-applied for PNG (suppressed info)")
                    except Exception as e:
                        logger.debug(f"AboutWindow: WM_SETICON PNG reapply failed: {e}")
        except Exception:
            pass
        finally:
            self._reapply_pending = False
    def _reapply_icons(self, event=None):
        return self._schedule_reapply_icons()
class BackupSelectionWindow(ctk.CTkToplevel):
    def __init__(self, master, backup_folders, load_callback):
        if hasattr(master, 'root'):
            parent_window = master.root
            self.app = master
        else:
            parent_window = master
            self.app = None
        super().__init__(parent_window)
        self.title("Select Backup Route")
        self.load_callback = load_callback
        self.geometry("800x550")
        self.resizable(True, True)
        if self.app and hasattr(self.app, 'theme_manager'):
            self.theme_colors = self.app.theme_manager.get_theme_colors()
        else:
            self.theme_colors = {
                'frame': '#2E2E2E',
                'primary': '#FF8C00',
                'secondary': '#666666',
                'text': '#E0E0E0',
                'background': '#212121'
            }
        try:
            parent_window.update_idletasks()
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (800 // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (550 // 2)
            self.geometry(f'+{x}+{y}')
        except Exception:
            pass
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            self,
            text="Select Backup Route to Load",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.theme_colors['primary']
        ).grid(row=0, column=0, padx=20, pady=(20, 10))
        ctk.CTkLabel(
            self,
            text="Select a backup folder to load both the route CSV and your progress",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme_colors['text']
        ).grid(row=1, column=0, padx=20, pady=(0, 15))
        header_frame = ctk.CTkFrame(self, fg_color=self.theme_colors['frame'], border_color=self.theme_colors['primary'], border_width=2, corner_radius=8)
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=0, minsize=30)
        header_frame.grid_columnconfigure(1, weight=3, minsize=200)
        header_frame.grid_columnconfigure(2, weight=1, minsize=80)
        header_frame.grid_columnconfigure(3, weight=1, minsize=80)
        header_frame.grid_columnconfigure(4, weight=1, minsize=80)
        header_frame.grid_columnconfigure(5, weight=1, minsize=60)
        ctk.CTkLabel(header_frame, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.theme_colors['primary'], width=30).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(header_frame, text="Route Name", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.theme_colors['primary']).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(header_frame, text="Systems", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.theme_colors['primary']).grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkLabel(header_frame, text="Progress", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.theme_colors['primary']).grid(row=0, column=3, padx=5, pady=5)
        ctk.CTkLabel(header_frame, text="Modified", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.theme_colors['primary']).grid(row=0, column=4, padx=5, pady=5)
        ctk.CTkLabel(header_frame, text="Status", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.theme_colors['primary']).grid(row=0, column=5, padx=5, pady=5)
        self.scrollable_frame = ctk.CTkScrollableFrame(self, height=300, fg_color=self.theme_colors['background'], border_color=self.theme_colors['primary'], border_width=1, corner_radius=8)
        self.scrollable_frame.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=0)
        self.scrollable_frame.grid_columnconfigure(1, weight=3)
        self.scrollable_frame.grid_columnconfigure(2, weight=1)
        self.scrollable_frame.grid_columnconfigure(3, weight=1)
        self.scrollable_frame.grid_columnconfigure(4, weight=1)
        self.scrollable_frame.grid_columnconfigure(5, weight=1)
        self.selected_folder = tk.StringVar()
        self.backup_folders = backup_folders
        self._populate_backup_list()
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        manual_btn = ctk.CTkButton(
            button_frame,
            text="📁 Manual Select",
            command=self._manual_select_folder,
            height=28,
            width=120,
            fg_color=self.theme_colors['secondary'],
            hover_color=self.theme_colors.get('secondary_hover', self.theme_colors['secondary']),
            border_color=self.theme_colors['primary'],
            border_width=1,
            text_color=self.theme_colors['primary'],
            font=ctk.CTkFont(family="Segoe UI", size=10)
        )
        manual_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="✕ Cancel",
            command=self.destroy,
            height=28,
            width=120,
            fg_color=self.theme_colors['secondary'],
            hover_color=self.theme_colors.get('secondary_hover', self.theme_colors['secondary']),
            text_color=self.theme_colors['text'],
            font=ctk.CTkFont(family="Segoe UI", size=10)
        )
        cancel_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        load_btn = ctk.CTkButton(
            button_frame,
            text="✅ Load Selected",
            command=self._load_selected,
            height=28,
            width=120,
            fg_color=self.theme_colors['primary'],
            hover_color=self.theme_colors.get('primary_hover', self.theme_colors['primary']),
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=10)
        )
        load_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        if backup_folders:
            self.selected_folder.set(backup_folders[0])
        try:
            self.bind('<Map>', lambda e: self._schedule_reapply_icons())
            self.bind('<FocusIn>', lambda e: self._schedule_reapply_icons())
        except Exception:
            pass
        self.grab_set()
        self.transient(parent_window)
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
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.iconbitmap(ico_path)
                except Exception:
                    pass
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon(ico_path)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            if not getattr(self, '_icon_set_logged', False):
                                logger.info("BackupSelectionWindow: WM_SETICON re-applied for ICO")
                                self._icon_set_logged = True
                            else:
                                logger.debug("BackupSelectionWindow: WM_SETICON re-applied for ICO (suppressed info)")
                    except Exception as e:
                        logger.debug(f"BackupSelectionWindow: WM_SETICON reapply failed: {e}")
        except Exception:
            pass
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                self._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.wm_iconphoto(True, self._title_icon)
                except Exception:
                    self.iconphoto(False, self._title_icon)
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon(logo_path)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            if not getattr(self, '_icon_set_logged', False):
                                logger.info("BackupSelectionWindow: WM_SETICON re-applied for PNG")
                                self._icon_set_logged = True
                            else:
                                logger.debug("BackupSelectionWindow: WM_SETICON re-applied for PNG (suppressed info)")
                    except Exception as e:
                        logger.debug(f"BackupSelectionWindow: WM_SETICON PNG reapply failed: {e}")
        except Exception:
            pass
        finally:
            self._reapply_pending = False
    def _reapply_icons(self, event=None):
        return self._schedule_reapply_icons()
    def _populate_backup_list(self):
        self.backup_folders.sort(
            key=lambda x: Path(x).stat().st_mtime if Path(x).exists() else 0,
            reverse=True
        )
        for i, folder_path in enumerate(self.backup_folders):
            folder = Path(folder_path)
            if not folder.exists() or not folder.is_dir():
                continue
            folder_name = folder.name
            if len(folder_name) > 25:
                folder_name = folder_name[:22] + "..."
            csv_files = list(folder.glob("*.csv"))
            csv_file = csv_files[0] if csv_files else None
            status_file = folder / "route_status.json"
            has_csv = csv_file is not None and csv_file.exists()
            has_status = status_file.exists()
            system_count = "?"
            if has_csv:
                try:
                    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        system_count = str(len(lines) - 1)
                except Exception:
                    system_count = "?"
            progress_text = "No data"
            progress_color = self.theme_colors['text']
            if has_status:
                try:
                    with open(status_file, 'r', encoding='utf-8') as f:
                        status_data = json.load(f)
                    if isinstance(status_data, list):
                        visited = sum(1 for item in status_data if isinstance(item, dict) and item.get('status', '').lower() == 'visited')
                        total = len(status_data)
                        progress_text = f"{visited}/{total}"
                        if total > 0:
                            pct = int((visited / total) * 100)
                            if pct == 0:
                                progress_color = self.theme_colors['text']
                            elif pct < 50:
                                progress_color = "#FFA500"
                            elif pct < 90:
                                progress_color = "#FFD700"
                            else:
                                progress_color = "#4CAF50"
                except Exception:
                    progress_text = "Error"
                    progress_color = "#FF6B6B"
            try:
                mtime = folder.stat().st_mtime
                modified_date = datetime.fromtimestamp(mtime).strftime('%m-%d')
            except Exception:
                modified_date = "Unknown"
            if has_csv and has_status:
                status_icon = "✅"
                status_color = "#4CAF50"
            elif has_csv:
                status_icon = "📝"
                status_color = "#FFA500"
            else:
                status_icon = "❌"
                status_color = "#FF6B6B"
            row_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=self.theme_colors['secondary'] if i % 2 == 0 else self.theme_colors['frame'], height=30, corner_radius=4)
            row_frame.grid(row=i, column=0, columnspan=6, padx=2, pady=1, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=0, minsize=30)
            row_frame.grid_columnconfigure(1, weight=3, minsize=200)
            row_frame.grid_columnconfigure(2, weight=1, minsize=80)
            row_frame.grid_columnconfigure(3, weight=1, minsize=80)
            row_frame.grid_columnconfigure(4, weight=1, minsize=80)
            row_frame.grid_columnconfigure(5, weight=1, minsize=60)
            row_frame.grid_propagate(False)
            radio = ctk.CTkRadioButton(row_frame, text="", variable=self.selected_folder, value=folder_path, width=16, height=16,
                                     radiobutton_width=16, radiobutton_height=16,
                                     border_color=self.theme_colors['primary'],
                                     fg_color=self.theme_colors['primary'],
                                     hover_color=self.theme_colors.get('primary_hover', self.theme_colors['primary']))
            radio.grid(row=0, column=0, padx=5, pady=0)
            ctk.CTkLabel(row_frame, text=folder_name, font=ctk.CTkFont(size=11), text_color=self.theme_colors['text'], anchor="w").grid(row=0, column=1, padx=5, pady=3, sticky="w")
            ctk.CTkLabel(row_frame, text=system_count, font=ctk.CTkFont(size=11), text_color=self.theme_colors['text']).grid(row=0, column=2, padx=5, pady=3)
            ctk.CTkLabel(row_frame, text=progress_text, font=ctk.CTkFont(size=11), text_color=progress_color).grid(row=0, column=3, padx=5, pady=3)
            ctk.CTkLabel(row_frame, text=modified_date, font=ctk.CTkFont(size=11), text_color=self.theme_colors['text']).grid(row=0, column=4, padx=5, pady=3)
            ctk.CTkLabel(row_frame, text=status_icon, font=ctk.CTkFont(size=12), text_color=status_color).grid(row=0, column=5, padx=5, pady=3)
    def _manual_select_folder(self):
        from tkinter import filedialog
        folder_path = filedialog.askdirectory(
            title="Select Backup Folder",
            initialdir=Path(self.backup_folders[0]).parent if self.backup_folders else "."
        )
        if folder_path:
            folder = Path(folder_path)
            csv_files = list(folder.glob("*.csv"))
            if not csv_files:
                tk.messagebox.showwarning(
                    "Warning",
                    f"No CSV file found in:\n{folder_path}\n\n"
                    "Please select a folder containing a route CSV file."
                )
                return
            self.load_callback(folder_path)
            self.destroy()
    def _load_selected(self):
        selected_path = self.selected_folder.get()
        if not selected_path:
            tk.messagebox.showwarning("Warning", "Please select a backup folder.")
            return
        if not Path(selected_path).exists():
            tk.messagebox.showerror("Error", f"Folder no longer exists:\n{selected_path}")
            return
        self.load_callback(selected_path)
        self.destroy()
    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self._populate_backup_list()
