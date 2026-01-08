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
    def start(self, data_callback, opacity=0.8):
        with self._lock:
            if self._running.is_set():
                return False
            self._running.set()
            self._instance = EDMRNOverlay(data_callback, opacity, self._command_queue)
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
                pass
            if self._ui_thread and self._ui_thread.is_alive():
                self._ui_thread.join(timeout=2.0)
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
            return False
    def set_size(self, size_label):
        if not self._running.is_set():
            return False
        try:
            self._command_queue.put(('size', size_label), timeout=0.5, block=False)
            return True
        except queue.Full:
            return False
    def toggle_visibility(self):
        if not self._running.is_set():
            return False
        try:
            self._command_queue.put(('toggle_visibility', None), timeout=0.5, block=False)
            return True
        except queue.Full:
            return False
    def update_data(self):
        if not self._running.is_set():
            return False
        try:
            self._command_queue.put(('update', None), timeout=0.5, block=False)
            return True
        except queue.Full:
            return False
    def is_running(self):
        return self._running.is_set()
class EDMRNOverlay:
    def __init__(self, data_callback, initial_opacity=0.8, command_queue=None):
        self.data_callback = data_callback
        self.root = None
        self.is_visible = True
        self.initial_opacity = initial_opacity
        self.command_queue = command_queue
        self.start_x = 0
        self.start_y = 0
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
    def create_window(self):
        try:
            self.root = tk.Tk()
            self.root.title("EDMRN Navigation")
            if hasattr(self, '_pending_size') and self._pending_size:
                w, h = self._pending_size
                self.root.geometry(f"{w}x{h}+100+100")
                self._pending_size = None
            else:
                self.root.geometry("220x300+100+100")
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
            close_btn.bind("<Button-1>", lambda e: self.toggle_visibility())
            content_frame = tk.Frame(self.root, bg=bg_color, padx=10, pady=8)
            content_frame.pack(fill="both", expand=True)
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
            bodies_frame = tk.Frame(content_frame, bg=bg_color, height=80)
            bodies_frame.pack(fill="both", expand=True)
            bodies_frame.pack_propagate(False)
            self.canvas = tk.Canvas(bodies_frame, bg=bg_color, highlightthickness=0, height=80)
            scrollbar = ttk.Scrollbar(bodies_frame, orient="vertical", command=self.canvas.yview)
            self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            )
            self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            self.canvas.configure(yscrollcommand=scrollbar.set)
            self.canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            self.body_labels = []
            footer_frame = tk.Frame(self.root, bg=bg_color, height=18)
            footer_frame.pack(fill="x", side="bottom")
            footer_frame.pack_propagate(False)
            footer_label = tk.Label(
                footer_frame,
                text="Drag header to move",
                font=("Segoe UI", 9),
                bg=bg_color,
                fg=text_color
            )
            footer_label.pack(pady=3)
            self.footer_label = footer_label
            try:
                if hasattr(self, '_pending_label') and self._pending_label:
                    self.set_size(self._pending_label)
                    self._pending_label = None
            except Exception as e:
                logger.error(f"Applying pending size label failed: {e}")
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
            return
        for i, body in enumerate(bodies[:6]):
            display_body = body[:25] + "..." if len(body) > 25 else body
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
            'Small': (200, 240),
            'Medium': (220, 300),
            'Large': (260, 360),
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
                    logger.info(f"Applied overlay geometry: {w}x{h}+{x}+{y}")
                except Exception as e:
                    logger.error(f"Failed to set geometry: {e}")
                try:
                    if self.canvas:
                        self.canvas.configure(height=max(60, h - 140))
                except Exception:
                    pass
                try:
                    if hasattr(self, 'footer_label') and self.footer_label:
                        self.footer_label.config(text=f"Size: {size_label}")
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
            data = self.current_data
            system_name = data['current_system']
            display_system = system_name[:18] + "..." if len(system_name) > 18 else system_name
            if self.system_label:
                self.system_label.config(text=f"{Icons.LOCATION} {display_system}")
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
            display_next = next_system[:22] + "..." if len(next_system) > 22 else next_system
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
        except Exception as e:
            logger.error(f"Overlay update error: {e}")
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
    def run(self, running_event):
        try:
            self.create_window()
            def process_commands():
                try:
                    while not self.command_queue.empty():
                        cmd, value = self.command_queue.get_nowait()
                        if cmd == 'stop':
                            return False
                        elif cmd == 'opacity' and value is not None:
                            self.set_opacity(value)
                        elif cmd == 'toggle_visibility':
                            self.toggle_visibility()
                        elif cmd == 'size' and value is not None:
                            self.set_size(value)
                        elif cmd == 'update':
                            pass
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
