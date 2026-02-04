import tkinter as tk
from tkinter import ttk

class TableTooltip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.text = ''
        widget.bind('<Motion>', self.on_motion)
        widget.bind('<Leave>', self.on_leave)

    def on_motion(self, event):
        rowid = self.widget.identify_row(event.y)
        colid = self.widget.identify_column(event.x)
        if not rowid or not colid:
            self.hide_tip()
            return
        columns = self.widget.cget('columns')
        if colid == '#0':
            value = self.widget.item(rowid, 'text')
        elif colid[1:] in columns:
            value = self.widget.set(rowid, colid[1:])
        else:
            self.hide_tip()
            return
        if value and len(str(value)) > 20:
            self.show_tip(str(value), event.x_root, event.y_root)
        else:
            self.hide_tip()

    def on_leave(self, event=None):
        self.hide_tip()

    def show_tip(self, text, x, y):
        if self.tipwindow and self.text == text:
            return
        self.hide_tip()
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f'+{x+10}+{y+10}')
        label = tk.Label(tw, text=text, background='#222', foreground='#FFD700', borderwidth=1, relief='solid', font=("Segoe UI", 10))
        label.pack(ipadx=2)
        self.text = text

    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
            self.text = ''

class SortableTable(ttk.Treeview):
    def __init__(self, master, columns, headings, theme_colors=None, disable_sorting=False, **kwargs):
        super().__init__(master, columns=columns, show="headings", **kwargs)
        self._columns = columns
        self.theme_colors = theme_colors or {
            'background': '#1a1a1a',
            'text': '#FFB300',  # amber
            'header': '#FFFFFF',  # header background white
            'header_fg': '#1a1a1a',  # header text black
            'selected': '#333300',
        }
        style = ttk.Style(self)
        style.theme_use('clam')
        style_name = f"EDMRN.Treeview"
        if not style.layout(style_name):
            style.layout(style_name, style.layout("Treeview"))
        style.configure(style_name,
            background=self.theme_colors['background'],
            fieldbackground=self.theme_colors['background'],
            foreground=self.theme_colors['text'],
            rowheight=26,
            font=("Segoe UI", 11),
            borderwidth=2,
            relief="groove",
            highlightthickness=2,
            highlightcolor="#888"
        )
        darker_bg = '#222222'
        style.map(style_name,
            background=[('selected', self.theme_colors['selected'])],
            foreground=[('selected', self.theme_colors['header_fg'])]
        )
        self.tag_configure('altrow', background=darker_bg)
        style.configure(f"{style_name}.Heading",
            background=self.theme_colors['header'],
            foreground=self.theme_colors['header_fg'],
            font=("Segoe UI", 11, "bold"),
            borderwidth=2,
            relief="groove",
            highlightthickness=2,
            highlightcolor="#888"
        )
        style.map(style_name,
            background=[('selected', self.theme_colors['selected'])],
            foreground=[('selected', self.theme_colors['header_fg'])]
        )
        self.configure(style=style_name)
        self['show'] = 'headings'
        for col, head in zip(columns, headings):
            if disable_sorting:
                self.heading(col, text=head, anchor="w")
            else:
                self.heading(col, text=head, anchor="w", command=lambda c=col: self._sort_by(c, False))
            self.column(col, anchor="w", width=80, minwidth=40, stretch=True)

        orig_insert = self.insert
        def altrow_insert(parent, index, iid=None, **kw):
            children = self.get_children(parent)
            row_idx = len(children) if index in ("end", tk.END) else index
            if row_idx % 2 == 1:
                tags = kw.get('tags', tuple())
                kw['tags'] = tuple(set(tags) | {'altrow'})
            return orig_insert(parent, index, iid=iid, **kw)
        self.insert = altrow_insert
        self._user_resized = False
        self.bind("<Configure>", self._auto_resize_columns)
        self.bind("<ButtonRelease-1>", self._on_user_resize)
        self._tooltip = TableTooltip(self)
        self._dragged_col = None
        self.heading_drag_bind_id = self.bind('<ButtonPress-1>', self._on_heading_press, add='+')
        self.heading_drag_motion_id = self.bind('<B1-Motion>', self._on_heading_motion, add='+')
        self.heading_drag_release_id = self.bind('<ButtonRelease-1>', self._on_heading_release, add='+')


    def _on_heading_press(self, event):
        region = self.identify_region(event.x, event.y)
        if region == 'heading':
            col = self.identify_column(event.x)
            if col and col != '#0':
                self._dragged_col = col
        else:
            self._dragged_col = None

    def _on_heading_motion(self, event):
        pass

    def _on_heading_release(self, event):
        if not self._dragged_col:
            return
        region = self.identify_region(event.x, event.y)
        if region == 'heading':
            target_col = self.identify_column(event.x)
            if target_col and target_col != '#0' and target_col != self._dragged_col:
                col_ids = list(self['columns'])
                def colid_to_key(colid):
                    if colid.startswith('#'):
                        idx = int(colid[1:]) - 1
                        if 0 <= idx < len(col_ids):
                            return col_ids[idx]
                    return colid
                from_key = colid_to_key(self._dragged_col)
                to_key = colid_to_key(target_col)
                if from_key in col_ids and to_key in col_ids:
                    from_idx = col_ids.index(from_key)
                    to_idx = col_ids.index(to_key)
                    col = col_ids.pop(from_idx)
                    col_ids.insert(to_idx, col)
                    self['columns'] = col_ids
                    if hasattr(self, 'on_column_reorder') and callable(self.on_column_reorder):
                        self.on_column_reorder(col_ids)
        self._dragged_col = None

    def _auto_resize_columns(self, event=None):
        if self._user_resized:
            return
        max_width = 300
        min_width = 40
        font = ("Segoe UI", 11)
        try:
            tkfont = tk.font.nametofont(self.cget("font"))
        except Exception:
            import tkinter.font as tkfont_mod
            tkfont = tkfont_mod.Font(family="Segoe UI", size=11)
        for col in self._columns:
            maxlen = len(str(self.heading(col)['text']))
            for item in self.get_children(''):
                val = str(self.set(item, col))
                if len(val) > maxlen:
                    maxlen = len(val)
            px = tkfont.measure('0')
            width = min(max_width, max(min_width, int(maxlen * px + 20)))
            self.column(col, width=width)

    def _on_user_resize(self, event=None):
        region = self.identify_region(event.x, event.y)
        if region == "separator":
            self._user_resized = True

    def _sort_by(self, col, descending):
        data = [(self.set(child, col), child) for child in self.get_children('')]
        try:
            data.sort(key=lambda t: float(t[0].replace(',','').replace('.','',1)) if t[0].replace(',','').replace('.','',1).isdigit() else t[0], reverse=descending)
        except Exception:
            data.sort(key=lambda t: t[0], reverse=descending)
        for idx, (val, child) in enumerate(data):
            self.move(child, '', idx)
        self.heading(col, command=lambda: self._sort_by(col, not descending))
