import customtkinter as ctk
import tkinter as tk
from edmrn.logger import get_logger
logger = get_logger('UIComponents')
class UIComponents:
    def __init__(self, app):
        self.app = app
    def create_header(self):
        colors = self.app.theme_manager.get_theme_colors()
        header_frame = ctk.CTkFrame(self.app.root,
                                   fg_color=colors['frame'],
                                   border_color=colors['border'],
                                   border_width=1,
                                   height=50)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 15))
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=0)
        header_frame.grid_propagate(False)
        cmdr_info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        cmdr_info_frame.grid(row=0, column=0, sticky="w", padx=15, pady=8)
        ctk.CTkLabel(cmdr_info_frame, text="CMDR:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=colors['primary']).grid(row=0, column=0, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.app.cmdr_name,
                     font=ctk.CTkFont(size=12),
                     text_color=colors['text']).grid(row=0, column=1, sticky="w", padx=(5, 15), pady=2)
        ctk.CTkLabel(cmdr_info_frame, text="CR:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=colors['primary']).grid(row=0, column=2, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.app.cmdr_cash,
                     font=ctk.CTkFont(size=11),
                     text_color=colors['text']).grid(row=0, column=3, sticky="w", padx=(5, 0), pady=2)
        update_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Check Update",
            command=self.app._check_for_updates,
            width=130,
            height=32,
            font=ctk.CTkFont(size=11)
        )
        self.app.theme_manager.apply_button_theme(update_btn, "primary")
        update_btn.grid(row=0, column=1, sticky="e", padx=(0, 15), pady=8)
    def create_optimizer_tab(self):
        colors = self.app.theme_manager.get_theme_colors()
        main_frame = ctk.CTkFrame(self.app.tab_optimizer, corner_radius=10, fg_color=colors['background'])
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        top_frame.columnconfigure(0, weight=4)
        top_frame.columnconfigure(2, weight=2)
        top_frame.columnconfigure(2, weight=2)
        csv_label = ctk.CTkLabel(top_frame, text="Route Data File (CSV):",
                                font=ctk.CTkFont(weight="bold"))
        csv_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        csv_input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        csv_input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        csv_input_frame.columnconfigure(0, weight=1)
        self.app.file_entry = ctk.CTkEntry(csv_input_frame, textvariable=self.app.csv_file_path)
        self.app.file_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        csv_btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        csv_btn_frame.grid(row=2, column=0, sticky="w", pady=(0, 10))
        self.app.file_button = ctk.CTkButton(
            csv_btn_frame,
            text="Browse / Reset",
            command=self.app._browse_file,
            width=80
        )
        self.app.theme_manager.apply_button_theme(self.app.file_button, "secondary")
        self.app.file_button.pack(side="left", padx=(0, 8))
        self.app.load_backup_btn = ctk.CTkButton(
            csv_btn_frame,
            text="Load Backup",
            command=self.app._load_backup_from_optimizer,
            width=100
        )
        self.app.theme_manager.apply_button_theme(self.app.load_backup_btn, "secondary")
        self.app.load_backup_btn.pack(side="left")
        jump_label = ctk.CTkLabel(top_frame, text="Ship Jump Range (LY):",
                                 font=ctk.CTkFont(weight="bold"))
        jump_label.grid(row=0, column=1, sticky="w", pady=(0, 8), padx=(15, 10))
        jump_input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        jump_input_frame.grid(row=1, column=1, sticky="w", pady=(0, 10), padx=(15, 10))
        self.app.range_entry = ctk.CTkEntry(jump_input_frame, textvariable=self.app.jump_range, width=120)
        self.app.jump_range.trace_add('write', lambda *args: self.app._save_jump_range())
        self.app.jump_range.trace_add('write', lambda *args: self.app._sync_neutron_jump_range())
        self.app.range_entry.pack(anchor="w")
        jump_btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent", height=30)
        jump_btn_frame.grid(row=2, column=1, sticky="w", pady=(0, 10), padx=(15, 10))
        jump_btn_frame.grid_propagate(False)
        start_label = ctk.CTkLabel(top_frame, text="Starting System (Optional):",
                                  font=ctk.CTkFont(weight="bold"))
        start_label.grid(row=0, column=2, sticky="w", pady=(0, 8), padx=(10, 0))
        start_input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        start_input_frame.grid(row=1, column=2, sticky="ew", pady=(0, 10), padx=(10, 0))
        start_input_frame.columnconfigure(0, weight=1)
        self.app.start_entry = ctk.CTkEntry(start_input_frame, textvariable=self.app.starting_system)
        self.app.start_entry.grid(row=0, column=0, sticky="ew")
        start_btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent", height=30)
        start_btn_frame.grid(row=2, column=2, sticky="w", pady=(0, 10), padx=(10, 0))
        start_btn_frame.grid_propagate(False)
        ctk.CTkLabel(main_frame, text="CSV Column Status:",
                    font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", pady=(15, 8))
        self.app.required_columns_frame = ctk.CTkFrame(main_frame, corner_radius=8, height=80)
        self.app.required_columns_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        self.app.required_columns_frame.grid_propagate(False)
        self.app.columns_container = ctk.CTkFrame(self.app.required_columns_frame, fg_color="transparent")
        self.app.columns_container.pack(fill="both", expand=True, padx=10, pady=8)
        self.app.column_status_label = ctk.CTkLabel(
            self.app.columns_container,
            text="Select a CSV file to check columns",
            text_color=("gray50", "gray70"),
            font=ctk.CTkFont(size=11)
        )
        self.app.column_status_label.pack(expand=True)
        self.app.column_indicators = {}
        self.app.current_csv_columns = []
        self.app.csv_file_path.trace_add('write', lambda *args: self.app._update_column_status_display())
        self.app.optional_toggle_btn = ctk.CTkButton(main_frame,
                                               text="Optional Columns",
                                               command=self.app._toggle_optional_columns,
                                               width=140, height=28)
        self.app.theme_manager.apply_button_theme(self.app.optional_toggle_btn, "secondary")
        self.app.optional_toggle_btn.grid(row=3, column=0, pady=(0, 20), sticky="w")
        self.app.run_button = ctk.CTkButton(main_frame, text="Optimize Route and Start Tracking",
                                       command=self.app._run_optimization_threaded,
                                       height=32,
                                       width=100,
                                       font=ctk.CTkFont(size=13, weight="bold"))
        self.app.theme_manager.apply_button_theme(self.app.run_button, "primary")
        self.app.run_button.grid(row=4, column=0, pady=20)
        ctk.CTkLabel(main_frame, text="Status/Output Console:",
                    font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, sticky="w", pady=(15, 8))
        self.app.output_text = ctk.CTkTextbox(main_frame, height=350)
        self.app.output_text.grid(row=6, column=0, padx=8, pady=(0, 15), sticky="nsew")
    def create_neutron_tab(self):
        colors = self.app.theme_manager.get_theme_colors()
        main_frame = ctk.CTkFrame(self.app.tab_neutron, corner_radius=10, fg_color=colors['background'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        left_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=colors['frame'])
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(6, weight=1)
        ctk.CTkLabel(left_frame, text="🌟 Neutron Highway Route Planner",
                    font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=(20, 20))
        input_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15), padx=20)
        input_frame.columnconfigure((0, 1), weight=1)
        from_frame = ctk.CTkFrame(input_frame, fg_color=colors['frame'])
        from_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(from_frame, text="From System:",
                    font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.app.neutron_from_var = ctk.StringVar()
        self.app.neutron_from_entry = ctk.CTkEntry(from_frame, textvariable=self.app.neutron_from_var,
                                              placeholder_text="Current system (auto-detected)")
        self.app.neutron_from_entry.pack(fill="x", padx=10, pady=(0, 10))
        to_frame = ctk.CTkFrame(input_frame, fg_color=colors['frame'])
        to_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ctk.CTkLabel(to_frame, text="To System:",
                    font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.app.neutron_to_var = ctk.StringVar()
        self.app.neutron_to_entry = ctk.CTkEntry(to_frame, textvariable=self.app.neutron_to_var,
                                            placeholder_text="Route destination (from CSV)")
        self.app.neutron_to_entry.pack(fill="x", padx=10, pady=(0, 10))
        settings_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        settings_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15), padx=20)
        settings_frame.columnconfigure((0, 1), weight=1)
        range_frame = ctk.CTkFrame(settings_frame, fg_color=colors['frame'])
        range_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(range_frame, text="Ship Jump Range (LY):",
                    font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.app.neutron_range_var = ctk.StringVar(value=self.app.jump_range.get())
        self.app.neutron_range_entry = ctk.CTkEntry(range_frame, textvariable=self.app.neutron_range_var)
        self.app.neutron_range_entry.pack(fill="x", padx=10, pady=(0, 10))
        boost_frame = ctk.CTkFrame(settings_frame, fg_color=colors['frame'])
        boost_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ctk.CTkLabel(boost_frame, text="FSD Boost:",
                    font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        colors = self.app.theme_manager.get_theme_colors()
        self.app.neutron_boost_var = ctk.StringVar(value="x4")
        self.app.neutron_boost_menu = ctk.CTkOptionMenu(
            boost_frame, values=["x4 (Normal)", "x6 (Caspian)"],
            variable=self.app.neutron_boost_var,
            fg_color=colors['primary'],
            button_color=colors['primary_hover'],
            text_color=colors['text'] if colors['text'] != colors['background'] else "#E0E0E0"
        )
        self.app.neutron_boost_menu.pack(fill="x", padx=10, pady=(0, 10))
        button_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, pady=(0, 15), padx=20)
        self.app.neutron_calculate_btn = ctk.CTkButton(
            button_frame, text="🚀 Calculate Neutron Route",
            command=self.app._calculate_neutron_route,
            height=35, width=200,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.neutron_calculate_btn, "primary")
        self.app.neutron_calculate_btn.pack(pady=(0, 10))
        nav_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(0, 5))
        self.app.neutron_prev_btn = ctk.CTkButton(
            nav_frame, text="<", width=40, height=35,
            command=self.app._neutron_prev_waypoint,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.neutron_prev_btn, "secondary")
        self.app.neutron_prev_btn.pack(side="left", padx=(0, 5))
        self.app.neutron_current_btn = ctk.CTkButton(
            nav_frame, text="No route calculated",
            command=self.app._copy_current_neutron_system,
            height=35, width=300,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.neutron_current_btn, "primary")
        self.app.neutron_current_btn.pack(side="left", padx=5)
        self.app.neutron_next_btn = ctk.CTkButton(
            nav_frame, text=">", width=40, height=35,
            command=self.app._neutron_next_waypoint,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.neutron_next_btn, "secondary")
        self.app.neutron_next_btn.pack(side="left", padx=(5, 0))
        info_frame = ctk.CTkFrame(left_frame, fg_color=colors['frame'])
        info_frame.grid(row=4, column=0, sticky="ew", pady=(0, 15), padx=20)
        info_frame.columnconfigure(0, weight=1)
        self.app.neutron_info_label = ctk.CTkLabel(
            info_frame, text="ℹ️ Enter systems and click Calculate to plan your neutron highway route",
            font=ctk.CTkFont(size=12)
        )
        self.app.neutron_info_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")
        stats_frame = ctk.CTkFrame(info_frame,
                                  fg_color=colors['frame'],
                                  border_color=colors['accent'],
                                  border_width=1,
                                  corner_radius=8)
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(5, 10), padx=10)
        stats_frame.columnconfigure(0, weight=1)
        self.app.neutron_stats_label = ctk.CTkLabel(stats_frame,
                                               text="📊 Neutron Statistics | No route calculated",
                                               font=ctk.CTkFont(family="Consolas", size=12, weight="normal"),
                                               text_color=colors['accent'])
        self.app.neutron_stats_label.grid(row=0, column=0, padx=8, pady=(8, 2), sticky="w")
        self.app.neutron_progress_label = ctk.CTkLabel(stats_frame,
                                                  text="🎯 Progress Status | Ready to calculate",
                                                  font=ctk.CTkFont(family="Consolas", size=12, weight="normal"),
                                                  text_color=colors['accent'])
        self.app.neutron_progress_label.grid(row=1, column=0, padx=8, pady=(2, 8), sticky="w")
        right_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=colors['frame'])
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        ctk.CTkLabel(right_frame, text="Neutron Route:",
                    font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=(15, 5), padx=15)
        self.app.neutron_output = ctk.CTkTextbox(right_frame, height=400)
        self.app.neutron_output.grid(row=1, column=0, sticky="nsew", pady=(0, 15), padx=15)
        self.app.neutron_output.insert("1.0", "No neutron route calculated yet.\n\nSteps:\n1. Enter your current system\n2. Enter destination system\n3. Set your ship's jump range\n4. Choose FSD boost type\n5. Click Calculate")
        self.app.neutron_output.configure(state="disabled")
    def create_bottom_buttons(self):
        bottom_frame = ctk.CTkFrame(self.app.root, fg_color="transparent", height=50)
        bottom_frame.grid(row=2, column=0, padx=25, pady=(10, 15), sticky="ew")
        bottom_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)
        github_btn = ctk.CTkButton(bottom_frame, text="GitHub",
                                   command=lambda: self.app._open_link("https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer"),
                                   height=32)
        self.app.theme_manager.apply_button_theme(github_btn, "secondary")
        github_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        discord_btn = ctk.CTkButton(bottom_frame, text="Discord",
                                   command=lambda: self.app._open_link("https://discord.gg/DWvCEXH7ae"),
                                   height=32)
        self.app.theme_manager.apply_button_theme(discord_btn, "secondary")
        discord_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        kofi_btn = ctk.CTkButton(bottom_frame, text="Ko-fi",
                                command=lambda: self.app._open_link("https://ko-fi.com/ninurtakalhu"),
                                fg_color="#FF5E5B",
                                text_color="white",
                                height=32)
        kofi_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        patreon_btn = ctk.CTkButton(bottom_frame, text="Patreon",
                                   command=lambda: self.app._open_link("https://www.patreon.com/c/NinurtaKalhu"),
                                   fg_color="#FF424D",
                                   text_color="white",
                                   height=32)
        patreon_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        about_btn = ctk.CTkButton(bottom_frame, text="About",
                                 command=self.app._show_about_info,
                                 height=32)
        self.app.theme_manager.apply_button_theme(about_btn, "primary")
        about_btn.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
