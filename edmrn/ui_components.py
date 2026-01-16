import customtkinter as ctk
import tkinter as tk
from pathlib import Path
from edmrn.logger import get_logger
from edmrn.autocomplete_entry import AutocompleteEntry

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
                     font=ctk.CTkFont(size=12),
                     text_color=colors['text']).grid(row=0, column=3, sticky="w", padx=(5, 12), pady=2)
        ctk.CTkLabel(cmdr_info_frame, text="Location:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=colors['primary']).grid(row=0, column=4, sticky="w", pady=2)
        ctk.CTkLabel(cmdr_info_frame, textvariable=self.app.cmdr_location,
                     font=ctk.CTkFont(size=12),
                     text_color=colors['text']).grid(row=0, column=5, sticky="w", padx=(5, 0), pady=2)
        update_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Check Update",
            command=self.app._check_for_updates,
            width=130,
            height=32,
            font=ctk.CTkFont(size=12)
        )
        self.app.theme_manager.apply_button_theme(update_btn, "primary")
        update_btn.grid(row=0, column=1, sticky="e", padx=(0, 15), pady=8)
    def create_optimizer_tab(self):
        colors = self.app.theme_manager.get_theme_colors()
        main_frame = ctk.CTkFrame(self.app.tab_optimizer, corner_radius=10, fg_color=colors['background'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=0)
        main_frame.rowconfigure(6, weight=1)
        top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top_frame.columnconfigure(0, weight=4)
        top_frame.columnconfigure(2, weight=2)
        top_frame.columnconfigure(2, weight=2)
        csv_label = ctk.CTkLabel(top_frame, text="Route Data File (CSV):",
                                font=ctk.CTkFont(size=13, weight="bold"))
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
            width=80,
            font=ctk.CTkFont(size=12)
        )
        self.app.theme_manager.apply_button_theme(self.app.file_button, "secondary")
        self.app.file_button.pack(side="left", padx=(0, 8))
        self.app.load_backup_btn = ctk.CTkButton(
            csv_btn_frame,
            text="Load Backup",
            command=self.app._load_backup_from_optimizer,
            width=100,
            font=ctk.CTkFont(size=12)
        )
        self.app.theme_manager.apply_button_theme(self.app.load_backup_btn, "secondary")
        self.app.load_backup_btn.pack(side="left")
        jump_label = ctk.CTkLabel(top_frame, text="Ship Jump Range (LY):",
                                 font=ctk.CTkFont(size=13, weight="bold"))
        jump_label.grid(row=0, column=1, sticky="w", pady=(0, 8), padx=(15, 10))
        jump_input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        jump_input_frame.grid(row=1, column=1, sticky="ew", pady=(0, 10), padx=(15, 10))
        jump_input_frame.columnconfigure(0, weight=1)
        self.app.range_entry = ctk.CTkEntry(jump_input_frame, textvariable=self.app.jump_range)
        self.app.jump_range.trace_add('write', lambda *args: self.app._save_jump_range())
        self.app.jump_range.trace_add('write', lambda *args: self.app._sync_neutron_jump_range())
        self.app.range_entry.pack(anchor="w", fill="x")
        jump_btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent", height=30)
        jump_btn_frame.grid(row=2, column=1, sticky="w", pady=(0, 10), padx=(15, 10))
        jump_btn_frame.grid_propagate(False)
        start_label = ctk.CTkLabel(top_frame, text="Starting System (Optional):",
                                  font=ctk.CTkFont(size=13, weight="bold"))
        start_label.grid(row=0, column=2, sticky="w", pady=(0, 8), padx=(10, 0))
        
        start_input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        start_input_frame.grid(row=1, column=2, sticky="ew", pady=(0, 10), padx=(10, 0))
        start_input_frame.columnconfigure(0, weight=1)
        
        entry_container = ctk.CTkFrame(start_input_frame, fg_color="transparent")
        entry_container.grid(row=0, column=0, sticky="ew")
        entry_container.columnconfigure(0, weight=1)
        
        self.app.start_entry = ctk.CTkEntry(
            entry_container,
            textvariable=self.app.starting_system,
            placeholder_text="Type or select system...",
            width=160
        )
        self.app.start_entry.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        
        self.app.start_dropdown_btn = ctk.CTkButton(
            entry_container,
            text="▼",
            width=38,
            command=self._toggle_system_dropdown
        )
        self.app.start_dropdown_btn.grid(row=0, column=1)
        
        self.app.start_dropdown_frame = None
        self.app.start_systems_list = []
        
        start_btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent", height=30)
        start_btn_frame.grid(row=2, column=2, sticky="w", pady=(0, 10), padx=(10, 0))
        start_btn_frame.grid_propagate(False)
        
        nearest_btn = ctk.CTkButton(
            start_btn_frame,
            text="🎯 Find Nearest",
            command=self.app._find_nearest_system,
            width=140,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        nearest_btn.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(main_frame, text="CSV Column Status:",
                    font=ctk.CTkFont(size=13, weight="bold")).grid(row=1, column=0, sticky="w", pady=(8, 8))
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
                                               width=140, height=28,
                                               font=ctk.CTkFont(size=12))
        self.app.theme_manager.apply_button_theme(self.app.optional_toggle_btn, "secondary")
        self.app.optional_toggle_btn.grid(row=3, column=0, pady=(0, 12), sticky="w")
        self.app.run_button = ctk.CTkButton(main_frame, text="Optimize & Track",
                                       command=self.app._run_optimization_threaded,
                                       height=36,
                                       width=200,
                                       font=ctk.CTkFont(size=13, weight="bold"))
        self.app.theme_manager.apply_button_theme(self.app.run_button, "primary")
        self.app.run_button.grid(row=4, column=0, pady=(10, 5))
        ctk.CTkLabel(main_frame, text="Console",
                font=ctk.CTkFont(size=13, weight="bold")).grid(row=5, column=0, sticky="w", pady=(5, 4), padx=8)

        console_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        console_container.grid(row=6, column=0, columnspan=2, padx=(8, 8), pady=(0, 15), sticky="nsew")
        console_container.columnconfigure(0, weight=1)
        console_container.rowconfigure(0, weight=1)
        
        self.app.output_text = ctk.CTkTextbox(console_container, height=350, wrap="word")
        self.app.output_text.grid(row=0, column=0, sticky="nsew")
    def create_neutron_tab(self):
        colors = self.app.theme_manager.get_theme_colors()
        main_frame = ctk.CTkFrame(self.app.tab_neutron, corner_radius=10, fg_color=colors['background'])
        main_frame.pack(fill="both", expand=True, padx=16, pady=12)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        left_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=colors['frame'])
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(6, weight=1)
        
        ctk.CTkLabel(left_frame, text="🌟 Neutron Highway Route Planner",
                    font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=(12, 12))
        
        input_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10), padx=15)
        input_frame.columnconfigure((0, 1), weight=1)
        
        from_frame = ctk.CTkFrame(input_frame, fg_color=colors['frame'])
        from_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(from_frame, text="From System:",
                    font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        self.app.neutron_from_autocomplete = AutocompleteEntry(
            from_frame, 
            placeholder_text="Type 3+ chars for suggestions...",
            suggestion_provider=self.app._get_system_suggestions,
            fg_color="transparent"
        )
        self.app.neutron_from_autocomplete.pack(fill="x", padx=10, pady=(0, 10))
        
        to_frame = ctk.CTkFrame(input_frame, fg_color=colors['frame'])
        to_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ctk.CTkLabel(to_frame, text="To System:",
                    font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        self.app.neutron_to_autocomplete = AutocompleteEntry(
            to_frame,
            placeholder_text="Type 3+ chars for suggestions...",
            suggestion_provider=self.app._get_system_suggestions,
            fg_color="transparent"
        )
        self.app.neutron_to_autocomplete.pack(fill="x", padx=10, pady=(0, 10))
        settings_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        settings_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10), padx=15)
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
        button_frame.grid(row=3, column=0, pady=(0, 10), padx=15)
        self.app.neutron_calculate_btn = ctk.CTkButton(
            button_frame, text="Optimize & Track",
            command=self.app._calculate_neutron_route,
            height=35, width=200,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.neutron_calculate_btn, "primary")
        self.app.neutron_calculate_btn.pack(pady=(0, 10))
        nav_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(0, 5))
        self.app.neutron_prev_btn = ctk.CTkButton(
            nav_frame, text="<", width=40, height=35,
            command=self.app._neutron_prev_waypoint,
            font=ctk.CTkFont(size=14, weight="bold")
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
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.neutron_next_btn, "secondary")
        self.app.neutron_next_btn.pack(side="left", padx=(5, 0))
        
        info_frame = ctk.CTkFrame(left_frame, fg_color=colors['frame'])
        info_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10), padx=15)
        info_frame.columnconfigure(0, weight=1)
        self.app.neutron_info_label = ctk.CTkLabel(
            info_frame, text="ℹ️ Enter systems and click Calculate to plan your neutron highway route",
            font=ctk.CTkFont(size=12)
        )
        self.app.neutron_info_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")
        
        nearest_frame = ctk.CTkFrame(info_frame, fg_color=colors['secondary'], corner_radius=6)
        nearest_frame.grid(row=1, column=0, sticky="ew", pady=(5, 5), padx=10)
        nearest_frame.columnconfigure((2, 4, 6), weight=1)
        
        ctk.CTkLabel(nearest_frame, text="Find Nearest System:", 
                     font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=(8, 12), pady=6, sticky="w")
        
        ctk.CTkLabel(nearest_frame, text="X:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=(0, 2), pady=6, sticky="e")
        self.app.nearest_x_entry = ctk.CTkEntry(nearest_frame, width=70, height=24, font=ctk.CTkFont(size=11))
        self.app.nearest_x_entry.grid(row=0, column=2, padx=(0, 8), pady=6, sticky="ew")
        
        ctk.CTkLabel(nearest_frame, text="Y:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=3, padx=(0, 2), pady=6, sticky="e")
        self.app.nearest_y_entry = ctk.CTkEntry(nearest_frame, width=70, height=24, font=ctk.CTkFont(size=11))
        self.app.nearest_y_entry.grid(row=0, column=4, padx=(0, 8), pady=6, sticky="ew")
        
        ctk.CTkLabel(nearest_frame, text="Z:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=5, padx=(0, 2), pady=6, sticky="e")
        self.app.nearest_z_entry = ctk.CTkEntry(nearest_frame, width=70, height=24, font=ctk.CTkFont(size=11))
        self.app.nearest_z_entry.grid(row=0, column=6, padx=(0, 8), pady=6, sticky="ew")
        
        self.app.nearest_find_btn = ctk.CTkButton(
            nearest_frame, text="FIND", width=60, height=24,
            command=self.app._find_nearest_system_by_coordinates,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.nearest_find_btn, "primary")
        self.app.nearest_find_btn.grid(row=0, column=7, padx=(0, 8), pady=6)
        
        stats_frame = ctk.CTkFrame(info_frame,
                                  fg_color=colors['frame'],
                                  border_color=colors['accent'],
                                  border_width=1,
                                  corner_radius=8)
        stats_frame.grid(row=2, column=0, sticky="ew", pady=(5, 10), padx=10)
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
        
        ctk.CTkLabel(stats_frame,
                    text="Data provided by Spansh.co.uk",
                    font=ctk.CTkFont(size=10),
                    text_color="#FFFFFF").grid(row=2, column=0, padx=8, pady=(2, 8), sticky="w")
        right_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=colors['frame'])
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        ctk.CTkLabel(right_frame, text="Neutron Systems:",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=colors['accent']).grid(row=0, column=0, sticky="w", pady=(12, 8), padx=12)
        self.app.neutron_scroll_frame = ctk.CTkScrollableFrame(
            right_frame, width=300,
            fg_color=colors['secondary'],
            border_color=colors['primary'],
            border_width=1,
            scrollbar_button_color=colors['primary'],
            scrollbar_button_hover_color=colors['primary_hover']
        )
        self.app.neutron_scroll_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 12), padx=12)

    def create_galaxy_plotter_tab(self):
        colors = self.app.theme_manager.get_theme_colors()
        
        main_frame = ctk.CTkFrame(self.app.tab_galaxy_plotter, corner_radius=10, fg_color=colors['background'])
        main_frame.pack(fill="both", expand=True, padx=16, pady=8)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        header_frame.columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            header_frame,
            text="🌌 Galaxy Plotter",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")
        
        help_btn = ctk.CTkButton(
            header_frame,
            text="Help",
            width=70,
            height=28,
            font=ctk.CTkFont(size=12),
            command=lambda: self.app._open_link(str(Path(Path(__file__).resolve()).parents[1] / 'GALAXY_PLOTTER_GUIDE.md'))
        )
        self.app.theme_manager.apply_button_theme(help_btn, "secondary")
        help_btn.grid(row=0, column=1, sticky="e")
        
        content_frame = ctk.CTkScrollableFrame(main_frame, fg_color=colors['frame'], corner_radius=10)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure((0, 1), weight=1)
        content_frame.rowconfigure(0, weight=1)

        left_col = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew")
        left_col.columnconfigure(0, weight=1)
        right_col = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 16))
        right_col.columnconfigure(0, weight=1)
        
        systems_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        systems_frame.grid(row=0, column=0, sticky="ew", pady=(6, 6), padx=16)
        systems_frame.columnconfigure((0, 1), weight=1)
        
        source_frame = ctk.CTkFrame(systems_frame, fg_color=colors['background'], corner_radius=8)
        source_frame.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(source_frame, text="Source System:",
                font=ctk.CTkFont(weight="bold", size=13)).pack(pady=(8, 4), padx=10, anchor="w")
        
        self.app.galaxy_source_autocomplete = AutocompleteEntry(
            source_frame,
            placeholder_text="Type 3+ chars for suggestions...",
            suggestion_provider=self.app._get_system_suggestions,
            fg_color="transparent"
        )
        self.app.galaxy_source_autocomplete.pack(fill="x", padx=10, pady=(0, 8))
        
        dest_frame = ctk.CTkFrame(systems_frame, fg_color=colors['background'], corner_radius=8)
        dest_frame.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        
        reverse_btn_frame = ctk.CTkFrame(dest_frame, fg_color="transparent")
        reverse_btn_frame.pack(fill="x", padx=10, pady=(8, 4))
        
        ctk.CTkLabel(reverse_btn_frame, text="Destination System:",
                    font=ctk.CTkFont(weight="bold", size=13)).pack(side="left")
        
        reverse_btn = ctk.CTkButton(
            reverse_btn_frame, text="⇄ Reverse",
            command=self.app._reverse_galaxy_route,
            width=80, height=24,
            font=ctk.CTkFont(size=12)
        )
        self.app.theme_manager.apply_button_theme(reverse_btn, "secondary")
        reverse_btn.pack(side="right")
        
        self.app.galaxy_dest_autocomplete = AutocompleteEntry(
            dest_frame,
            placeholder_text="Type 3+ chars for suggestions...",
            suggestion_provider=self.app._get_system_suggestions,
            fg_color="transparent"
        )
        self.app.galaxy_dest_autocomplete.pack(fill="x", padx=10, pady=(0, 8))
        
        ship_frame = ctk.CTkFrame(left_col, fg_color=colors['background'], corner_radius=8)
        ship_frame.grid(row=1, column=0, sticky="ew", pady=6, padx=16)
        
        ship_label_frame = ctk.CTkFrame(ship_frame, fg_color="transparent")
        ship_label_frame.pack(fill="x", padx=10, pady=(8, 4))
        
        ctk.CTkLabel(ship_label_frame, text="Ship Build URL (EDSY or Coriolis):",
                    font=ctk.CTkFont(weight="bold", size=13)).pack(side="left")
        
        help_label = ctk.CTkLabel(ship_label_frame, text="📋 Paste the share link",
                                 font=ctk.CTkFont(size=11),
                                 text_color=colors.get('secondary', '#888888')).pack(side="right", padx=(10, 0))
        
        self.app.galaxy_ship_build = ctk.CTkTextbox(ship_frame, height=60, wrap="word")
        self.app.galaxy_ship_build.pack(fill="x", padx=10, pady=(0, 8))
        self.app.galaxy_ship_build.insert("1.0", "Paste EDSY or Coriolis share URL here:\nhttps://edsy.org/#/L=...")
        
        options_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        options_frame.grid(row=2, column=0, sticky="ew", pady=6, padx=16)
        options_frame.columnconfigure((0, 1), weight=1)

        cargo_frame = ctk.CTkFrame(options_frame, fg_color=colors['background'], corner_radius=8)
        cargo_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        cargo_frame.columnconfigure(0, weight=1)
        reserve_frame = ctk.CTkFrame(options_frame, fg_color=colors['background'], corner_radius=8)
        reserve_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        reserve_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(cargo_frame, text="Cargo (tons):",
            font=ctk.CTkFont(weight="bold", size=13)).grid(row=0, column=0, pady=(8, 4), padx=10, sticky="w")
        self.app.galaxy_cargo_var = ctk.StringVar(value="0")
        ctk.CTkEntry(cargo_frame, textvariable=self.app.galaxy_cargo_var).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))

        ctk.CTkLabel(reserve_frame, text="Reserve Fuel (tons):",
            font=ctk.CTkFont(weight="bold", size=13)).grid(row=0, column=0, pady=(8, 4), padx=10, sticky="w")
        self.app.galaxy_reserve_fuel_var = ctk.StringVar(value="0")
        ctk.CTkEntry(reserve_frame, textvariable=self.app.galaxy_reserve_fuel_var).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))

        checks_left = ctk.CTkFrame(options_frame, fg_color=colors['background'], corner_radius=8)
        checks_left.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(6, 0))
        checks_left.columnconfigure(0, weight=1)
        checks_right = ctk.CTkFrame(options_frame, fg_color=colors['background'], corner_radius=8)
        checks_right.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(6, 0))
        checks_right.columnconfigure(0, weight=1)

        self.app.galaxy_use_supercharge = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(checks_left, text="Use Neutron Supercharge",
                variable=self.app.galaxy_use_supercharge).pack(pady=(8, 4), padx=10, anchor="w")

        self.app.galaxy_use_injections = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(checks_left, text="Use FSD Injections",
                variable=self.app.galaxy_use_injections).pack(pady=4, padx=10, anchor="w")

        self.app.galaxy_refuel_every = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(checks_left, text="Refuel Every Scoopable",
                variable=self.app.galaxy_refuel_every).pack(pady=(4, 8), padx=10, anchor="w")

        self.app.galaxy_already_supercharged = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(checks_right, text="Already Supercharged",
                variable=self.app.galaxy_already_supercharged).pack(pady=(8, 4), padx=10, anchor="w")

        self.app.galaxy_exclude_secondary = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(checks_right, text="Exclude Secondary Stars",
                variable=self.app.galaxy_exclude_secondary).pack(pady=(4, 8), padx=10, anchor="w")

        algo_frame = ctk.CTkFrame(options_frame, fg_color=colors['background'], corner_radius=8)
        algo_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(6, 0))
        algo_frame.columnconfigure(0, weight=1)
        ctk.CTkLabel(algo_frame, text="Routing Algorithm:",
                 font=ctk.CTkFont(weight="bold", size=13)).pack(pady=(8, 4), padx=10, anchor="w")
        self.app.galaxy_algorithm_var = ctk.StringVar(value="optimistic")
        ctk.CTkOptionMenu(
            algo_frame,
            values=["optimistic", "efficient"],
            variable=self.app.galaxy_algorithm_var,
            fg_color=colors['primary'],
            button_color=colors['primary_hover']
        ).pack(fill="x", padx=10, pady=(0, 10))
        
        button_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        button_frame.grid(row=3, column=0, pady=10)
        
        self.app.galaxy_calculate_btn = ctk.CTkButton(
            button_frame, text="Optimize & Track",
            command=self.app._calculate_galaxy_route,
            height=40, width=250,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.galaxy_calculate_btn, "primary")
        self.app.galaxy_calculate_btn.pack(side="left", padx=5)
        
        self.app.galaxy_export_btn = ctk.CTkButton(
            button_frame, text="💾 Export to CSV",
            command=self.app._export_galaxy_route,
            height=40, width=180,
            font=ctk.CTkFont(size=12)
        )
        self.app.theme_manager.apply_button_theme(self.app.galaxy_export_btn, "secondary")
        self.app.galaxy_export_btn.pack(side="left", padx=5)
        self.app.galaxy_export_btn.configure(state="disabled")
        
        right_top = ctk.CTkFrame(right_col, fg_color=colors['frame'], corner_radius=8)
        right_top.grid(row=0, column=0, sticky="nsew", pady=10)
        right_top.columnconfigure(0, weight=1)
        right_top.rowconfigure(1, weight=1)

        ctk.CTkLabel(right_top, text="Galaxy Systems:",
                     font=ctk.CTkFont(weight="bold", size=13),
                     text_color=colors['accent']).grid(row=0, column=0, pady=(10, 5), padx=10, sticky="w")

        self.app.galaxy_scroll_frame = ctk.CTkScrollableFrame(
            right_top,
            fg_color=colors['secondary'],
            border_color=colors['primary'],
            border_width=1,
            scrollbar_button_color=colors['primary'],
            scrollbar_button_hover_color=colors['primary_hover']
        )
        self.app.galaxy_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

        nav_frame = ctk.CTkFrame(right_top, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="ew", pady=(8, 10), padx=10)
        nav_frame.columnconfigure(1, weight=1)

        self.app.galaxy_prev_btn = ctk.CTkButton(
            nav_frame, text="<", height=32,
            command=self.app._galaxy_prev_waypoint,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.galaxy_prev_btn, "secondary")
        self.app.galaxy_prev_btn.pack(side="left", padx=(0, 6))

        self.app.galaxy_current_btn = ctk.CTkButton(
            nav_frame, text="No route calculated",
            command=self.app._copy_current_galaxy_system,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.galaxy_current_btn, "primary")
        self.app.galaxy_current_btn.pack(side="left", fill="x", expand=True, padx=6)

        self.app.galaxy_next_btn = ctk.CTkButton(
            nav_frame, text=">", height=32,
            command=self.app._galaxy_next_waypoint,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.app.theme_manager.apply_button_theme(self.app.galaxy_next_btn, "secondary")
        self.app.galaxy_next_btn.pack(side="left", padx=(6, 0))

        stats_frame = ctk.CTkFrame(right_top,
                                   fg_color=colors['background'],
                                   border_color=colors['accent'],
                                   border_width=2,
                                   corner_radius=8)
        stats_frame.grid(row=3, column=0, sticky="ew", pady=(5, 10), padx=10)
        stats_frame.columnconfigure(0, weight=1)

        self.app.galaxy_stats_label = ctk.CTkLabel(stats_frame,
                                                   text="📊 Galaxy Statistics | No route calculated",
                                                   font=ctk.CTkFont(size=11, weight="bold"),
                                                   text_color=colors['text'])
        self.app.galaxy_stats_label.grid(row=0, column=0, padx=10, pady=(8, 4), sticky="w")

        self.app.galaxy_progress_label = ctk.CTkLabel(stats_frame,
                                                      text="🎯 Progress Status | Ready to calculate",
                                                      font=ctk.CTkFont(size=11, weight="normal"),
                                                      text_color=colors['accent'])
        self.app.galaxy_progress_label.grid(row=1, column=0, padx=10, pady=(4, 8), sticky="w")
        
        ctk.CTkLabel(stats_frame,
                    text="Data provided by Spansh.co.uk",
                    font=ctk.CTkFont(size=10),
                    text_color="#FFFFFF").grid(row=2, column=0, padx=10, pady=(2, 8), sticky="w")

        right_output_frame = ctk.CTkFrame(right_top, fg_color=colors['frame'], corner_radius=8)
        right_output_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10), padx=10)
        right_top.rowconfigure(4, weight=1)
        right_output_frame.columnconfigure(0, weight=1)
        right_output_frame.rowconfigure(1, weight=0)

        ctk.CTkLabel(right_output_frame, text="Console",
             font=ctk.CTkFont(weight="bold", size=13)).grid(row=0, column=0, pady=(10, 5), padx=10, sticky="w")

        self.app.galaxy_output = ctk.CTkTextbox(right_output_frame, height=140, wrap="word")
        self.app.galaxy_output.grid(row=1, column=0, sticky="nsew", pady=(0, 6), padx=10)
        self.app.galaxy_output.insert("1.0", "No route calculated yet.\n\nSteps:\n1. Enter source and destination systems\n2. Paste your ship build from Coriolis.io or EDSY.org\n3. Configure options (cargo, fuel, neutron boost, etc.)\n4. Click 'Calculate Exact Route' button\n5. Wait for route calculation (may take 1-2 minutes)\n6. Export route to CSV if needed")
        self.app.galaxy_output.configure(state="disabled")

        self.app.galaxy_output_expanded = False
        def _toggle_galaxy_output():
            expanded = getattr(self.app, 'galaxy_output_expanded', False)
            if expanded:
                self.app.galaxy_output.configure(height=140)
                self.app.galaxy_output_expanded = False
                self.app.galaxy_output_toggle_btn.configure(text="Show full log")
            else:
                self.app.galaxy_output.configure(height=320)
                self.app.galaxy_output_expanded = True
                self.app.galaxy_output_toggle_btn.configure(text="Hide log")

        self.app.galaxy_output_toggle_btn = ctk.CTkButton(
            right_output_frame,
            text="Show full log",
            width=110,
            height=26,
            font=ctk.CTkFont(size=11),
            command=_toggle_galaxy_output
        )
        self.app.theme_manager.apply_button_theme(self.app.galaxy_output_toggle_btn, "secondary")
        self.app.galaxy_output_toggle_btn.grid(row=2, column=0, sticky="e", padx=10, pady=(0, 10))
        
        self.app.galaxy_prev_btn.configure(state="disabled")
        self.app.galaxy_next_btn.configure(state="disabled")
    
    def create_bottom_buttons(self):
        parent = self.app.content_root if hasattr(self.app, 'content_root') else self.app.root
        bottom_frame = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        bottom_frame.grid(row=2, column=0, padx=25, pady=(10, 15), sticky="ew")
        bottom_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)
        github_btn = ctk.CTkButton(bottom_frame, text="GitHub",
                                   command=lambda: self.app._open_link("https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer"),
                                   height=32,
                                   font=ctk.CTkFont(size=12))
        self.app.theme_manager.apply_button_theme(github_btn, "secondary")
        github_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        discord_btn = ctk.CTkButton(bottom_frame, text="Discord",
                                   command=lambda: self.app._open_link("https://discord.gg/DWvCEXH7ae"),
                                   height=32,
                                   font=ctk.CTkFont(size=12))
        self.app.theme_manager.apply_button_theme(discord_btn, "secondary")
        discord_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        kofi_btn = ctk.CTkButton(bottom_frame, text="Ko-fi",
                                command=lambda: self.app._open_link("https://ko-fi.com/ninurtakalhu"),
                                fg_color="#FF5E5B",
                                text_color="white",
                                height=32,
                                font=ctk.CTkFont(size=12))
        kofi_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        patreon_btn = ctk.CTkButton(bottom_frame, text="Patreon",
                                   command=lambda: self.app._open_link("https://www.patreon.com/c/NinurtaKalhu"),
                                   fg_color="#FF424D",
                                   text_color="white",
                                   height=32,
                                   font=ctk.CTkFont(size=12))
        patreon_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        about_btn = ctk.CTkButton(bottom_frame, text="About",
                                 command=self.app._show_about_info,
                                 height=32,
                                 font=ctk.CTkFont(size=12))
        self.app.theme_manager.apply_button_theme(about_btn, "primary")
        about_btn.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

    def _toggle_system_dropdown(self):
        if hasattr(self.app, 'start_dropdown_frame') and self.app.start_dropdown_frame:
            self.app.start_dropdown_frame.destroy()
            self.app.start_dropdown_frame = None
            return
        
        entry_x = self.app.start_entry.winfo_rootx()
        entry_y = self.app.start_entry.winfo_rooty()
        entry_height = self.app.start_entry.winfo_height()
        entry_width = self.app.start_entry.winfo_width() + self.app.start_dropdown_btn.winfo_width() + 2
        
        root_x = self.app.root.winfo_rootx()
        root_y = self.app.root.winfo_rooty()
        
        relative_x = entry_x - root_x
        relative_y = entry_y - root_y + entry_height
        
        self.app.start_dropdown_frame = ctk.CTkFrame(
            self.app.root,
            width=entry_width,
            height=300,
            border_width=2,
            border_color=("gray50", "gray50")
        )
        self.app.start_dropdown_frame.place(x=relative_x, y=relative_y)
        self.app.start_dropdown_frame.lift()
        
        def close_if_outside(event):
            widget = event.widget
            if not str(widget).startswith(str(self.app.start_dropdown_frame)):
                self._close_dropdown()
        
        self.app.root.bind("<Button-1>", close_if_outside, add="+")
        
        scroll_frame = ctk.CTkScrollableFrame(
            self.app.start_dropdown_frame,
            width=entry_width - 20,
            height=280
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        if not self.app.start_systems_list:
            no_data_label = ctk.CTkLabel(
                scroll_frame,
                text="Load CSV to see systems...",
                text_color="gray"
            )
            no_data_label.pack(pady=20)
        else:
            filter_var = ctk.StringVar()
            filter_entry = ctk.CTkEntry(
                scroll_frame,
                textvariable=filter_var,
                placeholder_text="Filter systems..."
            )
            filter_entry.pack(fill="x", pady=(0, 5))
            
            systems_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            systems_container.pack(fill="both", expand=True)
            
            def update_filter(*args):
                filter_text = filter_var.get().lower()
                for widget in systems_container.winfo_children():
                    widget.destroy()
                
                filtered = [s for s in self.app.start_systems_list if filter_text in s.lower()]
                
                for system in filtered[:100]:
                    btn = ctk.CTkButton(
                        systems_container,
                        text=system,
                        anchor="w",
                        command=lambda s=system: self._select_system(s),
                        fg_color="transparent",
                        hover_color=("gray75", "gray25")
                    )
                    btn.pack(fill="x", pady=1)
                
                if not filtered:
                    no_match = ctk.CTkLabel(
                        systems_container,
                        text="No matching systems",
                        text_color="gray"
                    )
                    no_match.pack(pady=10)
            
            filter_var.trace("w", update_filter)
            update_filter()
    
    def _select_system(self, system_name):
        self.app.starting_system.set(system_name)
        self._close_dropdown()
    
    def _close_dropdown(self):
        if hasattr(self.app, 'start_dropdown_frame') and self.app.start_dropdown_frame:
            self.app.start_dropdown_frame.destroy()
            self.app.start_dropdown_frame = None
            self.app.root.unbind("<Button-1>")
