import customtkinter as ctk
import json
from pathlib import Path
from tkinter import messagebox
from edmrn.logger import get_logger
from edmrn.gui import ErrorDialog
logger = get_logger('ThemeManager')
class ThemeManager:
    def __init__(self, app):
        self.app = app
    def _load_theme_from_json(self, theme_name):
        try:
            theme_path = Path(__file__).parent / "themes" / f"{theme_name}.json"
            if theme_path.exists():
                with open(theme_path, 'r') as f:
                    theme_data = json.load(f)
                    
                button_data = theme_data.get('CTkButton', {})
                frame_data = theme_data.get('CTkFrame', {})
                toplevel_data = theme_data.get('CTkToplevel', {})
                
                fg_color = button_data.get('fg_color', ['#FF8C00', '#FF8C00'])
                hover_color = button_data.get('hover_color', ['#FFA500', '#FFA500'])
                secondary = frame_data.get('fg_color', ['#2E2E2E', '#2E2E2E'])
                background = toplevel_data.get('fg_color', ['#212121', '#212121'])
                border = frame_data.get('border_color', ['#424242', '#424242'])
                
                return {
                    'primary': fg_color[0] if isinstance(fg_color, list) else fg_color,
                    'primary_hover': hover_color[0] if isinstance(hover_color, list) else hover_color,
                    'secondary': secondary[0] if isinstance(secondary, list) else secondary,
                    'secondary_hover': secondary[1] if isinstance(secondary, list) else secondary,
                    'background': background[0] if isinstance(background, list) else background,
                    'frame': secondary[0] if isinstance(secondary, list) else secondary,
                    'border': border[0] if isinstance(border, list) else border,
                    'text': '#E0E0E0',
                    'accent': fg_color[0] if isinstance(fg_color, list) else fg_color,
                    'success': '#4CAF50',
                    'success_hover': '#45A049'
                }
        except Exception as e:
            logger.error(f"Failed to load theme {theme_name}: {e}")
        
        return None
    
    def get_theme_colors(self):
        theme_colors = self._load_theme_from_json(self.app.current_theme)
        
        if theme_colors:
            return theme_colors
        
        return {
            'primary': '#FF8C00',
            'primary_hover': '#FFA500',
            'secondary': '#2E2E2E',
            'secondary_hover': '#3E3E3E',
            'background': '#212121',
            'frame': '#2E2E2E',
            'border': '#424242',
            'text': '#E0E0E0',
            'accent': '#FF8C00',
            'success': '#4CAF50',
            'success_hover': '#45A049'
        }
    def apply_button_theme(self, button, button_type="primary"):
        colors = self.get_theme_colors()
        if button_type == "secondary":
            button.configure(
                fg_color=colors['secondary'],
                hover_color=colors['secondary_hover'],
                text_color=colors['text'],
                border_color=colors['border'],
                border_width=1
            )
        elif button_type == "success":
            button.configure(
                fg_color=colors['primary'],
                hover_color=colors['primary_hover'],
                text_color="white",
                border_width=0
            )
        else:
            button.configure(
                fg_color=colors['primary'],
                hover_color=colors['primary_hover'],
                text_color="white",
                border_color=colors['border'],
                border_width=1
            )
    def apply_frame_theme(self, frame):
        colors = self.get_theme_colors()
        frame.configure(
            fg_color=colors['frame'],
            border_color=colors['border']
        )
    def change_theme(self, theme_name):
        try:
            theme_mapping = {
                "Elite Dangerous": "elite_dangerous",
                "Aisling Duval": "aisling_duval",
                "Archon Delaine": "archon_delaine",
                "Arissa Lavigny Duval": "arissa_lavigny_duval",
                "Denton Patreus": "denton_patreus",
                "Edmund Mahon": "edmund_mahon",
                "Felicia Winters": "felicia_winters",
                "Li Yong Rui": "li_yong_rui",
                "Pranav Antal": "pranav_antal",
                "Zachary Hudson": "zachary_hudson",
                "Zemina Torval": "zemina_torval"
            }
            file_theme_name = theme_mapping.get(theme_name, "elite_dangerous")
            self.app.current_theme = file_theme_name
            self.app.config.current_theme = file_theme_name
            self.app.config.save()
            logger.info(f"Theme changed to: {theme_name} (file: {file_theme_name})")
            return file_theme_name
        except Exception as e:
            logger.error(f"Theme change error: {e}")
            ErrorDialog(self.app, "Error", f"Failed to change theme: {e}")
            return "elite_dangerous"
