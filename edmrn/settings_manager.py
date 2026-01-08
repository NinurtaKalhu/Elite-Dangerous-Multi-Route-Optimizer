import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from edmrn.logger import get_logger
logger = get_logger('SettingsManager')
class SettingsManager:
    def __init__(self, app):
        self.app = app
    def create_settings_tab(self):
        colors = self.app.theme_manager.get_theme_colors()
        main_frame = ctk.CTkFrame(self.app.tab_settings, corner_radius=10, fg_color=colors['background'])
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        ctk.CTkLabel(main_frame, text="Application Settings",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 15))
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            height=550,
            fg_color=colors['frame'],
            border_color=colors['border'],
            border_width=1
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        for i in range(2):
            scroll_frame.rowconfigure(i, weight=1, uniform="settings_row")
        for j in range(2):
            scroll_frame.columnconfigure(j, weight=1, uniform="settings_col")
        overlay_frame = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color=colors['frame'])
        overlay_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.create_overlay_settings_card(overlay_frame)
        autosave_frame = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color=colors['frame'])
        autosave_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.create_autosave_settings_card(autosave_frame)
        journal_frame = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color=colors['frame'])
        journal_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.create_journal_settings_card(journal_frame)
        theme_frame = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color=colors['frame'])
        theme_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self.create_theme_settings_card(theme_frame)
    def create_overlay_settings_card(self, parent):
        ctk.CTkLabel(parent, text="📺 Overlay",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 15))
        self.app.overlay_btn = ctk.CTkButton(
            parent,
            text="▶ Start Overlay" if not self.app.overlay_enabled else "⏹ Stop Overlay",
            command=self.app._toggle_overlay,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.overlay_btn, "primary")
        self.app.overlay_btn.pack(pady=(0, 15), padx=10, fill="x")
        opacity_frame = ctk.CTkFrame(parent, fg_color="transparent")
        opacity_frame.pack(fill="x", padx=10, pady=(0, 10))
        opacity_header = ctk.CTkFrame(opacity_frame, fg_color="transparent")
        opacity_header.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(opacity_header, text="Opacity:",
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self.app.opacity_label = ctk.CTkLabel(opacity_header,
                                         text=f"{self.app.config.overlay_opacity}%",
                                         font=ctk.CTkFont(size=11, weight="bold"))
        self.app.opacity_label.pack(side="right")
        self.app.overlay_opacity = ctk.CTkSlider(opacity_frame, from_=50, to=100,
                                            number_of_steps=10,
                                            command=self.app._update_overlay_opacity)
        self.app.overlay_opacity.set(self.app.config.overlay_opacity)
        self.app.overlay_opacity.pack(fill="x", pady=(0, 5))
        size_frame = ctk.CTkFrame(parent, fg_color="transparent")
        size_frame.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(size_frame, text="Size:",
                     font=ctk.CTkFont(size=12)).pack(side="left", anchor="w")
        colors = self.app.theme_manager.get_theme_colors()
        self.app.overlay_size = ctk.CTkOptionMenu(size_frame,
                                             values=["Small", "Medium", "Large"],
                                             width=100, height=30,
                                             font=ctk.CTkFont(family="Segoe UI", size=12),
                                             fg_color=colors['primary'],
                                             button_color=colors['primary_hover'],
                                             button_hover_color=colors['primary'],
                                             text_color="white",
                                             command=self.app._update_overlay_size)
        self.app.overlay_size.set(self.app.config.overlay_size)
        self.app.overlay_size.pack(side="right", anchor="e")
    def create_autosave_settings_card(self, parent):
        ctk.CTkLabel(parent, text="💾 Auto-save",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 15))
        interval_frame = ctk.CTkFrame(parent, fg_color="transparent")
        interval_frame.pack(fill="x", padx=10, pady=(0, 15))
        ctk.CTkLabel(interval_frame, text="Interval:",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        colors = self.app.theme_manager.get_theme_colors()
        self.app.autosave_interval_menu = ctk.CTkOptionMenu(
            interval_frame,
            values=["1 minute", "5 minutes", "10 minutes", "Never"],
            variable=self.app.autosave_interval_var,
            width=120, height=30,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=colors['primary'],
            button_color=colors['primary_hover'],
            button_hover_color=colors['primary'],
            text_color="white",
            command=self.app._update_autosave_interval
        )
        self.app.autosave_interval_menu.grid(row=0, column=1, sticky="e")
        interval_frame.columnconfigure(1, weight=1)
        status_frame = ctk.CTkFrame(parent, fg_color="transparent")
        status_frame.pack(fill="x", padx=10, pady=(0, 15))
        ctk.CTkLabel(status_frame, text="Status:",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        colors = self.app.theme_manager.get_theme_colors()
        self.app.autosave_status = ctk.CTkLabel(status_frame, text="Stopped",
                                           font=ctk.CTkFont(size=12, weight="bold"),
                                           text_color=colors['secondary'])
        self.app.autosave_status.grid(row=0, column=1, sticky="e")
        status_frame.columnconfigure(1, weight=1)
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.app.autosave_start_btn = ctk.CTkButton(
            btn_frame, text="▶ Start", command=self.app._start_autosave,
            height=30, width=100,
            font=ctk.CTkFont(size=12)
        )
        self.app.theme_manager.apply_button_theme(self.app.autosave_start_btn, "success")
        self.app.autosave_start_btn.pack(side="left", padx=(0, 8))
        self.app.autosave_save_btn = ctk.CTkButton(
            btn_frame, text="💾 Save Now", command=self.app._manual_save,
            height=30, width=100,
            font=ctk.CTkFont(size=12)
        )
        self.app.theme_manager.apply_button_theme(self.app.autosave_save_btn, "secondary")
        self.app.autosave_save_btn.pack(side="left")
    def create_journal_settings_card(self, parent):
        ctk.CTkLabel(parent, text="📝 Journal",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 15))
        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.pack(fill="x", padx=10, pady=(0, 12))
        ctk.CTkLabel(path_frame, text="Path:",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.app.journal_entry = ctk.CTkEntry(path_frame, textvariable=self.app.journal_path_var,
                                         placeholder_text="Auto-detected",
                                         font=ctk.CTkFont(size=11))
        self.app.journal_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        path_frame.columnconfigure(1, weight=1)
        commanders = self.app._detect_all_commanders()
        cmdr_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cmdr_frame.pack(fill="x", padx=10, pady=(0, 15))
        ctk.CTkLabel(cmdr_frame, text="CMDR:",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        colors = self.app.theme_manager.get_theme_colors()
        self.app.cmdr_dropdown = ctk.CTkOptionMenu(cmdr_frame, values=commanders,
                                              variable=self.app.selected_commander,
                                              width=120, height=30,
                                              font=ctk.CTkFont(family="Segoe UI", size=12),
                                              fg_color=colors['primary'],
                                              button_color=colors['primary_hover'],
                                              button_hover_color=colors['primary'],
                                              text_color="white",
                                              command=self.app._switch_commander)
        self.app.cmdr_dropdown.grid(row=0, column=1, sticky="e")
        cmdr_frame.columnconfigure(1, weight=1)
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.app.journal_test_btn = ctk.CTkButton(
            btn_frame, text="🔍 Test", command=self.app._test_journal_path,
            height=30, width=90,
            font=ctk.CTkFont(size=12)
        )
        self.app.theme_manager.apply_button_theme(self.app.journal_test_btn, "secondary")
        self.app.journal_test_btn.pack(side="left", padx=(0, 8))
        self.app.journal_apply_btn = ctk.CTkButton(
            btn_frame, text="✓ Apply", command=self.app._apply_journal_settings,
            height=30, width=90,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.journal_apply_btn, "success")
        self.app.journal_apply_btn.pack(side="left")
        self.app.refresh_cmdr_btn = ctk.CTkButton(
            btn_frame, text="🔄 Refresh", command=self.app._refresh_commanders_list,
            height=30, width=90,
            font=ctk.CTkFont(size=12)
        )
        self.app.theme_manager.apply_button_theme(self.app.refresh_cmdr_btn, "secondary")
        self.app.refresh_cmdr_btn.pack(side="right")
    def create_theme_settings_card(self, parent):
        ctk.CTkLabel(parent, text="🎨 Theme",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 15))
        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.pack(fill="x", padx=10, pady=(0, 15))
        ctk.CTkLabel(theme_frame, text="Theme:",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        theme_files = [
            "Elite Dangerous",
            "Aisling Duval", "Archon Delaine", "Arissa Lavigny Duval",
            "Denton Patreus", "Edmund Mahon", "Felicia Winters",
            "Li Yong Rui", "Pranav Antal", "Zachary Hudson", "Zemina Torval"
        ]
        colors = self.app.theme_manager.get_theme_colors()
        self.app.theme_selector = ctk.CTkOptionMenu(
            theme_frame, values=theme_files,
            width=120, height=30,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=colors['primary'],
            button_color=colors['primary_hover'],
            button_hover_color=colors['primary'],
            text_color="white",
            command=self.app._change_theme_file
        )
        current_display = {
            'elite_dangerous': 'Elite Dangerous',
            'aisling_duval': 'Aisling Duval',
            'archon_delaine': 'Archon Delaine',
            'arissa_lavigny_duval': 'Arissa Lavigny Duval',
            'denton_patreus': 'Denton Patreus',
            'edmund_mahon': 'Edmund Mahon',
            'felicia_winters': 'Felicia Winters',
            'li_yong_rui': 'Li Yong Rui',
            'pranav_antal': 'Pranav Antal',
            'zachary_hudson': 'Zachary Hudson',
            'zemina_torval': 'Zemina Torval'
        }.get(self.app.current_theme, 'Elite Dangerous')
        self.app.theme_selector.set(current_display)
        self.app.theme_selector.grid(row=0, column=1, sticky="e")
        theme_frame.columnconfigure(1, weight=1)
