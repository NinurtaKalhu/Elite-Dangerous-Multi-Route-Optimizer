import sys
import os
import threading
import time
import json
import pandas as pd
import numpy as np
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from PIL import Image
import webbrowser
import glob
import platform
import subprocess
import traceback

from edmrn.logger import setup_logging
from edmrn.logger import get_logger
from edmrn.config import AppConfig, Paths
from edmrn.optimizer import RouteOptimizer
from edmrn.tracker import ThreadSafeRouteManager, RouteTracker, STATUS_VISITED, STATUS_SKIPPED, STATUS_UNVISITED
from edmrn.journal import JournalMonitor
from edmrn.overlay import get_overlay_manager
from edmrn.minimap import MiniMapFrame, MiniMapFrameFallback
from edmrn.backup import BackupManager
from edmrn.autosave import AutoSaveManager
from edmrn.platform import get_platform_detector
from edmrn.gui import ManualWindow, AboutWindow, BackupSelectionWindow
from edmrn.utils import resource_path
from edmrn.debug import get_debug_system, catch_and_record_errors, log_execution_time

logger = get_logger('App')

class EDMRN_App:
    def __init__(self):
        setup_logging()
        
        self.config = AppConfig.load()
        self.platform_detector = get_platform_detector()
        self.debug_system = get_debug_system()
        
        ctk.set_appearance_mode(self.config.appearance_mode)
        ctk.set_default_color_theme(self.config.color_theme)
        
        self._create_root_window()
        
        self.csv_file_path = ctk.StringVar()
        self.jump_range = ctk.StringVar(value="70.0")
        self.starting_system = ctk.StringVar()
        self.cmdr_name = ctk.StringVar(value="[CMDR Name: Loading...]")
        self.cmdr_cash = ctk.StringVar(value="N/A Cr")
        self.theme_mode = ctk.StringVar(value=self.config.appearance_mode)
        self.theme_color = ctk.StringVar(value=self.config.color_theme)
        self.journal_path_var = ctk.StringVar(value=self.config.journal_path)
        self.selected_commander = ctk.StringVar(value=self.config.selected_commander)
        self.autosave_interval_var = tk.StringVar(value=self.config.autosave_interval)
        
        self.route_manager = ThreadSafeRouteManager()
        self.route_tracker = RouteTracker(self.route_manager)
        self.route_optimizer = RouteOptimizer()
        
        self.system_labels = {}
        self.progress_label = None
        self.map_frame = None
        self.overlay_enabled = False
        self.overlay_manager = get_overlay_manager()
        self.journal_monitor = None
        self.column_vars = {}
        self.available_columns = []
        self.column_checkboxes = {}
        self.optional_window = None
        self._optimization_in_progress = False
        self.output_text = None
        self.debug_window = None
        
        self._create_widgets()
        self._setup_managers()
        self._autodetect_csv(initial_run=True)
        
        route_data = self.route_tracker.load_route_status()
        self.route_manager.load_route(route_data)
        
        if route_data:
            self._create_route_tracker_tab_content()
            self._start_journal_monitor()
        
        threading.Thread(target=self._get_latest_cmdr_data, daemon=True).start()
        self._setup_keyboard_shortcuts()
    
    def refresh_ui_theme(self):
        self.config = AppConfig.load()
        ctk.set_appearance_mode(self.config.appearance_mode)
        ctk.set_default_color_theme(self.config.color_theme)
        self._update_widget_colors()
        self._reapply_theme_to_widgets()
        if self.overlay_enabled:
            self.overlay_manager.stop()
            time.sleep(0.1)
            opacity = self.config.overlay_opacity / 100.0
            self.overlay_manager.start(self._get_overlay_data, opacity=opacity)
        self._log(f"UI theme refreshed: {self.config.appearance_mode} mode, {self.config.color_theme} color")
    
    def _create_root_window(self):
        self.root = ctk.CTk()
        self.root.title(f"ED Multi Route Navigation (EDMRN) v2.3.1")
        self.root.geometry("1100x800")
        self.root.minsize(1000, 700)
        try:
            self.root.iconbitmap(resource_path('assets/explorer_icon.ico'))
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_widgets(self):
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.tab_optimizer = self.tabview.add("1. Route Optimization")
        self.tab_tracker = self.tabview.add("2. Route Tracking")
        self.tab_settings = self.tabview.add("3. Settings")
        self.tabview.set("1. Route Optimization")
        self._create_header()
        self._create_optimizer_tab()
        self._create_settings_tab()
        self._create_bottom_buttons()
    
    def _create_header(self):
        header_frame = ctk.CTkFrame(self.root, fg_color=("gray85", "gray15"), height=45)
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=0)
        header_frame.grid_propagate(False)
        
        cmdr_info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        cmdr_info_frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        ctk.CTkLabel(cmdr_info_frame, text="CMDR:", 
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.cmdr_name, 
                     font=ctk.CTkFont(size=12)).grid(row=0, column=1, sticky="w", padx=(3, 12), pady=2)
        ctk.CTkLabel(cmdr_info_frame, text="CR:", 
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=2, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.cmdr_cash, 
                     font=ctk.CTkFont(size=11)).grid(row=0, column=3, sticky="w", padx=(3, 0), pady=2)
        
        debug_btn = ctk.CTkButton(
            header_frame, 
            text="🐛 Debug", 
            command=self._show_debug_window,
            width=80, height=28,
            fg_color="#FF9800",
            hover_color="#F57C00"
        )
        debug_btn.grid(row=0, column=1, sticky="e", padx=(0, 10), pady=5)
    
    def _create_optimizer_tab(self):
        main_frame = ctk.CTkFrame(self.tab_optimizer, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        row1_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        row1_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        row1_frame.columnconfigure(0, weight=3)
        row1_frame.columnconfigure(1, weight=1)
        row1_frame.columnconfigure(2, weight=2)
        
        ctk.CTkLabel(row1_frame, text="1. Route Data File (CSV):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        file_frame = ctk.CTkFrame(row1_frame, fg_color="transparent")
        file_frame.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        self.file_entry = ctk.CTkEntry(file_frame, textvariable=self.csv_file_path)
        self.file_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.file_button = ctk.CTkButton(file_frame, text="Browse / Reset", command=self._browse_file, width=80)
        self.file_button.grid(row=0, column=1, padx=5, sticky="e")
        
        ctk.CTkLabel(row1_frame, text="2. Ship Jump Range (LY):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", pady=(0, 5))
        self.range_entry = ctk.CTkEntry(row1_frame, textvariable=self.jump_range, width=120)
        self.range_entry.grid(row=1, column=1, padx=10, sticky="w")
        
        ctk.CTkLabel(row1_frame, text="3. Starting System (Optional):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w", pady=(0, 5))
        self.start_entry = ctk.CTkEntry(row1_frame, textvariable=self.starting_system)
        self.start_entry.grid(row=1, column=2, sticky="ew")
        
        ctk.CTkLabel(main_frame, text="4. CSV Column Status:", 
                    font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", pady=(10, 5))
        
        self.required_columns_frame = ctk.CTkFrame(main_frame, corner_radius=8, height=80)
        self.required_columns_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.required_columns_frame.grid_propagate(False)
        
        self.columns_container = ctk.CTkFrame(self.required_columns_frame, fg_color="transparent")
        self.columns_container.pack(fill="both", expand=True, padx=10, pady=8)
        
        self.column_status_label = ctk.CTkLabel(
            self.columns_container, 
            text="Select a CSV file to check columns",
            text_color=("gray50", "gray70"),
            font=ctk.CTkFont(size=11)
        )
        self.column_status_label.pack(expand=True)
        
        self.column_indicators = {}
        self.current_csv_columns = []
        self.csv_file_path.trace_add('write', lambda *args: self._update_column_status_display())
        
        self.optional_toggle_btn = ctk.CTkButton(main_frame, 
                                               text="Optional Columns", 
                                               command=self._toggle_optional_columns,
                                               width=140, height=28,
                                               fg_color="#2196F3", hover_color="#1976D2")
        self.optional_toggle_btn.grid(row=3, column=0, pady=(0, 15), sticky="w")
        
        self.run_button = ctk.CTkButton(main_frame, text="5. Optimize Route and Start Tracking", 
                                       command=self._run_optimization_threaded, 
                                       height=32,
                                       width=100,
                                       font=ctk.CTkFont(size=13, weight="bold"))
        self.run_button.grid(row=4, column=0, pady=15)
        
        ctk.CTkLabel(main_frame, text="Status/Output Console:", 
                    font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, sticky="w", pady=(10, 2))
        self.output_text = ctk.CTkTextbox(main_frame, height=350)
        self.output_text.grid(row=6, column=0, padx=5, pady=(0, 10), sticky="nsew")
    
    def _create_settings_tab(self):
        main_frame = ctk.CTkFrame(self.tab_settings, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        ctk.CTkLabel(main_frame, text="Application Settings", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 15))
        scroll_frame = ctk.CTkScrollableFrame(main_frame, height=550)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        for i in range(2):
            scroll_frame.rowconfigure(i, weight=1, uniform="settings_row")
        for j in range(2):
            scroll_frame.columnconfigure(j, weight=1, uniform="settings_col")
        
        overlay_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        overlay_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self._create_overlay_settings_card(overlay_frame)
        
        autosave_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        autosave_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self._create_autosave_settings_card(autosave_frame)
        
        journal_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        journal_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self._create_journal_settings_card(journal_frame)
        
        theme_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        theme_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self._create_theme_settings_card(theme_frame)
    
    def _create_overlay_settings_card(self, parent):
        ctk.CTkLabel(parent, text="📺 Overlay", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 15))
        self.overlay_btn = ctk.CTkButton(
            parent, 
            text="▶ Start Overlay" if not self.overlay_enabled else "⏹ Stop Overlay", 
            command=self._toggle_overlay,
            fg_color="#9C27B0", hover_color="#7B1FA2", height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.overlay_btn.pack(pady=(0, 15), padx=10, fill="x")
        opacity_frame = ctk.CTkFrame(parent, fg_color="transparent")
        opacity_frame.pack(fill="x", padx=10, pady=(0, 10))
        opacity_header = ctk.CTkFrame(opacity_frame, fg_color="transparent")
        opacity_header.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(opacity_header, text="Opacity:", 
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self.opacity_label = ctk.CTkLabel(opacity_header, 
                                         text=f"{self.config.overlay_opacity}%", 
                                         font=ctk.CTkFont(size=11, weight="bold"))
        self.opacity_label.pack(side="right")
        self.overlay_opacity = ctk.CTkSlider(opacity_frame, from_=50, to=100, 
                                            number_of_steps=10,
                                            command=self._update_overlay_opacity)
        self.overlay_opacity.set(self.config.overlay_opacity)
        self.overlay_opacity.pack(fill="x", pady=(0, 5))
        size_frame = ctk.CTkFrame(parent, fg_color="transparent")
        size_frame.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(size_frame, text="Size:", 
                     font=ctk.CTkFont(size=12)).pack(side="left", anchor="w")
        self.overlay_size = ctk.CTkOptionMenu(size_frame, 
                                             values=["Small", "Medium", "Large"],
                                             width=100, height=30, 
                                             font=ctk.CTkFont(size=12),
                                             command=self._update_overlay_size)
        self.overlay_size.set(self.config.overlay_size)
        self.overlay_size.pack(side="right", anchor="e")
    
    def _create_autosave_settings_card(self, parent):
        ctk.CTkLabel(parent, text="💾 Auto-save", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 15))
        interval_frame = ctk.CTkFrame(parent, fg_color="transparent")
        interval_frame.pack(fill="x", padx=10, pady=(0, 15))
        ctk.CTkLabel(interval_frame, text="Interval:", 
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.autosave_interval_menu = ctk.CTkOptionMenu(
            interval_frame, 
            values=["1 minute", "5 minutes", "10 minutes", "Never"],
            variable=self.autosave_interval_var,
            width=120, height=30,
            font=ctk.CTkFont(size=12),
            command=self._update_autosave_interval
        )
        self.autosave_interval_menu.grid(row=0, column=1, sticky="e")
        interval_frame.columnconfigure(1, weight=1)
        status_frame = ctk.CTkFrame(parent, fg_color="transparent")
        status_frame.pack(fill="x", padx=10, pady=(0, 15))
        ctk.CTkLabel(status_frame, text="Status:", 
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.autosave_status = ctk.CTkLabel(status_frame, text="Stopped", 
                                           font=ctk.CTkFont(size=12, weight="bold"),
                                           text_color="#757575")
        self.autosave_status.grid(row=0, column=1, sticky="e")
        status_frame.columnconfigure(1, weight=1)
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.autosave_start_btn = ctk.CTkButton(
            btn_frame, text="▶ Start", command=self._start_autosave,
            fg_color="#4CAF50", hover_color="#45a049", height=30, width=100,
            font=ctk.CTkFont(size=12)
        )
        self.autosave_start_btn.pack(side="left", padx=(0, 8))
        self.autosave_save_btn = ctk.CTkButton(
            btn_frame, text="💾 Save Now", command=self._manual_save,
            height=30, width=100,
            font=ctk.CTkFont(size=12)
        )
        self.autosave_save_btn.pack(side="left")
    
    def _create_journal_settings_card(self, parent):
        ctk.CTkLabel(parent, text="📝 Journal", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 15))
        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.pack(fill="x", padx=10, pady=(0, 12))
        ctk.CTkLabel(path_frame, text="Path:", 
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.journal_entry = ctk.CTkEntry(path_frame, textvariable=self.journal_path_var, 
                                         placeholder_text="Auto-detected",
                                         font=ctk.CTkFont(size=11))
        self.journal_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        path_frame.columnconfigure(1, weight=1)
        commanders = self._detect_all_commanders()
        cmdr_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cmdr_frame.pack(fill="x", padx=10, pady=(0, 15))
        ctk.CTkLabel(cmdr_frame, text="CMDR:", 
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.cmdr_dropdown = ctk.CTkOptionMenu(cmdr_frame, values=commanders, 
                                              variable=self.selected_commander,
                                              width=120, height=30, 
                                              font=ctk.CTkFont(size=12),
                                              command=self._switch_commander)
        self.cmdr_dropdown.grid(row=0, column=1, sticky="e")
        cmdr_frame.columnconfigure(1, weight=1)
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.journal_test_btn = ctk.CTkButton(
            btn_frame, text="🔍 Test", command=self._test_journal_path, 
            height=30, width=90,
            font=ctk.CTkFont(size=12)
        )
        self.journal_test_btn.pack(side="left", padx=(0, 8))
        self.journal_apply_btn = ctk.CTkButton(
            btn_frame, text="✓ Apply", command=self._apply_journal_settings,
            fg_color="#4CAF50", hover_color="#45a049", height=30, width=90,
            font=ctk.CTkFont(size=12)
        )
        self.journal_apply_btn.pack(side="left")
        self.refresh_cmdr_btn = ctk.CTkButton(
            btn_frame, text="🔄 Refresh", command=self._refresh_commanders_list,
            height=30, width=90,
            font=ctk.CTkFont(size=12)
        )
        self.refresh_cmdr_btn.pack(side="right")
    
    def _create_theme_settings_card(self, parent):
        ctk.CTkLabel(parent, text="🎨 Theme", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 15))
        mode_frame = ctk.CTkFrame(parent, fg_color="transparent")
        mode_frame.pack(fill="x", padx=10, pady=(0, 15))
        ctk.CTkLabel(mode_frame, text="Mode:", 
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.theme_mode_menu = ctk.CTkOptionMenu(
            mode_frame, values=["Dark", "Light", "System"],
            variable=self.theme_mode, width=120, height=30,
            font=ctk.CTkFont(size=12),
            command=self._change_appearance_mode_event
        )
        self.theme_mode_menu.grid(row=0, column=1, sticky="e")
        mode_frame.columnconfigure(1, weight=1)
        color_frame = ctk.CTkFrame(parent, fg_color="transparent")
        color_frame.pack(fill="x", padx=10, pady=(0, 15))
        ctk.CTkLabel(color_frame, text="Color:", 
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.theme_color_menu = ctk.CTkOptionMenu(
            color_frame, values=["green", "blue", "dark-blue"],
            variable=self.theme_color, width=120, height=30,
            font=ctk.CTkFont(size=12),
            command=self._change_color_theme_event
        )
        self.theme_color_menu.grid(row=0, column=1, sticky="e")
        color_frame.columnconfigure(1, weight=1)
        update_frame = ctk.CTkFrame(parent, fg_color="transparent")
        update_frame.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkButton(
            update_frame, text="Apply Theme", 
            command=lambda: self._change_color_theme_event(self.theme_color.get()),
            height=30, width=120,
            font=ctk.CTkFont(size=12),
            fg_color="#1E88E5", hover_color="#1565C0"
        ).pack()
    
    def _create_bottom_buttons(self):
        bottom_frame = ctk.CTkFrame(self.root, fg_color="transparent", height=40)
        bottom_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        bottom_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)
        github_btn = ctk.CTkButton(bottom_frame, text="GitHub", command=lambda: self._open_link("https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer"), height=28)
        github_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        discord_btn = ctk.CTkButton(bottom_frame, text="Discord", command=lambda: self._open_link("https://discord.gg/DWvCEXH7ae"), height=28)
        discord_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        kofi_btn = ctk.CTkButton(bottom_frame, text="Ko-fi", command=lambda: self._open_link("https://ko-fi.com/ninurtakalhu"), height=28, fg_color="#FF5E5B", hover_color="#E04E4B")
        kofi_btn.grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        patreon_btn = ctk.CTkButton(bottom_frame, text="Patreon", command=lambda: self._open_link("https://www.patreon.com/c/NinurtaKalhu"), height=28, fg_color="#FF424D", hover_color="#E03A45")
        patreon_btn.grid(row=0, column=3, padx=2, pady=2, sticky="ew")
        about_btn = ctk.CTkButton(bottom_frame, text="About", command=self._show_about_info, height=28, fg_color="#1E88E5", hover_color="#1565C0")
        about_btn.grid(row=0, column=4, padx=2, pady=2, sticky="ew")
    
    def _setup_managers(self):
        backup_dirs = [Paths.get_app_data_dir()]
        self.backup_manager = BackupManager(
            backup_dir=Paths.get_backup_folder(), 
            source_dirs=backup_dirs, 
            log_callback=self._log
        )
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
            self.overlay_manager.start(self._get_overlay_data, opacity=opacity)
            self.overlay_enabled = True
            self.overlay_btn.configure(text="Stop Overlay")
            self._log("Cross-Platform Overlay started!")
        else:
            self.overlay_manager.stop()
            self.overlay_enabled = False
            self.overlay_btn.configure(text="Start Overlay")
            self._log("Overlay stopped")
    
    def _get_overlay_data(self):
        return self.route_tracker.get_overlay_data(self)
    
    def _apply_autosave_interval(self, interval):
        self.config.autosave_interval = interval
        self.config.save()
        if interval == "1 minute": minutes = 1
        elif interval == "5 minutes": minutes = 5
        elif interval == "10 minutes": minutes = 10
        else: minutes = 0
        if self.autosave_manager: self.autosave_manager.set_interval(minutes)
        self._log(f"Auto-save interval: {interval}")
    
    def _browse_file(self):
        for widget in self.tab_tracker.winfo_children():
            widget.destroy()
        
        filename = filedialog.askopenfilename(
            defaultextension=".csv", 
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            self.csv_file_path.set(filename)
            self._log(f"File: {filename}")
    
    def _run_optimization_threaded(self):
        if self._optimization_in_progress:
            self._log("Optimization already in progress")
            return
        self._optimization_in_progress = True
        self.run_button.configure(state='disabled', text="Optimizing...")
        def optimization_wrapper():
            try:
                self._run_optimization()
            except Exception as e:
                error_msg = f"Optimization failed: {str(e)[:100]}"
                self.root.after(0, lambda: self._log(f"{error_msg}"))
            finally:
                self._optimization_in_progress = False
                self.root.after(0, lambda: self.run_button.configure(state='normal', text="5. Optimize Route and Start Tracking"))
        threading.Thread(target=optimization_wrapper, daemon=True).start()
    
    @catch_and_record_errors
    @log_execution_time
    def _run_optimization(self):
        csv_path = self.csv_file_path.get()
        if not csv_path or not Path(csv_path).exists():
            messagebox.showerror("Error", "Please select a valid CSV file.")
            return
        try:
            jump_range = float(self.jump_range.get())
            if jump_range <= 0:
                messagebox.showerror("Error", "Ship jump range must be a positive number.")
                return
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number for ship jump range.")
            return
        starting_system_name = self.starting_system.get().strip()
        existing_status = {}
        route_data = self.route_manager.get_route()
        for route in route_data:
            existing_status[route['name']] = route['status']
        result = self.route_optimizer.optimize_route(csv_path, jump_range, starting_system_name, existing_status)
        if not result['success']:
            messagebox.showerror("Error", result['error'])
            return
        optimized_df = result['optimized_df']
        output_file_name = f"Optimized_Route_{result['num_systems']}_J{result['total_jumps']}_M{jump_range:.1f}LY.csv"
        output_file_path = Path(Paths.get_backup_folder()) / output_file_name
        Path(Paths.get_backup_folder()).mkdir(exist_ok=True)
        optimized_df.to_csv(output_file_path, index=False)
        self.route_manager.load_route(result['route_data'])
        self.route_tracker.save_route_status(result['route_data'])
        self.total_distance_ly = result['total_distance']
        self._create_route_tracker_tab_content()
        self.tabview.set("2. Route Tracking")
        self._start_journal_monitor()
        self._copy_next_system_to_clipboard()
        self._log("\nOPTIMIZATION COMPLETE")
        self._log(f"Total Distance: {result['total_distance']:.2f} LY")
        self._log(f"Estimated Jumps: {result['total_jumps']} jumps")
        self._log(f"Route successfully saved to: '{output_file_path}'")
        self._log("Switched to Route Tracking tab (with 3D Map).")
        self._log("Auto-Tracking STARTED (Monitoring Elite Dangerous Journal).")
        messagebox.showinfo("Success", f"Route optimization complete and Auto-Tracking is ready.\nFile: {output_file_name}")
    
    def _create_route_tracker_tab_content(self):
        if hasattr(self, 'system_labels'):
            for label in self.system_labels.values():
                try:
                    label.destroy()
                except:
                    pass
            self.system_labels.clear()
        if hasattr(self, 'map_frame') and self.map_frame:
            try:
                if hasattr(self.map_frame, 'clear_plot'):
                    self.map_frame.clear_plot()
                self.map_frame.destroy()
            except:
                pass
            self.map_frame = None
        for attr in ['progress_label', 'stats_total_label', 'stats_traveled_label', 
                     'stats_avg_jump_label', 'scroll_frame']:
            if hasattr(self, attr):
                setattr(self, attr, None)
        for widget in self.tab_tracker.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        import gc
        gc.collect()
        self.root.update_idletasks()
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
        try:
            self.map_frame = MiniMapFrame(left_frame, on_system_selected=self._handle_system_click, corner_radius=8)
        except Exception:
            self.map_frame = MiniMapFrameFallback(left_frame, on_system_selected=self._handle_system_click, corner_radius=8)
        self.map_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        button_frame = ctk.CTkFrame(left_frame, corner_radius=8)
        button_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        button_frame.columnconfigure((0, 1, 2, 3), weight=1)
        button_frame.rowconfigure(0, weight=1)
        button_frame.rowconfigure(1, weight=1)
        copy_next_btn = ctk.CTkButton(button_frame, text="Copy Next", command=self._copy_next_system_to_clipboard, 
                                     fg_color="#FF9800", hover_color="#F57C00", height=22, font=ctk.CTkFont(size=11))
        copy_next_btn.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        open_folder_btn = ctk.CTkButton(button_frame, text="Data Folder", command=self._open_app_data_folder,
                                       height=22, font=ctk.CTkFont(size=11))
        open_folder_btn.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        open_csv_btn = ctk.CTkButton(button_frame, text="Open Excel", command=self._open_output_csv,
                                    height=22, font=ctk.CTkFont(size=11))
        open_csv_btn.grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        backup_btn = ctk.CTkButton(button_frame, text="Load Backup", command=self._load_from_backup,
                                  height=22, font=ctk.CTkFont(size=11), fg_color="#9C27B0", hover_color="#7B1FA2")
        backup_btn.grid(row=0, column=3, padx=3, pady=3, sticky="ew")
        stats_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=(2, 5), sticky="nsew")
        stats_frame.columnconfigure(0, weight=1)
        self.stats_total_label = ctk.CTkLabel(stats_frame, text="Total Route: 0.00 LY", font=ctk.CTkFont(size=11, weight="bold"))
        self.stats_total_label.grid(row=0, column=0, pady=(2, 0))
        self.stats_traveled_label = ctk.CTkLabel(stats_frame, text="Traveled: 0.00 LY", font=ctk.CTkFont(size=11))
        self.stats_traveled_label.grid(row=1, column=0, pady=(1, 0))
        self.stats_avg_jump_label = ctk.CTkLabel(stats_frame, text="Avg Jump: 0.0 LY", font=ctk.CTkFont(size=11))
        self.stats_avg_jump_label.grid(row=2, column=0, pady=(1, 0))
        right_frame = ctk.CTkFrame(main_container, corner_radius=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        self.progress_label = ctk.CTkLabel(right_frame, text="Loading route status...", font=ctk.CTkFont(weight="bold"))
        self.progress_label.pack(pady=(15, 10))
        ctk.CTkLabel(right_frame, text="Route Details:", font=ctk.CTkFont(weight="bold")).pack(pady=(0, 10))
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
            label = ctk.CTkLabel(self.scroll_frame, text=f"{i+1}. {display_name}", 
                                anchor="w", justify="left", cursor="hand2", 
                                font=ctk.CTkFont(size=14, underline=True), fg_color="transparent")
            label.pack(fill="x", padx=10, pady=2)
            label.bind("<Button-1>", lambda event, name=system_name: self._handle_system_click_manual(name))
            self.system_labels[system_name] = label
            self._update_label_color(system_name, status)
        has_coords = route_data and 'coords' in route_data[0]
        if has_coords:
            self.map_frame.plot_route(route_data)
        self._update_route_statistics()
        self._update_progress_info()
    
    def _handle_system_click_manual(self, system_name):
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
        if response:
            new_status = STATUS_VISITED
        else:
            new_status = STATUS_SKIPPED
        status_changed = self.route_manager.update_system_status(system_name, new_status)
        if status_changed:
            self._update_label_color(system_name, new_status)
            if self.map_frame:
                self.map_frame.update_system_status(system_name, new_status)
            self._update_progress_info()
            self._update_route_statistics()
            self.route_tracker.save_route_status(self.route_manager.get_route())
            self._log(f"'{system_name}' status updated to: {new_status.upper()}")
    
    def _update_label_color(self, system_name, status):
        if system_name in self.system_labels:
            label = self.system_labels[system_name]
            if status == STATUS_VISITED:
                label.configure(fg_color="#4CAF50", text_color='white')
            elif status == STATUS_SKIPPED:
                label.configure(fg_color="#E53935", text_color='white')
            else:
                text_color = ('#DCE4EE' if ctk.get_appearance_mode() == 'Dark' else '#212121')
                label.configure(fg_color="transparent", text_color=text_color)
    
    def _update_progress_info(self):
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
    
    def _update_route_statistics(self):
        try:
            ship_jump_range = float(self.jump_range.get() or "70.0")
        except ValueError:
            ship_jump_range = 70.0
        self.route_tracker.update_route_statistics(ship_jump_range)
        if hasattr(self, 'stats_total_label'):
            self.stats_total_label.configure(text=f"Total Route: {self.route_tracker.total_distance_ly:.2f} LY")
        if hasattr(self, 'stats_traveled_label'):
            self.stats_traveled_label.configure(text=f"Traveled: {self.route_tracker.traveled_distance_ly:.2f} LY")
        if hasattr(self, 'stats_avg_jump_label'):
            self.stats_avg_jump_label.configure(text=f"Avg Jump: {self.route_tracker.average_jump_range:.1f} LY")
    
    def _open_app_data_folder(self):
        try:
            import subprocess
            path = Paths.get_app_data_dir()
            Path(path).mkdir(exist_ok=True)
            if os.name == 'nt':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', path])
            else:
                subprocess.call(['xdg-open', path])
            self._log(f"Opened data folder: '{path}'")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open data folder:\n{Paths.get_app_data_dir()}")
            self._log(f"ERROR opening data folder: {e}")
    
    def _open_output_csv(self):
        backup_files = list(Path(Paths.get_backup_folder()).glob("Optimized_Route_*.csv"))
        if not backup_files:
            messagebox.showerror("Error", "No optimized route file found. Please run optimization first.")
            return
        latest_file = max(backup_files, key=lambda x: x.stat().st_mtime)
        try:
            import subprocess
            if os.name == 'nt':
                os.startfile(str(latest_file))
            elif sys.platform == 'darwin':
                subprocess.call(['open', str(latest_file)])
            else:
                subprocess.call(['xdg-open', str(latest_file)])
            self._log(f"Opened CSV file: '{latest_file.name}'")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file automatically:\n{latest_file}")
            self._log(f"ERROR opening CSV: {e}")
    
    def _load_from_backup(self):
        try:
            backup_files = list(Path(Paths.get_backup_folder()).glob("*.csv"))
            main_dir_files = list(Path(Paths.get_app_data_dir()).glob("Optimized_Route_*.csv"))
            backup_files.extend(main_dir_files)
            if not backup_files:
                messagebox.showinfo("Info", "No backup files found.")
                return
            file_str = "\n".join([f"- {f.name}" for f in backup_files[:5]])
            if len(backup_files) > 5:
                file_str += f"\n- ... and {len(backup_files) - 5} more"
            choice = messagebox.askyesno("Load Backup", f"Found {len(backup_files)} backup files.\n\nLoad the most recent one?\n\nRecent: {backup_files[0].name}")
            if choice:
                self._load_backup_file(str(backup_files[0]))
        except Exception as e:
            messagebox.showerror("Error", f"Error loading backup: {e}")
            self._log(f"Backup loading error: {e}")
    
    def _load_backup_file(self, file_path):
        try:
            df = pd.read_csv(file_path)
            route_data = []
            for _, row in df.iterrows():
                bodies_data = []
                if 'Bodies_To_Scan_List' in row:
                    bodies_str = row['Bodies_To_Scan_List']
                    if isinstance(bodies_str, str) and bodies_str.startswith('['):
                        import ast
                        bodies_data = ast.literal_eval(bodies_str)
                route_data.append({
                    'name': row['System Name'],
                    'status': row.get('Status', STATUS_UNVISITED),
                    'coords': [float(row['X']), float(row['Y']), float(row['Z'])],
                    'bodies_to_scan': bodies_data,
                    'body_count': len(bodies_data)
                })
            self.route_manager.load_route(route_data)
            self.route_tracker.save_route_status(route_data)
            self._create_route_tracker_tab_content()
            self._log(f"Backup loaded: {Path(file_path).name}")
            messagebox.showinfo("Success", f"Backup loaded successfully:\n{Path(file_path).name}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading backup file: {e}")
    
    def _handle_system_click(self, system_name):
        if self.map_frame:
            self.map_frame.highlight_system(system_name)
    
    def _start_journal_monitor(self):
        if self.journal_monitor:
            self.journal_monitor.stop()
        manual_path = self.journal_path_var.get().strip() or None
        self.journal_monitor = JournalMonitor(callback=self._handle_system_jump, manual_journal_path=manual_path, selected_commander=self.selected_commander.get())
        self.journal_monitor.start()
    
    @catch_and_record_errors
    def _handle_system_jump(self, system_name):
        self.root.after(0, lambda: self._update_system_status_from_monitor(system_name, 'visited'))
    
    def _update_system_status_from_monitor(self, system_name, new_status):
        if not self.route_manager.contains_system(system_name):
            self._log(f"Jumped to '{system_name}' (not on current route).")
            return
        status_changed = self.route_manager.update_system_status(system_name, new_status)
        if status_changed:
            self._update_label_color(system_name, new_status)
            if self.map_frame:
                self.map_frame.update_system_status(system_name, new_status)
            self._update_progress_info()
            self._update_route_statistics()
            self.route_tracker.save_route_status(self.route_manager.get_route())
            self._copy_next_system_to_clipboard()
            self._log(f"Auto-Detected Jump to '{system_name}'. Status updated to {new_status.upper()}.")
    
    def _copy_next_system_to_clipboard(self):
        next_system_name = self.route_tracker.get_next_unvisited_system()
        if next_system_name:
            try:
                temp_root = tk.Tk()
                temp_root.withdraw()
                temp_root.clipboard_clear()
                temp_root.clipboard_append(next_system_name)
                temp_root.update()
                temp_root.destroy()
                self._log(f"'{next_system_name}' (Next System) copied to clipboard.")
            except Exception:
                self._log("ERROR: Failed to copy system name to clipboard.")
        else:
            self._log("INFO: Route complete. Nothing to copy.")
    
    def _autodetect_csv(self, initial_run=False):
        csv_path = self.csv_file_path.get()
        if not csv_path or not Path(csv_path).exists():
            if initial_run:
                csv_files = list(Path.cwd().glob('*.csv'))
                if csv_files:
                    self.csv_file_path.set(str(csv_files[0]))
                    self._log(f"Auto-Detected: '{csv_files[0].name}' file selected.")
                else:
                    if initial_run:
                        self._log("Warning: CSV file not found. Please use 'Browse' to select one.")
    
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
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        event = data.get('event')
                        if event == 'Commander': cmdr_name_default = data.get('Name', cmdr_name_default)
                        elif event == 'LoadGame': cmdr_cash = data.get('Credits', cmdr_cash)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self._log(f"ERROR reading CMDR data from Journal: {e}")
        final_cmdr_name = cmdr_name_default
        final_cmdr_cash = self._format_cash(cmdr_cash)
        try:
            self.root.after(0, lambda: self.cmdr_name.set(final_cmdr_name))
            self.root.after(0, lambda: self.cmdr_cash.set(final_cmdr_cash))
        except RuntimeError:
            return
        self._log(f"CMDR Status Loaded: {final_cmdr_name}, {final_cmdr_cash}")
    
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
    
    def _show_about_info(self):
        self.about_window = AboutWindow(self.root, self._open_link, self._show_manual)
    
    def _show_manual(self):
        self.manual_window = ManualWindow(self.root)
    
    def _show_debug_window(self):
        try:
            if self.debug_window is None or not self.debug_window.winfo_exists():
                from edmrn.debug_gui import DebugWindow
                self.debug_window = DebugWindow(self.root)
            else:
                self.debug_window.lift()
                self.debug_window.focus_force()
        except Exception as e:
            logger.error(f"Error opening debug window: {e}")
            messagebox.showerror("Error", f"Cannot open debug window: {e}")
    
    def _setup_keyboard_shortcuts(self):
        self.root.bind('<Control-D>', lambda e: self._show_debug_window())
        self.root.bind('<F12>', lambda e: self._show_debug_window())
        self.root.bind('<Control-O>', lambda e: self._toggle_overlay())
    
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
            ctk.CTkLabel(self.columns_container, 
                        text="Select a CSV file to check column status",
                        text_color=("gray50", "gray70"),
                        font=ctk.CTkFont(size=11)).pack(expand=True)
            return
        try:
            columns_status, all_columns = self.route_optimizer.check_csv_columns(csv_path)
            if not columns_status:
                ctk.CTkLabel(self.columns_container, 
                            text="❌ Unable to read CSV file",
                            text_color="#E53935",
                            font=ctk.CTkFont(size=11, weight="bold")).pack(expand=True)
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
                status_color = "#4CAF50" if is_available else "#E53935"
                status_icon = "✓" if is_available else "✗"
                status_text = "Found" if is_available else "MISSING"
                col_label = ctk.CTkLabel(frame, text=display_name, font=ctk.CTkFont(size=10, weight="bold"), anchor="w")
                col_label.grid(row=0, column=0, padx=(6, 3), pady=5, sticky="w")
                status_label = ctk.CTkLabel(frame, text=status_text, text_color=status_color, font=ctk.CTkFont(size=9), anchor="e")
                status_label.grid(row=0, column=1, padx=3, pady=5, sticky="ew")
                icon_label = ctk.CTkLabel(frame, text=status_icon, text_color=status_color, font=ctk.CTkFont(size=12, weight="bold"), anchor="e")
                icon_label.grid(row=0, column=2, padx=(0, 6), pady=5, sticky="e")
                self.column_indicators[col_key] = {'frame': frame, 'available': is_available}
            all_required = all(columns_status[col] for col in ['System Name', 'Body Name', 'X Coord', 'Y Coord', 'Z Coord'])
            if all_required:
                self.run_button.configure(state='normal', text="5. Optimize Route and Start Tracking")
            else:
                self.run_button.configure(state='disabled', text="❌ Missing required columns")
        except Exception as e:
            self._log(f"Column status update error: {e}")
            ctk.CTkLabel(self.columns_container, 
                        text=f"Error checking CSV: {str(e)[:50]}",
                        text_color="#E53935",
                        font=ctk.CTkFont(size=11)).pack(expand=True)
    
    def _toggle_optional_columns(self):
        if self.optional_window and self.optional_window.winfo_exists():
            self.optional_window.destroy()
            self.optional_window = None
            return
        csv_path = self.csv_file_path.get()
        if not csv_path or not Path(csv_path).exists():
            messagebox.showwarning("Warning", "Please select a CSV file first.")
            return
        try:
            df = pd.read_csv(csv_path, nrows=5)
            self.available_columns = df.columns.tolist()
        except Exception as e:
            messagebox.showerror("Error", f"Cannot read CSV: {e}")
            return
        required_columns = ['System Name', 'X', 'Y', 'Z']
        optional_columns = [col for col in self.available_columns if col not in required_columns]
        if not optional_columns:
            messagebox.showinfo("Info", "No optional columns found in CSV.")
            return
        self.optional_window = ctk.CTkToplevel(self.root)
        self.optional_window.title("Optional Columns Selection")
        self.optional_window.geometry("500x400")
        self.optional_window.transient(self.root)
        self.optional_window.grab_set()
        main_container = ctk.CTkFrame(self.optional_window)
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        ctk.CTkLabel(main_container, text="Select Optional Columns", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))
        scroll_frame = ctk.CTkScrollableFrame(main_container)
        scroll_frame.pack(fill="both", expand=True, pady=5)
        for col in sorted(optional_columns):
            if col not in self.column_vars:
                self.column_vars[col] = tk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(scroll_frame, text=col, variable=self.column_vars[col])
            chk.pack(anchor="w", padx=10, pady=2)
            self.column_checkboxes[col] = chk
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        select_all_btn = ctk.CTkButton(button_frame, text="Select All", 
                                      command=self._select_all_optional, width=100)
        select_all_btn.pack(side="left", padx=(0, 10))
        deselect_all_btn = ctk.CTkButton(button_frame, text="Deselect All", 
                                        command=self._deselect_all_optional, width=100)
        deselect_all_btn.pack(side="left", padx=(0, 10))
        close_btn = ctk.CTkButton(button_frame, text="Close", 
                                 command=lambda: self.optional_window.destroy(),
                                 width=100, fg_color="#757575")
        close_btn.pack(side="right")
    
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
    
    def _start_autosave(self):
        if self.autosave_manager.start():
            self.autosave_status.configure(text="Running", text_color="#4CAF50")
            self.autosave_start_btn.configure(text="Stop", command=self._stop_autosave, fg_color="#f44336")
            self._log("Auto-save started")
        else:
            messagebox.showwarning("Auto-save", "Already running")
    
    def _stop_autosave(self):
        if self.autosave_manager.stop():
            self.autosave_status.configure(text="Stopped", text_color="#757575")
            self.autosave_start_btn.configure(text="Start", command=self._start_autosave, fg_color="#4CAF50")
            self._log("Auto-save stopped")
    
    def _manual_save(self):
        if self.autosave_manager.save_now():
            self._log("Manual save completed")
        else:
            messagebox.showerror("Save Error", "Manual save failed!")
    
    def _update_autosave_interval(self, interval):
        self._apply_autosave_interval(interval)
    
    def _detect_all_commanders(self):
        commanders = set()
        journal_path = self.journal_path_var.get().strip() or self._get_auto_journal_path()
        if not journal_path or not Path(journal_path).exists():
            return ["Auto"]
        try:
            pattern = Path(journal_path) / 'Journal.*.log'
            journal_files = glob.glob(str(pattern))
            for file_path in journal_files:
                filename = Path(file_path).name
                parts = filename.split('.')
                if len(parts) >= 3:
                    commander_name = parts[1]
                    if commander_name and commander_name not in ['beta', 'live', 'tmp']:
                        commanders.add(commander_name)
            commander_list = sorted(list(commanders))
            return ["Auto"] + commander_list
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
            messagebox.showerror("Error", "No journal path found")
            return
        if not Path(test_path).exists():
            messagebox.showerror("Error", f"Path does not exist:\n{test_path}")
            return
        pattern = Path(test_path) / 'Journal.*.log'
        journal_files = glob.glob(str(pattern))
        if journal_files:
            latest = max(journal_files, key=os.path.getmtime)
            messagebox.showinfo("Success", f"Journal path is valid!\n\nFound {len(journal_files)} files\nLatest: {Path(latest).name}")
        else:
            messagebox.showwarning("Warning", "Path exists but no journal files found")
    
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
        messagebox.showinfo("Success", "Journal monitor restarted")
    
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
            messagebox.showinfo("Success", f"Journal monitor restarted for commander: {selected}")
    
    def _change_appearance_mode_event(self, new_mode):
        ctk.set_appearance_mode(new_mode)
        self.config.appearance_mode = new_mode
        self.config.save()
        self._update_widget_colors()
        self._log(f"Appearance mode changed to: {new_mode}")
    
    def _change_color_theme_event(self, new_theme):
        ctk.set_default_color_theme(new_theme)
        self.config.color_theme = new_theme
        self.config.save()
        self.config = AppConfig.load()
        self._reapply_theme_to_widgets()
        self._log(f"Color theme changed to: {new_theme}")
    
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
                        label.configure(fg_color="#4CAF50", text_color='white')
                    elif status == 'skipped':
                        label.configure(fg_color="#E53935", text_color='white')
                    else:
                        text_color = ('#DCE4EE' if ctk.get_appearance_mode() == 'Dark' else '#212121')
                        label.configure(fg_color="transparent", text_color=text_color)
            if hasattr(self, 'map_frame'):
                self.map_frame.refresh_colors()
        except Exception as e:
            logger.error(f"Widget color update error: {e}")
    
    def _reapply_theme_to_widgets(self):
        try:
            if hasattr(self, 'overlay_btn'):
                self.overlay_btn.configure(fg_color="#9C27B0", hover_color="#7B1FA2")
            if hasattr(self, 'autosave_start_btn'):
                if self.autosave_start_btn.cget("text") == "▶ Start":
                    self.autosave_start_btn.configure(fg_color="#4CAF50", hover_color="#45a049")
                else:
                    self.autosave_start_btn.configure(fg_color="#f44336", hover_color="#d32f2f")
            if hasattr(self, 'journal_apply_btn'):
                self.journal_apply_btn.configure(fg_color="#4CAF50", hover_color="#45a049")
            self._refresh_settings_tab_buttons()
        except Exception as e:
            logger.error(f"Reapply theme error: {e}")
    
    def _refresh_settings_tab_buttons(self):
        try:
            if hasattr(self, 'overlay_btn'):
                self.overlay_btn.configure(
                    fg_color="#9C27B0", 
                    hover_color="#7B1FA2",
                    text_color=("white" if ctk.get_appearance_mode() == 'Dark' else "white")
                )
            if hasattr(self, 'autosave_start_btn'):
                text = self.autosave_start_btn.cget("text")
                if text == "▶ Start":
                    self.autosave_start_btn.configure(fg_color="#4CAF50", hover_color="#45a049")
                else:
                    self.autosave_start_btn.configure(fg_color="#f44336", hover_color="#d32f2f")
            if hasattr(self, 'autosave_save_btn'):
                self.autosave_save_btn.configure(
                    fg_color=("#2b2b2b" if ctk.get_appearance_mode() == 'Dark' else "#e0e0e0"),
                    hover_color=("#3b3b3b" if ctk.get_appearance_mode() == 'Dark' else "#d0d0d0"),
                    text_color=("white" if ctk.get_appearance_mode() == 'Dark' else "black")
                )
            if hasattr(self, 'journal_test_btn'):
                self.journal_test_btn.configure(
                    fg_color=("#2b2b2b" if ctk.get_appearance_mode() == 'Dark' else "#e0e0e0"),
                    hover_color=("#3b3b3b" if ctk.get_appearance_mode() == 'Dark' else "#d0d0d0")
                )
            if hasattr(self, 'journal_apply_btn'):
                self.journal_apply_btn.configure(
                    fg_color="#4CAF50", 
                    hover_color="#45a049",
                    text_color="white"
                )
            if hasattr(self, 'refresh_cmdr_btn'):
                self.refresh_cmdr_btn.configure(
                    fg_color=("#2b2b2b" if ctk.get_appearance_mode() == 'Dark' else "#e0e0e0"),
                    hover_color=("#3b3b3b" if ctk.get_appearance_mode() == 'Dark' else "#d0d0d0")
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
                theme_button.configure(
                    fg_color="#1E88E5", 
                    hover_color="#1565C0",
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
                        fg_color="#f44336", 
                        hover_color="#d32f2f"
                    )
            else:
                self.autosave_status.configure(text="Stopped", text_color="#757575")
                if hasattr(self, 'autosave_start_btn'):
                    self.autosave_start_btn.configure(
                        text="Start", 
                        command=self._start_autosave,
                        fg_color="#4CAF50", 
                        hover_color="#45a049"
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
        messagebox.showinfo("Success", "Journal monitor restarted with new settings!")
        threading.Thread(target=self._get_latest_cmdr_data, daemon=True).start()