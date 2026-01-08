import customtkinter as ctk
import json
from pathlib import Path
class EliteDangerousTheme:
    COLORS = {
        "primary_orange": "#FF7F00",
        "secondary_orange": "#CC6600",
        "dark_orange": "#994D00",
        "light_orange": "#FFAA55",
        "background_dark": "#0D0D0D",
        "panel_dark": "#1A1A1A",
        "panel_medium": "#262626",
        "text_orange": "#FF7F00",
        "text_white": "#E0E0E0",
        "text_gray": "#888888",
        "accent_blue": "#00AEFF",
        "success_green": "#4CAF50",
        "warning_red": "#FF6B6B",
        "border_orange": "#FF7F00"
    }
    @classmethod
    def apply_theme(cls):
        try:
            theme_path = Path(__file__).parent / "themes" / "elite_dangerous.json"
            if theme_path.exists():
                with open(theme_path, 'r') as f:
                    theme_data = json.load(f)
                for widget_type, properties in theme_data.items():
                    if hasattr(ctk, widget_type):
                        try:
                            widget_class = getattr(ctk, widget_type)
                            if hasattr(widget_class, '_set_appearance_mode'):
                                widget_class._set_appearance_mode("dark")
                            for prop_name, prop_value in properties.items():
                                if hasattr(widget_class, f'_set_{prop_name}'):
                                    setter = getattr(widget_class, f'_set_{prop_name}')
                                    if callable(setter):
                                        setter(prop_value)
                        except Exception as e:
                            print(f"Widget {widget_type} theme apply error: {e}")
            else:
                cls._apply_manual_theme()
        except Exception as e:
            print(f"Theme apply error: {e}")
            cls._apply_manual_theme()
    @classmethod
    def _apply_manual_theme(cls):
        ctk.set_appearance_mode("dark")
    @classmethod
    def get_button_style(cls, button_type="default"):
        styles = {
            "default": {
                "fg_color": cls.COLORS["primary_orange"],
                "hover_color": cls.COLORS["secondary_orange"],
                "text_color": cls.COLORS["background_dark"],
                "border_color": cls.COLORS["dark_orange"],
                "border_width": 1
            },
            "secondary": {
                "fg_color": cls.COLORS["panel_medium"],
                "hover_color": cls.COLORS["panel_dark"],
                "text_color": cls.COLORS["text_white"],
                "border_color": cls.COLORS["border_orange"],
                "border_width": 1
            },
            "success": {
                "fg_color": cls.COLORS["success_green"],
                "hover_color": "#45A049",
                "text_color": cls.COLORS["background_dark"],
                "border_width": 0
            },
            "warning": {
                "fg_color": cls.COLORS["warning_red"],
                "hover_color": "#CC5555",
                "text_color": cls.COLORS["text_white"],
                "border_width": 0
            }
        }
        return styles.get(button_type, styles["default"])
    @classmethod
    def get_frame_style(cls, frame_type="default"):
        styles = {
            "default": {
                "fg_color": cls.COLORS["panel_dark"],
                "border_color": cls.COLORS["border_orange"],
                "border_width": 1,
                "corner_radius": 8
            },
            "main": {
                "fg_color": cls.COLORS["background_dark"],
                "border_width": 0,
                "corner_radius": 10
            },
            "info": {
                "fg_color": cls.COLORS["panel_medium"],
                "border_color": cls.COLORS["light_orange"],
                "border_width": 1,
                "corner_radius": 6
            }
        }
        return styles.get(frame_type, styles["default"])
    @classmethod
    def get_text_style(cls, text_type="default"):
        styles = {
            "default": {
                "text_color": cls.COLORS["text_white"],
                "font": ctk.CTkFont(family="Segoe UI", size=12)
            },
            "header": {
                "text_color": cls.COLORS["text_orange"],
                "font": ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
            },
            "stats": {
                "text_color": cls.COLORS["light_orange"],
                "font": ctk.CTkFont(family="Consolas", size=11, weight="normal")
            },
            "navigation": {
                "text_color": cls.COLORS["text_white"],
                "font": ctk.CTkFont(family="Segoe UI", size=12)
            }
        }
        return styles.get(text_type, styles["default"])
def apply_elite_dangerous_theme():
    ctk.set_appearance_mode("dark")
    return EliteDangerousTheme
def load_theme_colors():
    try:
        theme_path = Path(__file__).parent / "themes" / "elite_dangerous.json"
        if theme_path.exists():
            with open(theme_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None
