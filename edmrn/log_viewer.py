import logging
import datetime
import re
import threading
import customtkinter as ctk
import tkinter as tk
from edmrn.column_display_names import COLUMN_DISPLAY_NAMES
from edmrn.edmrn_sheet import EDMRNSheet
from edmrn.ed_theme import EliteDangerousTheme
from edmrn.codex_translation import codex_translation

logger = logging.getLogger('LogViewer')

RECOMMENDED_KEYS = [
    'Timestamp', 'StarSystem', 'Body', 'BodyName', 'PlanetClass', 'Landable',
    'DistanceFromArrivalLS', 'SurfaceGravity', 'SurfaceTemperature', 'Atmosphere',
    'AtmosphereType', 'Volcanism', 'TerraformState', 'Signals', 'Discovery',
    'Composition', 'Ring', 'Radius', 'OrbitalPeriod', 'SemiMajorAxis', 'Eccentricity',
    'Inclination', 'Periapsis', 'AxialTilt', 'MassEM', 'ReserveLevel', 'TidalLock',
    'Luminosity', 'Age_MY', 'StellarMass', 'AbsoluteMagnitude', 'RotationPeriod',
    'Rings', 'ScanType', 'Species', 'Genus', 'Variant', 'Sample', 'SampleType',
    'SampleCount', 'BioType', 'BioSignal', 'BioLocation', 'BioDistance', 'BioName',
    'BioGenus', 'BioVariant'
]

TECHNICAL_KEYS = {
    'from_r', 'from_c', 'upto_r', 'upto_c', 'type_', 'name', 'kwargs', 'table',
    'index', 'header', 'tdisp', 'idisp', 'hdisp', 'transposed', 'ndim', 'convert',
    'undo', 'emit_event', 'widget'
}


