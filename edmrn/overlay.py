import tkinter as tk
from tkinter import ttk
import threading
import time
import platform
import queue
from edmrn.logger import get_logger

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
    
    def toggle_visibility(self):
        if not self._running.is_set():
            return False
        
        try:
            self._command_queue.put(('toggle_visibility', None), timeout=0.5, block=False)
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
        self.distance_label = None
        self.canvas = None
        self.scrollable_frame = None
        self.body_labels = []
    
    def create_window(self):
        try:
            self.root = tk.Tk()
            self.root.title("EDMRN Navigation")
            self.root.geometry("220x300+100+100")
            self.root.overrideredirect(True)
            self.root.attributes('-topmost', True)
            
            self._apply_platform_specific_settings()
            
            bg_color = "#1a1a2e"
            header_color = "#16213e"
            text_color = "#e6e6e6"
            
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
                fg="#f0a500",
                font=("Arial", 9, "bold")
            )
            title_label.pack(pady=5)
            title_label.bind("<Button-1>", self.start_drag)
            title_label.bind("<B1-Motion>", self.do_drag)
            title_label.bind("<ButtonRelease-1>", self.end_drag)
            
            close_btn = tk.Label(
                header_frame,
                text="✕",
                font=("Arial", 8, "bold"),
                bg=header_color,
                fg="white",
                cursor="hand2"
            )
            close_btn.place(relx=0.95, rely=0.5, anchor="e")
            close_btn.bind("<Button-1>", lambda e: self.toggle_visibility())
            
            content_frame = tk.Frame(self.root, bg=bg_color, padx=10, pady=8)
            content_frame.pack(fill="both", expand=True)
            
            self.system_label = tk.Label(
                content_frame,
                text="📍 Loading...",
                font=("Arial", 10, "bold"),
                bg=bg_color,
                fg=text_color,
                anchor="w"
            )
            self.system_label.pack(fill="x", pady=(0, 3))
            
            self.status_label = tk.Label(
                content_frame,
                text="READY",
                font=("Arial", 8, "bold"),
                bg=bg_color,
                fg="#4CAF50",
                anchor="e"
            )
            self.status_label.place(relx=1.0, rely=0.0, anchor="ne")
            
            ttk.Separator(content_frame, orient="horizontal").pack(fill="x", pady=4)
            
            self.next_label = tk.Label(
                content_frame,
                text="➡️ ...",
                font=("Arial", 9),
                bg=bg_color,
                fg="#ffd700",
                anchor="w"
            )
            self.next_label.pack(fill="x", pady=1)
            
            self.progress_label = tk.Label(
                content_frame,
                text="📊 0/0",
                font=("Arial", 8),
                bg=bg_color,
                fg="#a0a0ff",
                anchor="w"
            )
            self.progress_label.pack(fill="x", pady=1)
            
            self.distance_label = tk.Label(
                content_frame,
                text="🧭 0.00/0.00",
                font=("Arial", 8),
                bg=bg_color,
                fg="#87ceeb",
                anchor="w"
            )
            self.distance_label.pack(fill="x", pady=1)
            
            ttk.Separator(content_frame, orient="horizontal").pack(fill="x", pady=6)
            
            bodies_title = tk.Label(
                content_frame,
                text="🎯 Scan:",
                font=("Arial", 9, "bold"),
                bg=bg_color,
                fg="#90ee90",
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
                font=("Arial", 7),
                bg=bg_color,
                fg="gray"
            )
            footer_label.pack(pady=3)
            
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
                font=("Arial", 8),
                bg="#1a1a2e",
                fg="#a0a0a0",
                anchor="w"
            )
            label.pack(fill="x", pady=1)
            self.body_labels.append(label)
            return
        
        for i, body in enumerate(bodies[:6]):
            display_body = body[:20] + "..." if len(body) > 20 else body
            
            label = tk.Label(
                self.scrollable_frame,
                text=f"• {display_body}",
                font=("Arial", 8),
                bg="#1a1a2e",
                fg="#e0e0e0",
                anchor="w"
            )
            label.pack(fill="x", pady=1)
            self.body_labels.append(label)
        
        if len(bodies) > 6:
            more_label = tk.Label(
                self.scrollable_frame,
                text=f"... +{len(bodies) - 6} more",
                font=("Arial", 7),
                bg="#1a1a2e",
                fg="#808080",
                anchor="w"
            )
            more_label.pack(fill="x", pady=1)
            self.body_labels.append(more_label)
    
    def update_display(self):
        if not self.root:
            return
            
        try:
            new_data = self.data_callback()
            if new_data:
                self.current_data.update(new_data)
            
            data = self.current_data
            
            system_name = data['current_system']
            display_system = system_name[:15] + "..." if len(system_name) > 15 else system_name
            if self.system_label:
                self.system_label.config(text=f"📍 {display_system}")
            
            status = data['current_status']
            status_color = "#4CAF50" if status == 'visited' else "#f44336" if status == 'skipped' else "#2196F3"
            if self.status_label:
                self.status_label.config(text=status.upper(), fg=status_color)
            
            next_system = data['next_system']
            display_next = next_system[:18] + "..." if len(next_system) > 18 else next_system
            if self.next_label:
                self.next_label.config(text=f"➡️ {display_next}")
            
            if self.progress_label:
                self.progress_label.config(text=f"📊 {data['progress']}")
            
            if self.distance_label:
                dist_text = f"🧭 {data['traveled_distance']}/{data['total_distance']}"
                self.distance_label.config(text=dist_text)
            
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

_overlay_manager = ThreadSafeOverlay()

def get_overlay_manager():
    return _overlay_manager