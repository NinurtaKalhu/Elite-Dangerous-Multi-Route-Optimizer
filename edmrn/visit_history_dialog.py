import customtkinter as ctk
from tkinter import ttk

class VisitedSystemsDialog(ctk.CTkToplevel):
    
    def __init__(self, parent, visited_systems):
        super().__init__(parent)
        
        self.result = None
        self.selected_systems = set()
        
        self.title("Previously Visited Systems")
        self.geometry("550x400")
        self.resizable(False, False)
        
        try:
            from edmrn.utils import resource_path
            from pathlib import Path
            import ctypes
            import os
            from PIL import Image
            from edmrn.logger import get_logger
            logger = get_logger('VisitHistoryDialog')
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.iconbitmap(ico_path)
                except Exception as e:
                    logger.error(f"VisitedSystemsDialog: iconbitmap failed: {e}")
                if os.name == 'nt':
                    try:
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = ctypes.windll.user32.LoadImageW(0, str(ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    except Exception as e:
                        logger.error(f"VisitedSystemsDialog: WM_SETICON failed: {e}")
        except Exception as e:
            logger.error(f"VisitedSystemsDialog: Exception in icon set: {e}")
        
        self.transient(parent)
        self.grab_set()
        
        try:
            self.bind('<Map>', lambda e: self._schedule_reapply_icons())
            self.bind('<FocusIn>', lambda e: self._schedule_reapply_icons())
        except Exception:
            pass
        
        header_label = ctk.CTkLabel(
            self,
            text=f"Found {len(visited_systems)} Previously Visited Systems",
            font=("Segoe UI", 14, "bold"),
        )
        header_label.pack(pady=(15, 5))
        
        info_label = ctk.CTkLabel(
            self,
            text="These systems are already in your visit history. What would you like to do?",
            font=("Segoe UI", 11),
            text_color="#888888"
        )
        info_label.pack(pady=(0, 10))
        
        list_frame = ctk.CTkFrame(self, fg_color="#2A2A2A", corner_radius=8)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        scroll_frame = ctk.CTkScrollableFrame(
            list_frame,
            width=490,
            height=220,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.checkboxes = {}
        for i, system_info in enumerate(visited_systems):
            system_name = system_info['name']
            last_visit = system_info.get('last_visit', 'Unknown')
            visit_count = system_info.get('visit_count', 1)
            
            checkbox_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            checkbox_frame.pack(fill="x", pady=2)
            
            var = ctk.BooleanVar(value=True)
            checkbox = ctk.CTkCheckBox(
                checkbox_frame,
                text="",
                variable=var,
                width=20,
                checkbox_width=18,
                checkbox_height=18,
                font=("Segoe UI", 11)
            )
            checkbox.pack(side="left", padx=(0, 8))
            
            label_text = f"{system_name}"
            if visit_count > 1:
                label_text += f" (visited {visit_count} times)"
            
            system_label = ctk.CTkLabel(
                checkbox_frame,
                text=label_text,
                font=("Segoe UI", 11),
                anchor="w"
            )
            system_label.pack(side="left", fill="x", expand=True)
            
            date_label = ctk.CTkLabel(
                checkbox_frame,
                text=f"Last: {last_visit}",
                font=("Segoe UI", 9),
                text_color="#888888",
                anchor="e"
            )
            date_label.pack(side="right", padx=(10, 0))
            
            self.checkboxes[system_name] = var
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 15), padx=20, fill="x")
        
        remove_btn = ctk.CTkButton(
            button_frame,
            text="Remove Selected",
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            font=("Segoe UI", 12, "bold"),
            height=28,
            command=self.remove_selected
        )
        remove_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        
        keep_btn = ctk.CTkButton(
            button_frame,
            text="Keep All",
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=("Segoe UI", 12, "bold"),
            height=28,
            command=self.keep_all
        )
        keep_btn.pack(side="left", expand=True, fill="x", padx=4)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#666666",
            hover_color="#555555",
            font=("Segoe UI", 12, "bold"),
            height=28,
            command=self.cancel
        )
        cancel_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))
        
        button_frame.lift()
        remove_btn.lift()
        keep_btn.lift()
        cancel_btn.lift()
        
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        self.bind("<Escape>", lambda e: self.cancel())
    
    def remove_selected(self):
        self.selected_systems = {
            name for name, var in self.checkboxes.items() if var.get()
        }
        self.result = 'remove_selected'
        self.grab_release()
        self.destroy()
    
    def keep_all(self):
        self.result = 'keep_all'
        self.selected_systems = set()
        self.grab_release()
        self.destroy()
    
    def cancel(self):
        self.result = 'cancel'
        self.selected_systems = set()
        self.grab_release()
        self.destroy()
    
    def get_result(self):
        self.wait_window()
        return self.result, self.selected_systems
    
    def _schedule_reapply_icons(self):
        if getattr(self, '_reapply_pending', False):
            return
        self._reapply_pending = True
        try:
            self.after(100, lambda: self._do_reapply_icons())
        except Exception:
            self._do_reapply_icons()
    
    def _do_reapply_icons(self):
        from edmrn.logger import get_logger
        logger = get_logger('VisitHistoryDialog')
        try:
            from edmrn.utils import resource_path
            from pathlib import Path
            import ctypes
            import os
            ico_path = resource_path('../assets/explorer_icon.ico')
            if Path(ico_path).exists():
                try:
                    self.iconbitmap(ico_path)
                except Exception as e:
                    logger.error(f"VisitedSystemsDialog: (reapply) iconbitmap failed: {e}")
                if os.name == 'nt':
                    try:
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        hicon = ctypes.windll.user32.LoadImageW(0, str(ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
                        if hicon:
                            hwnd = self.winfo_id()
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    except Exception as e:
                        logger.error(f"VisitedSystemsDialog: (reapply) WM_SETICON failed: {e}")
        except Exception as e:
            logger.error(f"VisitedSystemsDialog: (reapply) Exception in icon set: {e}")
        finally:
            self._reapply_pending = False
