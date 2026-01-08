import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser, messagebox, filedialog
import json
import os
from .ed_theme import EliteDangerousTheme
class ThemeEditor:
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.current_theme = self.load_current_theme()
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Theme Editor")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()
        self.setup_ui()
    def load_current_theme(self):
        theme_path = os.path.join("edmrn", "themes", "elite_dangerous.json")
        try:
            with open(theme_path, 'r') as f:
                return json.load(f)
        except:
            return self.get_default_theme()
    def get_default_theme(self):
        return {
            "CTk": {"fg_color": ["#1A1A2E", "#1A1A2E"]},
            "CTkFrame": {"fg_color": ["#16213E", "#16213E"]},
            "CTkButton": {"fg_color": ["#FF8C00", "#FF8C00"]},
            "CTkLabel": {"text_color": ["#E0E0E0", "#E0E0E0"]}
        }
    def setup_ui(self):
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        title_label = ctk.CTkLabel(main_frame, text="Theme Editor", font=("Segoe UI", 20, "bold"))
        title_label.pack(pady=(0, 20))
        canvas = tk.Canvas(main_frame, bg="#1A1A2E")
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.create_color_section(scrollable_frame, "Background Colors", [
            ("Main Background", "CTk", "fg_color"),
            ("Frame Background", "CTkFrame", "fg_color"),
        ])
        self.create_color_section(scrollable_frame, "Button Colors", [
            ("Button Color", "CTkButton", "fg_color"),
            ("Button Hover", "CTkButton", "hover_color"),
        ])
        self.create_color_section(scrollable_frame, "Text Colors", [
            ("Label Text", "CTkLabel", "text_color"),
            ("Button Text", "CTkButton", "text_color"),
        ])
        self.create_color_section(scrollable_frame, "Border Colors", [
            ("Frame Border", "CTkFrame", "border_color"),
        ])
        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=10, pady=10)
        save_btn = ctk.CTkButton(button_frame, text="Save Theme", command=self.save_theme)
        save_btn.pack(side="left", padx=5)
        reset_btn = ctk.CTkButton(button_frame, text="Reset to Default", command=self.reset_theme)
        reset_btn.pack(side="left", padx=5)
        close_btn = ctk.CTkButton(button_frame, text="Close", command=self.window.destroy)
        close_btn.pack(side="right", padx=5)
    def create_color_section(self, parent, title, colors):
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=10)
        title_label = ctk.CTkLabel(section_frame, text=title, font=("Segoe UI", 14, "bold"))
        title_label.pack(pady=10)
        for name, widget_type, property_name in colors:
            self.create_color_row(section_frame, name, widget_type, property_name)
    def create_color_row(self, parent, name, widget_type, property_name):
        row_frame = ctk.CTkFrame(parent)
        row_frame.pack(fill="x", padx=10, pady=5)
        label = ctk.CTkLabel(row_frame, text=name, width=150)
        label.pack(side="left", padx=10)
        current_color = self.get_color_value(widget_type, property_name)
        color_display = ctk.CTkLabel(row_frame, text="", width=50, height=30,
                                   fg_color=current_color, corner_radius=5)
        color_display.pack(side="left", padx=5)
        pick_btn = ctk.CTkButton(row_frame, text="Pick Color", width=100,
                               command=lambda: self.pick_color(widget_type, property_name, color_display))
        pick_btn.pack(side="left", padx=5)
        color_entry = ctk.CTkEntry(row_frame, width=100)
        color_entry.insert(0, current_color)
        color_entry.pack(side="left", padx=5)
        color_entry.bind("<Return>", lambda e: self.update_color_from_entry(widget_type, property_name, color_entry, color_display))
    def get_color_value(self, widget_type, property_name):
        try:
            color_value = self.current_theme[widget_type][property_name]
            if isinstance(color_value, list):
                return color_value[0]
            return color_value
        except:
            return "#E0E0E0"
    def pick_color(self, widget_type, property_name, color_display):
        current_color = self.get_color_value(widget_type, property_name)
        color = colorchooser.askcolor(color=current_color, title="Pick Color")
        if color[1]:
            hex_color = color[1].upper()
            self.update_theme_color(widget_type, property_name, hex_color)
            color_display.configure(fg_color=hex_color)
    def update_color_from_entry(self, widget_type, property_name, entry, color_display):
        hex_color = entry.get().strip()
        if hex_color.startswith('#'):
            try:
                int(hex_color[1:], 16)
                self.update_theme_color(widget_type, property_name, hex_color.upper())
                color_display.configure(fg_color=hex_color)
            except ValueError:
                messagebox.showerror("Invalid Color", "Please enter a valid hex color (e.g., #FF8C00)")
        else:
            messagebox.showerror("Invalid Format", "Color must be in hex format (e.g., #FF8C00)")
    def update_theme_color(self, widget_type, property_name, hex_color):
        if widget_type not in self.current_theme:
            self.current_theme[widget_type] = {}
        self.current_theme[widget_type][property_name] = [hex_color, hex_color]
    def save_theme(self):
        theme_path = os.path.join("edmrn", "themes", "elite_dangerous.json")
        try:
            with open(theme_path, 'w') as f:
                json.dump(self.current_theme, f, indent=2)
            messagebox.showinfo("Success", "Theme saved successfully!\nRestart the application to see all changes.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save theme: {str(e)}")
    def reset_theme(self):
        if messagebox.askyesno("Reset Theme", "Are you sure you want to reset to default theme?"):
            self.current_theme = self.get_default_theme()
            self.window.destroy()
            ThemeEditor(self.parent, None)
