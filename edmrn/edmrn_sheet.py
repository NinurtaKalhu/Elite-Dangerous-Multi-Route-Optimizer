import tkinter as tk
from tksheet import Sheet

class EDMRNSheet(Sheet):
    def auto_resize_columns(self, min_width=60, max_width=400, padding=16):
        headers = self.headers() if callable(self.headers) else self.headers
        widths = []
        for col_index in range(self.total_columns()):
            header = str(headers[col_index]) if headers and col_index < len(headers) else ""
            max_len = len(header)
            for row_index in range(self.total_rows()):
                cell = str(self.get_cell_data(row_index, col_index))
                if len(cell) > max_len:
                    max_len = len(cell)
            width = min(max_width, max(min_width, max_len * 7 + padding))
            widths.append(width)
        self.set_column_widths(widths)
    def __init__(self, master, data, headers, theme_colors=None, *args, **kwargs):
        super().__init__(master, data=data, headers=headers, *args, **kwargs)
        self.theme_colors = theme_colors or {
            'background': '#1a1a1a',
            'text': '#FFB300',
            'header': '#FFFFFF',
            'header_fg': '#1a1a1a',
            'selected': '#333300',
            'grid': '#444444',
            'border': '#888888',
            'font': ('Segoe UI', 11, 'normal'),
        }
        self.set_options(
            table_bg=self.theme_colors['background'],
            table_fg=self.theme_colors['text'],
            header_bg=self.theme_colors['header'],
            header_fg=self.theme_colors['header_fg'],
            header_border_fg=self.theme_colors.get('border', '#888'),
            header_grid_fg=self.theme_colors.get('grid', '#444'),
            table_grid_fg=self.theme_colors.get('grid', '#444'),
            table_selected_cells_bg=self.theme_colors['selected'],
            table_selected_cells_fg=self.theme_colors['header_fg'],
            frame_bg=self.theme_colors['background'],
            top_left_bg=self.theme_colors['background'],
            top_left_fg=self.theme_colors['header_fg'],
            index_bg=self.theme_colors['background'],
            index_fg=self.theme_colors['text'],
            font=self.theme_colors.get('font', ('Segoe UI', 11, 'normal')),
            outline_thickness=2,
        )
        self.enable_bindings((
            "single_select",
            "row_select",
            "column_select",
            "drag_select",
            "column_drag_and_drop",
            "row_drag_and_drop",
            "column_width_resize",
            "double_click_column_resize",
            "row_width_resize",
            "arrowkeys",
            "right_click_popup_menu",
            "rc_select",
            "copy",
            "cut",
            "paste",
            "delete",
            "undo",
            "edit_cell"
        ))
        self.grid(row=0, column=0, sticky="nsew")