class LogViewer:
    def __init__(self, section):
        self.section = section
        self._log_data = []
        self._table_rows_backup = None
        self._log_filter_after_id = None
        self._log_update_in_progress = False
        self._pending_log_update = None

    def parse_ts(self, row):
        v = row.get('Timestamp')
        if not v:
            return datetime.datetime.min
        try:
            v = v.replace(' ', 'T')
            if v.endswith('Z'):
                v = v[:-1] + '+00:00'
            dt = datetime.datetime.fromisoformat(v)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            else:
                dt = dt.astimezone(datetime.timezone.utc)
            return dt
        except Exception:
            return datetime.datetime.min

    def format_ring(self, ring):
        if isinstance(ring, dict):
            name = ring.get('Name', '-')
            if isinstance(name, str) and ' Belt' in name:
                parts = name.split(' ')
                belt_index = [i for i, p in enumerate(parts) if p == 'Belt']
                if belt_index:
                    idx = belt_index[0]
                    if idx > 0:
                        name = f"{parts[idx-1]} Belt"
                    else:
                        name = 'Belt'
            ringclass_raw = ring.get('RingClass', '-')
            ringclass = ringclass_raw.replace('eRingClass_', '') if isinstance(ringclass_raw, str) else ringclass_raw
            ringclass = ringclass.capitalize() if isinstance(ringclass, str) else ringclass
            mass = ring.get('MassMT', None)
            mass_str = f"{mass/1e6:.1f} Mt" if isinstance(mass, (int, float)) else "-"
            return f"{name} ({ringclass}), Mass: {mass_str}"
        return str(ring)

    def format_number(self, col, val):
        col_l = col.lower()
        try:
            if val is None or val == '-' or str(val).lower() in ('n/a', 'none', 'unknown', ''):
                return '-'
            if col_l == 'distancefromarrivalls':
                return f"{float(val):,.2f} LS"
            if col_l == 'surfacegravity':
                return f"{float(val):.2f} g"
            if col_l == 'surfacetemperature':
                return f"{float(val):,.0f} K"
            if col_l == 'massem':
                return f"{float(val):.3f} EM"
            if col_l == 'radius':
                return f"{float(val):,.0f} km"
            if col_l in ('rotationperiod', 'orbitalperiod'):
                days = float(val) / 86400.0
                return f"{days:.2f} d"
            if col_l == 'age_my':
                return f"{float(val):,.0f} Myr"
            if col_l == 'stellarmass':
                return f"{float(val):.3f} M\u2609"
            if col_l == 'absolutemagnitude':
                return f"{float(val):.2f} mag"
            if col_l in ('eccentricity', 'inclination', 'periapsis', 'axialtilt'):
                return f"{float(val):.3f}"
            if col_l == 'semimajoraxis':
                try:
                    meters = float(val)
                    ls = meters / 299792458
                    return f"{ls:,.2f} LS"
                except Exception:
                    return str(val)
            if isinstance(val, (int, float)):
                return f"{val:,}"
            fval = float(val)
            return f"{fval:,}"
        except Exception:
            return str(val)

    def format_value(self, val, key=None):
        def fmt_num(x):
            if isinstance(x, (int, float)):
                absx = abs(x)
                if (absx > 1e7 or (absx < 1e-3 and absx != 0)):
                    return f"{x:.2e}"
                if absx >= 10000:
                    return f"{int(round(x)):,}"
                if absx >= 1:
                    s = f"{x:,.2f}"
                else:
                    s = f"{x:.4f}"
                s = s.rstrip('0').rstrip('.') if '.' in s else s
                return s
            return str(x)
        if isinstance(val, bool):
            return "Yes" if val else "No"
        if isinstance(val, (int, float)) and val in (0, 1):
            return "Yes" if val == 1 else "No"
        if key and key.lower() == "signals":
            if isinstance(val, list):
                out = []
                for sig in val:
                    if isinstance(sig, dict):
                        typ = sig.get("Type_Localised") or sig.get("Type")
                        count = sig.get("Count")
                        if typ:
                            if count is not None:
                                out.append(f"{typ.capitalize()} ({count})")
                            else:
                                out.append(f"{typ.capitalize()}")
                    elif isinstance(sig, str):
                        out.append(sig)
                return '\n'.join(out)
            elif isinstance(val, dict):
                typ = val.get("Type_Localised") or val.get("Type")
                count = val.get("Count")
                if typ:
                    return f"{typ.capitalize()} ({count})" if count is not None else typ.capitalize()
            elif isinstance(val, str):
                return val
        if key and key.lower() == "materials":
            out = []
            if isinstance(val, list):
                for mat in val:
                    if isinstance(mat, dict):
                        name = mat.get("Name")
                        percent = mat.get("Percent")
                        if name and percent is not None:
                            out.append(f"{name.capitalize()}: {fmt_num(percent*100) if percent<=1 else fmt_num(percent)}%")
                        elif name:
                            out.append(name.capitalize())
                return '\n'.join(out)
            elif isinstance(val, dict):
                name = val.get("Name")
                percent = val.get("Percent")
                if name and percent is not None:
                    return f"{name.capitalize()}: {fmt_num(percent*100) if percent<=1 else fmt_num(percent)}%"
                elif name:
                    return name.capitalize()
            elif isinstance(val, str):
                lines = []
                for part in val.split("Name:"):
                    if part.strip():
                        segs = part.split(",")
                        name = segs[0].replace(':', '').strip()
                        percent = None
                        for seg in segs:
                            if "Percent" in seg:
                                percent = seg.split(":")[-1].strip()
                        if name:
                            if percent:
                                lines.append(f"{name.capitalize()}: {percent}%")
                            else:
                                lines.append(name.capitalize())
                return '\n'.join(lines)
        if key and key.lower() in ("genuses", "genus", "genus_localised"):
            names = []
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        name = item.get("Genus_Localised") or item.get("Genus_Name")
                        if name:
                            names.append(name)
                    elif isinstance(item, str):
                        if "Genus_Localised" in item:
                            parts = item.split(",")
                            for part in parts:
                                if "Genus_Localised" in part:
                                    name = part.split(":")[-1].strip()
                                    names.append(name)
            elif isinstance(val, dict):
                name = val.get("Genus_Localised") or val.get("Genus_Name")
                if name:
                    names.append(name)
            elif isinstance(val, str):
                parts = val.split(",")
                for part in parts:
                    if "Genus_Localised" in part:
                        name = part.split(":")[-1].strip()
                        names.append(name)
            if names:
                return '\n'.join(names)
        if key and key.lower() in ("atmospherecomposition", "composition"):
            if isinstance(val, dict):
                return '\n'.join(f"{k.capitalize()}: {fmt_num(v)}" for k, v in val.items())
            elif isinstance(val, list):
                return '\n'.join(f"{k.capitalize()}: {fmt_num(v)}" for d in val for k, v in d.items())
        if isinstance(val, float):
            return fmt_num(val)
        if isinstance(val, int):
            return str(val)
        if isinstance(val, dict):
            return '\n'.join(f"{k.capitalize()}: {self.format_value(v)}" for k, v in val.items())
        elif isinstance(val, list):
            if all(isinstance(x, dict) for x in val):
                return '\n'.join(', '.join(f"{k.capitalize()}: {self.format_value(v)}" for k, v in x.items()) for x in val)
            else:
                return '\n'.join(str(x) for x in val)
        elif isinstance(val, str):
            try:
                import json
                parsed = json.loads(val)
                return self.format_value(parsed, key)
            except Exception:
                if ',' in val and len(val) > 30:
                    return '\n'.join([v.strip() for v in val.split(',')])
                return val
        else:
            return str(val)

    def update_log(self, system_data, _preparsed=None):
        try:
            if threading.current_thread() is not threading.main_thread():
                try:
                    parent = getattr(self.section, 'parent', None)
                    if parent and parent.winfo_exists():
                        parent.after(0, lambda: self.update_log(system_data, _preparsed=_preparsed))
                except Exception:
                    pass
                return
            tab_log = getattr(self.section, 'tab_log', None)
            bodies_table = getattr(self.section, 'bodies_table', None)
            stations_table = getattr(self.section, 'stations_table', None)
            safe_bodies = bodies_table and hasattr(bodies_table, 'winfo_exists') and bodies_table.winfo_exists()
            safe_stations = stations_table and hasattr(stations_table, 'winfo_exists') and stations_table.winfo_exists()
            if not (safe_bodies or safe_stations):
                return

            current_system = None
            if isinstance(system_data, dict):
                current_system = system_data.get('name') or system_data.get('StarSystem')
            if not current_system and hasattr(self.section, 'system_info_entry'):
                try:
                    entry = getattr(self.section.system_info_entry, 'entry', self.section.system_info_entry)
                    if hasattr(entry, 'get'):
                        current_system = entry.get().strip()
                except Exception:
                    pass

            if _preparsed is None and threading.current_thread() is threading.main_thread():
                if self._log_update_in_progress:
                    self._pending_log_update = system_data
                    return
                self._log_update_in_progress = True
                self._pending_log_update = None
                journal_cache = getattr(self.section, 'journal_cache', None)
                def _worker():
                    try:
                        parsed_all_keys, parsed_body_events = journal_cache.parse_log_files(current_system) if journal_cache else ([], {})
                    except Exception:
                        parsed_all_keys, parsed_body_events = [], {}
                    def _apply():
                        try:
                            self.update_log(system_data, _preparsed=(parsed_all_keys, parsed_body_events))
                        finally:
                            self._log_update_in_progress = False
                            pending = self._pending_log_update
                            self._pending_log_update = None
                            if pending is not None:
                                self.update_log(pending)
                    try:
                        parent = getattr(self.section, 'parent', None)
                        if parent and parent.winfo_exists():
                            parent.after(0, _apply)
                    except Exception:
                        self._log_update_in_progress = False
                threading.Thread(target=_worker, daemon=True).start()
                return

            if _preparsed is None:
                journal_cache = getattr(self.section, 'journal_cache', None)
                all_keys, body_events = journal_cache.parse_log_files(current_system) if journal_cache else ([], {})
            else:
                try:
                    all_keys, body_events = _preparsed
                except Exception:
                    all_keys, body_events = [], {}
            table_rows = []
        except Exception:
            return

        for body_name, events in body_events.items():
            merged = {}
            for ev in events:
                merged.update(ev)
            if 'Ring' in merged:
                val = merged['Ring']
                if isinstance(val, dict):
                    merged['Ring'] = self.format_ring(val)
                elif isinstance(val, list):
                    merged['Ring'] = ', '.join(self.format_ring(r) for r in val)
            if 'Rings' in merged:
                val = merged['Rings']
                if isinstance(val, dict):
                    merged['Rings'] = self.format_ring(val)
                elif isinstance(val, list):
                    merged['Rings'] = ', '.join(self.format_ring(r) for r in val)
            ts = merged.get('timestamp') or merged.get('Timestamp') or merged.get('Time') or merged.get('time')
            merged['Timestamp'] = ts
            if not merged.get('StarSystem') and current_system:
                merged['StarSystem'] = current_system
            if not merged.get('BodyName'):
                merged['BodyName'] = body_name
            table_rows.append(merged)

        for row in table_rows:
            body_val = row.get('BodyName') or row.get('Body')
            sys_val = row.get('StarSystem')
            if body_val and sys_val and isinstance(body_val, str) and isinstance(sys_val, str):
                if body_val.startswith(sys_val):
                    remaining = body_val[len(sys_val):].lstrip()
                    row['Body'] = remaining if remaining else body_val
                else:
                    row['Body'] = body_val.strip() if body_val else '-'
            elif body_val:
                row['Body'] = body_val.strip() if isinstance(body_val, str) else str(body_val)
            else:
                row['Body'] = '-'
        table_rows.sort(key=self.parse_ts, reverse=True)
        if not table_rows:
            try:
                prev_rows = self._table_rows_backup
                if prev_rows:
                    table_rows = list(prev_rows)
            except Exception:
                pass

        from edmrn.config import AppConfig
        config = AppConfig.load()
        if config.log_columns and isinstance(config.log_columns, list):
            shown_columns = [k for k in config.log_columns if k in all_keys]
            if not shown_columns:
                shown_columns = [k for k in all_keys if k in RECOMMENDED_KEYS]
        else:
            shown_columns = [k for k in all_keys if k in RECOMMENDED_KEYS]
        colors = self.section.colors
        self._log_data = []
        if tab_log:
            for child in tab_log.winfo_children():
                child.destroy()
        log_frame = ctk.CTkFrame(tab_log, fg_color=colors['background'])
        log_frame.pack(fill="both", expand=True, padx=8, pady=8)
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)

        def open_column_selector(all_keys, shown_columns, recommended_keys):
            theme = EliteDangerousTheme.COLORS
            selector = tk.Toplevel(self.section.parent)
            selector.title("Select Columns")
            selector.configure(bg=theme["panel_dark"])
            selector.resizable(True, True)
            selector.geometry("1000x600")
            all_keys_sorted = sorted(all_keys)
            technical_keys_list = [k for k in all_keys_sorted if k.lower() not in [rk.lower() for rk in recommended_keys]]
            top = tk.Frame(selector, bg=theme["panel_dark"])
            top.pack(fill="x", padx=16, pady=(12, 0))
            search_var = tk.StringVar()
            mode_var = tk.StringVar(value="normal")
            selected = {col: tk.BooleanVar(value=(col in shown_columns)) for col in all_keys}
            def get_options():
                if mode_var.get() == "normal":
                    return sorted([k for k in all_keys if k in recommended_keys])
                else:
                    return sorted(list(all_keys))
            def update_selected_count():
                count = sum(selected[k].get() for k in get_options())
                selected_count_label.config(text=f"Selected: {count}")
            tk.Label(top, text="Search:", bg=theme["panel_dark"], fg=theme["text_orange"], font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0, 4))
            search_entry = tk.Entry(top, textvariable=search_var, font=("Segoe UI", 10), bg=theme["panel_medium"], fg=theme["text_orange"], width=16)
            search_entry.grid(row=0, column=1, padx=(0, 8), sticky="ew")
            btn_normal = tk.Button(top, text="Normal", command=lambda: mode_var.set("normal"), bg=theme["primary_orange"], fg=theme["background_dark"], font=("Segoe UI", 9, "bold"), width=9, height=1)
            btn_normal.grid(row=0, column=2, padx=(0, 4))
            btn_advanced = tk.Button(top, text="Advanced", command=lambda: mode_var.set("advanced"), bg=theme["panel_medium"], fg=theme["primary_orange"], font=("Segoe UI", 9, "bold"), width=9, height=1)
            btn_advanced.grid(row=0, column=3, padx=(0, 8))
            tk.Button(top, text="Select All", command=lambda: [selected[k].set(True) for k in get_options()], bg=theme["primary_orange"], fg=theme["background_dark"], font=("Segoe UI", 9, "bold"), width=10, height=1).grid(row=0, column=4, padx=(0, 4))
            tk.Button(top, text="Deselect All", command=lambda: [selected[k].set(False) for k in get_options()], bg=theme["primary_orange"], fg=theme["background_dark"], font=("Segoe UI", 9, "bold"), width=12, height=1).grid(row=0, column=5, padx=(0, 8))
            selected_count_label = tk.Label(top, text="Selected: 0", bg=theme["panel_dark"], fg=theme["text_orange"], font=("Segoe UI", 10, "bold"))
            selected_count_label.grid(row=0, column=6, padx=(0, 8))
            top.columnconfigure(1, weight=1)
            tk.Button(top, text="Apply", command=lambda: apply_selection(), bg=theme["primary_orange"], fg=theme["background_dark"], font=("Segoe UI", 9, "bold"), width=10, height=1).grid(row=0, column=7, padx=(0, 4))
            tk.Button(top, text="Cancel", command=lambda: selector.destroy(), bg=theme["panel_medium"], fg=theme["primary_orange"], font=("Segoe UI", 9, "bold"), width=9, height=1).grid(row=0, column=8, padx=(0, 4))
            grid_frame = tk.Frame(selector, bg=theme["panel_dark"])
            grid_frame.pack(fill="both", expand=True, padx=16, pady=(8, 0))
            canvas = tk.Canvas(grid_frame, bg=theme["panel_dark"], highlightthickness=0)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar = tk.Scrollbar(grid_frame, orient="vertical", command=canvas.yview)
            scrollbar.pack(side="right", fill="y")
            frame = tk.Frame(canvas, bg=theme["panel_dark"])
            canvas.create_window((0, 0), window=frame, anchor="nw")
            def on_frame_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
            frame.bind("<Configure>", on_frame_configure)
            def render_checkboxes():
                for widget in frame.winfo_children():
                    widget.destroy()
                options = get_options()
                filtered = [k for k in options if search_var.get().lower() in k.lower()]
                groups = {}
                groups["Basic Info"] = [k for k in filtered if k in {"StarSystem", "BodyName", "PlanetClass", "Landable", "DistanceFromArrivalLS", "ScanType", "Discovery"}]
                groups["Surface Properties"] = [k for k in filtered if any(x in k for x in ["Surface", "Gravity", "Temperature", "Volcanism", "TerraformState", "Composition", "AxialTilt", "TidalLock", "MassEM", "Radius", "RotationPeriod", "Age_MY", "StellarMass", "AbsoluteMagnitude"])]
                groups["Atmosphere"] = [k for k in filtered if "Atmosphere" in k or "Luminosity" in k]
                groups["Biology"] = [k for k in filtered if any(x in k for x in ["Bio", "Species", "Genus", "Variant", "Sample", "SampleType", "SampleCount"])]
                groups["Orbit & Physics"] = [k for k in filtered if any(x in k for x in ["OrbitalPeriod", "SemiMajorAxis", "Eccentricity", "Inclination", "Periapsis", "ReserveLevel"])]
                groups["Signals & Rings"] = [k for k in filtered if any(x in k for x in ["Signal", "Ring", "Rings"])]
                grouped_keys = set(sum(groups.values(), []))
                groups["Technical/Other"] = [k for k in filtered if k not in grouped_keys]
                row_offset = 0
                for group_name, group_keys in groups.items():
                    if not group_keys:
                        continue
                    header = tk.Label(frame, text=group_name, bg=theme["panel_dark"], fg=theme["accent_blue"], font=("Segoe UI", 10, "bold"), anchor="w")
                    header.grid(row=row_offset, column=0, columnspan=6, sticky="w", pady=(8, 2))
                    row_offset += 1
                    n_cols = 6
                    n_rows = (len(group_keys) + n_cols - 1) // n_cols
                    for idx, col in enumerate(group_keys):
                        row = row_offset + (idx // n_cols)
                        col_idx = idx % n_cols
                        label = COLUMN_DISPLAY_NAMES.get(col, col)
                        if mode_var.get() == "advanced" and col in technical_keys_list:
                            cb = tk.Checkbutton(frame, text=label, variable=selected[col], bg=theme["panel_dark"], fg=theme["text_gray"], selectcolor=theme["panel_medium"], font=("Segoe UI", 9, "italic"), width=14, anchor="w")
                        else:
                            cb = tk.Checkbutton(frame, text=label, variable=selected[col], bg=theme["panel_dark"], fg=theme["text_orange"], selectcolor=theme["panel_medium"], font=("Segoe UI", 9), width=14, anchor="w")
                        cb.grid(row=row, column=col_idx, sticky="w", padx=2, pady=2)
                    row_offset += n_rows
                frame.update_idletasks()
                canvas.config(scrollregion=canvas.bbox("all"))
                canvas.configure(yscrollcommand=scrollbar.set)
                update_selected_count()
            def apply_selection():
                new_cols = [col for col, var in selected.items() if var.get()]
                shown_columns.clear()
                shown_columns.extend(new_cols)
                config = AppConfig.load()
                config.log_columns = list(shown_columns)
                config.save()
                update_log_table()
                selector.destroy()
            search_var.trace_add('write', lambda *a: render_checkboxes())
            mode_var.trace_add('write', lambda *a: render_checkboxes())
            for var in selected.values():
                var.trace_add('write', lambda *a: update_selected_count())
            render_checkboxes()

        log_filter_var = tk.StringVar()
        time_filter_var = tk.StringVar(value="All")
        note_dict = {}
        theme = EliteDangerousTheme.COLORS
        filter_row = ctk.CTkFrame(log_frame, fg_color="transparent")
        filter_row.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        filter_row.columnconfigure(3, weight=1)
        label_time = tk.Label(filter_row, text="Time:", bg=theme["panel_dark"], fg=theme["primary_orange"], font=("Segoe UI", 10, "bold"))
        label_time.grid(row=0, column=0, padx=(0, 4), pady=2, sticky="nsew")
        time_options = ["1h", "6h", "24h", "All"]
        def on_time_filter_change(*args):
            update_log_table()
        time_menu = tk.OptionMenu(filter_row, time_filter_var, *time_options)
        time_menu.config(width=4, font=("Segoe UI", 10, "bold"), bg=theme["panel_dark"], fg=theme["primary_orange"], highlightthickness=0, activebackground=theme["panel_medium"], activeforeground=theme["primary_orange"])
        time_menu.grid(row=0, column=1, padx=(0, 4), pady=2, sticky="nsew")
        time_filter_var.trace_add('write', on_time_filter_change)
        col_btn = tk.Button(
            filter_row, text="⋮", width=2,
            command=lambda: open_column_selector(all_keys, shown_columns, RECOMMENDED_KEYS),
            bg=theme["panel_medium"], fg=theme["primary_orange"], font=("Segoe UI", 12, "bold"), relief="flat", activebackground=theme["panel_dark"], activeforeground=theme["primary_orange"]
        )
        col_btn.grid(row=0, column=2, padx=(0, 4), pady=2, sticky="nsew")
        log_filter_entry = ctk.CTkEntry(filter_row, placeholder_text="Search...", textvariable=log_filter_var, width=320)
        log_filter_entry.grid(row=0, column=3, sticky="ew", pady=2)
        if table_rows:
            self._table_rows_backup = list(table_rows)

        def log_filter_table_debounced(*args):
            if self._log_filter_after_id and filter_row.winfo_exists():
                try:
                    filter_row.after_cancel(self._log_filter_after_id)
                except Exception:
                    pass
            if filter_row.winfo_exists():
                self._log_filter_after_id = filter_row.after(450, log_filter_table)

        def log_filter_table():
            query = log_filter_var.get().lower()
            backup = self._table_rows_backup
            if backup is None:
                backup = list(table_rows)
                self._table_rows_backup = backup
            def row_matches(row):
                if not query:
                    return True
                for col in shown_columns:
                    val = str(row.get(col, "")).lower()
                    if query in val:
                        return True
                return False
            filtered_rows = [row for row in backup if row_matches(row)]
            table_rows.clear()
            table_rows.extend(filtered_rows)
            update_log_table()
            log_filter_entry.focus_set()

        log_filter_var.trace_add('write', log_filter_table_debounced)

        def update_log_table():
            nonlocal log_table
            try:
                if log_table is not None:
                    log_table.destroy()
            except Exception:
                pass
            columns = list(shown_columns)
            if 'Body' not in columns:
                columns.append('Body')
            if 'StarSystem' in columns and 'Body' in columns:
                rest = [c for c in columns if c not in ('StarSystem', 'Body')]
                columns = ['StarSystem', 'Body'] + rest
            elif 'StarSystem' in columns:
                rest = [c for c in columns if c != 'StarSystem']
                columns = ['StarSystem'] + rest
            elif 'Body' in columns:
                rest = [c for c in columns if c != 'Body']
                columns = ['Body'] + rest
            if 'EventIcon' not in columns:
                columns = ['EventIcon'] + columns
            if 'Note' not in columns:
                columns = columns + ['Note']
            columns = tuple(columns)
            headings = ["-" if col == "EventIcon" else COLUMN_DISPLAY_NAMES.get(col, col) for col in columns]
            theme_colors = {
                'background': colors['background'],
                'text': colors['accent'],
                'header': colors['background'],
                'header_fg': colors['primary'],
                'selected': '#333300',
            }
            def on_column_reorder(new_order):
                cols = [c for c in new_order if c not in ('StarSystem', 'Body')]
                if 'StarSystem' in new_order and 'Body' in new_order:
                    forced = ['StarSystem', 'Body'] + cols
                elif 'StarSystem' in new_order:
                    forced = ['StarSystem'] + cols
                elif 'Body' in new_order:
                    forced = ['Body'] + cols
                else:
                    forced = cols
                shown_columns.clear()
                shown_columns.extend(forced)
                config = AppConfig.load()
                config.log_columns = list(shown_columns)
                config.save()
                update_log_table()
            new_table = EDMRNSheet(
                log_frame, data=[], headers=headings, theme_colors=theme_colors
            )
            new_table.on_column_reorder = on_column_reorder
            new_table.grid(row=1, column=0, sticky="nsew")

            def parse_time(row):
                v = row.get('timestamp') or row.get('Timestamp') or row.get('Time') or row.get('time')
                if not v:
                    return None
                try:
                    if isinstance(v, str):
                        v = v.replace(' ', 'T')
                        if v.endswith('Z'):
                            v = v[:-1] + '+00:00'
                        dt = datetime.datetime.fromisoformat(v)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=datetime.timezone.utc)
                        else:
                            dt = dt.astimezone(datetime.timezone.utc)
                        return dt
                    return None
                except Exception:
                    return None

            tf = time_filter_var.get()
            now = datetime.datetime.now(datetime.timezone.utc)
            min_time = None
            if tf and tf.lower() != "all":
                m = re.search(r'(\d+)\s*[hH]', tf)
                if m:
                    try:
                        hours = int(m.group(1))
                        min_time = now - datetime.timedelta(hours=hours)
                    except Exception:
                        min_time = None

            max_rows = 2000
            display_rows = table_rows[:max_rows] if len(table_rows) > max_rows else table_rows
            table_data = []
            for row in display_rows:
                t = parse_time(row)
                if min_time is not None:
                    if t is None or t < min_time:
                        continue
                values = []
                event = row.get('event', '') or row.get('Event', '')
                event_icon = ''
                if event:
                    if 'Scan' in event:
                        event_icon = '🔍'
                    elif 'FSS' in event:
                        event_icon = '🌐'
                    elif 'Discovery' in event:
                        event_icon = '✨'
                    elif 'Signal' in event:
                        event_icon = '📡'
                    elif 'Reservoir' in event:
                        event_icon = '💧'
                    elif 'Body' in event:
                        event_icon = '🪐'
                    else:
                        event_icon = '📝'
                note = note_dict.get(row.get('BodyName') or row.get('Name') or '', '')
                system_name = row.get('StarSystem', None)
                for col in columns:
                    if col == 'EventIcon':
                        values.append(event_icon)
                    elif col == 'Note':
                        values.append(note)
                    else:
                        val = row.get(col, '-')
                        if col != 'StarSystem' and system_name is not None and val == system_name:
                            val = '-'
                        if col.lower() in ('body', 'bodyname', 'name') and system_name is not None and isinstance(val, str):
                            pattern = re.compile(re.escape(system_name) + r'\s*', re.IGNORECASE)
                            val = pattern.sub('', val).strip()
                            if not val:
                                val = '-'
                        if col.lower() in ('ring', 'rings') and system_name is not None and isinstance(val, str) and system_name in val:
                            val = val.replace(system_name, '').strip()
                            if not val:
                                val = '-'
                        if col.lower() == 'landable':
                            if val is True:
                                val = 'Yes'
                            elif val is False:
                                val = 'No'
                            elif isinstance(val, str):
                                pass
                            else:
                                val = '-'
                        elif col.lower() == 'signals' and isinstance(val, list):
                            signals_strs = []
                            for sig in val:
                                if isinstance(sig, dict):
                                    count = sig.get('Count', '')
                                    typ = sig.get('Type_Localised')
                                    if not typ:
                                        typ_raw = sig.get('Type')
                                        typ = codex_translation.get(typ_raw, typ_raw)
                                    if count and typ:
                                        signals_strs.append(f"{count} {typ}")
                                    elif typ:
                                        signals_strs.append(str(typ))
                                    elif count:
                                        signals_strs.append(str(count))
                                else:
                                    signals_strs.append(str(sig))
                            val = ', '.join(signals_strs) if signals_strs else '-'
                        elif col.lower() == 'composition' and isinstance(val, dict):
                            val = ', '.join(f"{k}: {v*100:.1f}%" for k, v in val.items())
                        elif isinstance(val, list):
                            val = ', '.join(str(x) for x in val)
                        val = self.format_number(col, val) if col.lower() not in ('signals', 'composition', 'landable', 'body', 'bodyname', 'name') else val
                        values.append(val)
                table_data.append(values)
            try:
                new_table.set_sheet_data(table_data)
                new_table.auto_resize_columns()
            except Exception:
                pass

            def on_log_right_click(event):
                iid = new_table.identify_row(event)
                if iid:
                    try:
                        if hasattr(new_table, "select_row"):
                            new_table.select_row(iid)
                        elif hasattr(new_table, "selection_set"):
                            new_table.selection_set(iid)
                    except Exception:
                        pass
                menu = tk.Menu(self.section.parent, tearoff=0)
                menu.tk_popup(event.x_root, event.y_root)
            new_table.bind('<Button-3>', on_log_right_click)

            def show_detail_panel(event):
                row_index = new_table.identify_row(event)
                if row_index is None or row_index == -1:
                    return
                values = new_table.get_row_data(row_index)
                detail_win = tk.Toplevel(self.section.parent)
                detail_win.title("Log Detail")
                detail_win.configure(bg="#222")
                detail_win.resizable(True, True)
                try:
                    headers = new_table.headers() if callable(getattr(new_table, "headers", None)) else getattr(new_table, "headers", [])
                except Exception:
                    headers = []
                max_key_len = max(len(str(col)) for col in headers) if headers else 10
                key_width = min(max(12, max_key_len + 2), 24)
                log_row = None
                try:
                    log_row = table_rows[row_index]
                except Exception:
                    log_row = None
                if log_row:
                    panel_dark = theme.get("panel_dark", "#222")
                    panel_medium = theme.get("panel_medium", "#333")
                    accent = theme.get("accent", "#FFD700")
                    text_orange = theme.get("text_orange", "#FFD700")
                    display_items = [(k, log_row[k]) for k in log_row.keys() if k not in TECHNICAL_KEYS]
                    n = len(display_items)
                    mid = (n + 1) // 2
                    left_items = display_items[:mid]
                    right_items = display_items[mid:]
                    frame = tk.Frame(detail_win, bg=panel_dark)
                    frame.pack(fill="both", expand=True)
                    canvas = tk.Canvas(frame, bg=panel_dark, highlightthickness=0)
                    v_scroll = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
                    canvas.configure(yscrollcommand=v_scroll.set)
                    v_scroll.pack(side="right", fill="y")
                    canvas.pack(side="left", fill="both", expand=True)
                    inner = tk.Frame(canvas, bg=panel_dark)
                    canvas.create_window((0, 0), window=inner, anchor="nw")
                    def on_configure(event):
                        canvas.configure(scrollregion=canvas.bbox("all"))
                    inner.bind("<Configure>", on_configure)
                    for i, (col, val) in enumerate(left_items):
                        display_name = COLUMN_DISPLAY_NAMES.get(col, col)
                        tk.Label(inner, text=f"{display_name}", anchor="w", font=("Segoe UI", 9, "bold"), bg=panel_dark, fg=accent, width=18, justify="left", padx=5, pady=2).grid(row=i, column=0, sticky="ew", pady=1, padx=(8, 2))
                        tk.Label(inner, text=self.format_value(val, col), anchor="w", font=("Segoe UI", 9), bg=panel_medium, fg=text_orange, wraplength=180, justify="left", padx=5, pady=2).grid(row=i, column=1, sticky="ew", pady=1, padx=(0, 8))
                    for i, (col, val) in enumerate(right_items):
                        display_name = COLUMN_DISPLAY_NAMES.get(col, col)
                        tk.Label(inner, text=f"{display_name}", anchor="w", font=("Segoe UI", 9, "bold"), bg=panel_dark, fg=accent, width=18, justify="left", padx=5, pady=2).grid(row=i, column=2, sticky="ew", pady=1, padx=(8, 2))
                        tk.Label(inner, text=self.format_value(val, col), anchor="w", font=("Segoe UI", 9), bg=panel_medium, fg=text_orange, wraplength=180, justify="left", padx=5, pady=2).grid(row=i, column=3, sticky="ew", pady=1, padx=(0, 8))
                    inner.grid_columnconfigure(0, weight=0)
                    inner.grid_columnconfigure(1, weight=1)
                    inner.grid_columnconfigure(2, weight=0)
                    inner.grid_columnconfigure(3, weight=1)
                    detail_win.update_idletasks()
                    content_width = inner.winfo_width() + 40
                    content_height = inner.winfo_height() + 40
                    min_w, min_h = 380, 260
                    max_w, max_h = 900, 900
                    win_width = min(max(content_width, min_w), max_w)
                    win_height = min(max(content_height, min_h), max_h)
                    detail_win.minsize(min_w, min_h)
                    detail_win.geometry(f"{win_width}x{win_height}")
                    detail_win.configure(bg=panel_dark)
                    if 'Note' in columns:
                        note_frame = tk.Frame(detail_win, bg=panel_dark)
                        note_frame.pack(side="bottom", fill="x", padx=10, pady=10)
                        def save_note():
                            try:
                                key = values[columns.index('BodyName')] if 'BodyName' in columns else values[1]
                                note_dict[key] = note_entry.get()
                                detail_win.destroy()
                                update_log_table()
                            except Exception:
                                pass
                        tk.Label(note_frame, text="Note:", bg=panel_dark, fg=accent, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 5))
                        note_entry = tk.Entry(note_frame, width=40, bg=panel_medium, fg=text_orange, font=("Segoe UI", 10))
                        note_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
                        tk.Button(note_frame, text="Save", command=save_note, bg=accent, fg=panel_dark, font=("Segoe UI", 9, "bold")).pack(side="left")
            new_table.bind('<Double-1>', show_detail_panel)
            log_table = new_table

        log_table = None
        update_log_table()
