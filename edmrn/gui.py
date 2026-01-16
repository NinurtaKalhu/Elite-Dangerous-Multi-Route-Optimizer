import os
import json
import ctypes
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

from edmrn.logger import get_logger
from edmrn.utils import resource_path


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


logger = get_logger('GUI')


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
                
                try:
                        ico_path = resource_path('../assets/explorer_icon.ico')
                        if Path(ico_path).exists():
                                self.iconbitmap(ico_path)
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
                                        except Exception:
                                                pass
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
                except Exception:
                        pass
                
                if self.app and hasattr(self.app, 'theme_manager'):
                        self.theme_colors = self.app.theme_manager.get_theme_colors()
                else:
                        self.theme_colors = {
                                'frame': '#2E2E2E',
                                'primary': '#FF8C00',
                                'secondary': '#666666',
                                'text': '#E0E0E0',
                                'background': '#212121',
                                'primary_hover': '#FFB060'
                        }

                self.geometry("640x850")
                self.minsize(600, 800)
                try:
                        parent_window.update_idletasks()
                        x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (640 // 2)
                        y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (850 // 2)
                        self.geometry(f'+{x}+{y}')
                except Exception:
                        pass

                self.grid_rowconfigure(0, weight=1)
                self.grid_columnconfigure(1, weight=1)

                self.nav_frame = ctk.CTkFrame(self, width=150, fg_color=self.theme_colors['frame'])
                self.nav_frame.grid(row=0, column=0, sticky="nsw")
                self.nav_frame.grid_propagate(False)

                content_frame = ctk.CTkFrame(self, fg_color=self.theme_colors['background'])
                content_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
                content_frame.grid_rowconfigure(0, weight=1)
                content_frame.grid_columnconfigure(0, weight=1)

                self.manual_textbox = ctk.CTkTextbox(
                        content_frame,
                        wrap="word",
                        fg_color=self.theme_colors['background'],
                        text_color=self.theme_colors['text'],
                        font=ctk.CTkFont(family="Consolas", size=12)
                )
                self.manual_textbox.grid(row=0, column=0, sticky="nsew")

                self._build_nav_sections()
                self._build_section_content()
                if self.sections:
                    self._show_section(self.sections[0][0])
                self.after(80, self._adjust_height_to_nav)
                self.grab_set()
                try:
                        self.bind('<Map>', lambda e: self._schedule_reapply_icons())
                        self.bind('<FocusIn>', lambda e: self._schedule_reapply_icons())
                except Exception:
                        pass

        def _build_nav_sections(self):
                self.sections = [
                        ("whats_new", "What's New"),
                        ("quick_start", "Quick Start"),
                        ("tab1", "Tab 1: Route Opt"),
                        ("tab2", "Tab 2: Neutron"),
                        ("tab3", "Tab 3: Tracking"),
                        ("tab4", "Tab 4: Galaxy"),
                        ("settings", "Settings & Overlay"),
                        ("shortcuts", "Shortcuts"),
                        ("backup", "Backup"),
                        ("troubleshooting", "Troubleshooting"),
                        ("credits", "API Credits"),
                        ("support", "Support")
                ]
                self.nav_buttons = {}
                for idx, (key, label) in enumerate(self.sections):
                    btn = ctk.CTkButton(
                        self.nav_frame,
                        text=label,
                        anchor="w",
                        width=150,
                        height=24,
                        fg_color=self.theme_colors['frame'],
                        hover_color=self.theme_colors['secondary'],
                        text_color=self.theme_colors['text'],
                        command=lambda k=key: self._show_section(k),
                        font=ctk.CTkFont(size=11, weight="bold" if idx == 0 else "normal")
                    )
                    btn.grid(row=idx, column=0, sticky="ew", padx=6, pady=(2 if idx else 6, 2))
                    self.nav_buttons[key] = btn
                self.active_nav = None

        def _show_section(self, key: str):
            try:
                self._render_section(key)
                self._highlight_nav(key)
            except Exception:
                pass

        def _highlight_nav(self, active_key: str):
                if self.active_nav == active_key:
                        return
                primary = self.theme_colors['primary']
                primary_hover = self.theme_colors.get('primary_hover', primary)
                frame = self.theme_colors['frame']
                secondary = self.theme_colors['secondary']
                text = self.theme_colors['text']
                for key, btn in self.nav_buttons.items():
                        if key == active_key:
                                btn.configure(
                                        fg_color=primary,
                                        hover_color=primary_hover,
                                        text_color=self.theme_colors.get('background', '#1e1e1e')
                                )
                        else:
                                btn.configure(
                                        fg_color=frame,
                                        hover_color=secondary,
                                        text_color=text
                                )
                self.active_nav = active_key

        def _build_section_content(self):
            self.section_content = {
                "whats_new": (
                    "WHAT'S NEW IN v3.1",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "🚀 CORE FEATURES",
                        "  • Persistent Visit History - Duplicate systems automatically filtered",
                        "  • Smart Backup System - Auto-backup before critical actions with restore",
                        "  • Nearest Starting System - Auto-detect closest CSV system from journal",
                        "",
                        "🎮 PERFORMANCE & COMPATIBILITY",
                        "  • GeForce Now Optimization - Overlay tuned for cloud gaming",
                        "  • Borderless Mode Support - Enhanced overlay compatibility",
                        "",
                        "🌐 ENHANCED AUTOCOMPLETE",
                        "  • Spansh Primary Source - 70M+ systems database",
                        "  • EDSM Fallback - Seamless secondary source",
                        "  • Smart Debouncing - 300ms delay for optimal performance",
                        "  • 1-hour Caching - Reduced API calls, faster response",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "quick_start": (
                    "QUICK START GUIDE",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "📋 STEP 1: PREPARE YOUR ROUTE",
                        "  • Visit Spansh.co.uk Galaxy Plotter",
                        "  • Export CSV with: System Name, X, Y, Z coordinates",
                        "  • Optional: Include Body Name for specific destinations",
                        "",
                        "⚙️ STEP 2: CONFIGURE ROUTE",
                        "  • Tab 1: Browse and load your CSV file",
                        "  • Set accurate jump range for your ship",
                        "  • Choose starting system (auto-detect from journal or manual)",
                        "",
                        "🚀 STEP 3: OPTIMIZE & TRACK",
                        "  • Click 'Optimize & Track' button",
                        "  • Wait for TSP optimization (auto-backup created)",
                        "  • Route automatically loads in tracking tab",
                        "",
                        "🎮 STEP 4: IN-GAME USAGE",
                        "  • Tab 3: View 3D map and route status",
                        "  • Press Ctrl+O in-game to toggle overlay",
                        "  • Journal auto-tracks your progress",
                        "",
                        "🎨 STEP 5: CUSTOMIZE",
                        "  • Settings: Choose theme, overlay options",
                        "  • Journal path auto-detected",
                        "  • Configure autosave and overlay behavior",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "tab1": (
                    "TAB 1: ROUTE OPTIMIZATION",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "📂 CSV FILE REQUIREMENTS",
                        "  • Supported Sources: Spansh, EDSM, EDDB exports",
                        "  • Required Columns: System Name, X, Y, Z coordinates",
                        "  • Optional Column: Body Name for specific destinations",
                        "  • Format: Standard CSV with header row",
                        "",
                        "🎯 JUMP RANGE CONFIGURATION",
                        "  • Enter your ship's accurate FSD range",
                        "  • Used for distance matrix calculations",
                        "  • Critical for neutron route planning",
                        "",
                        "🌟 STARTING SYSTEM OPTIONS",
                        "  • Auto-Select: Nearest CSV system from journal location",
                        "  • Manual Pick: Dropdown list of all systems",
                        "  • Find Nearest: Button to auto-detect closest system",
                        "",
                        "✅ VALIDATION & OPTIMIZATION",
                        "  • Live column validation with visual indicators",
                        "  • Green/Red status for data quality",
                        "  • TSP optimization engine",
                        "  • Auto-backup before processing",
                        "  • Auto-switches to tracking tab on completion",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "tab2": (
                    "TAB 2: NEUTRON HIGHWAY",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "⚡ NEUTRON ROUTING SYSTEM",
                        "  • FSD Boost: x4 or x6 multiplier support",
                        "  • Waypoint Navigation: Step-by-step routing",
                        "  • Clipboard Copy: Quick system name copying",
                        "",
                        "🔍 SMART AUTOCOMPLETE",
                        "  • Primary: Spansh database (70M+ systems)",
                        "  • Minimum: 3 characters to start search",
                        "  • Debounce: 300ms for optimal performance",
                        "  • Cache: 1-hour duration for repeated searches",
                        "",
                        "🎮 CONTROLS & NAVIGATION",
                        "  • From/To System: Source and destination",
                        "  • Jump Range: Ship FSD range",
                        "  • Boost Selection: x4 or x6 neutron boost",
                        "  • Waypoint Buttons: < > to navigate route",
                        "",
                        "📊 STATISTICS & TRACKING",
                        "  • Total Distance: Full route length",
                        "  • Jump Counts: Normal vs neutron jumps",
                        "  • Efficiency: Route optimization percentage",
                        "  • Progress: Current waypoint tracking",
                        "  • Auto-Tracking: Journal integration for waypoint advance",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "tab3": (
                    "TAB 3: ROUTE TRACKING",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "📡 AUTO JOURNAL TRACKING",
                        "  • Real-time journal file monitoring",
                        "  • Multi-commander support",
                        "  • Automatic visit detection",
                        "  • Background processing",
                        "",
                        "✏️ MANUAL STATUS CONTROL",
                        "  • Mark Visited: Manually confirm system visits",
                        "  • Mark Skipped: Skip systems intentionally",
                        "  • Mark Unvisited: Reset system status",
                        "  • Useful when auto-detection misses visits",
                        "",
                        "🗺️ INTERACTIVE 3D MAP",
                        "  • Zoom: Mouse wheel for scale adjustment",
                        "  • Rotate: Click and drag to rotate view",
                        "  • Select: Click system for details",
                        "  • Color Coding:",
                        "    - Green: Visited systems",
                        "    - Orange: Skipped systems",
                        "    - Gray: Pending/unvisited systems",
                        "",
                        "📊 ROUTE STATISTICS",
                        "  • Total Distance: Complete route length",
                        "  • Traveled: Distance already covered",
                        "  • Remaining: Distance left to travel",
                        "  • System Counts: Total, visited, remaining",
                        "  • Progress Percentage: Completion tracker",
                        "",
                        "⚙️ QUICK ACTIONS",
                        "  • Copy Next: Copy next system to clipboard",
                        "  • Data Folder: Open route data directory",
                        "  • Open Excel: View route in spreadsheet",
                        "  • Load Backup: Restore previous route",
                        "  • Quick Save: Manual save current progress",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "tab4": (
                    "TAB 4: GALAXY PLOTTER",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "🚀 SPANSH EXACT ROUTER",
                        "  • Integrated routing with Spansh API",
                        "  • Advanced fuel management",
                        "  • Neutron star highway support",
                        "  • Real-time route calculation",
                        "",
                        "🛸 SHIP BUILD INTEGRATION",
                        "  • Coriolis Import: Paste Coriolis.io share URL",
                        "  • EDSY Import: Paste EDSY.org share URL",
                        "  • Auto-Extract: FSD range, fuel tank, cargo",
                        "  • Manual Override: Adjust values as needed",
                        "",
                        "⚙️ ROUTE CONFIGURATION",
                        "  • Cargo: Account for cargo weight",
                        "  • Reserve Fuel: Safety fuel margin",
                        "  • Neutron Boost: Enable x4 FSD boost",
                        "  • Injections: FSD synthesis support",
                        "  • Secondary Star Skip: Avoid non-primary stars",
                        "",
                        "📤 OUTPUT OPTIONS",
                        "  • Jump List: Detailed waypoint list",
                        "  • CSV Export: Export route for optimization",
                        "  • Log Panel: Real-time calculation feedback",
                        "  • Expand Toggle: Show/hide detailed logs",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "settings": (
                    "SETTINGS & OVERLAY",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "🎨 THEME CUSTOMIZATION",
                        "  • 11 PowerPlay-Inspired Themes",
                        "  • Aisling Duval, Zachary Hudson, Li Yong-Rui, etc.",
                        "  • Elite Dangerous official colors",
                        "  • Borderless Mode: Toggle window decorations",
                        "",
                        "📁 JOURNAL CONFIGURATION",
                        "  • Auto-Detection: Automatic journal path discovery",
                        "  • Multi-Commander: Support for multiple CMDRs",
                        "  • Manual Path: Override detection if needed",
                        "  • Real-time Monitoring: Background file watching",
                        "",
                        "🖥️ OVERLAY SETTINGS",
                        "  • Start/Stop: Manual overlay control",
                        "  • Opacity: Adjust transparency (0-100%)",
                        "  • Auto-Launch: Start overlay after optimization",
                        "  • In-Game Toggle: Ctrl+O keyboard shortcut",
                        "  • Position: Drag overlay to preferred location",
                        "",
                        "💾 AUTOSAVE OPTIONS",
                        "  • Intervals: 1 minute, 5 minutes, 10 minutes",
                        "  • Atomic Writes: Safe file operations",
                        "  • Progress Preservation: Never lose tracking data",
                        "  • Background Operation: No UI interruption",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "shortcuts": (
                    "KEYBOARD SHORTCUTS",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "⌨️ GLOBAL SHORTCUTS",
                        "",
                        "  Ctrl+O",
                        "    Toggle in-game overlay on/off",
                        "    Works while Elite Dangerous is in focus",
                        "",
                        "  Ctrl+S",
                        "    Quick save current route progress",
                        "    Saves tracking data and status",
                        "",
                        "  Ctrl+L",
                        "    Copy next system name to clipboard",
                        "    Ready to paste into galaxy map",
                        "",
                        "  F5",
                        "    Refresh UI and reload data",
                        "    Useful after manual file changes",
                        "",
                        "  Esc",
                        "    Close manual window",
                        "    Also closes most dialog windows",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "backup": (
                    "BACKUP SYSTEM",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "💾 AUTO-BACKUP FEATURES",
                        "  • Timestamped Backups: Automatic date/time stamps",
                        "  • Pre-Optimization: Created before TSP processing",
                        "  • Progress State: Saves visited/skipped status",
                        "  • Route Data: Complete CSV and metadata",
                        "",
                        "🔄 RESTORE CAPABILITIES",
                        "  • Full Route Restore: Original and filtered systems",
                        "  • Progress Recovery: Resume from saved state",
                        "  • Status Preservation: Visited/skipped flags intact",
                        "  • Metadata Included: Jump range, settings, etc.",
                        "",
                        "📂 BACKUP MANAGEMENT",
                        "  • Organized Structure: Timestamped folders",
                        "  • Easy Navigation: Backup selection dialog",
                        "  • Version Compatible: Works with older backups",
                        "  • Priority System: User-modified routes prioritized",
                        "",
                        "⚠️ PROTECTION SCENARIOS",
                        "  • Before Optimization: Preserve original route",
                        "  • Critical Actions: Before major changes",
                        "  • Data Safety: Prevents accidental loss",
                        "  • Recovery Options: Multiple restore points",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "troubleshooting": (
                    "TROUBLESHOOTING",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "❌ NO JOURNAL DATA DETECTED",
                        "  Problem: App not detecting your jumps",
                        "  Solutions:",
                        "    1. Verify journal path in Settings",
                        "    2. Make at least one jump in-game",
                        "    3. Restart journal monitor from Settings",
                        "    4. Check Elite Dangerous is running",
                        "",
                        "🔍 AUTOCOMPLETE NOT WORKING",
                        "  Problem: System search returns no results",
                        "  Solutions:",
                        "    1. Check internet connection",
                        "    2. Spansh primary source may be down",
                        "    3. EDSM fallback should activate automatically",
                        "    4. Wait for 300ms debounce timeout",
                        "    5. Try typing more than 3 characters",
                        "",
                        "👁️ OVERLAY NOT VISIBLE",
                        "  Problem: Overlay doesn't show in-game",
                        "  Solutions:",
                        "    1. Enable borderless mode in ED settings",
                        "    2. Press Ctrl+O to toggle overlay",
                        "    3. Adjust opacity slider in Settings",
                        "    4. Check overlay is started in Settings",
                        "    5. Try repositioning overlay window",
                        "",
                        "📋 DROPDOWN/UI MISALIGNMENT",
                        "  Problem: UI elements appear misaligned",
                        "  Solutions:",
                        "    1. Fixed in v3.1 - update if needed",
                        "    2. Restart application",
                        "    3. Check display scaling (100-150% recommended)",
                        "    4. Try different theme in Settings",
                        "",
                        "💥 APPLICATION CRASHES",
                        "  Problem: App closes unexpectedly",
                        "  Solutions:",
                        "    1. Check logs folder for error details",
                        "    2. Verify CSV file format is correct",
                        "    3. Restore from backup if after optimization",
                        "    4. Reinstall application if persistent",
                        "    5. Report on Discord/GitHub with logs",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "credits": (
                    "API CREDITS & ATTRIBUTION",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "🌐 THIRD-PARTY SERVICES",
                        "",
                        "  Spansh (spansh.co.uk)",
                        "    • Primary system database (70M+ systems)",
                        "    • Autocomplete primary source",
                        "    • Neutron router integration",
                        "    • Galaxy plotter API",
                        "",
                        "  EDSM (edsm.net)",
                        "    • Fallback system database",
                        "    • Autocomplete secondary source",
                        "    • System coordinate data",
                        "    • Community-driven updates",
                        "",
                        "  ⚠️ No official affiliation with either service",
                        "  ⚠️ Thanks to both teams for their amazing work!",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "👥 SPECIAL THANKS",
                        "",
                        "  • Ozgur KARATAS (Ta2ozg)",
                        "    Contributor & Developer",
                        "",
                        "  • Aydin AKYUZ",
                        "    Contributor & Beta Tester",
                        "    youtube.com/@drizzydnt",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
                "support": (
                    "SUPPORT & COMMUNITY",
                    [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "💬 DISCORD COMMUNITY",
                        "  • Server: discord.gg/DWvCEXH7ae",
                        "  • Get help from other commanders",
                        "  • Share routes and tips",
                        "  • Report bugs and suggest features",
                        "  • Beta testing opportunities",
                        "",
                        "📦 GITHUB REPOSITORY",
                        "  • github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer",
                        "  • Source code access",
                        "  • Issue tracker",
                        "  • Feature requests",
                        "  • Contribution guidelines",
                        "  • Release downloads",
                        "",
                        "📧 EMAIL SUPPORT",
                        "  • Contact: ninurtakalhu@gmail.com",
                        "  • Response time: 24-48 hours",
                        "  • For private inquiries",
                        "",
                        "🐛 REPORTING ISSUES",
                        "  When reporting bugs, please include:",
                        "    • Log files from logs folder",
                        "    • Sample CSV file (if route-related)",
                        "    • Steps to reproduce the issue",
                        "    • Screenshots if applicable",
                        "    • Your Windows version and app version",
                        "",
                        "💡 FEATURE REQUESTS",
                        "  • Post on GitHub Issues",
                        "  • Discuss on Discord #suggestions",
                        "  • Explain your use case",
                        "  • Community voting helps prioritize",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    ],
                ),
            }

        def _render_section(self, key: str):
            self.manual_textbox.configure(state="normal")
            self.manual_textbox.delete("1.0", "end")
            self.manual_textbox.insert("end", "ED MULTI ROUTE NAVIGATION (EDMRN) v3.1 - USER MANUAL\n")
            self.manual_textbox.insert("end", "Optimized routes, journal tracking, Spansh primary autocomplete.\n\n")
            title, lines = self.section_content.get(key, ("", []))
            if title:
                self.manual_textbox.insert("end", title + "\n\n")
            for line in lines:
                self.manual_textbox.insert("end", line + "\n")
            self.manual_textbox.configure(state="disabled")

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

        def _adjust_height_to_nav(self):
            try:
                total = 0
                for idx, _ in enumerate(self.sections):
                    pad_top = 8 if idx == 0 else 4
                    pad_bottom = 4
                    total += 30 + pad_top + pad_bottom
                desired_height = max(total + 16, 420)
                self.update_idletasks()
                current_width = max(self.winfo_width(), 640)
                x, y = self.winfo_x(), self.winfo_y()
                self.geometry(f"{current_width}x{desired_height}+{x}+{y}")
                self.minsize(600, desired_height)
            except Exception:
                pass


class ProcessingDialog(ctk.CTkToplevel):

    def __init__(self, master, on_cancel=None):
        if hasattr(master, 'root'):
            parent_window = master.root
            self.app = master
            try:
                self.theme_colors = self.app.theme_manager.get_theme_colors()
            except Exception:
                self.theme_colors = None
        else:
            parent_window = master
            self.app = None
            self.theme_colors = None
        super().__init__(parent_window)
        self.title("Processing…")
        self.on_cancel = on_cancel

        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                self.iconbitmap(ico_path)
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
                    except Exception:
                        pass
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
        except Exception:
            pass

        colors = self.theme_colors or {
            'frame': '#2E2E2E',
            'primary': '#FF8C00',
            'secondary': '#666666',
            'text': '#E0E0E0',
            'background': '#212121',
            'primary_hover': '#FFB060'
        }

        self.configure(fg_color=colors['background'])
        self.resizable(False, False)
        self.geometry("360x170")
        try:
            self.transient(parent_window)
            parent_window.update_idletasks()
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - 180
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - 85
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        body = ctk.CTkFrame(self, fg_color=colors['frame'])
        body.pack(fill="both", expand=True, padx=10, pady=10)

        self.status_label = ctk.CTkLabel(body, text="Preparing…", font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=colors['text'])
        self.status_label.pack(pady=(12, 8))

        self.progress = ctk.CTkProgressBar(body, width=280, height=14, progress_color=colors['primary'],
                           fg_color=colors['secondary'])
        self.progress.pack(pady=(6, 10))
        self.progress.set(0)

        self.cancel_button = ctk.CTkButton(
            body,
            text="Cancel",
            width=120,
            fg_color=colors['secondary'],
            hover_color=colors.get('primary_hover', colors['primary']),
            text_color=colors['text'],
            command=self._handle_cancel
        )
        self.cancel_button.pack(pady=(4, 8))

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._handle_cancel)

    def _handle_cancel(self):
        try:
            if callable(self.on_cancel):
                self.on_cancel()
        except Exception:
            pass
        self.close()

    def update(self, message: str, fraction: float | None):
        try:
            if not self.winfo_exists():
                return
            self.status_label.configure(text=message)
            if fraction is None:
                self.progress.configure(mode="indeterminate")
                self.progress.start()
            else:
                self.progress.configure(mode="determinate")
                self.progress.stop()
                clamped = max(0.0, min(1.0, float(fraction)))
                self.progress.set(clamped)
            self.update_idletasks()
        except Exception:
            pass

    def close(self):
        try:
            self.progress.stop()
        except Exception:
            pass
        try:
            self.withdraw()
        except Exception:
            pass
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


class SuccessDialog(ctk.CTkToplevel):

    def __init__(self, master, title, message):
        if hasattr(master, 'root'):
            parent_window = master.root
            self.app = master
            try:
                self.theme_colors = self.app.theme_manager.get_theme_colors()
            except Exception:
                self.theme_colors = None
        else:
            parent_window = master
            self.app = None
            self.theme_colors = None
        super().__init__(parent_window)
        self.title(title)
        
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                self.iconbitmap(ico_path)
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
                    except Exception:
                        pass
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
        except Exception:
            pass

        colors = self.theme_colors or {
            'frame': '#2E2E2E',
            'primary': '#FF8C00',
            'secondary': '#666666',
            'text': '#E0E0E0',
            'background': '#212121',
            'primary_hover': '#FFB060'
        }

        self.configure(fg_color=colors['background'])
        self.resizable(False, False)
        self.geometry("400x200")
        try:
            self.transient(parent_window)
            parent_window.update_idletasks()
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - 200
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - 100
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        body = ctk.CTkFrame(self, fg_color=colors['frame'])
        body.pack(fill="both", expand=True, padx=15, pady=15)

        icon_label = ctk.CTkLabel(body, text="✅", font=ctk.CTkFont(size=48))
        icon_label.pack(pady=(10, 5))

        msg_label = ctk.CTkLabel(
            body,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color=colors['text'],
            wraplength=350,
            justify="center"
        )
        msg_label.pack(pady=(5, 15))

        ok_button = ctk.CTkButton(
            body,
            text="OK",
            width=120,
            fg_color=colors['primary'],
            hover_color=colors.get('primary_hover', colors['primary']),
            text_color="white",
            command=self.destroy
        )
        ok_button.pack(pady=(0, 10))
        ok_button.lift()
        
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        try:
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (width // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (height // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass
        
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
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
                    except Exception:
                        pass
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
        except Exception:
            pass
        finally:
            self._reapply_pending = False


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
    Version 3.1.0 - AGPL-3 Licensed
January 2026
Developed by CMDR Ninurta Kalhu
Elite Dangerous © Frontier Developments plc.
*This tool is not affiliated with, endorsed by, 
or connected to Frontier Developments plc.*

Data & Services:
• Route calculations by Spansh (spansh.co.uk)
• System data by EDSM (edsm.net)

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
        
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                self.iconbitmap(ico_path)
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
                    except Exception:
                        pass
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
        except Exception:
            pass
        
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
                WarningDialog(
                    self,
                    "Warning",
                    f"No CSV file found in:\n{folder_path}\n\nPlease select a folder containing a route CSV file."
                )
                return
            self.load_callback(folder_path)
            self.destroy()
    def _load_selected(self):
        selected_path = self.selected_folder.get()
        if not selected_path:
            WarningDialog(self, "Warning", "Please select a backup folder.")
            return
        if not Path(selected_path).exists():
            ErrorDialog(self, "Error", f"Folder no longer exists:\n{selected_path}")
            return
        self.load_callback(selected_path)
        self.destroy()
    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self._populate_backup_list()

class InfoDialog(ctk.CTkToplevel):
    def __init__(self, master, title, message):
        if hasattr(master, 'root'):
            parent_window = master.root
            self.app = master
            try:
                self.theme_colors = self.app.theme_manager.get_theme_colors()
            except Exception:
                self.theme_colors = None
        else:
            parent_window = master
            self.app = None
            self.theme_colors = None
        super().__init__(parent_window)
        self.title(title)
        self._setup_icon()

        colors = self.theme_colors or {
            'frame': '#2E2E2E', 'primary': '#FF8C00', 'secondary': '#666666',
            'text': '#E0E0E0', 'background': '#212121', 'primary_hover': '#FFB060'
        }
        self.configure(fg_color=colors['background'])
        self.resizable(False, False)
        
        try:
            self.transient(parent_window)
        except Exception:
            pass

        body = ctk.CTkFrame(self, fg_color=colors['frame'])
        body.pack(fill="both", expand=True, padx=15, pady=15)

        icon_label = ctk.CTkLabel(body, text="ℹ️", font=ctk.CTkFont(size=48))
        icon_label.pack(pady=(10, 5))

        msg_label = ctk.CTkLabel(
            body, text=message, font=ctk.CTkFont(size=12), text_color=colors['text'],
            wraplength=350, justify="center"
        )
        msg_label.pack(pady=(5, 15))

        ok_button = ctk.CTkButton(
            body, text="OK", width=120,
            fg_color=colors['primary'], hover_color=colors.get('primary_hover', colors['primary']),
            text_color="white", command=self.destroy
        )
        ok_button.pack(pady=(0, 10))
        ok_button.lift()

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        try:
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (width // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (height // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass
        
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        try:
            self.bind('<Map>', lambda e: self._schedule_reapply_icons())
            self.bind('<FocusIn>', lambda e: self._schedule_reapply_icons())
        except Exception:
            pass

    def _setup_icon(self):
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.iconbitmap(ico_path)
                except Exception:
                    pass
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080; ICON_SMALL = 0; ICON_BIG = 1
                        hicon = _load_hicon(ico_path)
                        if hicon:
                            hwnd = self.winfo_id()
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
                self._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.wm_iconphoto(True, self._title_icon)
                except Exception:
                    self.iconphoto(False, self._title_icon)
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
                        WM_SETICON = 0x0080; ICON_SMALL = 0; ICON_BIG = 1
                        hicon = _load_hicon(ico_path)
                        if hicon:
                            hwnd = self.winfo_id()
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
                self._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.wm_iconphoto(True, self._title_icon)
                except Exception:
                    self.iconphoto(False, self._title_icon)
        except Exception:
            pass
        finally:
            self._reapply_pending = False


class WarningDialog(ctk.CTkToplevel):
    def __init__(self, master, title, message):
        if hasattr(master, 'root'):
            parent_window = master.root
            self.app = master
            try:
                self.theme_colors = self.app.theme_manager.get_theme_colors()
            except Exception:
                self.theme_colors = None
        else:
            parent_window = master
            self.app = None
            self.theme_colors = None
        super().__init__(parent_window)
        self.title(title)
        self._setup_icon()

        colors = self.theme_colors or {
            'frame': '#2E2E2E', 'primary': '#FF8C00', 'secondary': '#666666',
            'text': '#E0E0E0', 'background': '#212121', 'primary_hover': '#FFB060'
        }
        self.configure(fg_color=colors['background'])
        self.resizable(False, False)
        
        try:
            self.transient(parent_window)
        except Exception:
            pass

        body = ctk.CTkFrame(self, fg_color=colors['frame'])
        body.pack(fill="both", expand=True, padx=15, pady=15)

        icon_label = ctk.CTkLabel(body, text="⚠️", font=ctk.CTkFont(size=48))
        icon_label.pack(pady=(10, 5))

        msg_label = ctk.CTkLabel(
            body, text=message, font=ctk.CTkFont(size=12), text_color=colors['text'],
            wraplength=350, justify="center"
        )
        msg_label.pack(pady=(5, 15))

        ok_button = ctk.CTkButton(
            body, text="OK", width=120,
            fg_color="#FFA500", hover_color="#FFB84D",
            text_color="white", command=self.destroy
        )
        ok_button.pack(pady=(0, 10))
        ok_button.lift()

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        try:
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (width // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (height // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass
        
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        try:
            self.bind('<Map>', lambda e: self._schedule_reapply_icons())
            self.bind('<FocusIn>', lambda e: self._schedule_reapply_icons())
        except Exception:
            pass

    _setup_icon = InfoDialog._setup_icon
    _schedule_reapply_icons = InfoDialog._schedule_reapply_icons
    _do_reapply_icons = InfoDialog._do_reapply_icons


class ErrorDialog(ctk.CTkToplevel):
    def __init__(self, master, title, message):
        if hasattr(master, 'root'):
            parent_window = master.root
            self.app = master
            try:
                self.theme_colors = self.app.theme_manager.get_theme_colors()
            except Exception:
                self.theme_colors = None
        else:
            parent_window = master
            self.app = None
            self.theme_colors = None
        super().__init__(parent_window)
        self.title(title)
        self._setup_icon()

        colors = self.theme_colors or {
            'frame': '#2E2E2E', 'primary': '#FF8C00', 'secondary': '#666666',
            'text': '#E0E0E0', 'background': '#212121', 'primary_hover': '#FFB060'
        }
        self.configure(fg_color=colors['background'])
        self.resizable(False, False)
        
        try:
            self.transient(parent_window)
        except Exception:
            pass

        body = ctk.CTkFrame(self, fg_color=colors['frame'])
        body.pack(fill="both", expand=True, padx=15, pady=15)

        icon_label = ctk.CTkLabel(body, text="❌", font=ctk.CTkFont(size=48))
        icon_label.pack(pady=(10, 5))

        msg_label = ctk.CTkLabel(
            body, text=message, font=ctk.CTkFont(size=12), text_color=colors['text'],
            wraplength=350, justify="center"
        )
        msg_label.pack(pady=(5, 15))

        ok_button = ctk.CTkButton(
            body, text="OK", width=120,
            fg_color="#FF6B6B", hover_color="#FF5252",
            text_color="white", command=self.destroy
        )
        ok_button.pack(pady=(0, 10))
        ok_button.lift()

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        try:
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (width // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (height // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass
        
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        try:
            self.bind('<Map>', lambda e: self._schedule_reapply_icons())
            self.bind('<FocusIn>', lambda e: self._schedule_reapply_icons())
        except Exception:
            pass

    _setup_icon = InfoDialog._setup_icon
    _schedule_reapply_icons = InfoDialog._schedule_reapply_icons
    _do_reapply_icons = InfoDialog._do_reapply_icons


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, master, title, message):
        if hasattr(master, 'root'):
            parent_window = master.root
            self.app = master
            try:
                self.theme_colors = self.app.theme_manager.get_theme_colors()
            except Exception:
                self.theme_colors = None
        else:
            parent_window = master
            self.app = None
            self.theme_colors = None
        super().__init__(parent_window)
        self.title(title)
        self._setup_icon()
        self.result = False

        colors = self.theme_colors or {
            'frame': '#2E2E2E', 'primary': '#FF8C00', 'secondary': '#666666',
            'text': '#E0E0E0', 'background': '#212121', 'primary_hover': '#FFB060'
        }
        self.configure(fg_color=colors['background'])
        self.resizable(False, False)
        
        try:
            self.transient(parent_window)
        except Exception:
            pass

        body = ctk.CTkFrame(self, fg_color=colors['frame'])
        body.pack(fill="both", expand=True, padx=20, pady=20)

        icon_label = ctk.CTkLabel(body, text="❓", font=ctk.CTkFont(size=48))
        icon_label.pack(pady=(10, 5))

        msg_label = ctk.CTkLabel(
            body, text=message, font=ctk.CTkFont(size=12), text_color=colors['text'],
            wraplength=380, justify="center"
        )
        msg_label.pack(pady=(5, 15))

        btn_frame = ctk.CTkFrame(body, fg_color="transparent")
        btn_frame.pack(pady=(0, 10))

        yes_button = ctk.CTkButton(
            btn_frame, text="Yes", width=100,
            fg_color=colors['primary'], hover_color=colors.get('primary_hover', colors['primary']),
            text_color="white", command=self._on_yes
        )
        yes_button.pack(side="left", padx=5)

        no_button = ctk.CTkButton(
            btn_frame, text="No", width=100,
            fg_color=colors['secondary'], hover_color="#777777",
            text_color="white", command=self._on_no
        )
        no_button.pack(side="left", padx=5)
        
        btn_frame.lift()
        yes_button.lift()
        no_button.lift()

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_no)
        
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        try:
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (width // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (height // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass
        
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        try:
            self.bind('<Map>', lambda e: self._schedule_reapply_icons())
            self.bind('<FocusIn>', lambda e: self._schedule_reapply_icons())
        except Exception:
            pass

    def _on_yes(self):
        self.result = True
        self.destroy()

    def _on_no(self):
        self.result = False
        self.destroy()

    _setup_icon = InfoDialog._setup_icon
    _schedule_reapply_icons = InfoDialog._schedule_reapply_icons
    _do_reapply_icons = InfoDialog._do_reapply_icons

    def get_result(self):
        self.wait_window()
        return self.result

