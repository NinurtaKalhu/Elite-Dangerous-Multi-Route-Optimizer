import tkinter as tk
from tkinter import ttk
import threading
import platform
import queue
from edmrn.logger import get_logger
from edmrn.icons import Icons
logger = get_logger('Overlay')
class ThreadSafeOverlay:
    def __init__(self):
        self._command_queue = queue.Queue(maxsize=50)
        self._running = threading.Event()
        self._lock = threading.RLock()
        self._instance = None
        self._ui_thread = None
    def start(self, data_callback, opacity=0.8, app_instance=None):
        with self._lock:
            if self._running.is_set():
                return False
            self._running.set()
            self._instance = EDMRNOverlay(data_callback, opacity, self._command_queue, app_instance)
            self._ui_thread = threading.Thread(
                target=self._run_overlay,
                daemon=True,
                name="OverlayUIThread"
            )
            self._ui_thread.start()
            return True
    def stop(self):
        with self._lock:
            if not self._running.is_set():
                return False
            self._running.clear()
            try:
                self._command_queue.put(('stop', None), timeout=1.0, block=False)
            except queue.Full:
                logger.warning("Overlay command queue full during stop")
            
            try:
                while not self._command_queue.empty():
                    self._command_queue.get_nowait()
            except queue.Empty:
                pass
            
            if self._ui_thread and self._ui_thread.is_alive():
                self._ui_thread.join(timeout=1.0)
            self._instance = None
            self._ui_thread = None
            return True
    def _run_overlay(self):
        try:
            if self._instance:
                self._instance.run(self._running)
        except Exception as e:
            logger.error(f"Overlay thread error: {e}")
        finally:
            self._running.clear()
    def set_opacity(self, alpha_value):
        if not self._running.is_set():
            return False
        try:
            self._command_queue.put(('opacity', alpha_value), timeout=0.5, block=False)
            return True
        except queue.Full:
            logger.warning("Overlay command queue full, opacity command dropped")
            return False
    def set_size(self, size_label):
        if not self._running.is_set():
            return False
        try:
            self._command_queue.put(('size', size_label), timeout=0.5, block=False)
            try:
                self.root.update_idletasks()
                req_width = self.root.winfo_width()
                req_height = self.root.winfo_reqheight()
                self.root.geometry(f"{req_width}x{req_height}+{x}+{y}")
            except Exception as e:
                logger.error(f"Failed to shrink-to-fit after size change: {e}")
            self.update_display()
            return True
        except queue.Full:
            logger.warning("Overlay command queue full, size command dropped")
            return False
    def toggle_visibility(self):
        if not self._running.is_set():
            return False
        try:
            self._command_queue.put(('toggle_visibility', None), timeout=0.5, block=False)
            return True
        except queue.Full:
            logger.warning("Overlay command queue full, toggle visibility command dropped")
            return False
    def update_data(self):
        if not self._running.is_set():
            return False
        try:
            self._command_queue.put(('update', None), timeout=0.5, block=False)
            return True
        except queue.Full:
            logger.warning("Overlay command queue full, update data command dropped")
            return False
    
    def prev_waypoint(self):
        if not self._running.is_set():
            return False
        try:
            self._command_queue.put(('prev', None), timeout=0.5, block=False)
            return True
        except queue.Full:
            logger.warning("Overlay command queue full, prev waypoint command dropped")
            return False
    
    def next_waypoint(self):
        if not self._running.is_set():
            return False
        try:
            self._command_queue.put(('next', None), timeout=0.5, block=False)
            return True
        except queue.Full:
            logger.warning("Overlay command queue full, next waypoint command dropped")
            return False
    
    def switch_tab(self, tab_name):
        if not self._running.is_set():
            return False
        try:
            self._command_queue.put(('switch_tab', tab_name), timeout=0.5, block=False)
            return True
        except queue.Full:
            logger.warning("Overlay command queue full, switch tab command dropped")
            return False
    
    def is_running(self):
        return self._running.is_set()
