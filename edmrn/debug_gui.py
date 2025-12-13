import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from edmrn.logger import get_logger
from edmrn.debug import get_debug_system

logger = get_logger('DebugGUI')

class DebugWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("EDMRN Debug Console")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        
        self.debug_system = get_debug_system()
        self.auto_refresh = True
        self.refresh_interval = 2000
        self.current_filter = 'all'
        self.subscriber_id = None
        
        self._setup_ui()
        self._subscribe_to_debug_events()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self._schedule_refresh()
    
    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        control_frame.columnconfigure(0, weight=1)
        
        stats_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        stats_frame.grid(row=0, column=0, sticky="w", padx=10)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame, 
            text="Errors: 0 | Warnings: 0 | Uptime: 0s",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.stats_label.pack(side="left", padx=(0, 20))
        
        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, sticky="e")
        
        filter_label = ctk.CTkLabel(button_frame, text="Filter:", font=ctk.CTkFont(size=11))
        filter_label.pack(side="left", padx=(0, 5))
        
        self.filter_menu = ctk.CTkOptionMenu(
            button_frame, 
            values=["All", "Errors", "Warnings", "Info"],
            command=self._change_filter,
            width=100
        )
        self.filter_menu.pack(side="left", padx=(0, 10))
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = ctk.CTkCheckBox(
            button_frame, 
            text="Auto-refresh", 
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh
        )
        auto_refresh_check.pack(side="left", padx=(0, 10))
        
        refresh_btn = ctk.CTkButton(
            button_frame, 
            text="🔄 Refresh", 
            command=self._manual_refresh,
            width=80
        )
        refresh_btn.pack(side="left", padx=(0, 10))
        
        clear_btn = ctk.CTkButton(
            button_frame, 
            text="🗑️ Clear All", 
            command=self._clear_all,
            fg_color="#f44336",
            hover_color="#d32f2f",
            width=80
        )
        clear_btn.pack(side="left", padx=(0, 10))
        
        export_btn = ctk.CTkButton(
            button_frame, 
            text="💾 Export", 
            command=self._export_debug_data,
            fg_color="#4CAF50",
            hover_color="#45a049",
            width=80
        )
        export_btn.pack(side="left")
        
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        self.notebook = ctk.CTkTabview(content_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.error_tab = self.notebook.add("Errors")
        self._setup_error_tab()
        
        self.warning_tab = self.notebook.add("Warnings")
        self._setup_warning_tab()
        
        self.info_tab = self.notebook.add("Info")
        self._setup_info_tab()
        
        self.stats_tab = self.notebook.add("Statistics")
        self._setup_stats_tab()
        
        self.log_tab = self.notebook.add("Log Level")
        self._setup_log_tab()
    
    def _setup_error_tab(self):
        self.error_tab.grid_columnconfigure(0, weight=1)
        self.error_tab.grid_rowconfigure(1, weight=1)
        
        error_list_frame = ctk.CTkFrame(self.error_tab)
        error_list_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            error_list_frame, 
            text="Error List", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(10, 20))
        
        detail_frame = ctk.CTkFrame(self.error_tab)
        detail_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        detail_frame.grid_columnconfigure(0, weight=1)
        detail_frame.grid_rowconfigure(0, weight=1)
        
        self.error_listbox = tk.Listbox(
            error_list_frame,
            height=8,
            bg='#2b2b2b' if ctk.get_appearance_mode() == 'Dark' else '#f5f5f5',
            fg='white' if ctk.get_appearance_mode() == 'Dark' else 'black',
            selectbackground='#4CAF50',
            font=('Consolas', 10)
        )
        self.error_listbox.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.error_listbox.bind('<<ListboxSelect>>', self._on_error_select)
        
        self.error_details = ctk.CTkTextbox(detail_frame, font=('Consolas', 10))
        self.error_details.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    
    def _setup_warning_tab(self):
        self.warning_tab.grid_columnconfigure(0, weight=1)
        self.warning_tab.grid_rowconfigure(0, weight=1)
        
        self.warning_listbox = tk.Listbox(
            self.warning_tab,
            bg='#2b2b2b' if ctk.get_appearance_mode() == 'Dark' else '#f5f5f5',
            fg='white' if ctk.get_appearance_mode() == 'Dark' else 'black',
            font=('Consolas', 10)
        )
        self.warning_listbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def _setup_info_tab(self):
        self.info_tab.grid_columnconfigure(0, weight=1)
        self.info_tab.grid_rowconfigure(0, weight=1)
        
        self.info_listbox = tk.Listbox(
            self.info_tab,
            bg='#2b2b2b' if ctk.get_appearance_mode() == 'Dark' else '#f5f5f5',
            fg='white' if ctk.get_appearance_mode() == 'Dark' else 'black',
            font=('Consolas', 10)
        )
        self.info_listbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def _setup_stats_tab(self):
        self.stats_tab.grid_columnconfigure(0, weight=1)
        self.stats_tab.grid_rowconfigure(0, weight=1)
        
        self.stats_text = ctk.CTkTextbox(self.stats_tab, font=('Consolas', 11))
        self.stats_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.stats_text.configure(state='disabled')
    
    def _setup_log_tab(self):
        self.log_tab.grid_columnconfigure(0, weight=1)
        self.log_tab.grid_rowconfigure(1, weight=1)
        
        control_frame = ctk.CTkFrame(self.log_tab, fg_color="transparent")
        control_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            control_frame, 
            text="Current Log Level: ", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        self.current_level_label = ctk.CTkLabel(
            control_frame, 
            text=self.debug_system.log_level,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4CAF50"
        )
        self.current_level_label.pack(side="left", padx=(0, 20))
        
        levels_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        levels_frame.pack(side="left")
        
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            btn = ctk.CTkButton(
                levels_frame,
                text=level,
                command=lambda lvl=level: self._set_log_level(lvl),
                width=80,
                fg_color="#2196F3" if level == 'INFO' else "#757575",
                hover_color="#1976D2"
            )
            btn.pack(side="left", padx=2)
        
        log_frame = ctk.CTkFrame(self.log_tab)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_text = ctk.CTkTextbox(log_frame, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.log_text.configure(state='disabled')
        
        view_log_btn = ctk.CTkButton(
            log_frame,
            text="View Log Files",
            command=self._view_log_files,
            width=120
        )
        view_log_btn.grid(row=1, column=0, pady=(5, 0))
    
    def _subscribe_to_debug_events(self):
        def on_debug_event(event_type, data):
            self.after(0, lambda: self._handle_debug_event(event_type, data))
        
        self.subscriber_id = self.debug_system.subscribe(
            on_debug_event,
            ['error', 'warning', 'info']
        )
    
    def _handle_debug_event(self, event_type, data):
        if event_type == 'error':
            self._add_error_to_list(data)
        elif event_type == 'warning':
            self._add_warning_to_list(data)
        elif event_type == 'info':
            self._add_info_to_list(data)
        
        self._update_stats()
    
    def _add_error_to_list(self, error_data):
        timestamp = error_data['timestamp'].strftime('%H:%M:%S')
        error_type = error_data['type']
        message = error_data['message'][:100] + "..." if len(error_data['message']) > 100 else error_data['message']
        
        display_text = f"[{timestamp}] {error_type}: {message}"
        
        colors = {
            'GUI': '#FF9800',
            'Thread': '#9C27B0',
            'I/O': '#2196F3',
            'Network': '#00BCD4',
            'Other': '#757575'
        }
        
        self.error_listbox.insert(0, display_text)
        
        if self.error_listbox.size() > 100:
            self.error_listbox.delete(100, tk.END)
    
    def _add_warning_to_list(self, warning_data):
        timestamp = warning_data['timestamp'].strftime('%H:%M:%S')
        warning_type = warning_data['type']
        message = warning_data['message'][:150]
        
        display_text = f"[{timestamp}] {warning_type}: {message}"
        self.warning_listbox.insert(0, display_text)
        
        if self.warning_listbox.size() > 100:
            self.warning_listbox.delete(100, tk.END)
    
    def _add_info_to_list(self, info_data):
        timestamp = info_data['timestamp'].strftime('%H:%M:%S')
        info_type = info_data['type']
        message = info_data['message'][:200]
        
        display_text = f"[{timestamp}] {info_type}: {message}"
        self.info_listbox.insert(0, display_text)
        
        if self.info_listbox.size() > 100:
            self.info_listbox.delete(100, tk.END)
    
    def _on_error_select(self, event):
        selection = self.error_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        errors = self.debug_system.get_all_errors()
        
        if index < len(errors):
            error = errors[index]
            
            details = f"ERROR DETAILS\n"
            details += "=" * 60 + "\n"
            details += f"ID: {error['id']}\n"
            details += f"Time: {error['timestamp']}\n"
            details += f"Type: {error['type']}\n"
            details += f"Category: {error['category']}\n"
            details += f"Module: {error['module']}\n"
            details += f"Function: {error['function']}\n"
            details += f"Thread: {error['thread']}\n"
            details += f"Unhandled: {error['is_unhandled']}\n"
            details += "-" * 60 + "\n"
            details += f"Message:\n{error['message']}\n"
            details += "-" * 60 + "\n"
            
            if error.get('stack_trace'):
                details += f"Stack Trace:\n{error['stack_trace']}\n"
            
            self.error_details.configure(state='normal')
            self.error_details.delete("1.0", tk.END)
            self.error_details.insert("1.0", details)
            self.error_details.configure(state='disabled')
    
    def _update_stats(self):
        stats = self.debug_system.get_stats()
        
        self.stats_label.configure(
            text=f"Errors: {stats['error_count']} | "
                 f"Warnings: {stats['warning_count']} | "
                 f"Uptime: {stats['uptime']}"
        )
        
        stats_text = "DEBUG STATISTICS\n"
        stats_text += "=" * 60 + "\n\n"
        
        stats_text += f"Application Uptime: {stats['uptime']}\n"
        stats_text += f"Start Time: {stats['start_time']}\n"
        stats_text += f"Current Log Level: {stats['log_level']}\n"
        stats_text += f"Active Threads: {stats['thread_count']}\n\n"
        
        stats_text += "ERROR STATISTICS\n"
        stats_text += "-" * 40 + "\n"
        stats_text += f"Total Errors: {stats['error_stats']['total']}\n"
        stats_text += f"Unhandled Exceptions: {stats['error_stats']['unhandled']}\n"
        stats_text += f"GUI Errors: {stats['error_stats']['gui']}\n"
        stats_text += f"Thread Errors: {stats['error_stats']['thread']}\n"
        stats_text += f"I/O Errors: {stats['error_stats']['io']}\n"
        stats_text += f"Network Errors: {stats['error_stats']['network']}\n"
        stats_text += f"Other Errors: {stats['error_stats']['other']}\n\n"
        
        stats_text += "QUEUE SIZES\n"
        stats_text += "-" * 40 + "\n"
        for queue_name, size in stats['queue_sizes'].items():
            stats_text += f"{queue_name}: {size}\n"
        
        self.stats_text.configure(state='normal')
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert("1.0", stats_text)
        self.stats_text.configure(state='disabled')
        
        self.current_level_label.configure(text=self.debug_system.log_level)
    
    def _schedule_refresh(self):
        if self.auto_refresh:
            self._manual_refresh()
            self.after(self.refresh_interval, self._schedule_refresh)
    
    def _manual_refresh(self):
        try:
            self._refresh_error_list()
            self._refresh_warning_list()
            self._refresh_info_list()
            self._update_stats()
            self._refresh_log_viewer()
        except Exception as e:
            logger.error(f"Debug window refresh error: {e}")
    
    def _refresh_error_list(self):
        errors = self.debug_system.get_all_errors()
        self.error_listbox.delete(0, tk.END)
        
        for error in errors[-100:]:
            timestamp = error['timestamp'].strftime('%H:%M:%S')
            error_type = error['type']
            message = error['message'][:100]
            
            display_text = f"[{timestamp}] {error_type}: {message}"
            self.error_listbox.insert(tk.END, display_text)
    
    def _refresh_warning_list(self):
        warnings = self.debug_system.get_all_warnings()
        self.warning_listbox.delete(0, tk.END)
        
        for warning in warnings[-100:]:
            timestamp = warning['timestamp'].strftime('%H:%M:%S')
            warning_type = warning['type']
            message = warning['message'][:150]
            
            display_text = f"[{timestamp}] {warning_type}: {message}"
            self.warning_listbox.insert(tk.END, display_text)
    
    def _refresh_info_list(self):
        infos = self.debug_system.get_all_info()
        self.info_listbox.delete(0, tk.END)
        
        for info in infos[-100:]:
            timestamp = info['timestamp'].strftime('%H:%M:%S')
            info_type = info['type']
            message = info['message'][:200]
            
            display_text = f"[{timestamp}] {info_type}: {message}"
            self.info_listbox.insert(tk.END, display_text)
    
    def _refresh_log_viewer(self):
        try:
            from pathlib import Path
            from edmrn.config import AppConfig
            
            app_data_dir = Path(AppConfig.get_app_data_path())
            log_dir = app_data_dir / "logs"
            
            if log_dir.exists():
                log_files = list(log_dir.glob("*.log"))
                if log_files:
                    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                    
                    with open(latest_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-100:]
                    
                    log_content = f"Latest Log: {latest_log.name}\n"
                    log_content += "=" * 60 + "\n"
                    log_content += "".join(lines)
                    
                    self.log_text.configure(state='normal')
                    self.log_text.delete("1.0", tk.END)
                    self.log_text.insert("1.0", log_content)
                    self.log_text.configure(state='disabled')
                    self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.configure(state='normal')
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert("1.0", f"Error reading log file: {e}")
            self.log_text.configure(state='disabled')
    
    def _change_filter(self, value):
        self.current_filter = value.lower()
        self._manual_refresh()
    
    def _toggle_auto_refresh(self):
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            self._schedule_refresh()
    
    def _clear_all(self):
        self.debug_system.clear_all()
        self._manual_refresh()
    
    def _export_debug_data(self):
        filename = self.debug_system.export_to_file()
        if filename:
            from tkinter import messagebox
            messagebox.showinfo("Export Complete", f"Debug data exported to:\n{filename}")
    
    def _set_log_level(self, level):
        if self.debug_system.set_log_level(level):
            self.current_level_label.configure(text=level)
            self._manual_refresh()
    
    def _view_log_files(self):
        try:
            from pathlib import Path
            import subprocess
            import os
            import sys
            
            log_dir = Path("logs")
            if log_dir.exists():
                if os.name == 'nt':
                    os.startfile(str(log_dir))
                elif sys.platform == 'darwin':
                    subprocess.call(['open', str(log_dir)])
                else:
                    subprocess.call(['xdg-open', str(log_dir)])
        except Exception as e:
            logger.error(f"Error opening log directory: {e}")
    
    def _on_closing(self):
        if self.subscriber_id:
            self.debug_system.unsubscribe(self.subscriber_id)
        self.destroy()