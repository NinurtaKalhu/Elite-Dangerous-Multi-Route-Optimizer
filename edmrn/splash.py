import customtkinter as ctk
from PIL import Image
import os
import threading
import time
import random
import tkinter as tk


class SplashScreen(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("EDMRN - Loading")
        self.geometry("500x480")
        self.resizable(False, False)
        
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        self.attributes('-topmost', True)
        
        main_frame = ctk.CTkFrame(self, fg_color="#1A1A1A")
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Star field canvas (background layer) - use tkinter Canvas
        self.star_canvas = tk.Canvas(
            main_frame,
            width=500,
            height=480,
            bg="#1A1A1A",
            highlightthickness=0,
            borderwidth=0
        )
        self.star_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="Welcome Commander!",
            font=("Segoe UI", 20, "bold"),
            text_color="#FF8000",
            fg_color="transparent"
        )
        title_label.place(x=250, y=30, anchor="n")
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="From Sol's Dawn to Beagle's Edge – EDMRN Forges the Path.",
            font=("Arial", 11, "italic"),
            text_color="#CCCCCC",
            fg_color="transparent"
        )
        subtitle_label.place(x=250, y=70, anchor="n")
        
        logo_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a")
        logo_frame.place(x=250, y=110, anchor="n")
        
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "edmrn_logo.png")
            logo_image = ctk.CTkImage(light_image=Image.open(logo_path), size=(180, 180))
            logo_label = ctk.CTkLabel(logo_frame, image=logo_image, text="", fg_color="#1a1a1a")
            logo_label.image = logo_image
            logo_label.pack(padx=20, pady=10)
        except Exception:
            placeholder = ctk.CTkLabel(
                logo_frame,
                text="[EDMRN Logo]",
                font=("Arial", 14),
                text_color="#FF7F00",
                fg_color="#1a1a1a"
            )
            placeholder.pack(padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Systems online...",
            font=("Arial", 10),
            text_color="#FF7F00",
            fg_color="transparent"
        )
        self.status_label.place(x=250, y=340, anchor="n")
        
        self.progress = ctk.CTkProgressBar(main_frame, width=400, height=6, progress_color="#FF7F00")
        self.progress.place(x=250, y=370, anchor="n")
        self.progress.set(0)
        
        version_label = ctk.CTkLabel(
            main_frame,
            text="v2.3.0 | CMDR Ninurta KALHU © 2024 EDMRN",
            font=("Arial", 9),
            text_color="#666666",
            fg_color="transparent"
        )
        version_label.place(x=250, y=420, anchor="n")
        
        self.transient(master)
        self.grab_set()
        
        # Initialize stars for animation
        self.stars = []
        for _ in range(100):
            self.stars.append({
                'x': random.randint(0, 500),
                'y': random.randint(0, 480),
                'speed': random.uniform(0.5, 2.0),
                'size': random.choice([1, 1, 2, 2, 3]),
                'brightness': random.choice(['#FFFFFF', '#FFDD88', "#CECECE", "#D9D9FF", '#CCCCCC'])
            })
        
        self.transient(master)
        self.grab_set()
        
        self.running = True
        self.t = 0
        self.status_idx = 0
        self.status_messages = [
            "Powering up flight systems...",
            "Linking to EDSM...",
            "Linking to Spansh...",
            "Computing optimal jumps...",
            "Calibrating nav computer...",
            "Charging Frame Shift Drive...",
            "Clear for departure."
        ]
        
        # Start animation loop using after() instead of thread
        self._animate_all()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _on_close(self):
        self.running = False
        self.destroy()
    
    def _animate_all(self):
        """Animate stars and progress bar - called repeatedly via after()"""
        if not self.running:
            return
        
        try:
            # Clear and redraw stars
            self.star_canvas.delete("all")
            
            for star in self.stars:
                # Draw star
                if star['size'] <= 1:
                    self.star_canvas.create_rectangle(
                        star['x'], star['y'], 
                        star['x']+1, star['y']+1,
                        fill=star['brightness'], outline=""
                    )
                else:
                    self.star_canvas.create_oval(
                        star['x']-star['size'], star['y']-star['size'],
                        star['x']+star['size'], star['y']+star['size'],
                        fill=star['brightness'], outline=""
                    )
                
                # Move star to the right (hyperspace effect)
                star['x'] += star['speed']
                
                # Wrap around
                if star['x'] > 500:
                    star['x'] = -5
                    star['y'] = random.randint(0, 480)
                    star['brightness'] = random.choice(['#FFFFFF', '#FFDD88', "#CECECE", "#D9D9FF", '#CCCCCC'])
            
            # Update status message
            msg_idx = int(self.t * 3) % len(self.status_messages)
            if msg_idx != self.status_idx:
                self.status_idx = msg_idx
                self.status_label.configure(text=self.status_messages[self.status_idx])
            
            # Update progress bar
            progress_val = (self.t % 3.0) / 3.0
            self.progress.set(progress_val)
            
            self.t += 0.04
            
        except Exception:
            pass
        
        # Schedule next frame
        self.after(16, self._animate_all)
    
    def update_progress(self, value):
        try:
            self.progress.set(value)
        except Exception:
            pass
    
    def set_status(self, message):
        try:
            self.status_label.configure(text=message)
        except Exception:
            pass
