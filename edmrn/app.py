import sys
import os
import threading
import time
import json
import ctypes
import subprocess
import pandas as pd
import numpy as np
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from PIL import Image, ImageTk
import webbrowser
from edmrn.icons import Icons
from edmrn.updater import setup_auto_updates
from edmrn.logger import setup_logging, get_logger
from edmrn.utils import resource_path
from edmrn.ed_theme import apply_elite_dangerous_theme
from edmrn.theme_manager import ThemeManager
from edmrn.ui_components import UIComponents
from edmrn.settings_manager import SettingsManager
from edmrn.neutron_manager import NeutronManager
from edmrn.journal_operations import JournalOperations
from edmrn.file_operations import FileOperations
from edmrn.route_management import RouteManagement
from edmrn.system_autocomplete import SystemAutocompleter
from edmrn.galaxy_plotter import GalaxyPlotter
from edmrn.gui import ErrorDialog, InfoDialog, WarningDialog, ConfirmDialog
_hicon_cache_app = {}
def _load_hicon_app(path):
    try:
        p = str(path)
        if p in _hicon_cache_app:
            return _hicon_cache_app[p]
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        hicon = ctypes.windll.user32.LoadImageW(0, p, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
        _hicon_cache_app[p] = hicon
        return hicon
    except Exception:
        return None
from edmrn.config import AppConfig, Paths
from edmrn.optimizer import RouteOptimizer
from edmrn.tracker import ThreadSafeRouteManager, RouteTracker, STATUS_VISITED, STATUS_SKIPPED, STATUS_UNVISITED
from edmrn.journal import JournalMonitor
from edmrn.overlay import get_overlay_manager
from edmrn.minimap import MiniMapFrame, MiniMapFrameFallback
from edmrn.backup import BackupManager
from edmrn.autosave import AutoSaveManager
from edmrn.platform_detector import get_platform_detector
from edmrn.gui import ManualWindow, AboutWindow, BackupSelectionWindow
from edmrn.theme_editor import ThemeEditor
from edmrn.neutron import NeutronRouter
logger = get_logger('App')

class EDMRN_App:
    def __init__(self):
        setup_logging()
        self.config = AppConfig.load()
        self.current_theme = getattr(self.config, 'current_theme', 'elite_dangerous')
        self.platform_detector = get_platform_detector()
        self.theme_manager = ThemeManager(self)
        self.ui_components = UIComponents(self)
        self.settings_manager = SettingsManager(self)
        self.neutron_manager = NeutronManager(self)
        self.journal_operations = JournalOperations(self)
        self.file_operations = FileOperations(self)
        self.route_management = RouteManagement(self)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self._borderless = False
        self._is_maximized = False
        self._saved_geometry = None
        self._drag_offset = (0, 0)
        self._create_root_window()
        self.csv_file_path = ctk.StringVar()
        self.load_backup_btn = None
        self.jump_range = ctk.StringVar(value=self.config.ship_jump_range)
        self.starting_system = ctk.StringVar()
        self.cmdr_name = ctk.StringVar(value="[CMDR Name: Loading...]")
        self.cmdr_cash = ctk.StringVar(value="N/A Cr")
        self.cmdr_location = ctk.StringVar(value="[Location: Unknown]")
        self.journal_path_var = ctk.StringVar(value=self.config.journal_path)
        self.selected_commander = ctk.StringVar(value=self.config.selected_commander)
        self.autosave_interval_var = tk.StringVar(value=self.config.autosave_interval)
        self.route_manager = ThreadSafeRouteManager()
        self.route_tracker = RouteTracker(self.route_manager)
        self.route_optimizer = RouteOptimizer()
        self.neutron_router = NeutronRouter()
        self.system_autocompleter = SystemAutocompleter()
        self.galaxy_plotter = GalaxyPlotter()
        self.galaxy_plotter_route_data = None
        self.galaxy_route_waypoints = []
        self.galaxy_current_waypoint_index = 0
        self.current_backup_folder = None
        self.system_labels = {}
        self.progress_label = None
        self.map_frame = None
        self.overlay_enabled = False
        self.overlay_manager = get_overlay_manager()
        self.journal_monitor = None
        self._tab_switch_lock = threading.Lock()
        self._last_tab_switch_time = 0
        self.column_vars = {}
        self.available_columns = []
        self.column_checkboxes = {}
        self.optional_window = None
        self._optimization_in_progress = False
        self.output_text = None
        self._create_widgets()
        self._setup_managers()
        self._autodetect_csv(initial_run=True)
        self.root.after(500, self._complete_startup_in_background)
        self._start_journal_monitor()
        threading.Thread(target=self._get_latest_cmdr_data, daemon=True).start()
        self._setup_keyboard_shortcuts()
    
    def refresh_ui_theme(self):
        self.config = AppConfig.load()
        ctk.set_appearance_mode(self.config.appearance_mode)
        ctk.set_default_color_theme(self.config.color_theme)
        colors = self.theme_manager.get_theme_colors()
        self.root.configure(fg_color=colors['background'])
        self._update_widget_colors()
        self._reapply_theme_to_widgets()
        if self.overlay_enabled:
            self.overlay_manager.stop()
            time.sleep(0.1)
            opacity = self.config.overlay_opacity / 100.0
            self.overlay_manager.start(self._get_overlay_data, opacity=opacity, app_instance=self)
        self._log(f"UI theme refreshed: {self.config.appearance_mode} mode, {self.config.color_theme} color")
    
    def _create_root_window(self):
        self.root = ctk.CTk()
        self.root.title(f"ED Multi Route Navigation (EDMRN)")
        self.root.geometry(self.config.window_geometry)
        self.root.minsize(1000, 700)
        colors = self.theme_manager.get_theme_colors()
        self.root.configure(fg_color=colors['background'])
        if self._borderless:
            try:
                self.root.overrideredirect(True)
            except Exception:
                pass
            self._setup_borderless_chrome_ui()
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                self.root.iconbitmap(ico_path)
                logger.info(f"Root: iconbitmap set -> {ico_path}")
                if os.name == 'nt':
                    try:
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = ctypes.windll.user32.LoadImageW(0, str(ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                        if hicon:
                            hwnd = self.root.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            logger.info("Root: WM_SETICON applied for ICO")
                    except Exception as e:
                        logger.debug(f"Root: WM_SETICON failed: {e}")
        except Exception as e:
            logger.debug(f"Root: iconbitmap failed: {e}")
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                self._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.root.wm_iconphoto(True, self._title_icon)
                except Exception:
                    self.root.iconphoto(False, self._title_icon)
                if os.name == 'nt':
                    try:
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = ctypes.windll.user32.LoadImageW(0, str(logo_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                        if hicon:
                            hwnd = self.root.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            logger.info("Root: WM_SETICON applied for PNG")
                    except Exception as e:
                        logger.debug(f"Root: WM_SETICON PNG failed: {e}")
        except Exception as e:
            logger.debug(f"Root: iconphoto failed: {e}")
        try:
            self.root.bind('<Map>', lambda e: self._schedule_reapply_root_icon())
            self.root.bind('<FocusIn>', lambda e: self._schedule_reapply_root_icon())
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _schedule_reapply_root_icon(self):
        if getattr(self, '_reapply_pending', False):
            return
        self._reapply_pending = True
        try:
            self.root.after(100, lambda: self._do_reapply_root_icon())
        except Exception:
            self._do_reapply_root_icon()
    
    def _do_reapply_root_icon(self):
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.root.iconbitmap(ico_path)
                except Exception:
                    pass
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon_app(ico_path)
                        if hicon:
                            hwnd = self.root.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            if not getattr(self, '_icon_set_logged', False):
                                logger.info("Root: WM_SETICON re-applied for ICO")
                                self._icon_set_logged = True
                            else:
                                logger.debug("Root: WM_SETICON re-applied for ICO (suppressed info)")
                    except Exception as e:
                        logger.debug(f"Root: WM_SETICON reapply failed: {e}")
        except Exception:
            pass
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                self._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.root.wm_iconphoto(True, self._title_icon)
                except Exception:
                    self.root.iconphoto(False, self._title_icon)
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon_app(logo_path)
                        if hicon:
                            hwnd = self.root.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            if not getattr(self, '_icon_set_logged', False):
                                logger.info("Root: WM_SETICON re-applied for PNG")
                                self._icon_set_logged = True
                            else:
                                logger.debug("Root: WM_SETICON re-applied for PNG (suppressed info)")
                    except Exception as e:
                        logger.debug(f"Root: WM_SETICON PNG reapply failed: {e}")
        except Exception:
            pass
        finally:
            self._reapply_pending = False
    
    def _reapply_root_icon(self, event=None):
        return self._schedule_reapply_root_icon()
    
    def _create_widgets(self):
        colors = self.theme_manager.get_theme_colors()
        parent = self.chrome_body if getattr(self, '_borderless', False) and hasattr(self, 'chrome_body') else self.root
        self.main_container = ctk.CTkFrame(
            parent,
            fg_color=colors['background'],
            border_color=colors['border'],
            border_width=1,
            corner_radius=10
        )
        if self._borderless and hasattr(self, 'chrome_body'):
            self.main_container.pack(fill="both", expand=True, padx=4, pady=4)
        else:
            self.main_container.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
            parent.columnconfigure(0, weight=1)
            parent.rowconfigure(0, weight=1)
        self.content_root = ctk.CTkFrame(
            self.main_container,
            fg_color=colors['background'],
            corner_radius=9
        )
        self.content_root.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(0, weight=1)
        self.content_root.columnconfigure(0, weight=1)
        self.content_root.rowconfigure(1, weight=1)
        self.tabview = ctk.CTkTabview(
            self.content_root,
            fg_color=colors['frame'],
            border_color=colors['border'],
            border_width=1,
            segmented_button_fg_color=colors['primary'],
            segmented_button_selected_color=colors['primary_hover'],
            segmented_button_selected_hover_color=colors['primary'],
            segmented_button_unselected_color=colors['secondary'],
            segmented_button_unselected_hover_color=colors['secondary_hover'],
            text_color=colors['text']
        )
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.tab_optimizer = self.tabview.add("Route Optimization")
        self.tab_tracker = self.tabview.add("Route Tracking")
        self.tab_neutron = self.tabview.add("Neutron Highway")
        self.tab_galaxy_plotter = self.tabview.add("Galaxy Plotter")
        self.tab_settings = self.tabview.add("Settings")
        for tab in [self.tab_optimizer, self.tab_tracker, self.tab_neutron, self.tab_galaxy_plotter, self.tab_settings]:
            tab.configure(fg_color=colors['background'])
        self.tabview.set("Route Optimization")
        
        def on_tab_change():
            current_tab = self.tabview.get()
            if current_tab == "Neutron Highway" and self.neutron_router.last_route:
                if not self.journal_monitor:
                    self._start_journal_monitor()
                    self._log("Journal monitor started for neutron tracking")
            self._update_overlay_tab_state(current_tab)
            if self.overlay_enabled:
                self.overlay_manager.update_data()
        self.tabview.configure(command=on_tab_change)
        self._create_header()
        try:
            self.root.bind('<FocusIn>', lambda e: self._update_chrome_border_focus(True))
            self.root.bind('<FocusOut>', lambda e: self._update_chrome_border_focus(False))
        except Exception:
            pass
        self.ui_components.create_optimizer_tab()
        self.ui_components.create_neutron_tab()
        self.ui_components.create_galaxy_plotter_tab()
        self.settings_manager.create_settings_tab()
        self.ui_components.create_bottom_buttons()

    def _setup_borderless_chrome_ui(self):
        colors = self.theme_manager.get_theme_colors()
        self.chrome_root = ctk.CTkFrame(self.root, fg_color=colors['background'], corner_radius=0)
        self.chrome_root.pack(fill="both", expand=True)
        self.chrome_root.columnconfigure(0, weight=1)
        self.chrome_root.rowconfigure(1, weight=1)
        self.title_bar = ctk.CTkFrame(self.chrome_root, fg_color=colors['frame'], height=38,
                                      border_color=colors['primary'], border_width=2)
        self.title_bar.grid(row=0, column=0, sticky="ew")
        self.title_bar.grid_propagate(False)
        self.title_bar.bind('<ButtonPress-1>', self._start_move)
        self.title_bar.bind('<B1-Motion>', self._on_move)
        title_left = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        title_left.pack(side="left", padx=10, pady=4)
        ctk.CTkLabel(title_left, text="ED Multi Route Navigation (EDMRN)",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=colors['text']).pack(side="left")
        controls = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        controls.pack(side="right", padx=8, pady=4)
        self.btn_min = ctk.CTkButton(controls, text="—", width=28, height=26,
                                     command=self._on_minimize)
        self.theme_manager.apply_button_theme(self.btn_min, "secondary")
        self.btn_min.pack(side="left", padx=(0, 6))
        self.btn_max = ctk.CTkButton(controls, text="⬜", width=28, height=26,
                                     command=self._on_maximize_toggle)
        self.theme_manager.apply_button_theme(self.btn_max, "secondary")
        self.btn_max.pack(side="left", padx=(0, 6))
        self.btn_close = ctk.CTkButton(controls, text="✕", width=28, height=26,
                                       command=self._on_close_click)
        self.theme_manager.apply_button_theme(self.btn_close, "primary")
        self.btn_close.pack(side="left")
        self.chrome_body = ctk.CTkFrame(self.chrome_root, fg_color=colors['background'])
        self.chrome_body.grid(row=1, column=0, sticky="nsew")
        grip_size = 8
        self.resize_right = ctk.CTkFrame(self.root, fg_color="transparent", width=grip_size, cursor="sb_h_double_arrow")
        self.resize_right.place(relx=1.0, rely=0.05, anchor='ne', relheight=0.95, x=-2, y=0)
        self.resize_right.lower()
        self.resize_right.bind('<ButtonPress-1>', lambda e: self._start_resize(e, 'right'))
        self.resize_right.bind('<B1-Motion>', lambda e: self._do_resize(e))
        self.resize_bottom = ctk.CTkFrame(self.root, fg_color="transparent", height=grip_size, cursor="sb_v_double_arrow")
        self.resize_bottom.place(relx=0.0, rely=1.0, anchor='sw', relwidth=1.0, x=0, y=-2)
        self.resize_bottom.lower()
        self.resize_bottom.bind('<ButtonPress-1>', lambda e: self._start_resize(e, 'bottom'))
        self.resize_bottom.bind('<B1-Motion>', lambda e: self._do_resize(e))
        self.resize_corner = ctk.CTkFrame(self.root, fg_color="transparent", width=grip_size*2, height=grip_size*2, cursor="size_nw_se")
        self.resize_corner.place(relx=1.0, rely=1.0, anchor='se', x=-2, y=-2)
        self.resize_corner.lower()
        self.resize_corner.bind('<ButtonPress-1>', lambda e: self._start_resize(e, 'corner'))
        self.resize_corner.bind('<B1-Motion>', lambda e: self._do_resize(e))

    def _start_move(self, event):
        try:
            self._drag_offset = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())
        except Exception:
            pass

    def _on_move(self, event):
        try:
            x = event.x_root - self._drag_offset[0]
            y = event.y_root - self._drag_offset[1]
            self.root.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height()}+{x}+{y}")
        except Exception:
            pass

    def _on_minimize(self):
        try:
            logger.info("Minimize clicked")
            self._saved_min_geometry = self.root.winfo_geometry()
            if self._borderless:
                logger.info("Minimize: Disabling overrideredirect for taskbar minimize")
                self.root.overrideredirect(False)
                self.root.update_idletasks()
            logger.info("Minimize: Calling iconify")
            self.root.iconify()
            logger.info("Minimize: Window should now be in taskbar")
            self._check_window_restore()
        except Exception as e:
            logger.error(f"Minimize error: {e}")

    def _check_window_restore(self):
        try:
            if self.root.winfo_viewable() and self.root.state() != 'iconic':
                logger.info("Window restored from taskbar")
                if self._borderless:
                    logger.info("Re-enabling borderless mode")
                    self.root.overrideredirect(True)
                    if hasattr(self, '_saved_min_geometry') and self._saved_min_geometry:
                        self.root.geometry(self._saved_min_geometry)
                        logger.info(f"Restored geometry: {self._saved_min_geometry}")
                    self.root.update_idletasks()
                    self.root.lift()
                    self.root.focus()
                    logger.info("Window lifted to front and focused")
                return
            self.root.after(100, self._check_window_restore)
        except Exception as e:
            logger.debug(f"Restore check error: {e}")
            return

    def _on_restore_from_taskbar(self, event=None):
        try:
            logger.info("Window restored from taskbar, re-enabling borderless")
            if self._borderless:
                self.root.overrideredirect(True)
                self.root.update_idletasks()
                if hasattr(self, '_saved_min_geometry') and self._saved_min_geometry:
                    self.root.geometry(self._saved_min_geometry)
            self.root.unbind('<Map>', self._on_restore_from_taskbar)
            logger.info("Borderless mode restored")
        except Exception as e:
            logger.error(f"Restore error: {e}")



    def _on_close_click(self):
        try:
            self._on_closing()
        except Exception:
            self.root.destroy()

    def _on_maximize_toggle(self):
        try:
            if not self._is_maximized:
                self._saved_geometry = self.root.winfo_geometry()
                sw = self.root.winfo_screenwidth()
                sh = self.root.winfo_screenheight()
                self.root.geometry(f"{sw}x{sh}+0+0")
                self._is_maximized = True
                self.btn_max.configure(text="❐")
            else:
                if self._saved_geometry:
                    self.root.geometry(self._saved_geometry)
                self._is_maximized = False
                self.btn_max.configure(text="⬜")
        except Exception:
            pass

    def _start_resize(self, event, side):
        try:
            self._resize_side = side
            self._start_w = self.root.winfo_width()
            self._start_h = self.root.winfo_height()
            self._start_x = event.x_root
            self._start_y = event.y_root
        except Exception:
            pass

    def _do_resize(self, event):
        try:
            dx = event.x_root - self._start_x
            dy = event.y_root - self._start_y
            new_w = self._start_w
            new_h = self._start_h
            if self._resize_side in ('right', 'corner'):
                new_w = max(800, self._start_w + dx)
            if self._resize_side in ('bottom', 'corner'):
                new_h = max(600, self._start_h + dy)
            self.root.geometry(f"{new_w}x{new_h}+{self.root.winfo_x()}+{self.root.winfo_y()}")
        except Exception:
            pass

    def _toggle_borderless_setting(self, enabled: bool):
        try:
            self.config.borderless_mode = bool(enabled)
            self.config.save()
            InfoDialog(self, "Restart Required", "Please restart the app to apply borderless mode change.")
        except Exception:
            pass
    def _create_header(self):
        colors = self.theme_manager.get_theme_colors()
        header_frame = ctk.CTkFrame(
            self.content_root,
            fg_color=colors['frame'],
            border_color=colors['border'],
            border_width=1,
            height=45
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(2, weight=0)
        header_frame.grid_propagate(False)
        
        logo_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="w", padx=8, pady=5)
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                logo_img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                ctk_logo = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(32, 32))
                logo_label = ctk.CTkLabel(logo_frame, image=ctk_logo, text="")
                logo_label.image = ctk_logo
                logo_label.pack(side="left")
        except Exception as e:
            logger.debug(f"Logo load failed: {e}")
        
        cmdr_info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        cmdr_info_frame.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(cmdr_info_frame, text="CMDR:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=colors['primary']).grid(row=0, column=0, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.cmdr_name,
                     font=ctk.CTkFont(size=12),
                     text_color=colors['text']).grid(row=0, column=1, sticky="w", padx=(3, 12), pady=2)
        ctk.CTkLabel(cmdr_info_frame, text="CR:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=colors['primary']).grid(row=0, column=2, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.cmdr_cash,
                     font=ctk.CTkFont(size=11),
                     text_color=colors['text']).grid(row=0, column=3, sticky="w", padx=(3, 12), pady=2)
        ctk.CTkLabel(cmdr_info_frame, text="Location:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=colors['primary']).grid(row=0, column=4, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.cmdr_location,
                     font=ctk.CTkFont(size=11),
                     text_color=colors['text']).grid(row=0, column=5, sticky="w", padx=(3, 0), pady=2)
        
        update_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Check Update",
            command=self._check_for_updates,
            width=120,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        self.theme_manager.apply_button_theme(update_btn, "primary")
        update_btn.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=5)

    def _create_optimizer_tab(self):
        colors = self.theme_manager.get_theme_colors()
        self.tab_optimizer.configure(fg_color=colors['background'])
        main_frame = ctk.CTkFrame(
            self.tab_optimizer,
            corner_radius=10,
            fg_color=colors['background'],
            bg_color=colors['background'],
            border_color=colors['border'],
            border_width=1
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        top_frame.columnconfigure(0, weight=4)
        top_frame.columnconfigure(2, weight=2)
        top_frame.columnconfigure(2, weight=2)
        csv_label = ctk.CTkLabel(top_frame, text="Route Data File (CSV):",
                                font=ctk.CTkFont(weight="bold"))
        csv_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        csv_input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        csv_input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        csv_input_frame.columnconfigure(0, weight=1)
        self.file_entry = ctk.CTkEntry(csv_input_frame, textvariable=self.csv_file_path)
        self.file_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        csv_btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        csv_btn_frame.grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.file_button = ctk.CTkButton(
            csv_btn_frame,
            text="Browse / Reset",
            command=self._browse_file,
            width=80
        )
        self.theme_manager.apply_button_theme(self.file_button, "secondary")
        self.file_button.pack(side="left", padx=(0, 5))
        self.load_backup_btn = ctk.CTkButton(
            csv_btn_frame,
            text="Load Backup",
            command=self._load_backup_from_optimizer,
            width=100
        )
        self.theme_manager.apply_button_theme(self.load_backup_btn, "secondary")
        self.load_backup_btn.pack(side="left")
        jump_label = ctk.CTkLabel(top_frame, text="Ship Jump Range (LY):",
                                 font=ctk.CTkFont(weight="bold"))
        jump_label.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=10)
        jump_input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        jump_input_frame.grid(row=1, column=1, sticky="w", pady=(0, 5), padx=10)
        self.range_entry = ctk.CTkEntry(jump_input_frame, textvariable=self.jump_range, width=120)
        self.jump_range.trace_add('write', lambda *args: self._save_jump_range())
        self.jump_range.trace_add('write', lambda *args: self._sync_neutron_jump_range())
        self.range_entry.pack(anchor="w")
        jump_btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent", height=30)
        jump_btn_frame.grid(row=2, column=1, sticky="w", pady=(0, 5), padx=10)
        jump_btn_frame.grid_propagate(False)
        start_label = ctk.CTkLabel(top_frame, text="Starting System (Optional):",
                                  font=ctk.CTkFont(weight="bold"))
        start_label.grid(row=0, column=2, sticky="w", pady=(0, 5))
        start_input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        start_input_frame.grid(row=1, column=2, sticky="ew", pady=(0, 5))
        start_input_frame.columnconfigure(0, weight=1)
        self.start_entry = ctk.CTkEntry(start_input_frame, textvariable=self.starting_system)
        self.start_entry.grid(row=0, column=0, sticky="ew")
        start_btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent", height=30)
        start_btn_frame.grid(row=2, column=2, sticky="w", pady=(0, 5))
        start_btn_frame.grid_propagate(False)
        ctk.CTkLabel(main_frame, text="CSV Column Status:",
                    font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", pady=(10, 5))
        self.required_columns_frame = ctk.CTkFrame(
            main_frame,
            corner_radius=0,
            fg_color=colors['frame'],
            border_color=colors['border'],
            border_width=1
        )
        self.required_columns_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.required_columns_frame.grid_propagate(True)
        self.columns_container = ctk.CTkFrame(
            self.required_columns_frame,
            fg_color=colors['frame'],
            border_color=colors['border'],
            border_width=0,
            corner_radius=0
        )
        self.columns_container.pack(fill="auto", expand=True, padx=0, pady=0)
        self.column_status_label = ctk.CTkLabel(
            self.columns_container,
            text="Select a CSV file to check columns",
            text_color=colors['text'],
            font=ctk.CTkFont(size=11)
        )
        self.column_status_label.pack(expand=True)
        self.column_indicators = {}
        self.current_csv_columns = []
        self.csv_file_path.trace_add('write', lambda *args: self._update_column_status_display())
        self.optional_toggle_btn = ctk.CTkButton(main_frame,
                                               text="Optional Columns",
                                               command=self._toggle_optional_columns,
                                               width=140, height=28)
        self.theme_manager.apply_button_theme(self.optional_toggle_btn, "secondary")
        self.optional_toggle_btn.grid(row=3, column=0, pady=(0, 15), sticky="w")
        self.run_button = ctk.CTkButton(main_frame, text="Optimize & Track",
                                       command=self._run_optimization_threaded,
                                       height=32,
                                       width=100,
                                       font=ctk.CTkFont(size=13, weight="bold"))
        self.theme_manager.apply_button_theme(self.run_button, "primary")
        self.run_button.grid(row=4, column=0, pady=15)
        ctk.CTkLabel(main_frame, text="Status/Output Console:",
                    font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, sticky="w", pady=(10, 2))
        self.output_text = ctk.CTkTextbox(main_frame, height=350)
        self.output_text.grid(row=6, column=0, padx=5, pady=(0, 10), sticky="nsew")
    
    def _create_neutron_tab(self):
        main_frame = ctk.CTkFrame(self.tab_neutron, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        left_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(6, weight=1)
        ctk.CTkLabel(left_frame, text="🌟 Neutron Highway Route Planner",
                    font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=(20, 20))
        input_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15), padx=20)
        input_frame.columnconfigure((0, 1), weight=1)
        from_frame = ctk.CTkFrame(input_frame)
        from_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(from_frame, text="From System:",
                    font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.neutron_from_var = ctk.StringVar()
        self.neutron_from_entry = ctk.CTkEntry(from_frame, textvariable=self.neutron_from_var,
                                              placeholder_text="Current system (auto-detected)")
        self.neutron_from_entry.pack(fill="x", padx=10, pady=(0, 10))
        to_frame = ctk.CTkFrame(input_frame)
        to_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ctk.CTkLabel(to_frame, text="To System:",
                    font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.neutron_to_var = ctk.StringVar()
        self.neutron_to_entry = ctk.CTkEntry(to_frame, textvariable=self.neutron_to_var,
                                            placeholder_text="Route destination (from CSV)")
        self.neutron_to_entry.pack(fill="x", padx=10, pady=(0, 10))
        settings_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        settings_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15), padx=20)
        settings_frame.columnconfigure((0, 1), weight=1)
        range_frame = ctk.CTkFrame(settings_frame)
        range_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(range_frame, text="Ship Jump Range (LY):",
                    font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.neutron_range_var = ctk.StringVar(value=self.jump_range.get())
        self.neutron_range_entry = ctk.CTkEntry(range_frame, textvariable=self.neutron_range_var)
        self.neutron_range_entry.pack(fill="x", padx=10, pady=(0, 10))
        boost_frame = ctk.CTkFrame(settings_frame)
        boost_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ctk.CTkLabel(boost_frame, text="FSD Boost:",
                    font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        colors = self.theme_manager.get_theme_colors()
        self.neutron_boost_var = ctk.StringVar(value="x4")
        self.neutron_boost_menu = ctk.CTkOptionMenu(
            boost_frame, values=["x4 (Normal)", "x6 (Caspian)"],
            variable=self.neutron_boost_var,
            fg_color=colors['primary'],
            button_color=colors['primary_hover'],
            text_color=colors['text²']
        )
        self.neutron_boost_menu.pack(fill="x", padx=10, pady=(0, 10))
        button_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, pady=(0, 15), padx=20)
        self.neutron_calculate_btn = ctk.CTkButton(
            button_frame, text="🚀 Calculate Neutron Route",
            command=self._calculate_neutron_route,
            height=35, width=200,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.theme_manager.apply_button_theme(self.neutron_calculate_btn, "primary")
        self.neutron_calculate_btn.pack(pady=(0, 10))
        nav_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(0, 5))
        self.neutron_prev_btn = ctk.CTkButton(
            nav_frame, text="<", width=40, height=35,
            command=self._neutron_prev_waypoint,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.theme_manager.apply_button_theme(self.neutron_prev_btn, "secondary")
        self.neutron_prev_btn.pack(side="left", padx=(0, 5))
        self.neutron_current_btn = ctk.CTkButton(
            nav_frame, text="No route calculated",
            command=self._copy_current_neutron_system,
            height=35, width=300,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.theme_manager.apply_button_theme(self.neutron_current_btn, "primary")
        self.neutron_current_btn.pack(side="left", padx=5)
        self.neutron_next_btn = ctk.CTkButton(
            nav_frame, text=">", width=40, height=35,
            command=self._neutron_next_waypoint,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.theme_manager.apply_button_theme(self.neutron_next_btn, "secondary")
        self.neutron_next_btn.pack(side="left", padx=(5, 0))
        info_frame = ctk.CTkFrame(left_frame)
        info_frame.grid(row=4, column=0, sticky="ew", pady=(0, 15), padx=20)
        info_frame.columnconfigure(0, weight=1)
        self.neutron_info_label = ctk.CTkLabel(
            info_frame, text="ℹ️ Enter systems and click Calculate to plan your neutron highway route",
            font=ctk.CTkFont(size=12)
        )
        self.neutron_info_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")
        colors = self.theme_manager.get_theme_colors()
        stats_frame = ctk.CTkFrame(info_frame,
                                  fg_color=colors['frame'],
                                  border_color=colors['border'],
                                  border_width=1,
                                  corner_radius=8)
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(5, 10), padx=10)
        stats_frame.columnconfigure(0, weight=1)
        self.neutron_stats_label = ctk.CTkLabel(stats_frame,
                                               text="📊 Neutron Statistics | No route calculated",
                                               font=ctk.CTkFont(family="Consolas", size=12, weight="normal"),
                                               text_color=colors['text'])
        self.neutron_stats_label.grid(row=0, column=0, padx=8, pady=(8, 2), sticky="w")
        self.neutron_progress_label = ctk.CTkLabel(stats_frame,
                                                  text="🎯 Progress Status | Ready to calculate",
                                                  font=ctk.CTkFont(family="Consolas", size=12, weight="normal"),
                                                  text_color=colors['text'])
        self.neutron_progress_label.grid(row=1, column=0, padx=8, pady=(2, 8), sticky="w")
        right_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        ctk.CTkLabel(right_frame, text="Neutron Route:",
                    font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=(15, 5), padx=15)
        self.neutron_output = ctk.CTkTextbox(right_frame, height=400)
        self.neutron_output.grid(row=1, column=0, sticky="nsew", pady=(0, 15), padx=15)
        self.neutron_output.insert("1.0", "No neutron route calculated yet.\n\nSteps:\n1. Enter your current system\n2. Enter destination system\n3. Set your ship's jump range\n4. Choose FSD boost type\n5. Click Calculate")
        self.neutron_output.configure(state="disabled")
    
    def _setup_managers(self):
        backup_dirs = [Paths.get_app_data_dir()]
        if not hasattr(self, 'backup_manager') or self.backup_manager is None:
            self.backup_manager = BackupManager(
                backup_dir=Paths.get_backup_folder(),
                source_dirs=backup_dirs,
                log_callback=self._log,
                route_tracker=self.route_tracker
            )
        if not hasattr(self, 'autosave_manager') or self.autosave_manager is None:
            self.autosave_manager = AutoSaveManager(
                save_callback=self._perform_autosave,
                log_callback=self._log
            )
        interval = self.config.autosave_interval
        self._apply_autosave_interval(interval)
        self._update_autosave_status()
    
    def run(self):
        self.root.mainloop()
    
    def _log(self, message):
        try:
            self.output_text.configure(state='normal')
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.output_text.configure(state='disabled')
            logger.info(message)
        except Exception:
            print(message)
    
    def _perform_autosave(self):
        try:
            route_data = self.route_manager.get_route()
            self.route_tracker.save_route_status(route_data)
            self._log("Route status auto-saved")
        except Exception as e:
            self._log(f"Auto-save failed: {e}")
    
    def _toggle_overlay(self):
        if not self.overlay_enabled:
            opacity = self.config.overlay_opacity / 100.0
            self.overlay_manager.start(self._get_overlay_data, opacity=opacity, app_instance=self)
            self.overlay_enabled = True
            self.overlay_btn.configure(text="Stop Overlay")
            self._log("Cross-Platform Overlay started!")
            current_tab = self.tabview.get()
            if self.overlay_manager._instance:
                self.root.after(100, lambda: self._update_overlay_tab_state(current_tab))
        else:
            self.overlay_manager.stop()
            self.overlay_enabled = False
            self.overlay_btn.configure(text="Start Overlay")
            self._log("Overlay stopped")
    
    def _toggle_auto_overlay_start(self, enabled: bool):
        try:
            self.config.auto_start_overlay_when_ready = bool(enabled)
            self.config.save()
            self._log(f"Auto-start overlay when route ready: {'ON' if enabled else 'OFF'}")
        except Exception:
            pass
    
    def _ensure_overlay_started(self, tab_name: str = None):
        try:
            if not getattr(self.config, 'auto_start_overlay_when_ready', False):
                return
            if self.overlay_enabled or (self.overlay_manager and self.overlay_manager.is_running()):
                return
            opacity = self.config.overlay_opacity / 100.0
            started = self.overlay_manager.start(self._get_overlay_data, opacity=opacity, app_instance=self)
            if started:
                self.overlay_enabled = True
                if hasattr(self, 'overlay_btn') and self.overlay_btn:
                    try:
                        self.overlay_btn.configure(text="Stop Overlay")
                    except Exception:
                        pass
                current = tab_name or self.tabview.get()
                self.root.after(100, lambda: self._update_overlay_tab_state(current))
                self._log("Overlay auto-started (route ready)")
        except Exception:
            pass
    
    def _get_overlay_data(self):
        current_tab = self.tabview.get()
        if current_tab == "Neutron Highway":
            return self.neutron_router.get_overlay_data()
        elif current_tab == "Galaxy Plotter":
            return self.galaxy_plotter.get_overlay_data(
                self.galaxy_route_waypoints,
                self.galaxy_current_waypoint_index,
                self.galaxy_plotter_route_data
            )
        elif current_tab == "Route Tracking":
            return self.route_tracker.get_overlay_data(self)
        else:
            return self.route_tracker.get_overlay_data(self)
    
    def _update_overlay_tab_state(self, tab_name):
        if not self.overlay_enabled or not self.overlay_manager._instance:
            return
        
        current_time = time.time()
        if hasattr(self, '_last_tab_switch_time'):
            time_since_last = current_time - self._last_tab_switch_time
            if time_since_last < 0.5: 
                return
        
        self._last_tab_switch_time = current_time
        
        try:
            self.overlay_manager._instance.update_tab_buttons(tab_name)
        except Exception as e:
            logger.error(f"Error updating overlay tab state: {e}")
    
    def _apply_autosave_interval(self, interval):
        self.config.autosave_interval = interval
        self.config.save()
        if interval == "1 minute": minutes = 1
        elif interval == "5 minutes": minutes = 5
        elif interval == "10 minutes": minutes = 10
        else: minutes = 0
        if self.autosave_manager: self.autosave_manager.set_interval(minutes)
        self._log(f"Auto-save interval: {interval}")
    
    def _load_backup_from_optimizer(self):
        self.file_operations.load_from_backup()
    
    def _browse_file(self):
        self.file_operations.browse_file()
    
    def _run_optimization_threaded(self):
        self.route_management.run_optimization_threaded()
    
    def _run_optimization(self):
        csv_path = self.csv_file_path.get()
        if not csv_path or not Path(csv_path).exists():
            ErrorDialog(self, "Error", "Please select a valid CSV file.")
            return
        try:
            jump_range = float(self.jump_range.get())
            if jump_range <= 0:
                ErrorDialog(self, "Error", "Ship jump range must be a positive number.")
                return
            self.config.ship_jump_range = str(jump_range)
            self.config.save()
        except ValueError:
            ErrorDialog(self, "Error", "Enter a valid number for ship jump range.")
            return
        starting_system_name = self.starting_system.get().strip()
        existing_status = {}
        route_data = self.route_manager.get_route()
        for route in route_data:
            existing_status[route['name']] = route['status']
        result = self.route_optimizer.optimize_route(csv_path, jump_range, starting_system_name, existing_status)
        if not result['success']:
            ErrorDialog(self, "Error", result['error'])
            return
        optimized_df = result['optimized_df']
        output_file_name = f"Optimized_Route_{result['num_systems']}_J{result['total_jumps']}_M{jump_range:.1f}LY.csv"
        output_file_path = Path(Paths.get_backup_folder()) / output_file_name
        Path(Paths.get_backup_folder()).mkdir(exist_ok=True)
        if result['success']:
            self.current_backup_folder = result.get('backup_folder')
        backup_folder = Path(result.get('backup_folder', ''))
        if backup_folder.exists():
            self._log(f"Route saved to backup: {backup_folder.name}")
        else:
            self._log(f"Route optimization complete")
        self.route_tracker.load_route(result['route_data'])
        if 'backup_folder' in result:
            self.route_tracker.save_route_status(result['backup_folder'])
        self.total_distance_ly = result['total_distance']
        self._create_route_tracker_tab_content()
        self.tabview.set("Route Tracking")
        self._start_journal_monitor()
        self._copy_next_system_to_clipboard()
        self._ensure_overlay_started("Route Tracking")
        self._log("OPTIMIZATION COMPLETE")
        self._log(f"Total Distance: {result['total_distance']:.2f} LY")
        self._log(f"Estimated Jumps: {result['total_jumps']} jumps")
        self._log(f"Route successfully saved to: '{output_file_path}'")
        self._log("Switched to Route Tracking tab (with 3D Map).")
        self._log("Auto-Tracking STARTED (Monitoring Elite Dangerous Journal).")
        InfoDialog(self, "Success", f"Route optimization complete and Auto-Tracking is ready.\nFile: {output_file_name}")

    def _create_route_tracker_tab_content(self):
        self.route_management.create_route_tracker_tab_content()

    def _quick_save_route(self):
        self.file_operations.quick_save_route()

    def _handle_system_click_manual(self, system_name):
        self.route_management.handle_system_click_manual(system_name)

    def _update_label_color(self, system_name, status):
        self.route_management.update_label_color(system_name, status)

    def _update_progress_info(self):
        self.route_management.update_progress_info()

    def _update_route_statistics(self):
        self.route_management.update_route_statistics()

    def _open_app_data_folder(self):
        self.file_operations.open_app_data_folder()

    def _open_output_csv(self):
        self.file_operations.open_output_csv()

    def _open_file(self, file_path):
        self.file_operations._open_file(file_path)

    def _load_from_backup(self):
        self.file_operations.load_from_backup()

    def _load_backup_file(self, backup_folder_path):
        return self.file_operations.load_backup_file(backup_folder_path)

    def _handle_system_click(self, system_name):
        self.route_management.handle_system_click(system_name)

    def _start_journal_monitor(self):
        if self.journal_monitor:
            self.journal_monitor.stop()
        manual_path = self.journal_path_var.get().strip() or None
        self.journal_monitor = JournalMonitor(callback=self._handle_system_jump, manual_journal_path=manual_path, selected_commander=self.selected_commander.get())
        self.journal_monitor.start()
        self._log(f"Journal monitor started with path: {manual_path or 'auto-detected'}")

    def _handle_system_jump(self, system_name):
        
        current_tab = self.tabview.get()
        
        if system_name:
            try:
                self.root.after(0, lambda: self.cmdr_location.set(system_name))
            except Exception:
                pass
        if current_tab == "Neutron Highway":
            if self.neutron_router.last_route:
                self.neutron_manager.handle_neutron_system_jump(system_name)
        elif current_tab == "Galaxy Plotter":
            if self.galaxy_route_waypoints:
                self._handle_galaxy_system_jump(system_name)
        else:
            self.root.after(0, lambda: self._update_system_status_from_monitor(system_name, 'visited'))
    
    def _update_system_status_from_monitor(self, system_name, new_status):
        self.route_management.update_system_status_from_monitor(system_name, new_status)

    def _advance_route_tracking_from_overlay(self):
        route_data = self.route_manager.get_route()
        if not route_data:
            self._log("Overlay: No route loaded for Route Tracking.")
            return

        next_unvisited = next((item for item in route_data if item.get('status') == STATUS_UNVISITED), None)
        if not next_unvisited:
            self._log("Overlay: Route Tracking complete.")
            return

        system_name = next_unvisited.get('name')
        if not system_name:
            return

        status_changed = self.route_manager.update_system_status(system_name, STATUS_VISITED)
        if status_changed:
            self.route_management.update_label_color(system_name, STATUS_VISITED)
            if self.map_frame:
                self.map_frame.update_system_status(system_name, STATUS_VISITED)
            self.route_management.update_progress_info()
            self.route_management.update_route_statistics()
            if hasattr(self, 'current_backup_folder') and self.current_backup_folder:
                self.route_tracker.save_route_status(self.current_backup_folder)
            self._log(f"Overlay: '{system_name}' marked as visited.")

        self._copy_next_system_to_clipboard()
        if self.overlay_enabled:
            try:
                self.overlay_manager.update_data()
            except Exception:
                pass

    def _copy_next_system_to_clipboard(self):
        self.route_management.copy_next_system_to_clipboard()

    def _copy_prev_system_to_clipboard(self):
        self.route_management.copy_prev_system_to_clipboard()

    def _autodetect_csv(self, initial_run=False):
        self.file_operations.autodetect_csv(initial_run)

    def _get_latest_cmdr_data(self):
        cmdr_name_default = "CMDR NoName"
        cmdr_cash = 0
        selected_cmdr = self.config.selected_commander
        journal_monitor = JournalMonitor(None, selected_commander=selected_cmdr)
        latest_file = journal_monitor._get_latest_journal_file()
        if not latest_file:
            try:
                self.root.after(0, lambda: self.cmdr_name.set(f"CMDR Not Found ({cmdr_name_default})"))
                self.root.after(0, lambda: self.cmdr_cash.set("Where is the bank? (Saved Data)"))
            except RuntimeError:
                pass
            return
        self._log(f"Checking Journal file: {Path(latest_file).name}")
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
            self._log(f"ERROR reading CMDR data from Journal: {e}")
        final_cmdr_name = cmdr_name_default
        final_cmdr_cash = self._format_cash(cmdr_cash)
        final_location = current_system or "Unknown"
        try:
            self.root.after(0, lambda: self.cmdr_name.set(final_cmdr_name))
            self.root.after(0, lambda: self.cmdr_cash.set(final_cmdr_cash))
            self.root.after(0, lambda: self.cmdr_location.set(final_location))
        except RuntimeError:
            return
        self._log(f"CMDR Status Loaded: {final_cmdr_name}, {final_cmdr_cash}, Location: {final_location}")

    def _format_cash(self, amount):
        try:
            cash_int = int(amount)
            return f"{cash_int:,}".replace(",", ".") + " Cr"
        except Exception:
            return f"{amount} Cr"

    def _open_link(self, url):
        try:
            webbrowser.open(url)
        except Exception as e:
            self._log(f"ERROR: Failed to open link {url}: {e}")

    def _update_chrome_border_focus(self, focused: bool):
        try:
            colors = self.theme_manager.get_theme_colors()
            new_color = colors['primary_hover'] if focused else colors['border']
            if hasattr(self, 'main_container') and self.main_container:
                self.main_container.configure(border_color=new_color)
        except Exception:
            pass

    def _show_about_info(self):
        self.about_window = AboutWindow(self, self._open_link, self._show_manual)

    def _show_manual(self):
        self.manual_window = ManualWindow(self)

    def _setup_keyboard_shortcuts(self):
        self.root.bind('<Control-o>', lambda e: self._toggle_overlay())

    
    def _on_closing(self):
        self._cleanup()
        self.root.destroy()

    def _cleanup(self):
        try:
            if self.overlay_enabled:
                self.overlay_manager.stop()
            if self.journal_monitor:
                self.journal_monitor.stop()
            if self.autosave_manager:
                self.autosave_manager.stop()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def _update_column_status_display(self):
        for widget in self.columns_container.winfo_children():
            widget.destroy()
        csv_path = self.csv_file_path.get()
        if not csv_path or not Path(csv_path).exists():
            colors = self.theme_manager.get_theme_colors()
            ctk.CTkLabel(self.columns_container,
                        text="Select a CSV file to check column status",
                        text_color=colors['secondary'],
                        font=ctk.CTkFont(size=11)).pack(expand=True)
            return
        try:
            columns_status, all_columns = self.route_optimizer.check_csv_columns(csv_path)
            if not columns_status:
                ctk.CTkLabel(self.columns_container,
                            text="❌ Unable to read CSV file",
                            text_color="#FF6B6B",
                            font=ctk.CTkFont(size=11, weight="bold")).pack(expand=True)
                return
            self.current_csv_columns = all_columns
            colors = self.theme_manager.get_theme_colors()
            grid_frame = ctk.CTkFrame(
                self.columns_container,
                fg_color=colors['frame'],
                border_color=colors['border'],
                border_width=0,
                corner_radius=0
            )
            grid_frame.pack(fill="both", expand=True, padx=8, pady=8)
            for i in range(5):
                grid_frame.columnconfigure(i, weight=1)
            required_columns = [
                ('System Name', 'System Name (Required)'),
                ('Body Name', 'Body Name (Optional)'),
                ('X Coord', 'X Coordinate (Required)'),
                ('Y Coord', 'Y Coordinate (Required)'),
                ('Z Coord', 'Z Coordinate (Required)')
            ]
            for idx, (col_key, display_name) in enumerate(required_columns):
                frame = ctk.CTkFrame(grid_frame, fg_color=colors['secondary'], height=32)
                frame.grid(row=0, column=idx, padx=2, pady=2, sticky="ew")
                frame.grid_propagate(False)
                frame.grid_columnconfigure(1, weight=1)
                is_available = columns_status.get(col_key, False)
                status_color = "#4CAF50" if is_available else "#FF6B6B"
                status_icon = "✓" if is_available else "✗"
                status_text = "Found" if is_available else "MISSING"
                col_label = ctk.CTkLabel(frame, text=display_name, font=ctk.CTkFont(size=10, weight="bold"), anchor="w")
                col_label.grid(row=0, column=0, padx=(6, 3), pady=5, sticky="w")
                status_label = ctk.CTkLabel(frame, text=status_text, text_color=status_color, font=ctk.CTkFont(size=9), anchor="e")
                status_label.grid(row=0, column=1, padx=3, pady=5, sticky="ew")
                icon_label = ctk.CTkLabel(frame, text=status_icon, text_color=status_color, font=ctk.CTkFont(size=12, weight="bold"), anchor="e")
                icon_label.grid(row=0, column=2, padx=(0, 6), pady=5, sticky="e")
                self.column_indicators[col_key] = {'frame': frame, 'available': is_available}
            all_required = all(columns_status[col] for col in ['System Name', 'X Coord', 'Y Coord', 'Z Coord'])
            if all_required:
                self.run_button.configure(state='normal', text="Optimize & Track")
                self._load_csv_systems_for_autocomplete(csv_path)
            else:
                self.run_button.configure(state='disabled', text="❌ Missing required columns")
        except Exception as e:
            self._log(f"Column status update error: {e}")
            ctk.CTkLabel(self.columns_container,
                        text=f"Error checking CSV: {str(e)[:50]}",
                        text_color="#FF6B6B",
                        font=ctk.CTkFont(size=11)).pack(expand=True)
    
    def _load_csv_systems_for_autocomplete(self, csv_path: str):
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            
            if 'System Name' not in df.columns:
                return
                
            required_cols = ['System Name', 'X', 'Y', 'Z']
            if not all(col in df.columns for col in required_cols):
                logger.warning("CSV missing coordinate columns for nearest system calculation")
                systems = df['System Name'].dropna().unique().tolist()
                if hasattr(self, 'start_systems_list'):
                    self.start_systems_list = sorted(systems)
                return
            
            systems_df = df[required_cols].drop_duplicates('System Name')
            systems = systems_df['System Name'].tolist()
            
            if hasattr(self, 'start_systems_list'):
                self.start_systems_list = sorted(systems)
                logger.info(f"Loaded {len(systems)} systems to starting system dropdown")
            
            self.csv_systems_data = systems_df
            
            self._find_nearest_system(auto=True)
            
        except Exception as e:
            logger.error(f"Error loading CSV systems: {e}")
    
    def _toggle_optional_columns(self):
        if self.optional_window and self.optional_window.winfo_exists():
            self.optional_window.destroy()
            self.optional_window = None
            return
        csv_path = self.csv_file_path.get()
        if not csv_path or not Path(csv_path).exists():
            WarningDialog(self, "Warning", "Please select a CSV file first.")
            return
        try:
            df = pd.read_csv(csv_path, nrows=5)
            self.available_columns = df.columns.tolist()
        except Exception as e:
            ErrorDialog(self, "Error", f"Cannot read CSV: {e}")
            return
        required_columns = ['System Name', 'X', 'Y', 'Z']
        optional_columns = [col for col in self.available_columns if col not in required_columns]
        if not optional_columns:
            InfoDialog(self, "Info", "No optional columns found in CSV.")
            return
        colors = self.theme_manager.get_theme_colors()
        self.optional_window = ctk.CTkToplevel(self.root)
        self.optional_window.title("Optional Columns Selection")
        self.optional_window.geometry("500x400")
        self.optional_window.transient(self.root)
        self.optional_window.grab_set()
        
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                self.optional_window.iconbitmap(ico_path)
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon_app(ico_path)
                        if hicon:
                            hwnd = self.optional_window.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    except Exception:
                        pass
        except Exception:
            pass
        
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                optional_icon = ImageTk.PhotoImage(img)
                try:
                    self.optional_window.wm_iconphoto(True, optional_icon)
                except Exception:
                    self.optional_window.iconphoto(False, optional_icon)
                self.optional_window._title_icon = optional_icon
        except Exception:
            pass
        
        main_container = ctk.CTkFrame(self.optional_window, fg_color=colors['frame'], border_color=colors['primary'], border_width=1)
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        ctk.CTkLabel(main_container, text="Select Optional Columns",
                    font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                    text_color=colors['primary']).pack(pady=(0, 10))
        scroll_frame = ctk.CTkScrollableFrame(main_container, fg_color=colors['secondary'], border_color=colors['primary'], border_width=1)
        scroll_frame.pack(fill="both", expand=True, pady=5)
        for col in sorted(optional_columns):
            if col not in self.column_vars:
                self.column_vars[col] = tk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(scroll_frame, text=col, variable=self.column_vars[col],
                                 text_color=colors['text'],
                                 checkmark_color=colors['primary'],
                                 border_color=colors['primary'],
                                 hover_color=colors['primary_hover'],
                                 font=ctk.CTkFont(family="Segoe UI", size=12))
            chk.pack(anchor="w", padx=10, pady=2)
            self.column_checkboxes[col] = chk
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        select_all_btn = ctk.CTkButton(button_frame, text="Select All",
                                      command=self._select_all_optional, width=100,
                                      fg_color=colors['primary'], hover_color=colors['primary_hover'],
                                      text_color=colors['text'], font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        select_all_btn.pack(side="left", padx=(0, 10))
        deselect_all_btn = ctk.CTkButton(button_frame, text="Deselect All",
                                        command=self._deselect_all_optional, width=100,
                                        fg_color=colors['secondary'], hover_color=colors['secondary_hover'],
                                        border_color=colors['primary'], border_width=1,
                                        text_color=colors['primary'], font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        deselect_all_btn.pack(side="left", padx=(0, 10))
        colors = self.theme_manager.get_theme_colors()
        close_btn = ctk.CTkButton(button_frame, text="Close",
                                 command=lambda: self.optional_window.destroy(),
                                 width=100, fg_color=colors['secondary'], hover_color=colors['secondary_hover'],
                                 text_color=colors['text'], font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        close_btn.pack(side="right")
        
        try:
            self.optional_window.bind('<Map>', lambda e: self._schedule_optional_reapply_icons())
            self.optional_window.bind('<FocusIn>', lambda e: self._schedule_optional_reapply_icons())
        except Exception:
            pass
    
    def _schedule_optional_reapply_icons(self):
        if getattr(self, '_optional_reapply_pending', False):
            return
        self._optional_reapply_pending = True
        try:
            self.optional_window.after(100, lambda: self._do_optional_reapply_icons())
        except Exception:
            self._do_optional_reapply_icons()
    
    def _do_optional_reapply_icons(self):
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.optional_window.iconbitmap(ico_path)
                except Exception:
                    pass
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon_app(ico_path)
                        if hicon:
                            hwnd = self.optional_window.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                optional_icon = ImageTk.PhotoImage(img)
                try:
                    self.optional_window.wm_iconphoto(True, optional_icon)
                except Exception:
                    self.optional_window.iconphoto(False, optional_icon)
                self.optional_window._title_icon = optional_icon
        except Exception:
            pass
        finally:
            self._optional_reapply_pending = False

    def _select_all_optional(self):
        for var in self.column_vars.values():
            var.set(True)

    def _deselect_all_optional(self):
        for var in self.column_vars.values():
            var.set(False)

    def _update_overlay_opacity(self, value):
        opacity_value = int(value)
        alpha_value = opacity_value / 100.0
        self.opacity_label.configure(text=f"{opacity_value}%")
        self.config.overlay_opacity = opacity_value
        self.config.save()
        if self.overlay_enabled and self.overlay_manager:
            self.overlay_manager.set_opacity(alpha_value)

    def _update_overlay_size(self, size):
        self.config.overlay_size = size
        self.config.save()
        self._log(f"Overlay size: {size}")
        if self.overlay_enabled and self.overlay_manager and self.overlay_manager._instance:
            self.overlay_manager._instance.set_size(size)

    def _start_autosave(self):
        if self.autosave_manager.start():
            self.autosave_status.configure(text="Running", text_color="#4CAF50")
            self.autosave_start_btn.configure(text="Stop", command=self._stop_autosave, fg_color="#FF6B6B")
            self._log("Auto-save started")
        else:
            WarningDialog(self, "Auto-save", "Already running")

    def _stop_autosave(self):
        colors = self.theme_manager.get_theme_colors()
        if self.autosave_manager.stop():
            self.autosave_status.configure(text="Stopped", text_color=colors['secondary'])
            self.autosave_start_btn.configure(text="Start", command=self._start_autosave, fg_color=colors['primary'])
            self._log("Auto-save stopped")

    def _manual_save(self):
        if self.autosave_manager.save_now():
            self._log("Manual save completed")
        else:
            ErrorDialog(self, "Save Error", "Manual save failed!")

    def _update_autosave_interval(self, interval):
        self._apply_autosave_interval(interval)

    def _detect_all_commanders(self):
        try:
            journal_path = self.journal_path_var.get().strip() or self._get_auto_journal_path()
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
            self._log(f"Error detecting commanders: {e}")
            return ["Auto"]

    def _get_auto_journal_path(self):
        temp_monitor = JournalMonitor(None)
        return temp_monitor._find_journal_dir()

    def _browse_journal_path(self):
        folder = filedialog.askdirectory(title="Select Elite Dangerous Journal Folder")
        if folder:
            self.journal_path_var.set(folder)
            self.config.journal_path = folder
            self.config.save()

    def _test_journal_path(self):
        test_path = self.journal_path_var.get().strip()
        if not test_path:
            test_path = self._get_auto_journal_path()
        if not test_path:
            ErrorDialog(self, "Error", "No journal path found")
            return
        if not Path(test_path).exists():
            ErrorDialog(self, "Error", f"Path does not exist:\n{test_path}")
            return
        pattern_root = Path(test_path)
        journal_files = [str(p) for p in pattern_root.glob('Journal.*.log')]
        if journal_files:
            latest = max(journal_files, key=os.path.getmtime)
            InfoDialog(self, "Success", f"Journal path is valid!\n\nFound {len(journal_files)} files\nLatest: {Path(latest).name}")
        else:
            WarningDialog(self, "Warning", "Path exists but no journal files found")

    def _apply_journal_settings(self):
        manual_path = self.journal_path_var.get().strip() or None
        self.config.journal_path = manual_path if manual_path else ''
        self.config.save()
        if self.journal_monitor:
            self.journal_monitor.stop()
        self.journal_monitor = JournalMonitor(
            callback=self._handle_system_jump,
            manual_journal_path=manual_path,
            selected_commander=self.selected_commander.get()
        )
        self.journal_monitor.start()
        self._log(f"Journal monitor restarted")
        InfoDialog(self, "Success", "Journal monitor restarted")

    def _switch_commander(self, selected):
        if selected:
            self.config.selected_commander = selected
            self.config.save()
            self._log(f"Switching to commander: {selected}")
            if self.journal_monitor:
                self.journal_monitor.stop()
            manual_path = self.journal_path_var.get().strip() or None
            self.journal_monitor = JournalMonitor(
                callback=self._handle_system_jump,
                manual_journal_path=manual_path,
                selected_commander=selected
            )
            self.journal_monitor.start()
            threading.Thread(target=self._get_latest_cmdr_data, daemon=True).start()
            InfoDialog(self, "Success", f"Journal monitor restarted for commander: {selected}")

    def _update_widget_colors(self):
        try:
            if hasattr(self, 'system_labels'):
                for system_name, label in self.system_labels.items():
                    status = None
                    with self.route_manager as route:
                        for item in route:
                            if item.get('name') == system_name:
                                status = item.get('status', 'unvisited')
                                break
                    if status == 'visited':
                        label.configure(fg_color="#4CAF50")
                    elif status == 'skipped':
                        label.configure(fg_color="#FFA500")
                    else:
                        text_color = ("#E0E0E0",)
                        label.configure(fg_color="transparent", text_color=text_color)
            if hasattr(self, 'map_frame'):
                self.map_frame.refresh_colors()
        except Exception as e:
            logger.error(f"Widget color update error: {e}")

    def _reapply_theme_to_widgets(self):
        try:
            if hasattr(self, 'overlay_btn'):
                self.overlay_btn.configure(fg_color=self.theme_manager.get_theme_colors()['primary'])
            if hasattr(self, 'autosave_start_btn'):
                if self.autosave_start_btn.cget("text") == "▶ Start":
                    self.autosave_start_btn.configure(fg_color="#4CAF50")
                else:
                    self.autosave_start_btn.configure(fg_color="#FF6B6B")
            if hasattr(self, 'journal_apply_btn'):
                self.journal_apply_btn.configure(fg_color=self.theme_manager.get_theme_colors()['primary'])
            self._refresh_settings_tab_buttons()
        except Exception as e:
            logger.error(f"Reapply theme error: {e}")

    def _refresh_settings_tab_buttons(self):
        try:
            colors = self.theme_manager.get_theme_colors()
            if hasattr(self, 'overlay_btn'):
                self.overlay_btn.configure(
                    fg_color=colors['primary'],
                    hover_color=colors['secondary'],
                    text_color=("white" if ctk.get_appearance_mode() == 'Dark' else "white")
                )
            if hasattr(self, 'autosave_start_btn'):
                text = self.autosave_start_btn.cget("text")
                if text == "▶ Start":
                    self.autosave_start_btn.configure(fg_color="#4CAF50")
                else:
                    self.autosave_start_btn.configure(fg_color="#FF6B6B")
            if hasattr(self, 'autosave_save_btn'):
                self.autosave_save_btn.configure(
                    fg_color=(colors['primary'], colors['secondary']),
                    hover_color=(colors['secondary'], colors['primary']),
                    text_color=("white" if ctk.get_appearance_mode() == 'Dark' else "black")
                )
            if hasattr(self, 'journal_test_btn'):
                self.journal_test_btn.configure(
                    fg_color=(colors['primary'], colors['secondary']),
                    hover_color=(colors['secondary'], colors['primary']),
                )
            if hasattr(self, 'journal_apply_btn'):
                self.journal_apply_btn.configure(
                    fg_color=colors['primary'],
                    hover_color=colors['secondary'],
                    text_color="white"
                )
            if hasattr(self, 'refresh_cmdr_btn'):
                self.refresh_cmdr_btn.configure(
                    fg_color=(colors['primary'], colors['secondary']),
                    hover_color=(colors['secondary'], colors['primary']),
                )
            theme_button = None
            for widget in self.tab_settings.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkFrame) and hasattr(child, 'winfo_children'):
                            for subchild in child.winfo_children():
                                if isinstance(subchild, ctk.CTkButton) and "Apply Theme" in subchild.cget("text"):
                                    theme_button = subchild
                                    break
            if theme_button:
                colors = self.theme_manager.get_theme_colors()
                theme_button.configure(
                    fg_color=colors['primary'],
                    hover_color=colors['secondary'],
                    text_color="white"
                )
        except Exception as e:
            logger.error(f"Refresh settings buttons error: {e}")

    def _refresh_commanders_list(self):
        commanders = self._detect_all_commanders()
        if hasattr(self, 'cmdr_dropdown'):
            self.cmdr_dropdown.configure(values=commanders)
        current = self.selected_commander.get()
        if current not in commanders and commanders:
            self.selected_commander.set(commanders[0])
        self._log(f"Refreshed commanders list: {len(commanders)} found")
        return commanders

    def _update_autosave_status(self):
        if hasattr(self, 'autosave_manager') and self.autosave_manager:
            status = self.autosave_manager.get_status()
            if status['running']:
                next_save = status['next_save_in']
                if next_save:
                    mins = int(next_save / 60)
                    secs = int(next_save % 60)
                    status_text = f"Running ({mins}m {secs}s)"
                else:
                    status_text = "Running"
                self.autosave_status.configure(text=status_text, text_color="#4CAF50")
                if hasattr(self, 'autosave_start_btn'):
                    self.autosave_start_btn.configure(
                        text="Stop",
                        command=self._stop_autosave,
                        fg_color="#FF6B6B",
                        hover_color="#CC5555"
                    )
            else:
                colors = self.theme_manager.get_theme_colors()
                self.autosave_status.configure(text="Stopped", text_color=colors['secondary'])
                if hasattr(self, 'autosave_start_btn'):
                    colors = self.theme_manager.get_theme_colors()
                    self.autosave_start_btn.configure(
                        text="Start",
                        command=self._start_autosave,
                        fg_color=colors['primary'],
                        hover_color=colors['secondary']
                    )

    def _stop_autosave(self):
        if self.autosave_manager:
            if self.autosave_manager.stop():
                self._update_autosave_status()
                self._log("Auto-save stopped")
                return True
        return False

    def _apply_journal_settings(self):
        manual_path = self.journal_path_var.get().strip() or None
        self.config.journal_path = manual_path if manual_path else ''
        self.config.save()
        if self.journal_monitor:
            self.journal_monitor.stop()
            self.journal_monitor = None
        self.journal_monitor = JournalMonitor(
            callback=self._handle_system_jump,
            manual_journal_path=manual_path,
            selected_commander=self.selected_commander.get()
        )
        self.journal_monitor.start()
        path_used = manual_path if manual_path else "Auto-detected path"
        self._log(f"Journal Monitor restarted with: {path_used}")
        InfoDialog(self, "Success", "Journal monitor restarted with new settings!")
        threading.Thread(target=self._get_latest_cmdr_data, daemon=True).start()

    def _check_for_updates(self):
        if hasattr(self, 'update_manager') and self.update_manager:
            self.update_manager.manual_check()
        else:
            import webbrowser
            webbrowser.open("https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases")
            self._log("GitHub releases Page")

    def _save_jump_range(self):
        try:
            jump_range_str = self.jump_range.get().strip()
            if jump_range_str:
                try:
                    float_value = float(jump_range_str)
                    if float_value > 0:
                        self.config.ship_jump_range = jump_range_str
                        self.config.save()
                        logger.info(f"Ship jump range saved: {jump_range_str} LY")
                except ValueError:
                    pass
        except Exception as e:
            logger.error(f"Error saving jump range: {e}")

    def _open_theme_editor(self):
        try:
            ThemeEditor(self.root, self.ed_theme)
        except Exception as e:
            ErrorDialog(self, "Error", f"Could not open theme editor:\n{e}")
            logger.error(f"Theme editor error: {e}")

    def _get_available_themes(self):
        themes_dir = os.path.join("edmrn", "themes")
        theme_files = []
        if os.path.exists(themes_dir):
            for file in os.listdir(themes_dir):
                if file.endswith('.json'):
                    name = file.replace('.json', '').replace('_', ' ').title()
                    theme_files.append(name)
        if not theme_files:
            theme_files = ["Elite Dangerous"]
        return sorted(theme_files)

    def _change_theme_file(self, theme_name):
        theme_name = self.theme_manager.change_theme(theme_name)
        self.current_theme = theme_name
        self._log(f"Theme changed to: {theme_name}")
        
        theme_path = os.path.join(os.path.dirname(__file__), "themes", f"{theme_name}.json")
        if os.path.exists(theme_path):
            self.config.window_geometry = self.root.geometry()
            self.config.save()
            
            dialog = ConfirmDialog(
                self,
                "Theme Change",
                f"Theme '{theme_name}' selected!\n\nApplication will restart in 2 seconds to apply the new theme.\n\nContinue?"
            )
            
            if dialog.get_result():
                self._log("Restarting application to apply theme...")
                self.root.after(100, self._restart_application)
        else:
            WarningDialog(
                self,
                "Theme Not Found",
                f"Theme file '{theme_name}.json' not found."
            )
    def _calculate_neutron_route(self):
        self.neutron_manager.calculate_neutron_route()
    
    def _find_nearest_system_by_coordinates(self):
        try:
            x = self.nearest_x_entry.get().strip()
            y = self.nearest_y_entry.get().strip()
            z = self.nearest_z_entry.get().strip()
            
            if not all([x, y, z]):
                WarningDialog(self, "Input Error", "Please enter X, Y, and Z coordinates")
                return
            
            try:
                x_val = float(x)
                y_val = float(y)
                z_val = float(z)
            except ValueError:
                WarningDialog(self, "Input Error", "Coordinates must be numbers")
                return
            
            self._log(f"Searching for nearest system to coordinates: X={x_val}, Y={y_val}, Z={z_val}")
            
            def search_nearest():
                try:
                    import requests
                    url = "https://spansh.co.uk/api/nearest"
                    params = {
                        'x': x_val,
                        'y': y_val,
                        'z': z_val,
                        'limit': 5
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data and 'system' in data:
                        self.root.after(0, lambda: self._show_nearest_results(data, x_val, y_val, z_val))
                    else:
                        self.root.after(0, lambda: InfoDialog(self, "No Results", "No systems found near those coordinates"))
                
                except requests.RequestException as e:
                    self.root.after(0, lambda: ErrorDialog(self, "API Error", f"Failed to search: {str(e)[:100]}"))
                except Exception as e:
                    self.root.after(0, lambda: ErrorDialog(self, "Error", f"Search failed: {str(e)[:100]}"))
            
            threading.Thread(target=search_nearest, daemon=True).start()
            
        except Exception as e:
            ErrorDialog(self, "Error", f"Failed to search: {str(e)[:100]}")
    
    def _show_nearest_results(self, data, x, y, z):
        try:
            system = data.get('system')
            distance = data.get('distance', 0)
            
            if system:
                system_name = system.get('name', 'Unknown')
                sys_x = system.get('x', 0)
                sys_y = system.get('y', 0)
                sys_z = system.get('z', 0)
                
                message = f"Nearest System Found:\n\n"
                message += f"🌟 {system_name}\n"
                message += f"📍 Coordinates: X={sys_x:.2f}, Y={sys_y:.2f}, Z={sys_z:.2f}\n"
                message += f"📏 Distance: {distance:.2f} LY\n\n"
                message += f"Copy system name to use in route planner?"
                
                dialog = ConfirmDialog(self, "Nearest System", message)
                result = dialog.get_result()
                
                if result:
                    try:
                        temp_root = tk.Tk()
                        temp_root.withdraw()
                        temp_root.clipboard_clear()
                        temp_root.clipboard_append(system_name)
                        temp_root.update()
                        temp_root.destroy()
                        self._log(f"✓ '{system_name}' copied to clipboard (Distance: {distance:.2f} LY)")
                    except Exception:
                        self._log(f"ERROR: Failed to copy system name")
        
        except Exception as e:
            ErrorDialog(self, "Error", f"Failed to display results: {str(e)[:100]}")
    
    def _neutron_prev_waypoint(self):
        self.neutron_manager.neutron_prev_waypoint()
    def _neutron_next_waypoint(self):
        self.neutron_manager.neutron_next_waypoint()
    def _copy_current_neutron_system(self, auto=False):
        self.neutron_manager.copy_current_neutron_system(auto)
    def _update_neutron_navigation(self):
        self.neutron_manager.update_neutron_navigation()
    def _update_neutron_statistics(self, result):
        self.neutron_manager.update_neutron_statistics(result)
    def _update_neutron_statistics_from_loaded_route(self):
        self.neutron_manager.update_neutron_statistics_from_loaded_route()
    def _handle_neutron_system_jump(self, system_name):
        self.neutron_manager.handle_neutron_system_jump(system_name)
    
    def _handle_galaxy_system_jump(self, system_name: str):
        if not self.galaxy_route_waypoints:
            return
        
        for i, waypoint in enumerate(self.galaxy_route_waypoints):
            if waypoint.get('system', '').lower() == system_name.lower():
                self.galaxy_plotter.update_waypoint_status(self.galaxy_route_waypoints, system_name, 'visited')
                self.galaxy_current_waypoint_index = i
                self._update_galaxy_navigation()
                self._update_galaxy_statistics()
                self._log(f"Galaxy Plotter: Auto-detected jump to '{system_name}' (marked visited)")
                
                if hasattr(self, 'current_backup_folder') and self.current_backup_folder:
                    self.galaxy_plotter.save_galaxy_route(
                        self.current_backup_folder,
                        self.galaxy_route_waypoints,
                        self.galaxy_current_waypoint_index
                    )
                return
    def _get_current_system_from_journal(self):
        return self.neutron_manager.get_current_system_from_journal()
    def _sync_neutron_jump_range(self):
        if hasattr(self, 'neutron_range_var'):
            self.neutron_range_var.set(self.jump_range.get())
    
    def _use_current_location(self):
        try:
            if hasattr(self, 'journal_monitor') and self.journal_monitor:
                current_system = self.journal_monitor.get_current_system()
                if current_system:
                    self.starting_system.set(current_system)
                    self._log(f"Starting system set to current location: {current_system}")
                    InfoDialog(self, "Location Set", f"Starting system set to:\n{current_system}")
                else:
                    WarningDialog(self, "No Location", 
                                         "Could not detect current system.\n\n"
                                         "Make sure:\n"
                                         "• Elite Dangerous is running\n"
                                         "• You've jumped to a system recently\n"
                                         "• Journal monitoring is configured")
            else:
                WarningDialog(self, "Journal Not Ready", 
                                     "Journal monitoring not initialized.\n"
                                     "Please configure journal path in Settings first.")
        except Exception as e:
            logger.error(f"Error getting current location: {e}")
            ErrorDialog(self, "Error", f"Could not get current location:\n{e}")
    
    def _find_nearest_system(self, auto=False):
        try:
            if not hasattr(self, 'csv_systems_data') or self.csv_systems_data is None:
                if not auto:
                    WarningDialog(self, "No CSV Data", 
                                         "Please load a CSV file first.\n\n"
                                         "The CSV must contain System Name, X, Y, Z columns.")
                return
            
            if not hasattr(self, 'journal_monitor') or not self.journal_monitor:
                if not auto:
                    WarningDialog(self, "Journal Not Ready", 
                                         "Journal monitoring not initialized.\n"
                                         "Configure journal path in Settings first.")
                return
            
            if not hasattr(self.journal_monitor, 'journal_path') or not self.journal_monitor.journal_path:
                if not auto:
                    WarningDialog(self, "Journal Path Not Set", 
                                         "Journal path not configured.\n"
                                         "Configure journal path in Settings first.")
                return
            
            current_system = self.journal_monitor.get_current_system()
            if not current_system:
                if not auto:
                    WarningDialog(self, "No Location", 
                                         "Could not detect current system.\n\n"
                                         "Make sure Elite Dangerous is running\n"
                                         "and you've jumped recently.")
                return
            
            current_coords = self.journal_monitor.get_current_coordinates()
            if not current_coords or len(current_coords) != 3:
                if not auto:
                    WarningDialog(self, "No Coordinates", 
                                         f"Current system '{current_system}' detected\n"
                                         "but coordinates not available.\n\n"
                                         "Try jumping to another system first.")
                return
            
            import numpy as np
            curr_x, curr_y, curr_z = current_coords
            
            systems_df = self.csv_systems_data
            systems_df['distance'] = np.sqrt(
                (systems_df['X'] - curr_x)**2 + 
                (systems_df['Y'] - curr_y)**2 + 
                (systems_df['Z'] - curr_z)**2
            )
            
            nearest_row = systems_df.loc[systems_df['distance'].idxmin()]
            nearest_system = nearest_row['System Name']
            nearest_distance = nearest_row['distance']
            
            self.starting_system.set(nearest_system)
            
            info_msg = f"Nearest system from {current_system}:\n\n{nearest_system}\n\nDistance: {nearest_distance:.2f} LY"
            
            if not auto:
                InfoDialog(self, "Nearest System Found", info_msg)
            
            self._log(f"Nearest system: {nearest_system} ({nearest_distance:.2f} LY from {current_system})")
            
        except Exception as e:
            logger.error(f"Error finding nearest system: {e}")
            if not auto:
                ErrorDialog(self, "Error", f"Could not find nearest system:\n{e}")
    
    def _restart_application(self):
        try:
            self._cleanup()
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                subprocess.Popen([exe_path],
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                               close_fds=True,
                               stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                self.root.quit()
                self.root.destroy()
                os._exit(0)
            else:
                python = sys.executable
                os.execl(python, python, *sys.argv)
        except Exception as e:
            ErrorDialog(self, "Error", f"Could not restart application: {e}")
            logger.error(f"Restart error: {e}")
    
    def _get_system_suggestions(self, query: str, callback):
        self.system_autocompleter.get_suggestions_async(
            query, 
            callback,
            max_results=10
        )
    
    def _reverse_galaxy_route(self):
        source = self.galaxy_source_autocomplete.get()
        dest = self.galaxy_dest_autocomplete.get()
        
        self.galaxy_source_autocomplete.set(dest)
        self.galaxy_dest_autocomplete.set(source)
        
        self._log("Galaxy Plotter: Route reversed")
    
    def _calculate_galaxy_route(self):
        source = self.galaxy_source_autocomplete.get().strip()
        dest = self.galaxy_dest_autocomplete.get().strip()
        ship_build = self.galaxy_ship_build.get("1.0", "end").strip()
        
        if not source or not dest:
            WarningDialog(self, "Missing Input", "Please enter both source and destination systems.")
            return
        
        try:
            cargo = int(self.galaxy_cargo_var.get() or 0)
            reserve_fuel = float(self.galaxy_reserve_fuel_var.get() or 0.0)
        except ValueError:
            WarningDialog(self, "Invalid Input", "Cargo and Reserve Fuel must be numeric values.")
            return
        
        self.galaxy_output.configure(state="normal")
        self.galaxy_output.delete("1.0", "end")
        self.galaxy_output.insert("1.0", "Submitting route to Spansh API...\n\n")
        self.galaxy_output.insert("end", "⏳ Calculating route...\n\n")
        self.galaxy_output.configure(state="disabled")
        
        def progress_callback(message: str):
            self.galaxy_output.configure(state="normal")
            self.galaxy_output.insert("end", f"{message}\n")
            self.galaxy_output.see("end")
            self.galaxy_output.configure(state="disabled")
        
        def calculate_thread():
            try:
                result = self.galaxy_plotter.plot_route(
                    source_system=source,
                    destination_system=dest,
                    ship_build=ship_build,
                    cargo=cargo,
                    reserve_fuel=reserve_fuel,
                    already_supercharged=self.galaxy_already_supercharged.get(),
                    use_supercharge=self.galaxy_use_supercharge.get(),
                    use_injections=self.galaxy_use_injections.get(),
                    exclude_secondary=self.galaxy_exclude_secondary.get(),
                    refuel_every_scoopable=self.galaxy_refuel_every.get(),
                    routing_algorithm=self.galaxy_algorithm_var.get(),
                    progress_callback=lambda msg: self.root.after(0, lambda: progress_callback(msg))
                )
                
                self.root.after(0, lambda: self._display_galaxy_route_result(result))
                
            except Exception as e:
                error_msg = f"Error: {e}"
                logger.error(error_msg)
                self.root.after(0, lambda: self._display_galaxy_route_error(error_msg))
        
        threading.Thread(target=calculate_thread, daemon=True).start()
        self._log(f"Galaxy Plotter: Calculating route via Spansh API for {source} → {dest}")

    
    def _display_galaxy_route_result(self, result):
        self.galaxy_output.configure(state="normal")
        self.galaxy_output.delete("1.0", "end")
        
        if not result or "result" not in result:
            self.galaxy_output.insert("1.0", "No route data returned.\n")
            self.galaxy_output.configure(state="disabled")
            self.galaxy_current_btn.configure(text="No route calculated")
            self.galaxy_prev_btn.configure(state="disabled")
            self.galaxy_next_btn.configure(state="disabled")
            self._update_galaxy_systems_list()
            self._update_galaxy_statistics()
            return
        
        self.galaxy_plotter_route_data = result
        self.galaxy_export_btn.configure(state="normal")
        
        summary = self.galaxy_plotter.format_route_summary(result)
        self.galaxy_output.insert("1.0", "=== ROUTE SUMMARY ===\n")
        self.galaxy_output.insert("end", summary + "\n\n")
        
        self.galaxy_route_waypoints = self.galaxy_plotter.extract_system_jumps(result)
        self.galaxy_current_waypoint_index = 0
        self._update_galaxy_systems_list()
        self._update_galaxy_navigation()
        self._update_galaxy_statistics()
        self._copy_current_galaxy_system(auto=True)
        
        if hasattr(self, 'current_backup_folder') and self.current_backup_folder:
            self.galaxy_plotter.save_galaxy_route(self.current_backup_folder, self.galaxy_route_waypoints, self.galaxy_current_waypoint_index)
        
        if not self.journal_monitor:
            self._start_journal_monitor()
        self._ensure_overlay_started("Galaxy Plotter")
        
        self.galaxy_output.configure(state="disabled")

    
    def _display_galaxy_route_error(self, error_msg: str):
        self.galaxy_calculate_btn.configure(state="normal", text="🚀 Calculate Exact Route")
        self.galaxy_output.configure(state="normal")
        self.galaxy_output.insert("end", f"\n❌ {error_msg}\n")
        self.galaxy_output.configure(state="disabled")
        self._log(f"Galaxy Plotter: {error_msg}")
    
    def _export_galaxy_route(self):
        if not self.galaxy_plotter_route_data:
            WarningDialog(self, "No Route", "Please calculate a route first before exporting.")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            title="Export Galaxy Route",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            success = self.galaxy_plotter.export_route_to_csv(self.galaxy_plotter_route_data, filename)
            if success:
                InfoDialog(self, "Export Successful", f"Route exported to:\n{filename}")
                self._log(f"Galaxy Plotter: Route exported to {filename}")
            else:
                ErrorDialog(self, "Export Failed", "Failed to export route to CSV.")
                self._log("Galaxy Plotter: Route export failed")

    def _galaxy_prev_waypoint(self):
        if not self.galaxy_route_waypoints:
            return
        if self.galaxy_current_waypoint_index > 0:
            self.galaxy_current_waypoint_index -= 1
            self._update_galaxy_navigation()
            if hasattr(self, 'current_backup_folder') and self.current_backup_folder:
                self.galaxy_plotter.save_galaxy_route(
                    self.current_backup_folder,
                    self.galaxy_route_waypoints,
                    self.galaxy_current_waypoint_index
                )

    def _galaxy_next_waypoint(self):
        if not self.galaxy_route_waypoints:
            return
        if self.galaxy_current_waypoint_index < len(self.galaxy_route_waypoints) - 1:
            self.galaxy_plotter.mark_waypoint_as_visited(
                self.galaxy_route_waypoints,
                self.galaxy_current_waypoint_index
            )
            self.galaxy_current_waypoint_index += 1
            self._update_galaxy_navigation()
            self._update_galaxy_statistics()
            self._copy_current_galaxy_system(auto=True)
            if hasattr(self, 'current_backup_folder') and self.current_backup_folder:
                self.galaxy_plotter.save_galaxy_route(
                    self.current_backup_folder,
                    self.galaxy_route_waypoints,
                    self.galaxy_current_waypoint_index
                )

    def _copy_current_galaxy_system(self, auto: bool = False):
        if not self.galaxy_route_waypoints:
            if not auto:
                WarningDialog(self, "Warning", "No galaxy route calculated.")
            return
        current = self.galaxy_route_waypoints[self.galaxy_current_waypoint_index]
        current_system = current.get('system', 'Unknown')
        try:
            import pyperclip
            pyperclip.copy(current_system)
            if auto:
                self._log(f"Auto-copied galaxy waypoint: {current_system}")
            else:
                self._log(f"Copied galaxy waypoint: {current_system}")
        except ImportError:
            try:
                temp_root = tk.Tk()
                temp_root.withdraw()
                temp_root.clipboard_clear()
                temp_root.clipboard_append(current_system)
                temp_root.update()
                temp_root.destroy()
                self._log(f"Galaxy system copied: {current_system}")
            except Exception as e:
                if not auto:
                    ErrorDialog(self, "Error", f"Failed to copy to clipboard:\n{e}")
                self._log(f"Clipboard copy error (galaxy): {e}")

    def _update_galaxy_navigation(self):
        if not self.galaxy_route_waypoints:
            self.galaxy_current_btn.configure(text="No route calculated")
            self.galaxy_prev_btn.configure(state="disabled")
            self.galaxy_next_btn.configure(state="disabled")
            if hasattr(self, 'galaxy_scroll_frame'):
                for widget in self.galaxy_scroll_frame.winfo_children():
                    widget.destroy()
                no_route_label = ctk.CTkLabel(
                    self.galaxy_scroll_frame,
                    text="No route calculated",
                    font=ctk.CTkFont(size=12)
                )
                no_route_label.pack(pady=20)
            return

        idx = self.galaxy_current_waypoint_index
        total = len(self.galaxy_route_waypoints)
        current = self.galaxy_route_waypoints[idx]
        current_name = current.get('system', 'Unknown')
        self.galaxy_current_btn.configure(text=current_name)

        has_prev = idx > 0
        has_next = idx < total - 1
        self.galaxy_prev_btn.configure(state=("normal" if has_prev else "disabled"))
        self.galaxy_next_btn.configure(state=("normal" if has_next else "disabled"))

        self._update_galaxy_systems_list()
        
        if hasattr(self, 'galaxy_progress_label'):
            remaining = total - idx - 1
            progress_text = f"🎯 Progress Status | Current: {idx + 1}/{total} | Remaining: {remaining} waypoints"
            self.galaxy_progress_label.configure(text=progress_text)
        
        if self.overlay_enabled and self.tabview.get() == "Galaxy Plotter":
            try:
                self.overlay_manager.update_data()
            except Exception:
                pass
    
    def _update_galaxy_statistics(self):
        if not self.galaxy_route_waypoints or not self.galaxy_plotter_route_data:
            if hasattr(self, 'galaxy_stats_label'):
                self.galaxy_stats_label.configure(text="📊 Galaxy Statistics | No route calculated")
            if hasattr(self, 'galaxy_progress_label'):
                self.galaxy_progress_label.configure(text="🎯 Progress Status | Ready to calculate")
            return
        
        result = self.galaxy_plotter_route_data.get("result", {})
        total_distance = result.get("distance", 0)
        total_jumps = len(self.galaxy_route_waypoints)
        neutron_count = sum(1 for wp in self.galaxy_route_waypoints if wp.get("neutron_star", False))
        refuel_count = sum(1 for wp in self.galaxy_route_waypoints if wp.get("refuel", False))
        
        stats_text = f"📊 Galaxy Statistics | Distance: {total_distance:.2f} LY | Jumps: {total_jumps} | Neutrons: {neutron_count} | Refuels: {refuel_count}"
        
        if hasattr(self, 'galaxy_stats_label'):
            self.galaxy_stats_label.configure(text=stats_text)
        
        idx = self.galaxy_current_waypoint_index
        remaining = total_jumps - idx - 1
        progress_text = f"🎯 Progress Status | Current: {idx + 1}/{total_jumps} | Remaining: {remaining} waypoints"
        
        if hasattr(self, 'galaxy_progress_label'):
            self.galaxy_progress_label.configure(text=progress_text)
    
    def _update_galaxy_systems_list(self):
        if not hasattr(self, 'galaxy_scroll_frame'):
            return
        
        for widget in self.galaxy_scroll_frame.winfo_children():
            widget.destroy()
        
        if not self.galaxy_route_waypoints:
            no_route_label = ctk.CTkLabel(
                self.galaxy_scroll_frame,
                text="No route calculated",
                font=ctk.CTkFont(size=12)
            )
            no_route_label.pack(pady=20)
            return
        
        colors = self.theme_manager.get_theme_colors()
        
        for i, waypoint in enumerate(self.galaxy_route_waypoints):
            system_name = waypoint.get('system', 'Unknown')
            status = waypoint.get('status', 'unvisited')
            jumps_ct = waypoint.get('jumps', 1)
            neutron = waypoint.get('neutron_star', False)
            refuel = waypoint.get('refuel', False)
            
            if neutron:
                display_text = f"{i+1}. ⚡ {system_name}"
            elif refuel:
                display_text = f"{i+1}. ⛽ {system_name}"
            else:
                if jumps_ct > 1:
                    display_text = f"{i+1}. {system_name} ({jumps_ct} jumps)"
                else:
                    display_text = f"{i+1}. {system_name}"
            
            label = ctk.CTkLabel(
                self.galaxy_scroll_frame,
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

    def _complete_startup_in_background(self):
        try:
            self.update_manager = setup_auto_updates(self, delay_seconds=5)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_manager.create_backup(timestamp_str=timestamp)
            
            route_data = self.route_tracker.load_route_status()
            if route_data:
                self._create_route_tracker_tab_content()
            
            logger.info("Background startup completed successfully")
        except Exception as e:
            logger.error(f"Background startup error: {e}", exc_info=True)
