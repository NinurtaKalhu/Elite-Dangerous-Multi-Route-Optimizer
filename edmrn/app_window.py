import os
import logging
import ctypes
import customtkinter as ctk
from pathlib import Path
from PIL import Image, ImageTk
from edmrn.utils import resource_path
from edmrn.gui import InfoDialog

logger = logging.getLogger('AppWindow')

_hicon_cache = {}


def _load_hicon(path):
    try:
        p = str(path)
        if p in _hicon_cache:
            return _hicon_cache[p]
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        hicon = ctypes.windll.user32.LoadImageW(0, p, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
        _hicon_cache[p] = hicon
        return hicon
    except Exception:
        return None


class AppWindow:
    def __init__(self, app):
        self.app = app

    def create_root_window(self):
        self.app.root = ctk.CTk()
        self.app.root.title(f"ED Multi Route Navigation (EDMRN)")
        self.app.root.geometry("1196x730")
        self.app.root.minsize(1200, 700)
        colors = self.app.theme_manager.get_theme_colors()
        self.app.root.configure(fg_color=colors['background'])
        if self.app._borderless:
            try:
                self.app.root.overrideredirect(True)
            except Exception:
                pass
            self.setup_borderless_chrome_ui()
        self._apply_ico_icon()
        self._apply_png_icon()
        try:
            self.app.root.bind('<Map>', lambda e: self.schedule_reapply_root_icon())
            self.app.root.bind('<FocusIn>', lambda e: self.schedule_reapply_root_icon())
        except Exception:
            pass
        self.app.root.protocol("WM_DELETE_WINDOW", self.app._on_closing)

    def _apply_ico_icon(self):
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.app.root.iconbitmap(ico_path)
                except Exception as e:
                    logger.debug(f"Root: iconbitmap failed: {e}")
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = ctypes.windll.user32.LoadImageW(0, str(ico_path), 1, 0, 0, 0x00000010)
                        if hicon:
                            hwnd = self.app.root.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    except Exception as e:
                        logger.debug(f"Root: WM_SETICON failed: {e}")
        except Exception as e:
            logger.debug(f"Root: icon failed: {e}")

    def _apply_png_icon(self):
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                self.app._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.app.root.wm_iconphoto(True, self.app._title_icon)
                except Exception:
                    self.app.root.iconphoto(False, self.app._title_icon)
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon(logo_path)
                        if hicon:
                            hwnd = self.app.root.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            if not getattr(self.app, '_icon_set_logged', False):
                                logger.info("Root: WM_SETICON re-applied for PNG")
                                self.app._icon_set_logged = True
                            else:
                                logger.debug("Root: WM_SETICON re-applied for PNG (suppressed info)")
                    except Exception as e:
                        logger.debug(f"Root: WM_SETICON PNG failed: {e}")
        except Exception as e:
            logger.debug(f"Root: iconphoto failed: {e}")

    def schedule_reapply_root_icon(self):
        if getattr(self.app, '_reapply_pending', False):
            return
        self.app._reapply_pending = True
        try:
            self.app.root.after(100, lambda: self.do_reapply_root_icon())
        except Exception:
            self.do_reapply_root_icon()

    def do_reapply_root_icon(self):
        try:
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.app.root.iconbitmap(ico_path)
                except Exception:
                    pass
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon(ico_path)
                        if hicon:
                            hwnd = self.app.root.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    except Exception as e:
                        logger.debug(f"Root: WM_SETICON reapply failed: {e}")
        except Exception:
            pass
        try:
            logo_path = resource_path('../assets/explorer_icon.png')
            if Path(logo_path).exists():
                img = Image.open(logo_path).resize((32, 32), Image.LANCZOS)
                self.app._title_icon = ImageTk.PhotoImage(img)
                try:
                    self.app.root.wm_iconphoto(True, self.app._title_icon)
                except Exception:
                    self.app.root.iconphoto(False, self.app._title_icon)
                if os.name == 'nt':
                    try:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = _load_hicon(logo_path)
                        if hicon:
                            hwnd = self.app.root.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                            if not getattr(self.app, '_icon_set_logged', False):
                                logger.info("Root: WM_SETICON re-applied for PNG")
                                self.app._icon_set_logged = True
                            else:
                                logger.debug("Root: WM_SETICON re-applied for PNG (suppressed info)")
                    except Exception as e:
                        logger.debug(f"Root: WM_SETICON PNG reapply failed: {e}")
        except Exception:
            pass
        finally:
            self.app._reapply_pending = False

    def reapply_root_icon(self, event=None):
        return self.schedule_reapply_root_icon()

    def setup_borderless_chrome_ui(self):
        colors = self.app.theme_manager.get_theme_colors()
        self.app.chrome_root = ctk.CTkFrame(self.app.root, fg_color=colors['background'], corner_radius=0)
        self.app.chrome_root.pack(fill="both", expand=True)
        self.app.chrome_root.columnconfigure(0, weight=1)
        self.app.chrome_root.rowconfigure(1, weight=1)
        self.app.title_bar = ctk.CTkFrame(self.app.chrome_root, fg_color=colors['frame'], height=38,
                                          border_color=colors['primary'], border_width=2)
        self.app.title_bar.grid(row=0, column=0, sticky="ew")
        self.app.title_bar.grid_propagate(False)
        self.app.title_bar.bind('<ButtonPress-1>', self.start_move)
        self.app.title_bar.bind('<B1-Motion>', self.on_move)
        title_left = ctk.CTkFrame(self.app.title_bar, fg_color="transparent")
        title_left.pack(side="left", padx=10, pady=4)
        ctk.CTkLabel(title_left, text="ED Multi Route Navigation (EDMRN)",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=colors['text']).pack(side="left")
        controls = ctk.CTkFrame(self.app.title_bar, fg_color="transparent")
        controls.pack(side="right", padx=8, pady=4)
        self.app.btn_min = ctk.CTkButton(controls, text="--", width=28, height=26,
                                         command=self.on_minimize)
        self.app.theme_manager.apply_button_theme(self.app.btn_min, "secondary")
        self.app.btn_min.pack(side="left", padx=(0, 6))
        self.app.btn_max = ctk.CTkButton(controls, text="[]", width=28, height=26,
                                         command=self.on_maximize_toggle)
        self.app.theme_manager.apply_button_theme(self.app.btn_max, "secondary")
        self.app.btn_max.pack(side="left", padx=(0, 6))
        self.app.btn_close = ctk.CTkButton(controls, text="X", width=28, height=26,
                                           command=self.on_close_click)
        self.app.theme_manager.apply_button_theme(self.app.btn_close, "primary")
        self.app.btn_close.pack(side="left")
        self.app.chrome_body = ctk.CTkFrame(self.app.chrome_root, fg_color=colors['background'])
        self.app.chrome_body.grid(row=1, column=0, sticky="nsew")
        grip_size = 8
        self.app.resize_right = ctk.CTkFrame(self.app.root, fg_color="transparent", width=grip_size, cursor="sb_h_double_arrow")
        self.app.resize_right.place(relx=1.0, rely=0.05, anchor='ne', relheight=0.95, x=-2, y=0)
        self.app.resize_right.lower()
        self.app.resize_right.bind('<ButtonPress-1>', lambda e: self.start_resize(e, 'right'))
        self.app.resize_right.bind('<B1-Motion>', lambda e: self.do_resize(e))
        self.app.resize_bottom = ctk.CTkFrame(self.app.root, fg_color="transparent", height=grip_size, cursor="sb_v_double_arrow")
        self.app.resize_bottom.place(relx=0.0, rely=1.0, anchor='sw', relwidth=1.0, x=0, y=-2)
        self.app.resize_bottom.lower()
        self.app.resize_bottom.bind('<ButtonPress-1>', lambda e: self.start_resize(e, 'bottom'))
        self.app.resize_bottom.bind('<B1-Motion>', lambda e: self.do_resize(e))
        self.app.resize_corner = ctk.CTkFrame(self.app.root, fg_color="transparent", width=grip_size*2, height=grip_size*2, cursor="size_nw_se")
        self.app.resize_corner.place(relx=1.0, rely=1.0, anchor='se', x=-2, y=-2)
        self.app.resize_corner.lower()
        self.app.resize_corner.bind('<ButtonPress-1>', lambda e: self.start_resize(e, 'corner'))
        self.app.resize_corner.bind('<B1-Motion>', lambda e: self.do_resize(e))

    def start_move(self, event):
        try:
            self.app._drag_offset = (event.x_root - self.app.root.winfo_x(), event.y_root - self.app.root.winfo_y())
        except Exception:
            pass

    def on_move(self, event):
        try:
            x = event.x_root - self.app._drag_offset[0]
            y = event.y_root - self.app._drag_offset[1]
            self.app.root.geometry(f"{self.app.root.winfo_width()}x{self.app.root.winfo_height()}+{x}+{y}")
        except Exception:
            pass

    def on_minimize(self):
        try:
            logger.info("Minimize clicked")
            self.app._saved_min_geometry = self.app.root.winfo_geometry()
            if self.app._borderless:
                logger.info("Minimize: Disabling overrideredirect for taskbar minimize")
                self.app.root.overrideredirect(False)
                self.app.root.update_idletasks()
            logger.info("Minimize: Calling iconify")
            self.app.root.iconify()
            logger.info("Minimize: Window should now be in taskbar")
            self.check_window_restore()
        except Exception as e:
            logger.error(f"Minimize error: {e}")

    def check_window_restore(self):
        try:
            if self.app.root.winfo_viewable() and self.app.root.state() != 'iconic':
                logger.info("Window restored from taskbar")
                if self.app._borderless:
                    logger.info("Re-enabling borderless mode")
                    self.app.root.overrideredirect(True)
                    if hasattr(self.app, '_saved_min_geometry') and self.app._saved_min_geometry:
                        self.app.root.geometry(self.app._saved_min_geometry)
                        logger.info(f"Restored geometry: {self.app._saved_min_geometry}")
                    self.app.root.update_idletasks()
                    self.app.root.lift()
                    self.app.root.focus()
                    logger.info("Window lifted to front and focused")
                return
            self.app.root.after(100, self.check_window_restore)
        except Exception as e:
            logger.debug(f"Restore check error: {e}")
            return

    def on_restore_from_taskbar(self, event=None):
        try:
            logger.info("Window restored from taskbar, re-enabling borderless")
            if self.app._borderless:
                self.app.root.overrideredirect(True)
                self.app.root.update_idletasks()
                if hasattr(self.app, '_saved_min_geometry') and self.app._saved_min_geometry:
                    self.app.root.geometry(self.app._saved_min_geometry)
            self.app.root.unbind('<Map>', self.on_restore_from_taskbar)
            logger.info("Borderless mode restored")
        except Exception as e:
            logger.error(f"Restore error: {e}")

    def on_close_click(self):
        try:
            self.app._on_closing()
        except Exception:
            self.app.root.destroy()

    def on_maximize_toggle(self):
        try:
            if not self.app._is_maximized:
                self.app._saved_geometry = self.app.root.winfo_geometry()
                sw = self.app.root.winfo_screenwidth()
                sh = self.app.root.winfo_screenheight()
                self.app.root.geometry(f"{sw}x{sh}+0+0")
                self.app._is_maximized = True
                self.app.btn_max.configure(text="[]")
            else:
                if self.app._saved_geometry:
                    self.app.root.geometry(self.app._saved_geometry)
                self.app._is_maximized = False
                self.app.btn_max.configure(text="[]")
        except Exception:
            pass

    def start_resize(self, event, side):
        try:
            self.app._resize_side = side
            self.app._start_w = self.app.root.winfo_width()
            self.app._start_h = self.app.root.winfo_height()
            self.app._start_x = event.x_root
            self.app._start_y = event.y_root
        except Exception:
            pass

    def do_resize(self, event):
        try:
            dx = event.x_root - self.app._start_x
            dy = event.y_root - self.app._start_y
            new_w = self.app._start_w
            new_h = self.app._start_h
            if self.app._resize_side in ('right', 'corner'):
                new_w = max(800, self.app._start_w + dx)
            if self.app._resize_side in ('bottom', 'corner'):
                new_h = max(600, self.app._start_h + dy)
            self.app.root.geometry(f"{new_w}x{new_h}+{self.app.root.winfo_x()}+{self.app.root.winfo_y()}")
        except Exception:
            pass

    def toggle_borderless_setting(self, enabled: bool):
        try:
            self.app.config.borderless_mode = bool(enabled)
            self.app.config.save()
            InfoDialog(self.app, "Restart Required", "Please restart the app to apply borderless mode change.")
        except Exception:
            pass

    def update_chrome_border_focus(self, focused: bool):
        try:
            colors = self.app.theme_manager.get_theme_colors()
            new_color = colors['primary_hover'] if focused else colors['border']
            if hasattr(self.app, 'main_container') and self.app.main_container:
                self.app.main_container.configure(border_color=new_color)
        except Exception:
            pass
