import logging
import os
import json
import customtkinter as ctk
import tkinter as tk
import webbrowser
import re
from edmrn.autocomplete_entry import AutocompleteEntry
from edmrn.edmrn_sheet import EDMRNSheet
from edmrn.config import Paths
from edmrn.exobiology import ExobioManager
from edmrn.journal_cache import JournalCache
from edmrn.log_viewer import LogViewer

logger = logging.getLogger('SystemInfoSection')


class SystemInfoSection:
    def update_system_info(self, system_data):
        import threading
        try:
            if not isinstance(system_data, dict):
                return
            if not hasattr(self, 'info_values') or not hasattr(self, 'stats_labels'):
                return

            info = system_data.get('information') if isinstance(system_data.get('information'), dict) else {}
            primary_star = system_data.get('primaryStar') if isinstance(system_data.get('primaryStar'), dict) else {}

            def _get_permit_info():
                require_permit = system_data.get('requirePermit')
                if isinstance(require_permit, bool):
                    return "Yes" if require_permit else "No"
                permit_val = system_data.get('permit')
                if isinstance(permit_val, bool):
                    return "Yes" if permit_val else "No"
                if isinstance(permit_val, str) and permit_val and permit_val != '-':
                    return permit_val
                info_permit = info.get('permit')
                if isinstance(info_permit, bool):
                    return "Yes" if info_permit else "No"
                if isinstance(info_permit, str) and info_permit and info_permit != '-':
                    return info_permit
                permit_name = info.get('permitName')
                if isinstance(permit_name, str) and permit_name and permit_name != '-':
                    return permit_name
                return '-'

            def _get_controlling_faction():
                cf = system_data.get('controllingFaction') or info.get('faction')
                if isinstance(cf, dict):
                    return cf.get('name', '-')
                if isinstance(cf, str) and cf:
                    return cf
                factions = system_data.get('factions')
                if isinstance(factions, list):
                    for f in factions:
                        try:
                            if f.get('isControllingFaction'):
                                return f.get('name', '-')
                        except Exception:
                            continue
                return '-'

            def _format_population(pop):
                if pop == '-' or pop is None:
                    return '-'
                try:
                    pop_int = int(pop)
                    return f"{pop_int:,}"
                except Exception:
                    return str(pop)

            overview_values = {
                'allegiance': system_data.get('allegiance') or info.get('allegiance', '-'),
                'population': _format_population(system_data.get('population') or info.get('population', '-')),
                'security': system_data.get('security') or info.get('security', '-'),
                'permit': _get_permit_info(),
                'faction': _get_controlling_faction(),
                'star_type': system_data.get('starType') or primary_star.get('type', '-'),
            }

            name = system_data.get('name', '-')
            if 'system_name' in self.info_values:
                try:
                    self.info_values['system_name'].configure(text=name)
                except:
                    pass

            self.edsm_url = system_data.get('url', None)

            for key, label in self.info_values.items():
                if key == 'system_name':
                    continue
                try:
                    if key == 'allegiance':
                        label.configure(text=overview_values.get('allegiance', '-'))
                    elif key == 'population':
                        label.configure(text=str(overview_values.get('population', '-')))
                    elif key == 'security':
                        label.configure(text=overview_values.get('security', '-'))
                    elif key == 'permit':
                        label.configure(text=str(overview_values.get('permit', '-')))
                    elif key == 'faction':
                        label.configure(text=overview_values.get('faction', '-'))
                    elif key == 'star_type':
                        label.configure(text=overview_values.get('star_type', '-'))
                except:
                    pass

            if hasattr(self, 'trivia_label'):
                try:
                    trivia = system_data.get('trivia', '')
                    self.trivia_label.configure(text=trivia if trivia else '-')
                except:
                    pass

            def _update_stats_background():
                try:
                    stats = system_data.get('stats', {}) if isinstance(system_data.get('stats', {}), dict) else {}
                    bodies = system_data.get('bodies', []) if isinstance(system_data.get('bodies'), list) else []
                    stations = system_data.get('stations', []) if isinstance(system_data.get('stations'), list) else []

                    def _to_int(value):
                        try:
                            return int(value)
                        except Exception:
                            return None

                    def _calc_stats_from_bodies():
                        planet_count = 0
                        moon_count = 0
                        landable_count = 0
                        atmo_count = 0
                        for b in bodies:
                            try:
                                body_type = str(b.get('type', '')).lower()
                                if b.get('isPlanet') or body_type == 'planet':
                                    planet_count += 1
                                elif body_type == 'moon':
                                    moon_count += 1
                                if b.get('isLandable'):
                                    landable_count += 1
                                atmo = b.get('atmosphereType')
                                if atmo and str(atmo).lower() not in ('none', 'no atmosphere', 'no_atmosphere'):
                                    atmo_count += 1
                            except Exception:
                                continue
                        return planet_count, moon_count, landable_count, atmo_count

                    def _first_not_none(*values):
                        for v in values:
                            if v is not None:
                                return v
                        return None

                    info_planet_count = _to_int(info.get('planetCount'))
                    info_moon_count = _to_int(info.get('moonCount'))
                    info_body_count = _to_int(info.get('bodyCount'))

                    calc_planet_count, calc_moon_count, calc_landable_count, calc_atmo_count = _calc_stats_from_bodies()

                    def _get_permit_required():
                        pr_val = stats.get('permit_required')
                        if pr_val is not None:
                            if isinstance(pr_val, bool):
                                return "Yes" if pr_val else "No"
                            return str(pr_val)
                        info_pr = info.get('requirePermit') or info.get('permit_required')
                        if info_pr is not None:
                            if isinstance(info_pr, bool):
                                return "Yes" if info_pr else "No"
                            return str(info_pr)
                        return overview_values.get('permit', '-')

                    stats_values = {
                        'planet_count': _first_not_none(stats.get('planet_count'), info_planet_count, calc_planet_count, '-'),
                        'moon_count': _first_not_none(stats.get('moon_count'), info_moon_count, calc_moon_count, '-'),
                        'landable_count': _first_not_none(stats.get('landable_count'), calc_landable_count, '-'),
                        'atmo_count': _first_not_none(stats.get('atmo_count'), calc_atmo_count, '-'),
                        'station_count': _first_not_none(stats.get('station_count'), len(stations) if stations else None, '-'),
                        'permit_required': _get_permit_required(),
                    }

                    if stats_values.get('planet_count') in (None, '-') and info_body_count is not None:
                        stats_values['planet_count'] = info_body_count

                    if hasattr(self, 'parent') and hasattr(self.parent, 'after'):
                        def _update_ui():
                            try:
                                for key, label in self.stats_labels.items():
                                    try:
                                        if key == 'planet_count':
                                            label.configure(text=str(stats_values.get('planet_count', '-')))
                                        elif key == 'moon_count':
                                            label.configure(text=str(stats_values.get('moon_count', '-')))
                                        elif key == 'landable_count':
                                            label.configure(text=str(stats_values.get('landable_count', '-')))
                                        elif key == 'atmo_count':
                                            label.configure(text=str(stats_values.get('atmo_count', '-')))
                                        elif key == 'station_count':
                                            label.configure(text=str(stats_values.get('station_count', '-')))
                                        elif key == 'permit_required':
                                            label.configure(text=str(stats_values.get('permit_required', '-')))
                                    except:
                                        pass
                            except Exception:
                                pass
                        try:
                            self.parent.after(0, _update_ui)
                        except Exception:
                            pass
                except Exception as e:
                    logging.getLogger('SystemInfoSection').debug(f"[update_system_info] Background stats error: {e}")

            threading.Thread(target=_update_stats_background, daemon=True).start()

        except Exception as e:
            logging.getLogger('SystemInfoSection').error(f"[update_system_info] Exception: {e}")

    @staticmethod
    def get_history_path():
        return os.path.join(os.path.dirname(Paths.get_backup_folder()), 'visited_systems_history.json')

    def __init__(self, parent, theme_manager, fetch_callback, tab_log, app=None):
        self.theme_manager = theme_manager
        self.colors = theme_manager.get_theme_colors()
        self.parent = parent
        self.app = app if app is not None else getattr(parent, 'app', None)
        self.fetch_callback = fetch_callback
        self.tab_log = tab_log

        self.journal_cache = JournalCache(self)
        self.journal_cache.prime_async()
        self.exobio = ExobioManager(self)
        self.log_viewer = LogViewer(self)

        self._build_ui()
        self.update_planetary_access([])
        self.update_stations([])
        self.update_gmp(None)
        self.log_viewer.update_log({})

    def add_onfoot_bio_sample(self, genus, body=None, system=None, geo=False, completed=False):
        self.exobio.add_onfoot_bio_sample(genus, body=body, system=system, geo=geo, completed=completed)

    def update_bio_summary(self, exobio_samples, system=None, body=None):
        self.exobio.update_bio_summary(exobio_samples, system, body)

    def _enqueue_bio_update(self, exobio_samples, system=None, body=None):
        self.exobio._enqueue_bio_update(exobio_samples, system, body)

    def update_log(self, system_data, _preparsed=None):
        self.log_viewer.update_log(system_data, _preparsed)

    def _build_ui(self):
        colors = self.colors

        name_row = ctk.CTkFrame(self.parent, fg_color="transparent")
        name_row.columnconfigure(0, weight=0)
        name_row.columnconfigure(1, weight=1)
        name_row.columnconfigure(2, weight=0)

        def on_suggestion_selected(selected):
            self.fetch_callback()

        app = getattr(self.parent, 'app', None)
        if app and hasattr(app, '_get_system_suggestions'):
            suggestion_provider = app._get_system_suggestions
        else:
            from edmrn.system_autocomplete import SystemAutocompleter
            system_autocompleter = SystemAutocompleter()
            def suggestion_provider(query, callback):
                def fetch():
                    suggestions = system_autocompleter.get_suggestions(query, max_results=10)
                    callback(suggestions)
                import threading
                threading.Thread(target=fetch, daemon=True).start()

        self.system_info_entry = AutocompleteEntry(
            name_row,
            placeholder_text="Enter system name (e.g., Sol, Achenar)",
            suggestion_provider=suggestion_provider,
            on_suggestion_callback=on_suggestion_selected,
            fg_color="transparent"
        )
        self.system_info_entry.grid(row=0, column=0, sticky="w", padx=(0, 10))

        fetch_btn = ctk.CTkButton(name_row, text="🔍", command=self.fetch_callback, width=40, height=32)
        self.theme_manager.apply_button_theme(fetch_btn, "secondary")
        fetch_btn.grid(row=0, column=1, sticky="w", padx=(0, 10))

        self.system_info_status = ctk.CTkLabel(self.parent, text="Enter a system name and click Fetch Data", text_color=colors['text'], font=ctk.CTkFont(size=11))

        self.tabview = ctk.CTkTabview(self.parent, fg_color=colors['background'], border_color=colors['border'], border_width=1)
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.tab_overview = self.tabview.add("Overview")
        self.tab_bodies = self.tabview.add("Bodies")
        self.tab_stations = self.tabview.add("Stations")
        self.tab_gmp = self.tabview.add("System History")
        name_row.pack(fill="x", padx=20, pady=(8, 4))
        self.system_info_status.pack(anchor="w", padx=24, pady=(0, 6))

        overview_frame = ctk.CTkFrame(self.tab_overview, fg_color=colors['background'])
        overview_frame.pack(fill="both", expand=True, padx=8, pady=8)
        for i in range(3):
            overview_frame.columnconfigure(i, weight=1)
        overview_frame.rowconfigure(0, weight=1)

        left_card = ctk.CTkFrame(overview_frame, fg_color=colors['background'], border_width=1, border_color=colors['border'])
        left_card.grid(row=0, column=0, sticky="nsew", padx=(8, 8), pady=8)
        self.info_values = {}
        title_label = ctk.CTkLabel(left_card, text="-", font=ctk.CTkFont(size=22, weight="bold"), text_color=colors['accent'])
        title_label.grid(row=0, column=0, sticky="w", pady=(8, 8), padx=(12, 12))
        self.info_values['system_name'] = title_label
        info_grid = ctk.CTkFrame(left_card, fg_color=colors['background'])
        info_grid.grid(row=1, column=0, sticky="nw", pady=(0, 8), padx=(12, 12))
        labels = [
            ("Allegiance", 'allegiance'),
            ("Population", 'population'),
            ("Security", 'security'),
            ("Permit", 'permit'),
            ("Controlling Faction", 'faction'),
            ("Star Type", 'star_type'),
        ]
        for i, (lbl, key) in enumerate(labels):
            l = ctk.CTkLabel(info_grid, text=lbl + ":", font=ctk.CTkFont(size=13), text_color=colors['accent'])
            l.grid(row=i, column=0, sticky="w", padx=(0, 8), pady=2)
            v = ctk.CTkLabel(info_grid, text="-", font=ctk.CTkFont(size=13, weight="bold"), text_color=colors['accent'])
            v.grid(row=i, column=1, sticky="w", pady=2)
            self.info_values[key] = v
        self.edsm_url = None
        def open_edsm():
            if self.edsm_url:
                webbrowser.open(self.edsm_url)
        self.edsm_link = ctk.CTkButton(left_card, text="View on EDSM", width=120, height=28, fg_color=colors['accent'], text_color=colors['background'], command=open_edsm)
        self.edsm_link.grid(row=2, column=0, sticky="w", pady=(0, 8), padx=(12, 12))
        trivia_frame = ctk.CTkFrame(left_card, fg_color=colors['background'])
        trivia_frame.grid(row=3, column=0, sticky="ew", padx=(12, 12), pady=(0, 8))
        trivia_label = ctk.CTkLabel(trivia_frame, text="", font=ctk.CTkFont(size=12, slant="italic"), text_color=colors['accent'], justify="left")
        trivia_label.pack(anchor="w", padx=0, pady=0)
        self.trivia_label = trivia_label

        stats_card = ctk.CTkFrame(overview_frame, fg_color=colors['background'], border_width=1, border_color=colors['border'])
        stats_card.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        stats_title = ctk.CTkLabel(stats_card, text="Statistics", font=ctk.CTkFont(size=16, weight="bold"), text_color=colors['primary'])
        stats_title.pack(anchor="w", pady=(8, 8), padx=(12, 12))
        self.stats_labels = {}
        stats_grid = ctk.CTkFrame(stats_card, fg_color=colors['background'])
        stats_grid.pack(anchor="w", padx=(12, 12), pady=(0, 8))
        stats_fields = [
            ("Planet Count", 'planet_count'),
            ("Moon Count", 'moon_count'),
            ("Landable Bodies", 'landable_count'),
            ("Atmosphere Bodies", 'atmo_count'),
            ("Stations", 'station_count'),
            ("Permit Required", 'permit_required'),
        ]
        for i, (lbl, key) in enumerate(stats_fields):
            l = ctk.CTkLabel(stats_grid, text=lbl + ":", font=ctk.CTkFont(size=13), text_color=colors['accent'])
            l.grid(row=i, column=0, sticky="w", padx=(0, 8), pady=2)
            v = ctk.CTkLabel(stats_grid, text="-", font=ctk.CTkFont(size=13, weight="bold"), text_color=colors['accent'])
            v.grid(row=i, column=1, sticky="w", pady=2)
            self.stats_labels[key] = v

        self.bio_card = ctk.CTkFrame(overview_frame, fg_color=colors['background'], border_width=1, border_color=colors['border'])
        self.bio_card.grid(row=0, column=2, sticky="nsew", padx=8, pady=8)
        self.bio_title_label = ctk.CTkLabel(self.bio_card, text="Exobiology Scans", font=ctk.CTkFont(size=16, weight="bold"), text_color=colors['primary'])
        self.bio_title_label.pack(anchor="w", pady=(8, 8), padx=(12, 12))
        self.bio_summary_label = ctk.CTkLabel(self.bio_card, text="-", font=ctk.CTkFont(size=13), text_color=colors['accent'], justify="left")
        self.bio_summary_label.pack(anchor="w", padx=(12, 12), pady=(0, 8))

        bodies_frame = ctk.CTkFrame(self.tab_bodies, fg_color=colors['background'])
        bodies_frame.pack(fill="both", expand=True, padx=8, pady=8)
        bodies_frame.rowconfigure(1, weight=1)
        bodies_frame.columnconfigure(0, weight=1)
        bodies_filter_var = tk.StringVar()
        bodies_filter_entry = ctk.CTkEntry(bodies_frame, placeholder_text="Filter bodies...", textvariable=bodies_filter_var, width=320)
        bodies_filter_entry.grid(row=0, column=0, columnspan=2, sticky="n", pady=(0, 8))
        self.bodies_table = EDMRNSheet(
            bodies_frame, data=[],
            headers=["Name", "Type", "Gravity", "Landable", "Atmosphere", "Subtype"],
            theme_colors={
                'background': colors['background'],
                'text': colors['accent'],
                'header': colors['background'],
                'header_fg': colors['primary'],
                'selected': '#333300',
            }
        )
        self.bodies_table.set_column_widths([120, 120, 120, 120, 120, 120])
        self._bodies_roworder = []
        self.bodies_table.grid(row=1, column=0, sticky="nsew")
        def on_bodies_destroy(event=None):
            self.bodies_table = None
        self.bodies_table.bind("<Destroy>", on_bodies_destroy)
        self._bodies_data = []
        def bodies_filter_table(*args):
            query = bodies_filter_var.get().lower()
            filtered_rows = []
            for b in self._bodies_data:
                name = b.get('name', '-')
                type_ = b.get('type', '-')
                gravity = f"{b.get('gravity', 0):.2f}" if b.get('gravity') is not None else "-"
                landable = "Yes" if b.get('isLandable') else "No"
                atmosphere = b.get('atmosphereType', '-')
                subtype = b.get('subType', '-')
                values = [str(name), str(type_), str(gravity), str(landable), str(atmosphere), str(subtype)]
                if any(query in v.lower() for v in values):
                    filtered_rows.append(values)
            self.bodies_table.set_sheet_data(filtered_rows)
            self.bodies_table.auto_resize_columns()
        bodies_filter_var.trace_add('write', bodies_filter_table)
        def show_body_details(event):
            row_index = self.bodies_table.identify_row(event)
            if row_index is None or row_index == -1:
                return
            values = self.bodies_table.get_row_data(row_index)
            detail_dict = {
                "Name": values[1] if len(values) > 1 else '-',
                "Type": values[2] if len(values) > 2 else '-',
                "Gravity": values[3] if len(values) > 3 else '-',
                "Landable": values[4] if len(values) > 4 else '-',
                "Atmosphere": values[5] if len(values) > 5 else '-',
                "Subtype": values[6] if len(values) > 6 else '-'
            }
            popup = tk.Toplevel(self.parent)
            popup.title("Body Details")
            popup.configure(bg="#222")
            popup.resizable(True, True)
            frame = tk.Frame(popup, bg="#222")
            frame.pack(fill="both", expand=True, padx=18, pady=18)
            for i in range(6):
                frame.grid_rowconfigure(i, weight=1)
            frame.grid_columnconfigure(1, weight=1)
            row = 0
            for key in ["Name", "Type", "Gravity", "Landable", "Atmosphere", "Subtype"]:
                tk.Label(frame, text=key + ":", anchor="w", font=("Segoe UI", 11, "bold"), bg="#222", fg="#FFD700").grid(row=row, column=0, sticky="w", pady=2, padx=(0, 10))
                tk.Label(frame, text=detail_dict[key], anchor="w", font=("Segoe UI", 11), bg="#222", fg="#FFF").grid(row=row, column=1, sticky="ew", pady=2)
                row += 1
            popup.update_idletasks()
            popup.geometry("")
            popup.transient(self.parent)
            popup.grab_set()
        self.bodies_table.bind('<Double-1>', show_body_details)
        def copy_selected_bodies(event=None):
            selected_rows = self.bodies_table.get_selected_rows()
            if not selected_rows:
                return
            rows = []
            for row_index in selected_rows:
                values = self.bodies_table.get_row_data(row_index)
                rows.append('\t'.join(str(v) for v in values))
            text = '\n'.join(rows)
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
        def on_bodies_right_click(event):
            row_index = self.bodies_table.identify_row(event)
            if row_index is not None and row_index != -1:
                self.bodies_table.select_row(row_index)
            menu = tk.Menu(self.parent, tearoff=0)
            menu.add_command(label="Copy selected", command=copy_selected_bodies)
            menu.tk_popup(event.x_root, event.y_root)
        self.bodies_table.bind('<Button-3>', on_bodies_right_click)

        stations_frame = ctk.CTkFrame(self.tab_stations, fg_color=colors['background'])
        stations_frame.pack(fill="both", expand=True, padx=8, pady=8)
        stations_frame.rowconfigure(1, weight=1)
        stations_frame.columnconfigure(0, weight=1)
        filter_var = tk.StringVar()
        filter_entry = ctk.CTkEntry(stations_frame, placeholder_text="Filter stations...", textvariable=filter_var, width=320)
        filter_entry.grid(row=0, column=0, columnspan=2, sticky="n", pady=(0, 8))
        self.stations_table = EDMRNSheet(
            stations_frame, data=[],
            headers=["Name", "Type", "Planet", "Distance (ls)", "Services"],
            theme_colors={
                'background': colors['background'],
                'text': colors['accent'],
                'header': colors['background'],
                'header_fg': colors['primary'],
                'selected': '#333300',
            }
        )
        self.stations_table.set_column_widths([260, 180, 260, 120, 120])
        self._stations_roworder = []
        self.stations_table.grid(row=1, column=0, sticky="nsew")
        def on_stations_destroy(event=None):
            self.stations_table = None
        self.stations_table.bind("<Destroy>", on_stations_destroy)
        self._stations_data = []
        def filter_table(*args):
            query = filter_var.get().lower()
            filtered_rows = []
            for s in self._stations_data:
                planet = s.get('body', '-')
                if isinstance(planet, dict):
                    planet = planet.get('name', '-')
                dist = s.get('distanceToArrival', '-')
                if isinstance(dist, (int, float)):
                    dist = f"{dist:,.0f}"
                services = ', '.join(s.get('otherServices', [])) if s.get('otherServices') else '-'
                name = s.get('name', '-')
                type_ = s.get('type', '-')
                values = [str(name), str(type_), str(planet), str(dist), str(services)]
                if any(query in v.lower() for v in values):
                    filtered_rows.append(values)
            self.stations_table.set_sheet_data(filtered_rows)
            self.stations_table.auto_resize_columns()
        filter_var.trace_add('write', filter_table)

        def show_row_details(event):
            row_index = self.stations_table.identify_row(event)
            if row_index is None or row_index == -1:
                return
            values = self.stations_table.get_row_data(row_index)
            detail_dict = {
                "Name": values[1] if len(values) > 1 else '-',
                "Type": values[2] if len(values) > 2 else '-',
                "Planet": values[3] if len(values) > 3 else '-',
                "Distance (ls)": values[4] if len(values) > 4 else '-',
                "Services": values[5].split(', ') if len(values) > 5 else ['-']
            }
            popup = tk.Toplevel(self.parent)
            popup.title("Station Details")
            popup.configure(bg="#222")
            popup.resizable(True, True)
            frame = tk.Frame(popup, bg="#222")
            frame.pack(fill="both", expand=True, padx=18, pady=18)
            for i in range(5):
                frame.grid_rowconfigure(i, weight=1)
            frame.grid_columnconfigure(1, weight=1)
            row = 0
            for key in ["Name", "Type", "Planet", "Distance (ls)"]:
                tk.Label(frame, text=key + ":", anchor="w", font=("Segoe UI", 11, "bold"), bg="#222", fg="#FFD700").grid(row=row, column=0, sticky="w", pady=2, padx=(0, 10))
                tk.Label(frame, text=detail_dict[key], anchor="w", font=("Segoe UI", 11), bg="#222", fg="#FFF").grid(row=row, column=1, sticky="ew", pady=2)
                row += 1
            tk.Label(frame, text="Services:", anchor="nw", font=("Segoe UI", 11, "bold"), bg="#222", fg="#FFD700").grid(row=row, column=0, sticky="nw", pady=(8, 2), padx=(0, 10))
            services_text = "\n".join(detail_dict["Services"]) if isinstance(detail_dict["Services"], list) else detail_dict["Services"]
            services_label = tk.Label(frame, text=services_text, anchor="nw", justify="left", font=("Segoe UI", 11), bg="#222", fg="#FFF", wraplength=320)
            services_label.grid(row=row, column=1, sticky="nsew", pady=(8, 2))
            def on_resize(event):
                new_wrap = max(200, event.width - 180)
                services_label.config(wraplength=new_wrap)
            popup.bind('<Configure>', on_resize)
            popup.update_idletasks()
            popup.geometry("")
            popup.transient(self.parent)
            popup.grab_set()
        self.stations_table.bind('<Double-1>', show_row_details)

        def copy_selected_rows(event=None):
            selected_rows = self.stations_table.get_selected_rows()
            if not selected_rows:
                return
            rows = []
            for row_index in selected_rows:
                values = self.stations_table.get_row_data(row_index)
                rows.append('\t'.join(str(v) for v in values))
            text = '\n'.join(rows)
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
        def on_right_click(event):
            row_index = self.stations_table.identify_row(event)
            if row_index is not None and row_index != -1:
                self.stations_table.select_row(row_index)
            menu = tk.Menu(self.parent, tearoff=0)
            menu.add_command(label="Copy selected", command=copy_selected_rows)
            menu.tk_popup(event.x_root, event.y_root)
        self.stations_table.bind('<Button-3>', on_right_click)

    def update_planetary_access(self, bodies):
        if not hasattr(self, 'bodies_table') or self.bodies_table is None:
            return
        try:
            if not self.bodies_table.winfo_exists():
                return
        except Exception:
            return
        try:
            self.bodies_table.set_sheet_data([])
        except Exception:
            pass
        if not bodies or not isinstance(bodies, list) or len(bodies) == 0:
            self._bodies_roworder = []
            return
        def safe(val):
            return val if val is not None else "-"
        def body_sort_key(b):
            t = b.get('type', '').lower()
            if 'star' in t:
                return (0, b.get('id', 0))
            elif b.get('isPlanet', False):
                return (1, b.get('orbitalOrder', b.get('id', 0)))
            else:
                return (2, b.get('orbitalOrder', b.get('id', 0)))
        bodies_sorted = sorted(bodies, key=body_sort_key)
        self._bodies_roworder = []
        for b in bodies_sorted:
            row = (
                safe(b.get('name', '-')),
                safe(b.get('type', '-')),
                safe(f"{b.get('gravity', 0):.2f}" if b.get('gravity') is not None else "-"),
                "Yes" if b.get('isLandable') else "No",
                safe(b.get('atmosphereType', '-')),
                safe(b.get('subType', '-'))
            )
            bodies_data = list(self.bodies_table.get_sheet_data())
            bodies_data.append(row)
            self.bodies_table.set_sheet_data(bodies_data)
            self.bodies_table.auto_resize_columns()
            self._bodies_roworder.append(row)
        self._bodies_data = bodies_sorted

    def update_stations(self, stations):
        if not hasattr(self, 'stations_table') or self.stations_table is None:
            return
        try:
            if not self.stations_table.winfo_exists():
                return
        except Exception:
            return
        try:
            self.stations_table.set_sheet_data([])
        except Exception:
            pass
        if not stations or not isinstance(stations, list):
            self._stations_roworder = []
            self._stations_data = []
            return
        def safe(val):
            return val if val is not None else "-"
        self._stations_roworder = []
        rows = []
        for s in stations:
            planet = s.get('body', '-')
            if isinstance(planet, dict):
                planet = planet.get('name', '-')
            dist = s.get('distanceToArrival', '-')
            if isinstance(dist, (int, float)):
                dist = f"{dist:,.0f}"
            services = ', '.join(s.get('otherServices', [])) if s.get('otherServices') else '-'
            row = (
                safe(s.get('name', '-')),
                safe(s.get('type', '-')),
                safe(planet),
                safe(dist),
                services
            )
            rows.append(row)
            self._stations_roworder.append(row)
        self.stations_table.set_sheet_data(rows)
        self.stations_table.auto_resize_columns()
        self._stations_data = stations

    def _format_gmp_content(self, gmp_text):
        lines = [line.strip() for line in gmp_text.split('\n') if line.strip()]
        formatted_sections = []
        current_section = []
        current_type = 'paragraph'
        for line in lines[1:]:
            if line.startswith('Link :') or line.startswith('Link:'):
                if current_section:
                    formatted_sections.append((current_type, '\n'.join(current_section)))
                    current_section = []
                link_section = [f"🔗 {line}"]
                formatted_sections.append(('link', '\n'.join(link_section)))
                current_section = []
                current_type = 'paragraph'
                continue
            if (line.isupper() or
                line.endswith('?') or
                ':' in line and len(line.split(':')[0].split()) <= 5 or
                re.match(r'^[A-Z][^a-z]*:', line)):
                if current_section:
                    formatted_sections.append((current_type, '\n'.join(current_section)))
                    current_section = []
                formatted_sections.append(('header', f"📌 {line}"))
                current_section = []
                current_type = 'paragraph'
                continue
            if line.startswith('"') or '."' in line:
                if current_section:
                    formatted_sections.append((current_type, '\n'.join(current_section)))
                    current_section = []
                formatted_sections.append(('quote', f"💭 {line}"))
                current_section = []
                current_type = 'paragraph'
                continue
            if line:
                current_section.append(line)
        if current_section:
            formatted_sections.append((current_type, '\n'.join(current_section)))
        return formatted_sections

    def _create_formatted_gmp_text(self, sections):
        formatted_text = ""
        for section_type, content in sections:
            if section_type == 'header':
                formatted_text += f"\n{content}\n{'─' * 50}\n"
            elif section_type == 'link':
                formatted_text += f"{content}\n\n"
            elif section_type == 'quote':
                formatted_text += f"{content}\n\n"
            elif section_type == 'paragraph':
                sentences = re.split(r'(?<=[.!?])\s+', content)
                formatted_paragraph = '\n'.join(sentences)
                formatted_text += f"{formatted_paragraph}\n\n"
        return formatted_text.strip()

    def _format_gmp_markdown(self, text):
        import re
        lines = text.split('\n')
        result = []
        in_quote = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                result.append('')
                continue
            if stripped.startswith('![') or stripped.startswith('![IMAGE'):
                continue
            if stripped == '---':
                result.append('═' * 50)
                continue
            if stripped.startswith('> '):
                quote_text = stripped[2:]
                quote_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', quote_text)
                wrapped = []
                words = quote_text.split()
                current_line = '  │ '
                for word in words:
                    if len(current_line) + len(word) + 1 > 70:
                        wrapped.append(current_line)
                        current_line = '  │ ' + word
                    else:
                        current_line += ' ' + word if current_line != '  │ ' else word
                wrapped.append(current_line)
                result.extend(wrapped)
                result.append('  │')
                continue
            if re.match(r'^(TYPE|REGION):', stripped):
                result.append(f'  ★ {stripped}')
                result.append('')
                continue
            if stripped.startswith('*--') and stripped.endswith('*'):
                credit = stripped.strip('*').strip()
                result.append('')
                result.append(f'  ─── {credit} ───')
                result.append('')
                continue
            if stripped.startswith('*IMAGE CREDIT'):
                credit = stripped.replace('*IMAGE CREDIT:', '').replace('*', '').strip()
                result.append(f'  [Image: {credit}]')
                continue
            cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', stripped)
            cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
            cleaned = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', cleaned)
            if cleaned.strip():
                wrapped = []
                words = cleaned.split()
                current_line = ''
                for word in words:
                    if len(current_line) + len(word) + 1 > 70:
                        wrapped.append(current_line)
                        current_line = word
                    else:
                        current_line += ' ' + word if current_line else word
                if current_line:
                    wrapped.append(current_line)
                result.extend(wrapped)
                result.append('')
        return '\n'.join(result).strip()

    def update_gmp(self, gmp):
        if not hasattr(self, 'tab_gmp') or self.tab_gmp is None:
            return
        try:
            if not self.tab_gmp.winfo_exists():
                return
        except Exception:
            return
        colors = self.colors
        try:
            for child in self.tab_gmp.winfo_children():
                child.destroy()
        except Exception:
            pass
        gmp_frame = ctk.CTkFrame(self.tab_gmp, fg_color=colors['background'])
        gmp_frame.pack(fill="both", expand=True, padx=8, pady=8)
        gmp_frame.rowconfigure(0, weight=1)
        gmp_frame.columnconfigure(0, weight=1)
        row = 0
        if not gmp:
            label = ctk.CTkLabel(gmp_frame, text="No System History data.", text_color="#888", font=ctk.CTkFont(size=16), justify="left")
            label.grid(row=row, column=0, sticky="nw", padx=4, pady=4)
            self.gmp_info_label = label
            return
        if isinstance(gmp, str):
            formatted_text = self._format_gmp_markdown(gmp)
            custom_font = ctk.CTkFont(family="Consolas", size=14)
            text_box = ctk.CTkTextbox(gmp_frame, wrap="word", font=custom_font)
            text_box.insert("0.0", formatted_text)
            text_box.configure(state="disabled", text_color=colors['text'], fg_color=colors['frame'])
            text_box.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
            self.gmp_info_label = text_box
            return
        gmp_list = gmp if isinstance(gmp, list) else [gmp]
        if len(gmp_list) == 0:
            label = ctk.CTkLabel(gmp_frame, text="No System History data.", text_color="#888", font=ctk.CTkFont(size=16), justify="left")
            label.grid(row=row, column=0, sticky="nw", padx=4, pady=4)
            self.gmp_info_label = label
            return
        for idx, entry in enumerate(gmp_list):
            title = entry.get('name', '-')
            typ = entry.get('type', '-')
            desc = entry.get('description', '-')
            discoverer = entry.get('discoverer', None)
            link = entry.get('link', None)
            coords = entry.get('coordinates', None)
            edsm_id = entry.get('id', None)
            section_frame = ctk.CTkFrame(gmp_frame, fg_color=colors['frame'])
            section_frame.grid(row=row, column=0, sticky="ew", padx=0, pady=(8 if idx > 0 else 4, 0))
            section_row = 0
            title_label = ctk.CTkLabel(section_frame, text=f"{title}", font=ctk.CTkFont(size=20, weight="bold"), text_color=colors['accent'], anchor="w", justify="left")
            title_label.grid(row=section_row, column=0, sticky="w", padx=8, pady=(4, 0))
            section_row += 1
            type_label = ctk.CTkLabel(section_frame, text=f"Type: {typ}", font=ctk.CTkFont(size=16), text_color=colors['primary'], anchor="w", justify="left")
            type_label.grid(row=section_row, column=0, sticky="w", padx=16, pady=0)
            section_row += 1
            desc_label = ctk.CTkLabel(section_frame, text=f"{desc[:400]}" + ("..." if len(desc) > 400 else ""), font=ctk.CTkFont(size=16), text_color=colors['accent'], anchor="w", justify="left", wraplength=600)
            desc_label.grid(row=section_row, column=0, sticky="w", padx=16, pady=0)
            section_row += 1
            if discoverer:
                discoverer_label = ctk.CTkLabel(section_frame, text=f"Discoverer: {discoverer}", font=ctk.CTkFont(size=15), text_color="#FFD700", anchor="w", justify="left")
                discoverer_label.grid(row=section_row, column=0, sticky="w", padx=16, pady=0)
                section_row += 1
            if coords:
                coords_label = ctk.CTkLabel(section_frame, text=f"Coords: {coords}", font=ctk.CTkFont(size=15), text_color="#4FC3F7", anchor="w", justify="left")
                coords_label.grid(row=section_row, column=0, sticky="w", padx=16, pady=0)
                section_row += 1
            if link:
                link_label = ctk.CTkLabel(section_frame, text=f"Link: {link}", font=ctk.CTkFont(size=15, underline=True), text_color="#4FC3F7", anchor="w", justify="left", cursor="hand2")
                link_label.grid(row=section_row, column=0, sticky="w", padx=16, pady=(0, 8))
                def open_url(url=link):
                    webbrowser.open(url)
                link_label.bind("<Button-1>", lambda e, url=link: open_url(url))
                section_row += 1
            if edsm_id:
                id_label = ctk.CTkLabel(section_frame, text=f"EDSM ID: {edsm_id}", font=ctk.CTkFont(size=10), text_color="#888", anchor="w", justify="left")
                id_label.grid(row=section_row, column=0, sticky="w", padx=16, pady=0)
                section_row += 1
            row += 1
        self.gmp_info_label = gmp_frame

    def update_trivia(self, data):
        name = data.get('name', '-')
        info = data.get('information', {})
        permit = data.get('requirePermit', False)
        permit_name = data.get('permitName', None)
        pop = info.get('population', None)
        star_type = data.get('primaryStar', {}).get('type', None)
        bodies = data.get('bodies', [])
        trivia = []
        if name.lower() == 'sol':
            trivia.append("Sol is the only system with Earth in-game.")
            trivia.append("Permit is obtained via Federation rank.")
            trivia.append("Sol hosts iconic stations in ED history.")
        elif name.lower() == 'cubeo':
            trivia.append("Cubeo is the capital of the Prismatic Imperium.")
            trivia.append("Known for its beautiful blue star.")
        else:
            if permit:
                trivia.append(f"Permit required: {permit_name if permit_name else 'Yes'}.")
            if pop:
                trivia.append(f"Population: {pop:,}")
            if star_type:
                trivia.append(f"Primary star type: {star_type}")
            if bodies:
                trivia.append(f"{len([b for b in bodies if b.get('isPlanet', False)])} planets in this system.")
            if info.get('faction'):
                trivia.append(f"Controlled by: {info['faction']}")
            if not trivia:
                trivia.append(f"{name} is a notable system in Elite Dangerous.")
        self.trivia_label.configure(text="\n".join(trivia))
