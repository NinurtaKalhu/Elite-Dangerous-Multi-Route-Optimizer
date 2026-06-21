import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
import os
import random


class SplashScreen(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("EDMRN - Loading")
        self.geometry("500x400")
        self.resizable(False, False)
        
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        self.attributes('-topmost', True)
        self.configure(fg_color="#0d0d14")
        
        # Canvas
        self.canvas = ctk.CTkCanvas(self, width=500, height=400, bg="#0d0d14", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Background gradient
        self._draw_gradient()
        
        # Stars (will be animated)
        self.stars = []
        for _ in range(80):
            self.stars.append({
                'x': random.randint(0, 500),
                'y': random.randint(0, 400),
                'speed': random.uniform(0.2, 1.0),
                'brightness': random.randint(150, 255)
            })
        
        # Logo (centered, 100x100)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "edmrn_logo.png")
            img = Image.open(logo_path).resize((100, 100), Image.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
            self.canvas.create_image(250, 160, image=self.logo_image, tags='logo')
        except Exception:
            self.canvas.create_text(250, 160, text="EDMRN", fill='#ff8c00', font=("Segoe UI", 28, "bold"), tags='logo')
        
        # Thin line (gradient effect)
        self._draw_gradient_line(220, 235, 280, 235)
        
        # Tagline
        self.canvas.create_text(250, 255, text="Elite Dangerous Multi Route Navigation", fill='#555555', font=("Arial", 10), anchor="center", tags='text')
        
        # Status
        self.canvas.create_text(250, 330, text="Welcome home, Commander. EDMRN routing services are at your disposal", fill='#ff8c00', font=("Arial", 8), anchor="center", tags='text')
        
        # Progress bar
        self.canvas.create_rectangle(175, 348, 325, 350, fill="#1a1a1a", outline="", tags='text')
        self.progress_bar = self.canvas.create_rectangle(175, 348, 250, 350, fill="#ff8c00", outline="", tags='text')
        
        # Version (gray)
        self.canvas.create_text(250, 370, text="v3.3.0 | CMDR Ninurta KALHU", fill='#9c9c9c', font=("Arial", 7), anchor="center", tags='text')
        
        self.running = True
        self.time = 0
        self._animate()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _draw_gradient(self):
        for y in range(400):
            r = int(13 - y * 0.0075)
            g = int(13 - y * 0.0075)
            b = int(20 - y * 0.0125)
            color = f'#{max(r,10):02x}{max(g,10):02x}{max(b,10):02x}'
            self.canvas.create_line(0, y, 500, y, fill=color, tags='bg')
    
    def _draw_gradient_line(self, x1, y1, x2, y2):
        steps = x2 - x1
        for i in range(steps):
            x = x1 + i
            alpha = abs(i - steps/2) / (steps/2)
            r = int(255 * (1 - alpha))
            g = int(140 * (1 - alpha))
            b = 0
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(x, y1, x+1, y2, fill=color)
    
    def _on_close(self):
        self.running = False
        self.destroy()
    
    def _animate(self):
        if not self.running:
            return
        
        try:
            # Delete only stars, keep everything else
            self.canvas.delete('star')
            
            # Draw stars
            for star in self.stars:
                star['x'] -= star['speed']
                if star['x'] < -1:
                    star['x'] = 501
                    star['y'] = random.randint(0, 400)
                
                brightness = star['brightness']
                color = f'#{brightness:02x}{brightness:02x}{brightness:02x}'
                self.canvas.create_rectangle(star['x'], star['y'], star['x'], star['y'], fill=color, outline='', tags='star')
            
            # Bring logo and UI elements to front
            self.canvas.tag_raise('logo')
            self.canvas.tag_raise('line')
            self.canvas.tag_raise('text')
            
            # Update progress
            progress = (self.time % 30) / 30
            self.canvas.coords(self.progress_bar, 175, 348, 175 + progress * 150, 350)
            self.time += 0.02
        except Exception:
            pass
        
        self.after(33, self._animate)
    
    def update_progress(self, value):
        try:
            self.canvas.coords(self.progress_bar, 175, 348, 175 + value * 150, 350)
        except Exception:
            pass
    
    def set_status(self, message):
        pass
