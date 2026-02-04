import customtkinter as ctk
import tkinter as tk
from typing import List, Callable, Optional
from edmrn.logger import get_logger

logger = get_logger('AutocompleteEntry')


class AutocompleteEntry(ctk.CTkFrame):
    def __init__(self, master, placeholder_text=None, suggestion_provider=None, on_suggestion_callback=None, fg_color=None, **kwargs):
        self.dropdown_frame = None
        self.listbox = None
        frame_kwargs = {}
        if fg_color is not None:
            frame_kwargs['fg_color'] = fg_color
        super().__init__(master, **frame_kwargs)

        self.suggestion_provider = suggestion_provider
        self.on_suggestion_callback = on_suggestion_callback
        self.placeholder_text = placeholder_text or ""
        self.max_suggestions = 10
        self.min_chars = 3
        self.debounce_delay = 200
        self.debounce_timer = None
        self.local_suggestions = []
        self.suggestions_list = []
        self.is_dropdown_open = False
        self.selected_index = -1
        self.user_has_typed = False

        self.entry_var = tk.StringVar()
        self.entry = ctk.CTkEntry(self, textvariable=self.entry_var, placeholder_text=self.placeholder_text)
        self.entry.pack(fill="x", padx=2, pady=2)
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Down>", self._on_down_arrow)
        self.entry.bind("<Up>", self._on_up_arrow)
        self.entry.bind("<Return>", self._on_return)

    def _create_dropdown(self):
        if not self.winfo_exists():
            return
        try:
            parent = self.winfo_toplevel()
            if not str(parent):
                return
        except Exception:
            return

        if self.is_dropdown_open:
            self._hide_dropdown()
        self.dropdown_frame = None
        self.listbox = None
        self.is_dropdown_open = False
        self.selected_index = -1

        try:
            if not self.entry.winfo_exists():
                return
            self.entry.update_idletasks()
            root_x = self.entry.winfo_rootx()
            root_y = self.entry.winfo_rooty() + self.entry.winfo_height()
        except Exception:
            return

        try:
            self.dropdown_frame = tk.Toplevel(self.winfo_toplevel())
            self.dropdown_frame.wm_overrideredirect(True)
            self.dropdown_frame.wm_attributes("-topmost", True)
        except Exception:
            return

        toplevel = self.winfo_toplevel()
        toplevel.bind("<Configure>", self._on_window_move, add="+")

        try:
            colors = self.master.master.master.theme_manager.get_theme_colors()
            frame_color = colors.get('frame', '#2b2b2b')
            text_color = colors.get('text', '#ffffff')
            primary_color = colors.get('primary', '#0078d7')
        except:
            frame_color = '#2b2b2b'
            text_color = '#ffffff'
            primary_color = '#0078d7'

        if not self.winfo_exists():
            return
        frame = tk.Frame(self.dropdown_frame, bg=frame_color, relief=tk.RAISED, bd=1)
        frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame, bg=frame_color)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            frame,
            bg=frame_color,
            fg=text_color,
            selectmode=tk.SINGLE,
            font=("Segoe UI", 11),
            width=40,
            height=8,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            bd=0,
            activestyle='none',
            selectbackground=primary_color
        )
        self.listbox.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.listbox.bind("<ButtonRelease-1>", self._on_listbox_select)
        self.listbox.bind("<Return>", self._on_listbox_select)

        footer_frame = tk.Frame(self.dropdown_frame, bg=frame_color)
        footer_frame.pack(fill="x", side=tk.BOTTOM)
        footer_label = tk.Label(
            footer_frame,
            text="System data by Spansh (primary) / EDSM (fallback)",
            bg=frame_color,
            fg=text_color,
            font=("Segoe UI", 7),
            pady=3
        )
        footer_label.pack(side=tk.BOTTOM)
        self.is_dropdown_open = True
    
    def _on_window_move(self, event=None):
        if not self.is_dropdown_open or not self.dropdown_frame:
            return
        if not self.winfo_exists() or not self.entry.winfo_exists():
            return
        try:
            self.entry.update_idletasks()
            root_x = self.entry.winfo_rootx()
            root_y = self.entry.winfo_rooty() + self.entry.winfo_height()
            entry_width = self.entry.winfo_width()
            self.dropdown_frame.geometry(f"{entry_width}x200+{root_x}+{root_y}")
        except Exception:
            pass
    
    def _hide_dropdown(self):
        if not self.winfo_exists():
            return
        try:
            toplevel = self.winfo_toplevel()
            toplevel.unbind("<Configure>", self._on_window_move)
        except Exception:
            pass
        if self.dropdown_frame is not None:
            try:
                self.dropdown_frame.destroy()
            except Exception:
                pass
            self.dropdown_frame = None
            self.listbox = None
            self.is_dropdown_open = False
            self.selected_index = -1
    
    def _on_key_release(self, event):
        if event.keysym in ('Up', 'Down', 'Return'):
            return
        
        self.user_has_typed = True
        
        text = self.entry_var.get().strip()
        
        if len(text) < self.min_chars:
            self._hide_dropdown()
            if self.debounce_timer:
                self.after_cancel(self.debounce_timer)
                self.debounce_timer = None
            return
        
        if self.debounce_timer:
            self.after_cancel(self.debounce_timer)
        
        self.debounce_timer = self.after(self.debounce_delay, lambda: self._fetch_suggestions(text))
    
    def _fetch_suggestions(self, text: str):
        self.debounce_timer = None
        
        local_matches = []
        if self.local_suggestions:
            text_lower = text.lower()
            exact = [s for s in self.local_suggestions if s.lower() == text_lower]
            starts = [s for s in self.local_suggestions if s.lower().startswith(text_lower) and s not in exact]
            contains = [s for s in self.local_suggestions if text_lower in s.lower() and s not in exact and s not in starts]
            local_matches = exact + starts + contains
        
        if local_matches:
            final_suggestions = local_matches[:self.max_suggestions]
            self._update_suggestions(final_suggestions)
        elif self.suggestion_provider:
            self.suggestion_provider(text, self._update_suggestions)
        else:
            self._hide_dropdown()
    
    def _update_suggestions(self, suggestions: List[str]):
        self.suggestions_list = suggestions[:self.max_suggestions]
        
        if not self.suggestions_list:
            self._hide_dropdown()
            return
        
        if not self.is_dropdown_open:
            self._create_dropdown()
        
        if not self.is_dropdown_open or self.listbox is None:
            return
        
        try:
            self.listbox.delete(0, tk.END)
            for suggestion in self.suggestions_list:
                self.listbox.insert(tk.END, suggestion)
        except Exception:
            return
        
        self.selected_index = -1
        
        if self.dropdown_frame:
            try:
                self.entry.update_idletasks()
                root_x = self.entry.winfo_rootx()
                root_y = self.entry.winfo_rooty() + self.entry.winfo_height()
                entry_width = self.entry.winfo_width()
                self.dropdown_frame.geometry(f"{entry_width}x200+{root_x}+{root_y}")
            except Exception:
                pass
    
    def _on_focus_in(self, event):
        if not self.user_has_typed:
            return
        
        text = self.entry_var.get().strip()
        if len(text) >= self.min_chars and self.suggestions_list:
            if not self.is_dropdown_open:
                self._create_dropdown()
                self._update_suggestions(self.suggestions_list)
    
    def _on_focus_out(self, event):
        self.after(200, self._check_and_hide_dropdown)
    
    def _check_and_hide_dropdown(self):
        try:
            focused = self.focus_get()
            if focused != self.listbox:
                self._hide_dropdown()
        except:
            self._hide_dropdown()
    
    def _on_down_arrow(self, event):
        if not self.is_dropdown_open or not self.listbox:
            return
        
        self.selected_index = min(self.selected_index + 1, len(self.suggestions_list) - 1)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.selected_index)
        self.listbox.see(self.selected_index)
        return 'break'
    
    def _on_up_arrow(self, event):
        if not self.is_dropdown_open or not self.listbox:
            return
        
        self.selected_index = max(self.selected_index - 1, -1)
        self.listbox.selection_clear(0, tk.END)
        if self.selected_index >= 0:
            self.listbox.selection_set(self.selected_index)
            self.listbox.see(self.selected_index)
        return 'break'
    
    def _on_return(self, event):
        if self.is_dropdown_open and self.selected_index >= 0:
            self._select_suggestion(self.selected_index)
            return 'break'
        elif self.is_dropdown_open:
            self._hide_dropdown()
            return 'break'
        return None
    
    def _on_listbox_select(self, event):
        if self.listbox:
            selection = self.listbox.curselection()
            if selection:
                self._select_suggestion(selection[0])
                self.user_has_typed = False
                return 'break'
    
    def _select_suggestion(self, index: int):
        if 0 <= index < len(self.suggestions_list):
            selected = self.suggestions_list[index]
            self.entry_var.set(selected)
            
            self._hide_dropdown()
            
            if self.on_suggestion_callback:
                self.on_suggestion_callback(selected)
            
            self.entry.focus_set()
            self.entry.icursor(tk.END)
    
    def get(self) -> str:
        return self.entry_var.get()
    
    def set(self, value: str):
        self.entry_var.set(value)
    
    def _update_suggestions(self, suggestions: List[str]):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.suggestions_list = suggestions[:self.max_suggestions]
        if not self.suggestions_list:
            self._hide_dropdown()
            return
        if not self.is_dropdown_open:
            self._create_dropdown()
        if not self.is_dropdown_open or self.listbox is None:
            return
        try:
            self.listbox.delete(0, tk.END)
            for suggestion in self.suggestions_list:
                self.listbox.insert(tk.END, suggestion)
        except Exception:
            return
        self.selected_index = -1
        if self.dropdown_frame:
            try:
                self.entry.update_idletasks()
                root_x = self.entry.winfo_rootx()
                root_y = self.entry.winfo_rooty() + self.entry.winfo_height()
                entry_width = self.entry.winfo_width()
                self.dropdown_frame.geometry(f"{entry_width}x200+{root_x}+{root_y}")
            except Exception:
                pass
