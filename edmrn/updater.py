import requests
import threading
import time
import webbrowser
from packaging import version as pkg_version
import customtkinter as ctk
from edmrn.logger import get_logger
from edmrn.gui import InfoDialog
logger = get_logger('Updater')
class SimpleUpdateChecker:
    def __init__(self, current_version):
        self.current_version = current_version
        self.github_repo = "NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer"
        self.latest_release_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        self.update_available = False
        self.latest_version = None
        self.release_url = None
    def check_for_updates(self):
        try:
            logger.info("Checking for updates from GitHub...")
            response = requests.get(
                self.latest_release_url,
                headers={'Accept': 'application/vnd.github.v3+json'},
                timeout=10
            )
            if response.status_code == 200:
                release_data = response.json()
                latest_tag = release_data.get('tag_name', '').lstrip('vV')
                self.latest_version = latest_tag
                self.release_url = release_data.get('html_url', '')
                try:
                    current_ver = pkg_version.parse(self.current_version)
                    latest_ver = pkg_version.parse(latest_tag)
                    self.update_available = latest_ver > current_ver
                    logger.info(f"Current: {self.current_version}, Latest: {latest_tag}, Update: {self.update_available}")
                except Exception as e:
                    logger.error(f"Version comparison error: {e}")
                    self.update_available = False
            else:
                logger.warning(f"GitHub API error: {response.status_code}")
                self.update_available = False
        except requests.exceptions.Timeout:
            logger.warning("GitHub API timeout")
            self.update_available = False
        except requests.exceptions.ConnectionError:
            logger.warning("GitHub API connection error")
            self.update_available = False
        except Exception as e:
            logger.error(f"Update check error: {e}")
            self.update_available = False
        return self.update_available
    def show_update_dialog(self, parent_window):
        if not self.update_available or not self.latest_version:
            return
        dialog = ctk.CTkToplevel(parent_window)
        dialog.title("EDMRN - New Version Available")
        dialog.resizable(False, False)
        dialog.transient(parent_window)
        dialog.grab_set()
        
        try:
            from edmrn.utils import resource_path
            from pathlib import Path
            import ctypes
            import os
            from edmrn.logger import get_logger
            logger = get_logger('UpdaterDialog')
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    dialog.iconbitmap(ico_path)
                except Exception as e:
                    logger.error(f"UpdateDialog: iconbitmap failed: {e}")
                if os.name == 'nt':
                    try:
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = ctypes.windll.user32.LoadImageW(0, str(ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                        if hicon:
                            hwnd = dialog.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    except Exception as e:
                        logger.error(f"UpdateDialog: WM_SETICON failed: {e}")
        except Exception as e:
            logger.error(f"UpdateDialog: Exception in icon set: {e}")
        ctk.CTkLabel(
            dialog,
            text="🎉 New Version Available!",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#4CAF50"
        ).pack(pady=(20, 10))
        version_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        version_frame.pack(pady=10)
        ctk.CTkLabel(
            version_frame,
            text=f"Current: v{self.current_version}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#888888"
        ).pack()
        ctk.CTkLabel(
            version_frame,
            text=f"New: v{self.latest_version}",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#4CAF50"
        ).pack(pady=(5, 0))
        message_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        message_frame.pack(pady=20, padx=20)
        ctk.CTkLabel(
            message_frame,
            text="Download the new version from GitHub.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#E0E0E0",
            wraplength=350
        ).pack()
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=(10, 20), padx=20, fill="x")
        
        github_btn = ctk.CTkButton(
            button_frame,
            text="🐙 Download from GitHub",
            command=lambda: [webbrowser.open(self.release_url), dialog.destroy()],
            fg_color="#4CAF50",
            hover_color="#45A049",
            text_color="white",
            height=40,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        github_btn.pack(side="left", padx=(0, 10), fill="x", expand=True, pady=5)
        
        colors = getattr(parent_window, 'theme_manager', None)
        if colors and hasattr(colors, 'get_theme_colors'):
            theme_colors = colors.get_theme_colors()
        else:
            theme_colors = {
                'frame': '#2B2B2B',
                'primary': '#4CAF50',
                'secondary': '#666666',
                'text': '#E0E0E0'
            }
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=dialog.destroy,
            fg_color=theme_colors['secondary'],
            hover_color=theme_colors.get('secondary_hover', '#555555'),
            text_color=theme_colors['text'],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=40
        )
        close_btn.pack(side="right", fill="x", expand=True, pady=5)
        
        button_frame.lift()
        github_btn.lift()
        close_btn.lift()
        
        dialog.update_idletasks()
        width = dialog.winfo_reqwidth()
        height = dialog.winfo_reqheight()
        try:
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (width // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass
        
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        try:
            dialog.bind('<Map>', lambda e: _reapply_update_icons(dialog))
            dialog.bind('<FocusIn>', lambda e: _reapply_update_icons(dialog))
        except Exception:
            pass

def _reapply_update_icons(dialog):
    try:
        from edmrn.utils import resource_path
        from pathlib import Path
        import ctypes
        import os
        
        ico_path = resource_path('../assets/explorer_icon.ico')
        if Path(ico_path).exists():
            try:
                dialog.iconbitmap(ico_path)
            except Exception:
                pass
            if os.name == 'nt':
                try:
                    IMAGE_ICON = 1
                    LR_LOADFROMFILE = 0x00000010
                    WM_SETICON = 0x0080
                    ICON_SMALL = 0
                    ICON_BIG = 1
                    hicon = ctypes.windll.user32.LoadImageW(0, str(ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                    if hicon:
                        hwnd = dialog.winfo_id()
                        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                except Exception:
                    pass
    except Exception:
        pass

class UpdateManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.update_checker = None
        self._setup_update_checker()
    def _setup_update_checker(self):
        try:
            from edmrn import __version__
            current_version = __version__
            self.update_checker = SimpleUpdateChecker(current_version)
        except Exception as e:
            logger.error(f"Update checker setup error: {e}")
            self.update_checker = None
    def start_auto_check(self, delay_seconds=5):
        if not self.update_checker:
            return
        def check_thread_func():
            time.sleep(delay_seconds)
            try:
                update_available = self.update_checker.check_for_updates()
                if update_available:
                    self.app.root.after(0, lambda: self.update_checker.show_update_dialog(self.app.root))
            except Exception as e:
                logger.error(f"Auto update check error: {e}")
        threading.Thread(target=check_thread_func, daemon=True).start()
    def manual_check(self):
        if not self.update_checker:
            return
        try:
            update_available = self.update_checker.check_for_updates()
            if update_available:
                self.update_checker.show_update_dialog(self.app.root)
            else:
                import tkinter as tk
                from tkinter import messagebox
                InfoDialog(self.app, 
                    "Update Check",
                    f"✅ EDMRN is already up to date!\n\n"
                    f"Current Version: v{self.update_checker.current_version}\n"
                    f"Latest Version: v{self.update_checker.latest_version or 'Unknown'}"
                )
        except Exception as e:
            logger.error(f"Update check error: {e}")
def setup_auto_updates(app_instance, delay_seconds=5):
    update_manager = UpdateManager(app_instance)
    update_manager.start_auto_check(delay_seconds)
    return update_manager