class EDMRNOverlay:
    def _resize_canvas_to_content(self, min_height, max_height):
        self.scrollable_frame.update_idletasks()
        content_height = self.scrollable_frame.winfo_reqheight()
        new_height = max(min_height, min(content_height, max_height))
        self.canvas.configure(height=new_height)
    def __init__(self, data_callback, initial_opacity=0.8, command_queue=None, app_instance=None):
        self.data_callback = data_callback
        self.app_instance = app_instance
        self.root = None
        self.is_visible = True
        self.initial_opacity = initial_opacity
        self.command_queue = command_queue
        self.start_x = 0
        self.start_y = 0
        self.current_tab = "Route Tracking"
        self._tab_switch_in_progress = False
        self.current_data = {
            'current_system': 'EDMRN',
            'current_status': 'READY',
            'bodies_to_scan': ['Load route...'],
            'next_system': 'N/A',
            'progress': '0/0 (0%)',
            'total_distance': '0.00 LY',
            'traveled_distance': '0.00 LY'
        }
        self.system_label = None
        self.status_label = None
        self.next_label = None
        self.progress_label = None
        self.progress_label2 = None
        self.distance_label = None
        self.canvas = None
        self.scrollable_frame = None
        self.body_labels = []
        self.copy_btn = None
        self.prev_btn = None
        self.next_btn = None
    def create_window(self):
        try:
            self.root = tk.Tk()
            self.root.title("EDMRN Navigation")
            if hasattr(self, '_pending_size') and self._pending_size:
                w, h = self._pending_size
                self.root.geometry(f"{w}x{h}+100+100")
                self._pending_size = None
            else:
                self.root.geometry("220x220+100+100")
            self.root.overrideredirect(True)
            self.root.attributes('-topmost', True)
            self._apply_platform_specific_settings()
            bg_color = "#0D0D0D"
            header_color = "#1A1A1A"
            text_color = "#E0E0E0"
            accent_color = "#FF8C00"
            self.root.configure(bg=bg_color)
            header_frame = tk.Frame(self.root, bg=header_color, height=25, cursor="fleur")
            header_frame.pack(fill="x", side="top")
            header_frame.pack_propagate(False)
            header_frame.bind("<Button-1>", self.start_drag)
            header_frame.bind("<B1-Motion>", self.do_drag)
            header_frame.bind("<ButtonRelease-1>", self.end_drag)
            title_label = tk.Label(
                header_frame,
                text="EDMRN",
                bg=header_color,
                fg=accent_color,
                font=("Segoe UI", 9, "bold")
            )
            title_label.pack(pady=5)
            title_label.bind("<Button-1>", self.start_drag)
            title_label.bind("<B1-Motion>", self.do_drag)
            title_label.bind("<ButtonRelease-1>", self.end_drag)
            close_btn = tk.Label(
                header_frame,
                text=Icons.CLOSE,
                font=("Segoe UI", 8, "bold"),
                bg=header_color,
                fg=accent_color,
                cursor="hand2"
            )
            close_btn.place(relx=0.95, rely=0.5, anchor="e")
            close_btn.bind("<Button-1>", lambda e: self.handle_close())
            content_frame = tk.Frame(self.root, bg=bg_color, padx=10, pady=8)
            expand_content = getattr(self, '_current_size_label', 'Medium') != 'Small'
            content_frame.pack(fill="both", expand=expand_content)
            self.system_label = tk.Label(
                content_frame,
                text=f"{Icons.LOCATION} Loading...",
                font=("Segoe UI", 9, "normal"),
                bg=bg_color,
                fg=text_color,
                anchor="w"
            )
            self.system_label.pack(fill="x", pady=(0, 3))
            self.status_label = tk.Label(
                content_frame,
                text="READY",
                font=("Segoe UI", 8, "bold"),
                bg=bg_color,
                fg=accent_color,
                anchor="e"
            )
            self.status_label.place(relx=1.0, rely=0.0, anchor="ne")
            ttk.Separator(content_frame, orient="horizontal").pack(fill="x", pady=4)
            self.next_label = tk.Label(
                content_frame,
                text=f"{Icons.ARROW_RIGHT} ...",
                font=("Segoe UI", 9),
                bg=bg_color,
                fg=accent_color,
                anchor="w"
            )
            self.next_label.pack(fill="x", pady=1)
            self.progress_label = tk.Label(
                content_frame,
                text="0/0",
                font=("Consolas", 9),
                bg=bg_color,
                fg=text_color,
                anchor="w"
            )
            self.progress_label.pack(fill="x", pady=1)
            self.progress_label2 = tk.Label(
                content_frame,
                text="",
                font=("Consolas", 9),
                bg=bg_color,
                fg=text_color,
                anchor="w"
            )
            self.progress_label2.pack(fill="x", pady=1)
            self.distance_label = tk.Label(
                content_frame,
                text=f"{Icons.COMPASS} 0.00/0.00",
                font=("Consolas", 9),
                bg=bg_color,
                fg=text_color,
                anchor="w"
            )
            self.distance_label.pack(fill="x", pady=1)
            ttk.Separator(content_frame, orient="horizontal").pack(fill="x", pady=6)
            bodies_title = tk.Label(
                content_frame,
                text=f"{Icons.TARGET} Scan:",
                font=("Segoe UI", 9, "bold"),
                bg=bg_color,
                fg=accent_color,
                anchor="w"
            )
            bodies_title.pack(fill="x", pady=(2, 1))
            min_height = 60
            max_height = 220
            self.bodies_frame = tk.Frame(content_frame, bg=bg_color)
            self.bodies_frame.pack(fill="x", expand=False)
            self.canvas = tk.Canvas(self.bodies_frame, bg=bg_color, highlightthickness=0)
            scrollbar = ttk.Scrollbar(self.bodies_frame, orient="vertical", command=self.canvas.yview)
            self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: [
                    self.canvas.configure(scrollregion=self.canvas.bbox("all")),
                    self._resize_canvas_to_content(min_height, max_height)
                ]
            )
            self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            self.canvas.configure(yscrollcommand=scrollbar.set)
            self.canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            self.body_labels = []
            
            control_frame = tk.Frame(self.root, bg=bg_color)
            control_frame.pack(fill="x", side="bottom")
            tab_frame = tk.Frame(control_frame, bg=bg_color)
            tab_frame.pack(fill="x", pady=(2, 4))
            
            tab_btn_config = {
                'font': ('Segoe UI', 8, 'bold'),
                'width': 3,
                'height': 1,
                'relief': 'flat',
                'cursor': 'hand2'
            }
            
            self.tab_rt_btn = tk.Button(
                tab_frame,
                text='RT',
                bg='#FF8C00',
                fg='#0D0D0D',
                activebackground='#FFA500',
                command=lambda: self.handle_tab_switch('Route Tracking'),
                **tab_btn_config
            )
            self.tab_rt_btn.pack(side='left', padx=2)
            
            self.tab_nh_btn = tk.Button(
                tab_frame,
                text='NH',
                bg='#2A2A2A',
                fg='#888888',
                activebackground='#3A3A3A',
                command=lambda: self.handle_tab_switch('Neutron Highway'),
                **tab_btn_config
            )
            self.tab_nh_btn.pack(side='left', padx=2)
            
            self.tab_gp_btn = tk.Button(
                tab_frame,
                text='GP',
                bg='#2A2A2A',
                fg='#888888',
                activebackground='#3A3A3A',
                command=lambda: self.handle_tab_switch('Galaxy Plotter'),
                **tab_btn_config
            )
            self.tab_gp_btn.pack(side='left', padx=2)
            
            nav_frame = tk.Frame(control_frame, bg=bg_color)
            nav_frame.pack(fill="x", pady=(0, 0))
            
            nav_btn_config = {
                'font': ('Segoe UI', 10, 'bold'),
                'width': 2,
                'height': 1,
                'relief': 'flat',
                'bg': '#2A2A2A',
                'fg': '#E0E0E0',
                'activebackground': '#3A3A3A',
                'cursor': 'hand2'
            }
            
            self.prev_btn = tk.Button(
                nav_frame,
                text='<',
                command=self.handle_prev,
                **nav_btn_config
            )
            self.prev_btn.pack(side='left', padx=(0, 4))
            
            self.copy_btn = tk.Button(
                nav_frame,
                text='EDMRN',
                font=('Segoe UI', 8, 'bold'),
                width=8,
                height=1,
                relief='flat',
                bg='#FF8C00',
                fg='#0D0D0D',
                activebackground='#FFA500',
                cursor='hand2',
                command=self.handle_copy_current
            )
            self.copy_btn.pack(side='left', padx=2, expand=True, fill='x')
            
            self.next_btn = tk.Button(
                nav_frame,
                text='>',
                command=self.handle_next,
                **nav_btn_config
            )
            self.next_btn.pack(side='left', padx=(4, 0))
            try:
                if hasattr(self, '_pending_label') and self._pending_label:
                    self.set_size(self._pending_label)
                    self._pending_label = None
            except Exception as e:
                logger.error(f"Applying pending size label failed: {e}")
            self.root.update_idletasks()
            req_width = self.root.winfo_width()
            req_height = self.root.winfo_reqheight()
            self.root.geometry(f"{req_width}x{req_height}")
        except Exception as e:
            logger.error(f"Window creation error: {e}")
            if self.root:
                try:
                    self.root.destroy()
                except Exception:
                    pass
            self.root = None
            raise
    def _apply_platform_specific_settings(self):
        try:
            self.root.attributes('-alpha', self.initial_opacity)
            if platform.system() == "Linux":
                try:
                    self.root.attributes('-type', 'dock')
                except Exception:
                    pass
        except Exception:
            pass
    def start_drag(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
    def do_drag(self, event):
        if not self.start_x or not self.start_y:
            return
        x = self.root.winfo_x() + (event.x_root - self.start_x)
        y = self.root.winfo_y() + (event.y_root - self.start_y)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        self.root.geometry(f"+{x}+{y}")
        self.start_x = event.x_root
        self.start_y = event.y_root
    def end_drag(self, event):
        self.start_x = 0
        self.start_y = 0
    
    def handle_prev(self):
        try:
            if self.command_queue:
                try:
                    self.command_queue.put(('prev', None), block=False)
                except queue.Full:
                    pass
        except Exception as e:
            logger.error(f"Handle prev error: {e}")
    
    def handle_next(self):
        try:
            if self.command_queue:
                try:
                    self.command_queue.put(('next', None), block=False)
                except queue.Full:
                    pass
        except Exception as e:
            logger.error(f"Handle next error: {e}")
    
    def handle_copy_current(self):
        try:
            if self.command_queue:
                try:
                    self.command_queue.put(('copy_current', None), block=False)
                except queue.Full:
                    pass
        except Exception as e:
            logger.error(f"Handle copy error: {e}")
    
    def handle_close(self):
        try:
            self.toggle_visibility()
            
            if self.app_instance and self.app_instance.root:
                self.app_instance.root.after(10, self.app_instance._toggle_overlay)
        except Exception as e:
            logger.error(f"Handle close error: {e}")
    
    def handle_tab_switch(self, tab_name):
        try:
            if tab_name not in ("Route Tracking", "Neutron Highway", "Galaxy Plotter"):
                logger.warning(f"Overlay tab switch: Invalid tab name '{tab_name}', skipping.")
                return
            if self._tab_switch_in_progress:
                logger.debug(f"Tab switch already in progress, ignoring: {tab_name}")
                return
            self._tab_switch_in_progress = True
            self._disable_tab_buttons()
            if self.app_instance and self.app_instance.root:
                try:
                    self.app_instance.root.after(0, lambda: self._handle_tab_switch_callback(tab_name))
                except Exception as e:
                    logger.error(f"Failed to schedule tab switch: {e}")
                    self._enable_tab_buttons()
                    self._tab_switch_in_progress = False
                    return
            if self.root:
                self.root.after(600, self._reset_tab_switch_flag)
        except Exception as e:
            logger.error(f"Handle tab switch error: {e}")
            self._tab_switch_in_progress = False
            self._enable_tab_buttons()
    
    def _reset_tab_switch_flag(self):
        self._tab_switch_in_progress = False
        self._enable_tab_buttons()
    
    def _disable_tab_buttons(self):
        try:
            if hasattr(self, 'tab_rt_btn'):
                self.tab_rt_btn.config(state='disabled')
            if hasattr(self, 'tab_nh_btn'):
                self.tab_nh_btn.config(state='disabled')
            if hasattr(self, 'tab_gp_btn'):
                self.tab_gp_btn.config(state='disabled')
        except Exception as e:
            logger.error(f"Error disabling tab buttons: {e}")
    
    def _enable_tab_buttons(self):
        try:
            if hasattr(self, 'tab_rt_btn'):
                self.tab_rt_btn.config(state='normal')
            if hasattr(self, 'tab_nh_btn'):
                self.tab_nh_btn.config(state='normal')
            if hasattr(self, 'tab_gp_btn'):
                self.tab_gp_btn.config(state='normal')
        except Exception as e:
            logger.error(f"Error enabling tab buttons: {e}")
    
    def update_tab_buttons(self, active_tab):
        self.current_tab = active_tab
        
        inactive_bg = '#2A2A2A'
        inactive_fg = '#888888'
        active_bg = '#FF8C00'
        active_fg = '#0D0D0D'
        
        if hasattr(self, 'tab_rt_btn'):
            if active_tab == 'Route Tracking':
                self.tab_rt_btn.config(bg=active_bg, fg=active_fg)
            else:
                self.tab_rt_btn.config(bg=inactive_bg, fg=inactive_fg)
        
        if hasattr(self, 'tab_nh_btn'):
            if active_tab == 'Neutron Highway':
                self.tab_nh_btn.config(bg=active_bg, fg=active_fg)
            else:
                self.tab_nh_btn.config(bg=inactive_bg, fg=inactive_fg)
        
        if hasattr(self, 'tab_gp_btn'):
            if active_tab == 'Galaxy Plotter':
                self.tab_gp_btn.config(bg=active_bg, fg=active_fg)
            else:
                self.tab_gp_btn.config(bg=inactive_bg, fg=inactive_fg)
    def set_opacity(self, alpha_value):
        if self.root:
            try:
                self.root.attributes('-alpha', alpha_value)
            except Exception:
                pass
        logger.info(f"Overlay opacity set to: {alpha_value}")
    def update_bodies_display(self, bodies):
        for label in self.body_labels:
            try:
                label.destroy()
            except Exception:
                pass
        self.body_labels.clear()
        size_limits = {
            'Small': 18,
            'Medium': 25,
            'Large': 30,
        }
        current_size = getattr(self, '_current_size_label', 'Medium')
        body_char_limit = size_limits.get(current_size, 25)
        if not bodies or bodies[0] in ['Load route...', 'No bodies to scan']:
            label = tk.Label(
                self.scrollable_frame,
                text="• No bodies",
                font=("Segoe UI", 8),
                bg="#0D0D0D",
                fg="#888888",
                anchor="w"
            )
            label.pack(fill="x", pady=1)
            self.body_labels.append(label)
        else:
            for i, body in enumerate(bodies[:6]):
                display_body = body[:body_char_limit] + "..." if len(body) > body_char_limit else body
                label = tk.Label(
                    self.scrollable_frame,
                    text=f"• {display_body}",
                    font=("Segoe UI", 8),
                    bg="#0D0D0D",
                    fg="#E0E0E0",
                    anchor="w"
                )
                label.pack(fill="x", pady=1)
                self.body_labels.append(label)
            if len(bodies) > 6:
                more_label = tk.Label(
                    self.scrollable_frame,
                    text=f"... +{len(bodies) - 6} more",
                    font=("Segoe UI", 7),
                    bg="#0D0D0D",
                    fg="#888888",
                    anchor="w"
                )
                more_label.pack(fill="x", pady=1)
                self.body_labels.append(more_label)
    def set_size(self, size_label):
        presets = {
            'Small': (200, 320),
            'Medium': (220, 380),
            'Large': (260, 440),
        }
        logger.info(f"Requested overlay size: {size_label}")
        if size_label not in presets:
            logger.warning(f"Unknown size label requested: {size_label}")
            return False
        w, h = presets[size_label]
        try:
            if self.root:
                try:
                    x = self.root.winfo_x()
                    y = self.root.winfo_y()
                except Exception:
                    x = 100
                    y = 100
                try:
                    self.root.geometry(f"{w}x{h}+{x}+{y}")
                    self.root.update()
                    self.root.update_idletasks()
                    logger.info(f"Applied overlay geometry: {w}x{h}+{x}+{y}")
                except Exception as e:
                    logger.error(f"Failed to set geometry: {e}")
                try:
                    if size_label == 'Small':
                        bodies_height = 40
                    elif size_label == 'Medium':
                        bodies_height = 80
                    else:
                        bodies_height = 100
                    
                    if hasattr(self, 'bodies_frame') and self.bodies_frame:
                        self.bodies_frame.configure(height=bodies_height)
                    if self.canvas:
                        self.canvas.configure(height=bodies_height)
                except Exception as e:
                    logger.error(f"Failed to adjust bodies frame: {e}")
                try:
                    canvas_height = max(60, h - 140)
                    if self.canvas:
                        self.canvas.configure(height=canvas_height)
                except Exception:
                    pass
                self._current_size_label = size_label
            else:
                self._pending_size = (w, h)
                self._pending_label = size_label
                logger.info(f"Stored pending overlay size: {size_label} -> {w}x{h}")
            return True
        except Exception as e:
            logger.error(f"Set size error: {e}")
            return False
    def update_display(self):
        if not self.root:
            return
        try:
            new_data = self.data_callback()
            if new_data:
                self.current_data.update(new_data)
            elif new_data is None:
                pass
            if not isinstance(self.current_data, dict):
                logger.warning(f"[Overlay] current_data is not dict, got {type(self.current_data).__name__}")
                return
            self.root.update_idletasks()
            req_width = self.root.winfo_width()
            req_height = self.root.winfo_reqheight()
            self.root.geometry(f"{req_width}x{req_height}")
            data = self.current_data
            system_name = data['current_system']
            size_limits = {
                'Small': 18,
                'Medium': 25,
                'Large': 30,
            }
            current_size = getattr(self, '_current_size_label', 'Medium')
            char_limit = size_limits.get(current_size, 18)
            display_system = system_name[:char_limit] + "..." if len(system_name) > char_limit else system_name
            if self.system_label:
                self.system_label.config(text=f"{Icons.LOCATION} {display_system}")
            if self.copy_btn:
                btn_char_limit = size_limits.get(current_size, 18) - 5
                btn_system = system_name[:btn_char_limit] + "..." if len(system_name) > btn_char_limit else system_name
                self.copy_btn.config(text=btn_system)
            status = data['current_status']
            if status == 'NEUTRON':
                status_color = "#00AEFF"
                status_text = "NEUTRON"
            elif status == 'visited':
                status_color = "#4CAF50"
                status_text = "VISITED"
            elif status == 'skipped':
                status_color = "#FFA500"
                status_text = "SKIPPED"
            else:
                status_color = "#E0E0E0"
                status_text = "READY"
            if self.status_label:
                self.status_label.config(text=status_text, fg=status_color)
            next_system = data['next_system']
            next_char_limit = size_limits.get(current_size, 22)
            display_next = next_system[:next_char_limit] + "..." if len(next_system) > next_char_limit else next_system
            if self.next_label:
                self.next_label.config(text=f"{Icons.ARROW_RIGHT} {display_next}")
            if self.progress_label:
                progress_text = data['progress']
                if '\n' in progress_text:
                    lines = progress_text.split('\n')
                    self.progress_label.config(text=lines[0])
                    if len(lines) > 1 and self.progress_label2:
                        self.progress_label2.config(text=lines[1])
                else:
                    self.progress_label.config(text=progress_text)
                    if self.progress_label2:
                        self.progress_label2.config(text="")
            if self.distance_label:
                if 'distance' in data:
                    dist_text = data['distance']
                else:
                    dist_text = f"{data['traveled_distance']}/{data['total_distance']}"
                self.distance_label.config(text=f"{Icons.COMPASS} {dist_text}")
            bodies = data['bodies_to_scan']
            self.update_bodies_display(bodies)
            exobio_species = data.get('exobio_species', [])
            if hasattr(self, 'exobio_labels'):
                for label in self.exobio_labels:
                    try:
                        label.destroy()
                    except Exception:
                        pass
                self.exobio_labels.clear()
            else:
                self.exobio_labels = []
            if exobio_species:
                sep = tk.Label(self.scrollable_frame, text="Exobiology scans:", font=("Segoe UI", 8, "bold"), bg="#0D0D0D", fg="#FFD700", anchor="w")
                sep.pack(fill="x", pady=(6, 0))
                self.exobio_labels.append(sep)
                for species, count in exobio_species[:6]:
                    icon = "🟢" if count >= 3 else ("🟡" if count == 2 else ("🟠" if count == 1 else "🔴"))
                    label = tk.Label(
                        self.scrollable_frame,
                        text=f"{icon} {species} ({count}/3)",
                        font=("Segoe UI", 8),
                        bg="#0D0D0D",
                        fg="#A3FFB0" if count >= 3 else ("#FFD700" if count == 2 else ("#FFA500" if count == 1 else "#FF5D5D")),
                        anchor="w"
                    )
                    label.pack(fill="x", pady=1)
                    self.exobio_labels.append(label)
                if len(exobio_species) > 6:
                    more_label = tk.Label(
                        self.scrollable_frame,
                        text=f"... +{len(exobio_species) - 6} more",
                        font=("Segoe UI", 7),
                        bg="#0D0D0D",
                        fg="#888888",
                        anchor="w"
                    )
                    more_label.pack(fill="x", pady=1)
                    self.exobio_labels.append(more_label)
        except Exception as e:
            logger.error(f"Overlay update error: {e}")
        try:
            if self.root:
                self.root.update_idletasks()
                req_width = self.root.winfo_width()
                req_height = self.root.winfo_reqheight()
                x = self.root.winfo_x()
                y = self.root.winfo_y()
                self.root.geometry(f"{req_width}x{req_height}+{x}+{y}")
        except Exception as e:
            logger.error(f"Overlay shrink-to-fit after update_display failed: {e}")
    def toggle_visibility(self):
        if not self.root:
            return
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False
        else:
            self.root.deiconify()
            try:
                self.root.attributes('-topmost', True)
            except Exception:
                pass
            self.is_visible = True
    
    def _handle_prev_callback(self):
        if not self.app_instance:
            return
        try:
            current_tab = self.app_instance.tabview.get()
            if current_tab not in ("Route Tracking", "Neutron Highway", "Galaxy Plotter"):
                logger.warning(f"Overlay prev: No valid tab selected (current_tab={current_tab!r}), skipping action.")
                return
            if current_tab == "Route Tracking":
                self.app_instance._copy_prev_system_to_clipboard()
            elif current_tab == "Neutron Highway":
                self.app_instance._neutron_prev_waypoint()
            elif current_tab == "Galaxy Plotter":
                self.app_instance._galaxy_prev_waypoint()
        except Exception as e:
            logger.error(f"Prev callback error: {e}")
            try:
                from edmrn.gui import ErrorDialog
                ErrorDialog(self.app_instance, "Overlay Error", f"Overlay prev/next error (prev):\n{e}")
            except Exception:
                pass
    
    def _handle_next_callback(self):
        if not self.app_instance:
            return
        try:
            current_tab = self.app_instance.tabview.get()
            if current_tab not in ("Route Tracking", "Neutron Highway", "Galaxy Plotter"):
                logger.warning(f"Overlay next: No valid tab selected (current_tab={current_tab!r}), skipping action.")
                return
            if current_tab == "Route Tracking":
                self.app_instance._advance_route_tracking_from_overlay()
            elif current_tab == "Neutron Highway":
                self.app_instance._neutron_next_waypoint()
            elif current_tab == "Galaxy Plotter":
                self.app_instance._galaxy_next_waypoint()
            if self.root:
                self.root.after(100, self.update_display)
        except Exception as e:
            logger.error(f"Next callback error: {e}")
            try:
                from edmrn.gui import ErrorDialog
                ErrorDialog(self.app_instance, "Overlay Error", f"Overlay prev/next error (next):\n{e}")
            except Exception:
                pass
    
    def _handle_copy_callback(self):
        if not self.app_instance:
            return
        try:
            current_tab = self.app_instance.tabview.get()
            if current_tab == "Route Tracking":
                self.app_instance._copy_next_system_to_clipboard()
            elif current_tab == "Neutron Highway":
                self.app_instance._copy_current_neutron_system()
            elif current_tab == "Galaxy Plotter":
                self.app_instance._copy_current_galaxy_system()
        except Exception as e:
            logger.error(f"Copy callback error: {e}")
    
    def _handle_tab_switch_callback(self, tab_name):
        if not self.app_instance:
            logger.warning("Overlay tab switch callback: app_instance missing, skipping.")
            return
        try:
            if tab_name not in ("Route Tracking", "Neutron Highway", "Galaxy Plotter"):
                logger.warning(f"Overlay tab switch callback: Invalid tab name '{tab_name}', skipping.")
                return
            current = self.app_instance.tabview.get()
            if current == tab_name:
                logger.debug(f"Already on tab: {tab_name}")
                if self.root:
                    self.root.after(0, lambda: self.update_tab_buttons(tab_name))
                return
            self.app_instance.tabview.set(tab_name)
            if self.root:
                self.root.after(0, lambda: self.update_tab_buttons(tab_name))
            logger.info(f"Tab switched to: {tab_name}")
        except Exception as e:
            logger.error(f"Tab switch callback error: {e}")
    def run(self, running_event):
        try:
            self.create_window()
            def process_commands():
                try:
                    while not self.command_queue.empty():
                        cmd, value = self.command_queue.get_nowait()
                        if cmd == 'stop':
                            running_event.clear()
                            return False
                        elif cmd == 'opacity' and value is not None:
                            self.set_opacity(value)
                        elif cmd == 'toggle_visibility':
                            self.toggle_visibility()
                        elif cmd == 'size' and value is not None:
                            self.set_size(value)
                        elif cmd == 'update':
                            pass
                        elif cmd == 'prev':
                            if self.app_instance:
                                self.app_instance.root.after(0, self._handle_prev_callback)
                        elif cmd == 'next':
                            if self.app_instance:
                                self.app_instance.root.after(0, self._handle_next_callback)
                        elif cmd == 'copy_current':
                            if self.app_instance:
                                self.app_instance.root.after(0, self._handle_copy_callback)
                        elif cmd == 'switch_tab' and value is not None:
                            if self.app_instance:
                                self.app_instance.root.after(0, lambda: self._handle_tab_switch_callback(value))
                except queue.Empty:
                    pass
                return True
            def update_loop():
                if not running_event.is_set() or not self.root:
                    return
                if not process_commands():
                    return
                self.update_display()
                if self.root:
                    self.root.after(1000, update_loop)
            self.root.after(100, update_loop)
            try:
                self.root.mainloop()
            except KeyboardInterrupt:
                pass
        finally:
            if self.root:
                try:
                    self.root.quit()
                    self.root.destroy()
                except Exception:
                    pass
                self.root = None
            try:
                if hasattr(self, '_pending_label'):
                    self._pending_label = None
                if hasattr(self, '_pending_size'):
                    self._pending_size = None
            except Exception:
                pass
_overlay_manager = ThreadSafeOverlay()
def get_overlay_manager():
    return _overlay_manager
