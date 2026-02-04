import logging
from collections import defaultdict, Counter, deque
from edmrn.codex_translation import codex_translation
import customtkinter as ctk
import tkinter as tk
import webbrowser
import re
from edmrn.autocomplete_entry import AutocompleteEntry
from edmrn.edmrn_sheet import EDMRNSheet
import os
import json
import hashlib
from edmrn.config import Paths

class SystemInfoSection:
    def update_system_info(self, system_data):
        """Update System Info tab UI with new system_data."""
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
            
            # Move heavy calculations to background thread to prevent UI freeze
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

                    # Update UI back on main thread
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
                    import logging
                    logging.getLogger('SystemInfoSection').debug(f"[update_system_info] Background stats error: {e}")
            
            threading.Thread(target=_update_stats_background, daemon=True).start()
            
        except Exception as e:
            import logging
            logging.getLogger('SystemInfoSection').error(f"[update_system_info] Exception: {e}")

    @staticmethod
    def get_history_path():
        return os.path.join(os.path.dirname(Paths.get_backup_folder()), 'visited_systems_history.json')

    def _load_incomplete_exobio(self, system=None):
        import threading
        def read_history():
            try:
                history_path = self.get_history_path()
                if os.path.exists(history_path):
                    with open(history_path, 'r', encoding='utf-8') as f:
                        all_data = json.load(f)
                    if system and system in all_data:
                        result = all_data[system].get('exobio', [])
                    else:
                        result = []
                else:
                    result = []
            except Exception:
                result = []
            try:
                if hasattr(self, 'parent') and hasattr(self.parent, 'after') and self.parent.winfo_exists():
                    self.parent.after(0, lambda: setattr(self, '_incomplete_exobio', result))
                else:
                    self._incomplete_exobio = result
            except Exception:
                self._incomplete_exobio = result
        threading.Thread(target=read_history, daemon=True).start()

    def _save_incomplete_exobio(self, system=None):
        try:
            history_path = self.get_history_path()
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            if os.path.exists(history_path):
                with open(history_path, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            else:
                all_data = {}
            if system:
                if system not in all_data:
                    all_data[system] = {}
                all_data[system]['exobio'] = self._incomplete_exobio
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def __init__(self, parent, theme_manager, fetch_callback, tab_log, app=None):
        self.theme_manager = theme_manager
        self.colors = theme_manager.get_theme_colors()
        self.parent = parent
        self.app = app if app is not None else getattr(parent, 'app', None)
        self.fetch_callback = fetch_callback
        self.tab_log = tab_log
        import threading
        self._journal_events = []
        self._journal_seen_hashes = set()
        self._journal_seen_order = deque(maxlen=200000)
        self._journal_cache_ready = False
        self._journal_cache_lock = threading.Lock()
        self._journal_latest_file = None
        self._journal_latest_size = 0
        self._prime_journal_cache_async()
        self._build_ui()
        self.update_planetary_access([])
        self.update_stations([])
        self.update_gmp(None)
        self.update_log({})
        self._load_incomplete_exobio()
        try:
            import queue
            self._bio_update_queue = queue.Queue()
        except Exception:
            self._bio_update_queue = None
        self._start_bio_update_poller()

    def _start_bio_update_poller(self):
        try:
            if hasattr(self, 'bio_card') and self.bio_card:
                self.bio_card.after(100, self._process_bio_update_queue)
        except Exception:
            pass

    def _process_bio_update_queue(self):
        try:
            if not hasattr(self, '_bio_update_queue') or self._bio_update_queue is None:
                return
            while True:
                try:
                    exobio_samples, system, body = self._bio_update_queue.get_nowait()
                except Exception:
                    break
                try:
                    self.update_bio_summary(exobio_samples, system, body)
                except Exception:
                    pass
        finally:
            try:
                self._bio_update_scheduled = False
            except Exception:
                pass
            try:
                if hasattr(self, 'bio_card') and self.bio_card:
                    self.bio_card.after(100, self._process_bio_update_queue)
            except Exception:
                pass

    def _enqueue_bio_update(self, exobio_samples, system=None, body=None):
        try:
            if not hasattr(self, '_bio_update_queue') or self._bio_update_queue is None:
                import queue
                self._bio_update_queue = queue.Queue()
            self._bio_update_queue.put((exobio_samples, system, body))
            if not hasattr(self, '_bio_update_scheduled'):
                self._bio_update_scheduled = False
            if not self._bio_update_scheduled:
                self._bio_update_scheduled = True
                try:
                    if hasattr(self, 'parent') and hasattr(self.parent, 'after'):
                        self.parent.after(0, self._process_bio_update_queue)
                    elif hasattr(self, 'bio_card') and self.bio_card:
                        self.bio_card.after(0, self._process_bio_update_queue)
                except Exception:
                    self._bio_update_scheduled = False
        except Exception:
            pass

    def add_onfoot_bio_sample(self, genus, body=None, system=None, geo=False, completed=False):
        import logging
        logging.getLogger('SystemInfoSection').info(f"[DEBUG] add_onfoot_bio_sample called: genus={genus}, body={body}, system={system}, geo={geo}, completed={completed}")
        if not hasattr(self, '_onfoot_bio_samples'):
            self._onfoot_bio_samples = []
        if not hasattr(self, '_last_body'):
            self._last_body = None
        
        if body is not None and self._last_body is not None and body != self._last_body:
            logging.getLogger('SystemInfoSection').info(f"[DEBUG] Body changed from {self._last_body} to {body}, resetting samples")
            self._onfoot_bio_samples = []
        
        if body is not None:
            self._last_body = body
        
        if genus:
            self._onfoot_bio_samples.append(genus)
            if body and system:
                history_path = self.get_history_path()
                os.makedirs(os.path.dirname(history_path), exist_ok=True)
                try:
                    if os.path.exists(history_path):
                        with open(history_path, 'r', encoding='utf-8') as f:
                            all_data = json.load(f)
                    else:
                        all_data = {}
                    if system not in all_data:
                        all_data[system] = {}
                    all_data[system]['body'] = body
                    all_data[system]['type'] = 'geo' if geo else 'bio'
                    all_data[system]['genus'] = genus
                    all_data[system]['completed'] = completed
                    for k in ('first_visit','last_visit','visit_count','source_files'):
                        if k not in all_data[system]:
                            if k == 'source_files':
                                all_data[system][k] = []
                            elif k == 'visit_count':
                                all_data[system][k] = 1
                            else:
                                import datetime
                                all_data[system][k] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    with open(history_path, 'w', encoding='utf-8') as f:
                        json.dump(all_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    import logging
                    logging.getLogger('SystemInfoSection').warning(f"Could not add exobio record to json: {e}")
                try:
                    from edmrn.visit_history import get_history_manager
                    history_manager = get_history_manager()
                    visit_info = history_manager.get_visit_info(system)
                    if visit_info is not None:
                        if 'bodies' not in visit_info:
                            visit_info['bodies'] = {}
                        if body not in visit_info['bodies']:
                            visit_info['bodies'][body] = {'exobio': [], 'geo': []}
                        key = 'geo' if geo else 'exobio'
                        genus_list = visit_info['bodies'][body][key]
                        found_genus = False
                        for g in genus_list:
                            if g['genus'] == genus:
                                g['completed'] = completed
                                found_genus = True
                                break
                        if not found_genus:
                            genus_list.append({'genus': genus, 'completed': completed})
                        history_manager._save_history()
                except Exception as e:
                    import logging
                    logging.getLogger('SystemInfoSection').warning(f"Could not add exobio/geo record to central source: {e}")
            exobio_samples = list(getattr(self, '_last_edsm_exobio_samples', []))
            exobio_samples += self._onfoot_bio_samples
            self._enqueue_bio_update(exobio_samples, system, body)
        try:
            history_path = self.get_history_path()
            if os.path.exists(history_path):
                with open(history_path, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
                if system and system in all_data:
                    rec = all_data[system]
                    self._incomplete_exobio = [{
                        'system': system,
                        'body': rec.get('body'),
                        'type': rec.get('type'),
                        'genus': rec.get('genus'),
                        'completed': rec.get('completed', False)
                    }]
                else:
                    self._incomplete_exobio = []
            else:
                self._incomplete_exobio = []
        except Exception:
            self._incomplete_exobio = []

    def update_bio_summary(self, exobio_samples, system=None, body=None):
        import logging
        import threading
        try:
            if threading.current_thread() is not threading.main_thread():
                if getattr(self, '_bio_summary_scheduled', False):
                    self._pending_bio_summary = (exobio_samples, system, body)
                    return
                self._pending_bio_summary = (exobio_samples, system, body)
                self._bio_summary_scheduled = True
                def _run_on_main():
                    try:
                        self._bio_summary_scheduled = False
                        args = getattr(self, '_pending_bio_summary', (exobio_samples, system, body))
                        self.update_bio_summary(*args)
                    except Exception:
                        self._bio_summary_scheduled = False
                try:
                    if hasattr(self, 'bio_card') and self.bio_card:
                        self.bio_card.after(0, _run_on_main)
                except Exception:
                    pass
                return
        except Exception:
            pass
        try:
            if not hasattr(self, 'bio_card') or not hasattr(self, 'bio_summary_label'):
                return
            children = []
            try:
                children = list(self.bio_card.winfo_children())
            except Exception:
                return
            for widget in children:
                if widget not in (self.bio_title_label, self.bio_summary_label):
                    try:
                        widget.destroy()
                    except Exception:
                        pass
            logging.getLogger('SystemInfoSection').info(f"[DEBUG] update_bio_summary called: exobio_samples={exobio_samples}, system={system}, body={body}")
            def normalize_key(s):
                if not isinstance(s, str):
                    return str(s)
                key = s.strip()
                if not key.endswith(';'):
                    key += ';'
                if key in codex_translation:
                    return codex_translation[key]
                elif key.startswith('$') and key[1:] in codex_translation:
                    return codex_translation[key[1:]]
                elif not key.startswith('$') and ('$' + key) in codex_translation:
                    return codex_translation['$' + key]
                else:
                    try:
                        with open('unknown_codex_keys.log', 'a', encoding='utf-8') as f:
                            f.write(f"{key}\n")
                    except Exception:
                        pass
                    return key
            incomplete_lines = []
            incomplete_exobio = getattr(self, '_incomplete_exobio', [])
            if incomplete_exobio is None:
                incomplete_exobio = []
            if isinstance(incomplete_exobio, dict):
                incomplete_exobio = [incomplete_exobio]
            if incomplete_exobio:
                for rec in incomplete_exobio:
                    if not isinstance(rec, dict):
                        continue
                    if (system is None or rec.get('system') == system) and (body is None or rec.get('body') == body):
                        if not rec.get('completed'):
                            continue
                        status = 'COMPLETED'
                        genus_code = rec.get('genus','?')
                        genus_name = codex_translation.get(genus_code, genus_code)
                        incomplete_lines.append(f"[{status}] {rec.get('system','?')} / {rec.get('body','?')}: {genus_name}")
            normalized_samples = []
            if exobio_samples is None:
                exobio_samples = []
            for s in exobio_samples:
                genus = s.get('genus') if isinstance(s, dict) else s
                if genus:
                    normalized_samples.append(normalize_key(genus))
            counts = Counter(normalized_samples)
            species_list = [(species, min(counts[species], 3)) for species in counts]
            species_list.sort(key=lambda x: (-(x[1] >= 3), x[0].lower()))
            try:
                state_hash = hashlib.md5(json.dumps(species_list, sort_keys=True).encode('utf-8')).hexdigest()
            except Exception:
                state_hash = None
            try:
                children_now = list(self.bio_card.winfo_children()) if hasattr(self, 'bio_card') else []
            except Exception:
                children_now = []
            has_rendered_widgets = len([w for w in children_now if w not in (self.bio_title_label, self.bio_summary_label)]) > 0
            if hasattr(self, '_last_bio_summary_hash') and self._last_bio_summary_hash == state_hash and has_rendered_widgets:
                return
            if getattr(self, 'app', None) is not None and hasattr(self.app, '_overlay_exobio_species'):
                try:
                    self.app._overlay_exobio_species = species_list
                except Exception:
                    pass
                if hasattr(self.app, 'overlay_enabled') and self.app.overlay_enabled and hasattr(self.app, 'overlay_manager') and hasattr(self.app.overlay_manager, '_instance') and self.app.overlay_manager._instance:
                    def safe_update_async():
                        """Run overlay update in background to prevent UI blocking"""
                        def _do_update():
                            try:
                                import signal
                                # Set a timeout to prevent hanging
                                self.app.overlay_manager._instance.update_display()
                            except Exception:
                                pass
                        threading.Thread(target=_do_update, daemon=True).start()
                    
                    if threading.current_thread() is threading.main_thread():
                        safe_update_async()
                    else:
                        try:
                            self.app.root.after(0, safe_update_async)
                        except Exception:
                            pass
            self._last_bio_summary_hash = state_hash
            summary_text = "\n".join(incomplete_lines) + ("\n" if incomplete_lines else "")
            try:
                self.bio_summary_label.configure(text=summary_text)
            except Exception:
                pass
            
            if not species_list and not incomplete_lines:
                try:
                    self.bio_summary_label.configure(text="-")
                except Exception:
                    pass
                return
            
            try:
                row_frame = tk.Frame(self.bio_card, bg=self.colors['background'])
                row_frame.pack(anchor="w", padx=12, pady=(0, 8), fill="x")
            except Exception:
                return
            
            use_canvas = len(species_list) <= 5
            logging.getLogger('SystemInfoSection').info(f"[DEBUG] Rendering {len(species_list)} species, use_canvas={use_canvas}")
            
            def make_tooltip(widget, text):
                if not use_canvas:
                    return
                delay_ms = 200
                tooltip_id = {'after': None}
                def show_tooltip():
                    try:
                        if not widget.winfo_exists():
                            return
                        x, y = widget.winfo_pointerxy()
                        if widget.winfo_containing(x, y) != widget:
                            return
                        if hasattr(self, '_bio_tooltip') and self._bio_tooltip:
                            try:
                                self._bio_tooltip.destroy()
                            except Exception:
                                pass
                        self._bio_tooltip = tk.Toplevel(widget)
                        self._bio_tooltip.wm_overrideredirect(True)
                        wx = widget.winfo_rootx() + 20
                        wy = widget.winfo_rooty() + 20
                        self._bio_tooltip.wm_geometry(f"+{wx}+{wy}")
                        label = tk.Label(self._bio_tooltip, text=text, bg="#222", fg="#FFD700", font=("Segoe UI", 9), relief="solid", borderwidth=1)
                        label.pack()
                        self._bio_tooltip_widget = widget
                    except Exception:
                        pass
                def on_enter(e):
                    try:
                        if tooltip_id['after'] and widget.winfo_exists():
                            widget.after_cancel(tooltip_id['after'])
                    except Exception:
                        pass
                    try:
                        if widget.winfo_exists():
                            tooltip_id['after'] = widget.after(delay_ms, show_tooltip)
                    except Exception:
                        pass
                def on_leave(e):
                    try:
                        if tooltip_id['after'] and widget.winfo_exists():
                            widget.after_cancel(tooltip_id['after'])
                            tooltip_id['after'] = None
                    except Exception:
                        pass
                    try:
                        if hasattr(self, '_bio_tooltip') and self._bio_tooltip:
                            self._bio_tooltip.destroy()
                            self._bio_tooltip = None
                            self._bio_tooltip_widget = None
                    except Exception:
                        pass
                try:
                    widget.bind("<Enter>", on_enter)
                    widget.bind("<Leave>", on_leave)
                except Exception:
                    pass
            
            for i, (species, count) in enumerate(species_list):
                try:
                    row = tk.Frame(row_frame, bg=self.colors['background'])
                    row.pack(anchor="w", pady=2, fill="x")
                except Exception:
                    continue
                
                try:
                    if count >= 3:
                        icon = "\U0001F7E2"
                        icon_text = "Complete"
                    elif count == 2:
                        icon = "\U0001F7E1"
                        icon_text = "2/3 samples"
                    elif count == 1:
                        icon = "\U0001F7E0"
                        icon_text = "1/3 samples"
                    else:
                        icon = "\U0001F534"
                        icon_text = "Incomplete"
                    icon_label = tk.Label(row, text=icon, font=("Segoe UI", 13), bg=self.colors['background'], fg="#4FC3F7")
                    icon_label.pack(side="left", padx=(0, 4))
                    make_tooltip(icon_label, icon_text)
                except Exception:
                    pass
                
                try:
                    if use_canvas:
                        name_label = tk.Label(row, text=species, font=("Segoe UI", 12, "bold"), bg=self.colors['background'], fg=self.colors['accent'])
                    else:
                        name_label = tk.Label(row, text=f"{species} [{count}/3]", font=("Segoe UI", 11), bg=self.colors['background'], fg=self.colors['accent'])
                    name_label.pack(side="left", padx=(0, 8))
                except Exception:
                    pass
                
                if use_canvas:
                    for j in range(3):
                        try:
                            color = "#4FC3F7" if j < count and count < 3 else ("#A3FFB0" if j < count else "#888")
                            circle = tk.Canvas(row, width=16, height=16, bg=self.colors['background'], highlightthickness=0)
                            circle.create_oval(2, 2, 14, 14, fill=color, outline="#333")
                            circle.pack(side="left", padx=1)
                            make_tooltip(circle, f"Sample {j+1} {'scanned' if j < count else 'not scanned'}")
                        except Exception:
                            pass
                
                try:
                    wiki_url = f"https://elite-dangerous.fandom.com/wiki/{species.replace(' ', '_')}"
                    def open_link(url=wiki_url):
                        try:
                            webbrowser.open(url)
                        except Exception:
                            pass
                    link_btn = tk.Label(row, text="🔗", font=("Segoe UI", 12), fg="#4FC3F7", bg=self.colors['background'], cursor="hand2")
                    link_btn.pack(side="left", padx=(6, 0))
                    if use_canvas:
                        make_tooltip(link_btn, "Open wiki page")
                    link_btn.bind("<Button-1>", lambda e, url=wiki_url: open_link(url))
                except Exception:
                    pass
        except Exception as e:
            import logging
            logging.getLogger('SystemInfoSection').error(f"update_bio_summary crash-proofed: {e}")
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

        self.plot_btn = ctk.CTkButton(name_row, text="Plot route to -", command=self._plot_route, width=180)
        self.theme_manager.apply_button_theme(self.plot_btn, "primary")
        self.plot_btn.grid(row=0, column=2, sticky="e")

        self.system_info_status = ctk.CTkLabel(self.parent, text="Enter a system name and click Fetch Data", text_color=colors['text'], font=ctk.CTkFont(size=11))

        self.tabview = ctk.CTkTabview(self.parent, fg_color=colors['background'], border_color=colors['border'], border_width=1)
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.tab_overview = self.tabview.add("Overview")
        self.tab_bodies = self.tabview.add("Bodies")
        self.tab_stations = self.tabview.add("Stations")
        self.tab_gmp = self.tabview.add("Galactic Notes")
        name_row.pack(fill="x", padx=20, pady=(8, 4))
        self.system_info_status.pack(anchor="w", padx=24, pady=(0, 6))

        overview_frame = ctk.CTkFrame(self.tab_overview, fg_color=colors['background'])
        overview_frame.pack(fill="both", expand=True, padx=8, pady=8)
        for i in range(3):
            overview_frame.columnconfigure(i, weight=1)
        overview_frame.rowconfigure(0, weight=1)

        left_card = ctk.CTkFrame(overview_frame, fg_color=colors['background'], border_width=1, border_color=colors['border'])
        left_card.grid(row=0, column=0, sticky="nsew", padx=(8,8), pady=8)
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
            l = ctk.CTkLabel(info_grid, text=lbl+":", font=ctk.CTkFont(size=13), text_color=colors['accent'])
            l.grid(row=i, column=0, sticky="w", padx=(0, 8), pady=2)
            v = ctk.CTkLabel(info_grid, text="-", font=ctk.CTkFont(size=13, weight="bold"), text_color=colors['accent'])
            v.grid(row=i, column=1, sticky="w", pady=2)
            self.info_values[key] = v
        self.edsm_url = None
        def open_edsm():
            if self.edsm_url:
                import webbrowser
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
            l = ctk.CTkLabel(stats_grid, text=lbl+":", font=ctk.CTkFont(size=13), text_color=colors['accent'])
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
        bodies_filter_entry.grid(row=0, column=0, columnspan=2, sticky="n", pady=(0,8))
        self.bodies_table = EDMRNSheet(
            bodies_frame,
            data=[],
            headers=["Name","Type","Gravity","Landable","Atmosphere","Subtype"],
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
                name = b.get('name','-')
                type_ = b.get('type','-')
                gravity = f"{b.get('gravity',0):.2f}" if b.get('gravity') is not None else "-"
                landable = "Yes" if b.get('isLandable') else "No"
                atmosphere = b.get('atmosphereType','-')
                subtype = b.get('subType','-')
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
                tk.Label(frame, text=key+":", anchor="w", font=("Segoe UI", 11, "bold"), bg="#222", fg="#FFD700").grid(row=row, column=0, sticky="w", pady=2, padx=(0,10))
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
        filter_entry.grid(row=0, column=0, columnspan=2, sticky="n", pady=(0,8))
        self.stations_table = EDMRNSheet(
            stations_frame,
            data=[],
            headers=["Name","Type","Planet","Distance (ls)","Services"],
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
                name = s.get('name','-')
                type_ = s.get('type','-')
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
                tk.Label(frame, text=key+":", anchor="w", font=("Segoe UI", 11, "bold"), bg="#222", fg="#FFD700").grid(row=row, column=0, sticky="w", pady=2, padx=(0,10))
                tk.Label(frame, text=detail_dict[key], anchor="w", font=("Segoe UI", 11), bg="#222", fg="#FFF").grid(row=row, column=1, sticky="ew", pady=2)
                row += 1
            tk.Label(frame, text="Services:", anchor="nw", font=("Segoe UI", 11, "bold"), bg="#222", fg="#FFD700").grid(row=row, column=0, sticky="nw", pady=(8,2), padx=(0,10))
            services_text = "\n".join(detail_dict["Services"]) if isinstance(detail_dict["Services"], list) else detail_dict["Services"]
            services_label = tk.Label(frame, text=services_text, anchor="nw", justify="left", font=("Segoe UI", 11), bg="#222", fg="#FFF", wraplength=320)
            services_label.grid(row=row, column=1, sticky="nsew", pady=(8,2))
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

    def _prime_journal_cache_async(self):
        import threading
        if getattr(self, '_journal_cache_thread', None) and self._journal_cache_thread.is_alive():
            return
        self._journal_cache_thread = threading.Thread(target=self._prime_journal_cache, daemon=True)
        self._journal_cache_thread.start()

    def _track_seen_journal_line(self, line):
        try:
            h = hashlib.md5(line.encode('utf-8', errors='ignore')).hexdigest()
        except Exception:
            return False
        if h in self._journal_seen_hashes:
            return False
        self._journal_seen_hashes.add(h)
        if len(self._journal_seen_order) >= 200000:
            old = self._journal_seen_order[0]
            try:
                self._journal_seen_hashes.discard(old)
            except Exception:
                pass
        self._journal_seen_order.append(h)
        return True

    def _prime_journal_cache(self):
        import os, glob, json
        journal_dir = os.path.join(os.path.expanduser('~'), 'Saved Games', 'Frontier Developments', 'Elite Dangerous')
        pattern = os.path.join(journal_dir, 'Journal.*.log')
        files = sorted(glob.glob(pattern), key=os.path.getmtime)
        events = []
        current_tracking_system = None
        try:
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '"event"' not in line:
                                continue
                            if not self._track_seen_journal_line(line):
                                continue
                            try:
                                data = json.loads(line)
                                event_name = data.get('event')
                                if event_name in ('FSDJump', 'Location', 'CarrierJump'):
                                    current_tracking_system = data.get('StarSystem')
                                if not data.get('StarSystem') and current_tracking_system:
                                    data['StarSystem'] = current_tracking_system
                                events.append(data)
                            except Exception:
                                continue
                except Exception:
                    continue
        finally:
            try:
                if files:
                    newest = files[-1]
                    self._journal_latest_file = newest
                    try:
                        self._journal_latest_size = os.path.getsize(newest)
                    except Exception:
                        self._journal_latest_size = 0
                with self._journal_cache_lock:
                    self._journal_events = events
                    self._journal_cache_ready = True
            except Exception:
                pass

    def _tail_lines(self, file_path, n=10, chunk_size=4096):
        lines = []
        try:
            with open(file_path, 'rb') as f:
                f.seek(0, os.SEEK_END)
                end = f.tell()
                buf = b''
                while end > 0 and len(lines) <= n:
                    read_size = min(chunk_size, end)
                    end -= read_size
                    f.seek(end)
                    buf = f.read(read_size) + buf
                    lines = buf.splitlines()
                tail = lines[-n:]
            return [ln.decode('utf-8', errors='ignore') for ln in tail]
        except Exception:
            return []

    def _refresh_latest_journal_tail(self):
        import os, glob, json
        journal_dir = os.path.join(os.path.expanduser('~'), 'Saved Games', 'Frontier Developments', 'Elite Dangerous')
        pattern = os.path.join(journal_dir, 'Journal.*.log')
        files = sorted(glob.glob(pattern), key=os.path.getmtime)
        if not files:
            return
        newest = files[-1]
        try:
            newest_size = os.path.getsize(newest)
        except Exception:
            newest_size = 0
        if newest != self._journal_latest_file or newest_size != self._journal_latest_size:
            tail_lines = self._tail_lines(newest, n=100)
            new_events = []
            current_tracking_system = None
            try:
                with self._journal_cache_lock:
                    for evt in reversed(self._journal_events):
                        if evt.get('event') in ('FSDJump', 'Location', 'CarrierJump'):
                            current_tracking_system = evt.get('StarSystem')
                            break
            except Exception:
                pass
            for line in tail_lines:
                if '"event"' not in line:
                    continue
                if not self._track_seen_journal_line(line):
                    continue
                try:
                    data = json.loads(line)
                    event_name = data.get('event')
                    if event_name in ('FSDJump', 'Location', 'CarrierJump'):
                        current_tracking_system = data.get('StarSystem')
                    if not data.get('StarSystem') and current_tracking_system:
                        data['StarSystem'] = current_tracking_system
                    new_events.append(data)
                except Exception:
                    continue
            if new_events:
                try:
                    with self._journal_cache_lock:
                        self._journal_events.extend(new_events)
                except Exception:
                    pass
            self._journal_latest_file = newest
            self._journal_latest_size = newest_size

    def _parse_log_files(self, current_system):
        if not getattr(self, '_journal_cache_ready', False):
            self._prime_journal_cache_async()
            import os, glob, json
            table_rows = []
            all_keys = set()
            body_events = defaultdict(list)
            journal_dir = os.path.join(os.path.expanduser('~'), 'Saved Games', 'Frontier Developments', 'Elite Dangerous')
            pattern = os.path.join(journal_dir, 'Journal.*.log')
            files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)[:10]
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '"event"' not in line:
                                continue
                            try:
                                data = json.loads(line)
                                all_keys.update(data.keys())
                                body_name = data.get('BodyName')
                                if body_name:
                                    try:
                                        skip_body = False
                                        if isinstance(body_name, str):
                                            body_lower = body_name.lower()
                                            if 'belt' in body_lower or 'cluster' in body_lower or 'ring' in body_lower:
                                                skip_body = True
                                            if not skip_body:
                                                clean_name = body_name
                                                if current_system and isinstance(current_system, str) and body_name.startswith(current_system):
                                                    clean_name = body_name[len(current_system):].strip()
                                                if clean_name:
                                                    if len(clean_name) == 1:
                                                        skip_body = True
                                                    if not skip_body:
                                                        try:
                                                            float(clean_name)
                                                            skip_body = True
                                                        except (ValueError, TypeError):
                                                            pass
                                        if skip_body:
                                            continue
                                    except Exception:
                                        pass
                                    ts = data.get('timestamp') or data.get('Timestamp') or data.get('Time') or data.get('time')
                                    data['Timestamp'] = ts
                                    body_events[body_name].append(data)
                            except Exception:
                                continue
                except Exception:
                    continue
            all_keys = sorted(list(all_keys | {'Timestamp', 'StarSystem', 'BodyName', 'Body'}))
            return all_keys, body_events
        try:
            self._refresh_latest_journal_tail()
        except Exception:
            pass
        try:
            with self._journal_cache_lock:
                events = list(self._journal_events)
        except Exception:
            events = []
        table_rows = []
        all_keys = set()
        body_events = defaultdict(list)
        for data in events:
            try:
                if not isinstance(data, dict):
                    continue
                data = dict(data)
                all_keys.update(data.keys())
                body_name = data.get('BodyName')
                if body_name:
                    try:
                        skip_body = False
                        if isinstance(body_name, str):
                            body_lower = body_name.lower()
                            if 'belt' in body_lower or 'cluster' in body_lower or 'ring' in body_lower:
                                skip_body = True
                            if not skip_body:
                                clean_name = body_name
                                if current_system and isinstance(current_system, str) and body_name.startswith(current_system):
                                    clean_name = body_name[len(current_system):].strip()
                                if clean_name:
                                    if len(clean_name) == 1:
                                        skip_body = True
                                    if not skip_body:
                                        try:
                                            float(clean_name)
                                            skip_body = True
                                        except (ValueError, TypeError):
                                            pass
                        if skip_body:
                            continue
                    except Exception:
                        pass
                    ts = data.get('timestamp') or data.get('Timestamp') or data.get('Time') or data.get('time')
                    data['Timestamp'] = ts
                    body_events[body_name].append(data)
            except Exception:
                continue
        all_keys = sorted(list(all_keys | {'Timestamp', 'StarSystem', 'BodyName', 'Body'}))
        return all_keys, body_events

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
                safe(b.get('name','-')),
                safe(b.get('type','-')),
                safe(f"{b.get('gravity',0):.2f}" if b.get('gravity') is not None else "-"),
                "Yes" if b.get('isLandable') else "No",
                safe(b.get('atmosphereType','-')),
                safe(b.get('subType','-'))
            )
            bodies_data = list(self.bodies_table.get_sheet_data())
            bodies_data.append(row)
            self.bodies_table.set_sheet_data(bodies_data)
            self.bodies_table.auto_resize_columns()
            self._bodies_roworder.append(row)
        self._bodies_data = bodies_sorted
        def restore_bodies_order():
            try:
                self.bodies_table.set_sheet_data([row for row in self._bodies_roworder])
                self.bodies_table.auto_resize_columns()
            except Exception:
                pass

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
                safe(s.get('name','-')),
                safe(s.get('type','-')),
                safe(planet),
                safe(dist),
                services
            )
            rows.append(row)
            self._stations_roworder.append(row)
        self.stations_table.set_sheet_data(rows)
        self.stations_table.auto_resize_columns()
        self._stations_data = stations
        def restore_stations_order():
            try:
                self.stations_table.set_sheet_data([row for row in self._stations_roworder])
                self.stations_table.auto_resize_columns()
            except Exception:
                pass

    def _format_gmp_content(self, gmp_text):
        """Categorizes and formats GMP text"""
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
        """Creates formatted text from sections"""
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
            label = ctk.CTkLabel(gmp_frame, text="No Galactic Notes data.", text_color="#888", font=ctk.CTkFont(size=16), justify="left")
            label.grid(row=row, column=0, sticky="nw", padx=4, pady=4)
            self.gmp_info_label = label
            return
        if isinstance(gmp, str):
            sections = self._format_gmp_content(gmp)
            formatted_text = ""
            for section_type, content in sections:
                if section_type == 'header':
                    formatted_text += f"\n{content.replace('📌 ', '').upper()}\n{'-'*40}\n"
                elif section_type == 'paragraph':
                    formatted_text += f"{content}\n\n"
            custom_font = ctk.CTkFont(family="Calibri", size=16)
            text_box = ctk.CTkTextbox(gmp_frame, wrap="word", font=custom_font)
            text_box.insert("0.0", formatted_text.strip())
            text_box.configure(state="disabled", text_color=colors['primary'])
            text_box.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
            self.gmp_info_label = text_box
            return
        gmp_list = gmp if isinstance(gmp, list) else [gmp]
        if len(gmp_list) == 0:
            label = ctk.CTkLabel(gmp_frame, text="No Galactic Notes data.", text_color="#888", font=ctk.CTkFont(size=16), justify="left")
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
            section_frame.grid(row=row, column=0, sticky="ew", padx=0, pady=(8 if idx>0 else 4, 0))
            section_row = 0
            title_label = ctk.CTkLabel(section_frame, text=f"{title}", font=ctk.CTkFont(size=20, weight="bold"), text_color=colors['accent'], anchor="w", justify="left")
            title_label.grid(row=section_row, column=0, sticky="w", padx=8, pady=(4, 0))
            section_row += 1
            type_label = ctk.CTkLabel(section_frame, text=f"Type: {typ}", font=ctk.CTkFont(size=16), text_color=colors['primary'], anchor="w", justify="left")
            type_label.grid(row=section_row, column=0, sticky="w", padx=16, pady=0)
            section_row += 1
            desc_label = ctk.CTkLabel(section_frame, text=f"{desc[:400]}" + ("..." if len(desc)>400 else ""), font=ctk.CTkFont(size=16), text_color=colors['accent'], anchor="w", justify="left", wraplength=600)
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
                link_label.grid(row=section_row, column=0, sticky="w", padx=16, pady=(0,8))
                def open_url(url=link):
                    import webbrowser
                    webbrowser.open(url)
                link_label.bind("<Button-1>", lambda e, url=link: open_url(url))
                section_row += 1
            if edsm_id:
                id_label = ctk.CTkLabel(section_frame, text=f"EDSM ID: {edsm_id}", font=ctk.CTkFont(size=10), text_color="#888", anchor="w", justify="left")
                id_label.grid(row=section_row, column=0, sticky="w", padx=16, pady=0)
                section_row += 1
            row += 1
        self.gmp_info_label = gmp_frame

    def update_log(self, system_data, _preparsed=None):
        try:
            import threading
            if threading.current_thread() is not threading.main_thread():
                try:
                    if hasattr(self, 'parent') and self.parent and self.parent.winfo_exists():
                        self.parent.after(0, lambda: self.update_log(system_data, _preparsed=_preparsed))
                except Exception:
                    pass
                return
            bodies_table = getattr(self, 'bodies_table', None)
            stations_table = getattr(self, 'stations_table', None)
            safe_bodies = bodies_table and hasattr(bodies_table, 'winfo_exists') and bodies_table.winfo_exists()
            safe_stations = stations_table and hasattr(stations_table, 'winfo_exists') and stations_table.winfo_exists()
            if not (safe_bodies or safe_stations):
                return
            from edmrn.column_display_names import COLUMN_DISPLAY_NAMES
            from edmrn.config import AppConfig
            
            current_system = None
            if isinstance(system_data, dict):
                current_system = system_data.get('name') or system_data.get('StarSystem')
            if not current_system and hasattr(self, 'system_info_entry'):
                try:
                    entry = getattr(self.system_info_entry, 'entry', self.system_info_entry)
                    if hasattr(entry, 'get'):
                        current_system = entry.get().strip()
                except Exception:
                    pass
            
            if _preparsed is None and threading.current_thread() is threading.main_thread():
                if getattr(self, '_log_update_in_progress', False):
                    self._pending_log_update = system_data
                    return
                self._log_update_in_progress = True
                self._pending_log_update = None
                def _worker():
                    try:
                        parsed_all_keys, parsed_body_events = self._parse_log_files(current_system)
                    except Exception:
                        parsed_all_keys, parsed_body_events = [], {}
                    def _apply():
                        try:
                            self.update_log(system_data, _preparsed=(parsed_all_keys, parsed_body_events))
                        finally:
                            self._log_update_in_progress = False
                            pending = getattr(self, '_pending_log_update', None)
                            self._pending_log_update = None
                            if pending is not None:
                                self.update_log(pending)
                    try:
                        if hasattr(self, 'parent') and self.parent and self.parent.winfo_exists():
                            self.parent.after(0, _apply)
                    except Exception:
                        self._log_update_in_progress = False
                threading.Thread(target=_worker, daemon=True).start()
                return

            if _preparsed is None:
                all_keys, body_events = self._parse_log_files(current_system)
            else:
                try:
                    all_keys, body_events = _preparsed
                except Exception:
                    all_keys, body_events = [], {}
            table_rows = []
        except Exception:
            return
        def format_ring(ring):
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
        for body_name, events in body_events.items():
            merged = {}
            for ev in events:
                merged.update(ev)
            if 'Ring' in merged:
                val = merged['Ring']
                if isinstance(val, dict):
                    merged['Ring'] = format_ring(val)
                elif isinstance(val, list):
                    merged['Ring'] = ', '.join(format_ring(r) for r in val)
            if 'Rings' in merged:
                val = merged['Rings']
                if isinstance(val, dict):
                    merged['Rings'] = format_ring(val)
                elif isinstance(val, list):
                    merged['Rings'] = ', '.join(format_ring(r) for r in val)
            ts = merged.get('timestamp') or merged.get('Timestamp') or merged.get('Time') or merged.get('time')
            merged['Timestamp'] = ts
            if not merged.get('StarSystem') and current_system:
                merged['StarSystem'] = current_system
            if not merged.get('BodyName'):
                merged['BodyName'] = body_name
            table_rows.append(merged)
        import datetime
        def parse_ts(row):
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
        table_rows.sort(key=parse_ts, reverse=True)
        if not table_rows:
            try:
                prev_rows = getattr(self, '_table_rows_backup', None)
                if prev_rows:
                    table_rows = list(prev_rows)
            except Exception:
                pass
        recommended_keys = [
            'Timestamp','StarSystem','Body','BodyName','PlanetClass','Landable','DistanceFromArrivalLS','SurfaceGravity','SurfaceTemperature','Atmosphere','AtmosphereType',
            'Volcanism','TerraformState','Signals','Discovery','Composition','Ring','Radius','OrbitalPeriod','SemiMajorAxis','Eccentricity','Inclination',
            'Periapsis','AxialTilt','MassEM','ReserveLevel','TidalLock','Luminosity','Age_MY','StellarMass','AbsoluteMagnitude','RotationPeriod','Rings','ScanType',
            'Species','Genus','Variant','Sample','SampleType','SampleCount','BioType','BioSignal','BioLocation','BioDistance','BioName','BioGenus','BioVariant'
        ]
        config = AppConfig.load()
        if config.log_columns and isinstance(config.log_columns, list):
            shown_columns = [k for k in config.log_columns if k in all_keys]
            if not shown_columns:
                shown_columns = [k for k in all_keys if k in recommended_keys]
        else:
            shown_columns = [k for k in all_keys if k in recommended_keys]
        colors = self.colors
        self._log_data = []
        for child in self.tab_log.winfo_children():
            child.destroy()
        log_frame = ctk.CTkFrame(self.tab_log, fg_color=colors['background'])
        log_frame.pack(fill="both", expand=True, padx=8, pady=8)
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        def open_column_selector(all_keys, shown_columns, recommended_keys):
            from edmrn.column_display_names import COLUMN_DISPLAY_NAMES
            from edmrn.ed_theme import EliteDangerousTheme
            theme = EliteDangerousTheme.COLORS
            selector = tk.Toplevel(self.parent)
            selector.title("Select Columns")
            selector.configure(bg=theme["panel_dark"])
            selector.resizable(True, True)
            selector.geometry("1000x600")
            all_keys_sorted = sorted(all_keys)
            technical_keys = [k for k in all_keys_sorted if k.lower() not in [rk.lower() for rk in recommended_keys]]
            top = tk.Frame(selector, bg=theme["panel_dark"])
            top.pack(fill="x", padx=16, pady=(12,0))
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
            tk.Label(top, text="Search:", bg=theme["panel_dark"], fg=theme["text_orange"], font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0,4))
            search_entry = tk.Entry(top, textvariable=search_var, font=("Segoe UI", 10), bg=theme["panel_medium"], fg=theme["text_orange"], width=16)
            search_entry.grid(row=0, column=1, padx=(0,8), sticky="ew")
            btn_normal = tk.Button(top, text="Normal", command=lambda: mode_var.set("normal"), bg=theme["primary_orange"], fg=theme["background_dark"], font=("Segoe UI", 9, "bold"), width=9, height=1)
            btn_normal.grid(row=0, column=2, padx=(0,4))
            btn_advanced = tk.Button(top, text="Advanced", command=lambda: mode_var.set("advanced"), bg=theme["panel_medium"], fg=theme["primary_orange"], font=("Segoe UI", 9, "bold"), width=9, height=1)
            btn_advanced.grid(row=0, column=3, padx=(0,8))
            tk.Button(top, text="Select All", command=lambda: [selected[k].set(True) for k in get_options()], bg=theme["primary_orange"], fg=theme["background_dark"], font=("Segoe UI", 9, "bold"), width=10, height=1).grid(row=0, column=4, padx=(0,4))
            tk.Button(top, text="Deselect All", command=lambda: [selected[k].set(False) for k in get_options()], bg=theme["primary_orange"], fg=theme["background_dark"], font=("Segoe UI", 9, "bold"), width=12, height=1).grid(row=0, column=5, padx=(0,8))
            selected_count_label = tk.Label(top, text="Selected: 0", bg=theme["panel_dark"], fg=theme["text_orange"], font=("Segoe UI", 10, "bold"))
            selected_count_label.grid(row=0, column=6, padx=(0,8))
            top.columnconfigure(1, weight=1)
            tk.Button(top, text="Apply", command=lambda: apply_selection(), bg=theme["primary_orange"], fg=theme["background_dark"], font=("Segoe UI", 9, "bold"), width=10, height=1).grid(row=0, column=7, padx=(0,4))
            tk.Button(top, text="Cancel", command=lambda: selector.destroy(), bg=theme["panel_medium"], fg=theme["primary_orange"], font=("Segoe UI", 9, "bold"), width=9, height=1).grid(row=0, column=8, padx=(0,4))
            grid_frame = tk.Frame(selector, bg=theme["panel_dark"])
            grid_frame.pack(fill="both", expand=True, padx=16, pady=(8,0))
            canvas = tk.Canvas(grid_frame, bg=theme["panel_dark"], highlightthickness=0)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar = tk.Scrollbar(grid_frame, orient="vertical", command=canvas.yview)
            scrollbar.pack(side="right", fill="y")
            frame = tk.Frame(canvas, bg=theme["panel_dark"])
            canvas.create_window((0,0), window=frame, anchor="nw")
            def on_frame_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
            frame.bind("<Configure>", on_frame_configure)
            def render_checkboxes():
                for widget in frame.winfo_children():
                    widget.destroy()
                options = get_options()
                filtered = [k for k in options if search_var.get().lower() in k.lower()]
                groups = {}
                groups["Basic Info"] = [k for k in filtered if k in {"StarSystem","BodyName","PlanetClass","Landable","DistanceFromArrivalLS","ScanType","Discovery"}]
                groups["Surface Properties"] = [k for k in filtered if any(x in k for x in ["Surface","Gravity","Temperature","Volcanism","TerraformState","Composition","AxialTilt","TidalLock","MassEM","Radius","RotationPeriod","Age_MY","StellarMass","AbsoluteMagnitude"])]
                groups["Atmosphere"] = [k for k in filtered if "Atmosphere" in k or "Luminosity" in k]
                groups["Biology"] = [k for k in filtered if any(x in k for x in ["Bio","Species","Genus","Variant","Sample","SampleType","SampleCount"])]
                groups["Orbit & Physics"] = [k for k in filtered if any(x in k for x in ["OrbitalPeriod","SemiMajorAxis","Eccentricity","Inclination","Periapsis","ReserveLevel"])]
                groups["Signals & Rings"] = [k for k in filtered if any(x in k for x in ["Signal","Ring","Rings"])]
                grouped_keys = set(sum(groups.values(), []))
                groups["Technical/Other"] = [k for k in filtered if k not in grouped_keys]
                row_offset = 0
                for group_name, group_keys in groups.items():
                    if not group_keys:
                        continue
                    header = tk.Label(frame, text=group_name, bg=theme["panel_dark"], fg=theme["accent_blue"], font=("Segoe UI", 10, "bold"), anchor="w")
                    header.grid(row=row_offset, column=0, columnspan=6, sticky="w", pady=(8,2))
                    row_offset += 1
                    n_cols = 6
                    n_rows = (len(group_keys) + n_cols - 1) // n_cols
                    for idx, col in enumerate(group_keys):
                        row = row_offset + (idx // n_cols)
                        col_idx = idx % n_cols
                        label = COLUMN_DISPLAY_NAMES.get(col, col)
                        if mode_var.get() == "advanced" and col in technical_keys:
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
                from edmrn.config import AppConfig
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
        recommended_keys = [
            'StarSystem','Body','BodyName','PlanetClass','Landable','DistanceFromArrivalLS','SurfaceGravity','SurfaceTemperature','Atmosphere','AtmosphereType',
            'Volcanism','TerraformState','Signals','Discovery','Composition','Ring','Radius','OrbitalPeriod','SemiMajorAxis','Eccentricity','Inclination',
            'Periapsis','AxialTilt','MassEM','ReserveLevel','TidalLock','Luminosity','Age_MY','StellarMass','AbsoluteMagnitude','RotationPeriod','Rings','ScanType',
            'Species','Genus','Variant','Sample','SampleType','SampleCount','BioType','BioSignal','BioLocation','BioDistance','BioName','BioGenus','BioVariant'
        ]
        
        import datetime
        log_filter_var = tk.StringVar()
        time_filter_var = tk.StringVar(value="All")
        note_dict = {}
        from edmrn.ed_theme import EliteDangerousTheme
        theme = EliteDangerousTheme.COLORS
        filter_row = ctk.CTkFrame(log_frame, fg_color="transparent")
        filter_row.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0,8))
        filter_row.columnconfigure(3, weight=1)
        label_time = tk.Label(filter_row, text="Time:", bg=theme["panel_dark"], fg=theme["primary_orange"], font=("Segoe UI", 10, "bold"))
        label_time.grid(row=0, column=0, padx=(0,4), pady=2, sticky="nsew")
        time_options = ["1h", "6h", "24h", "All"]
        def on_time_filter_change(*args):
            update_log_table()
        time_menu = tk.OptionMenu(filter_row, time_filter_var, *time_options)
        time_menu.config(width=4, font=("Segoe UI", 10, "bold"), bg=theme["panel_dark"], fg=theme["primary_orange"], highlightthickness=0, activebackground=theme["panel_medium"], activeforeground=theme["primary_orange"])
        time_menu.grid(row=0, column=1, padx=(0,4), pady=2, sticky="nsew")
        time_filter_var.trace_add('write', on_time_filter_change)
        col_btn = tk.Button(
            filter_row,
            text="⋮",
            width=2,
            command=lambda: open_column_selector(all_keys, shown_columns, recommended_keys),
            bg=theme["panel_medium"], fg=theme["primary_orange"], font=("Segoe UI", 12, "bold"), relief="flat", activebackground=theme["panel_dark"], activeforeground=theme["primary_orange"]
        )
        col_btn.grid(row=0, column=2, padx=(0,4), pady=2, sticky="nsew")
        log_filter_entry = ctk.CTkEntry(filter_row, placeholder_text="Search...", textvariable=log_filter_var, width=320)
        log_filter_entry.grid(row=0, column=3, sticky="ew", pady=2)
        if table_rows:
            self._table_rows_backup = list(table_rows)
        self._log_filter_after_id = None
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
            backup = getattr(self, '_table_rows_backup', None)
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
                from edmrn.config import AppConfig
                config = AppConfig.load()
                config.log_columns = list(shown_columns)
                config.save()
                update_log_table()
            import tkinter.ttk as ttk
            style = ttk.Style()
            style.configure("Custom.Treeview", borderwidth=1, relief="solid", rowheight=24)
            border_color = "#666"
            for col in columns:
                style.configure(f"Custom.Treeview.Cell.{col}", padding=(0, 0, 6, 0), background=theme_colors['background'])
                style.map(f"Custom.Treeview.Cell.{col}", background=[('selected', theme_colors['selected'])])
            new_table = EDMRNSheet(
                log_frame,
                data=[],
                headers=headings,
                theme_colors=theme_colors
            )
            new_table.on_column_reorder = on_column_reorder
            new_table.grid(row=1, column=0, sticky="nsew")
            import datetime, re
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
                def format_number(col, val):
                    col_l = col.lower()
                    try:
                        if val is None or val == '-' or str(val).lower() in ('n/a','none','unknown',''):
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
                        if col_l in ('rotationperiod','orbitalperiod'):
                            days = float(val) / 86400.0
                            return f"{days:.2f} d"
                        if col_l == 'age_my':
                            return f"{float(val):,.0f} Myr"
                        if col_l == 'stellarmass':
                            return f"{float(val):.3f} M\u2609"
                        if col_l == 'absolutemagnitude':
                            return f"{float(val):.2f} mag"
                        if col_l in ('eccentricity','inclination','periapsis','axialtilt'):
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
                event = row.get('event','') or row.get('Event','')
                event_icon = ''
                event_color = '#FFD700'
                if event:
                    if 'Scan' in event:
                        event_icon = '🔍'
                        event_color = '#4FC3F7'
                    elif 'FSS' in event:
                        event_icon = '🌐'
                        event_color = '#FFD700'
                    elif 'Discovery' in event:
                        event_icon = '✨'
                        event_color = '#A3FFB0'
                    elif 'Signal' in event:
                        event_icon = '📡'
                        event_color = '#FFB347'
                    elif 'Reservoir' in event:
                        event_icon = '💧'
                        event_color = '#4FC3F7'
                    elif 'Body' in event:
                        event_icon = '🪐'
                        event_color = '#B0A3FF'
                    else:
                        event_icon = '📝'
                        event_color = '#FFD700'
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
                            import re
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
                        val = format_number(col, val) if col.lower() not in ('signals','composition','landable','body','bodyname','name') else val
                        values.append(val)
                table_data.append(values)
            try:
                new_table.set_sheet_data(table_data)
                new_table.auto_resize_columns()
            except Exception:
                pass
            import re as _re
            try:
                used_tags = set()
                for row_id in new_table.get_children():
                    for tag in new_table.item(row_id, 'tags'):
                        used_tags.add(tag)
                hex_color_re = _re.compile(r'^#[0-9A-Fa-f]{6}$')
                for tag in used_tags:
                    if isinstance(tag, str) and hex_color_re.match(tag):
                        new_table.tag_configure(tag, foreground=tag)
            except (AttributeError, Exception):
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
                menu = tk.Menu(self.parent, tearoff=0)
                menu.tk_popup(event.x_root, event.y_root)
            new_table.bind('<Button-3>', on_log_right_click)
            def show_detail_panel(event):
                row_index = new_table.identify_row(event)
                if row_index is None or row_index == -1:
                    return
                values = new_table.get_row_data(row_index)
                detail_win = tk.Toplevel(self.parent)
                detail_win.title("Log Detail")
                detail_win.configure(bg="#222")
                detail_win.resizable(True, True)
                try:
                    headers = new_table.headers() if callable(getattr(new_table, "headers", None)) else getattr(new_table, "headers", [])
                except Exception:
                    headers = []
                max_key_len = max(len(str(col)) for col in headers) if headers else 10
                key_width = min(max(12, max_key_len + 2), 24)
                from edmrn.column_display_names import COLUMN_DISPLAY_NAMES
                from edmrn.column_display_names import COLUMN_DISPLAY_NAMES
                technical_keys = {
                    'from_r','from_c','upto_r','upto_c','type_','name','kwargs','table','index','header',
                    'tdisp','idisp','hdisp','transposed','ndim','convert','undo','emit_event','widget'
                }
                log_row = None
                try:
                    log_row = table_rows[row_index]
                except Exception:
                    log_row = None
                if log_row:
                    from edmrn.ed_theme import EliteDangerousTheme
                    theme = EliteDangerousTheme.COLORS
                    panel_dark = theme.get("panel_dark", "#222")
                    panel_medium = theme.get("panel_medium", "#333")
                    accent = theme.get("accent", "#FFD700")
                    text_orange = theme.get("text_orange", "#FFD700")
                    display_items = [(k, log_row[k]) for k in log_row.keys() if k not in technical_keys]
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
                    canvas.create_window((0,0), window=inner, anchor="nw")
                    def on_configure(event):
                        canvas.configure(scrollregion=canvas.bbox("all"))
                    inner.bind("<Configure>", on_configure)
                    def format_value(val, key=None):
                        import json
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
                                        name = segs[0].replace(':','').strip()
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
                            return '\n'.join(f"{k.capitalize()}: {format_value(v)}" for k, v in val.items())
                        elif isinstance(val, list):
                            if all(isinstance(x, dict) for x in val):
                                return '\n'.join(', '.join(f"{k.capitalize()}: {format_value(v)}" for k, v in x.items()) for x in val)
                            else:
                                return '\n'.join(str(x) for x in val)
                        elif isinstance(val, str):
                            try:
                                parsed = json.loads(val)
                                return format_value(parsed, key)
                            except Exception:
                                if ',' in val and len(val) > 30:
                                    return '\n'.join([v.strip() for v in val.split(',')])
                                return val
                        else:
                            return str(val)
                    for i, (col, val) in enumerate(left_items):
                        display_name = COLUMN_DISPLAY_NAMES.get(col, col)
                        tk.Label(
                            inner, text=f"{display_name}", anchor="w",
                            font=("Segoe UI", 9, "bold"), bg=panel_dark, fg=accent,
                            width=18, justify="left", padx=5, pady=2
                        ).grid(row=i, column=0, sticky="ew", pady=1, padx=(8,2))
                        tk.Label(
                            inner, text=format_value(val, col), anchor="w",
                            font=("Segoe UI", 9), bg=panel_medium, fg=text_orange,
                            wraplength=180, justify="left", padx=5, pady=2
                        ).grid(row=i, column=1, sticky="ew", pady=1, padx=(0,8))
                    for i, (col, val) in enumerate(right_items):
                        display_name = COLUMN_DISPLAY_NAMES.get(col, col)
                        tk.Label(
                            inner, text=f"{display_name}", anchor="w",
                            font=("Segoe UI", 9, "bold"), bg=panel_dark, fg=accent,
                            width=18, justify="left", padx=5, pady=2
                        ).grid(row=i, column=2, sticky="ew", pady=1, padx=(8,2))
                        tk.Label(
                            inner, text=format_value(val, col), anchor="w",
                            font=("Segoe UI", 9), bg=panel_medium, fg=text_orange,
                            wraplength=180, justify="left", padx=5, pady=2
                        ).grid(row=i, column=3, sticky="ew", pady=1, padx=(0,8))
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
                        tk.Label(note_frame, text="Note:", bg=panel_dark, fg=accent, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0,5))
                        note_entry = tk.Entry(note_frame, width=40, bg=panel_medium, fg=text_orange, font=("Segoe UI", 10))
                        note_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
                        tk.Button(note_frame, text="Save", command=save_note, bg=accent, fg=panel_dark, font=("Segoe UI", 9, "bold")).pack(side="left")
            new_table.bind('<Double-1>', show_detail_panel)
            log_table = new_table
        log_table = None
        update_log_table()


    def _on_planet_select(self, event=None):
        name = self.planet_var.get()
        body = getattr(self, '_current_bodies', {}).get(name)
        if body and body.get('name'):
            txt = f"{body.get('name', '-')}: {body.get('type', '-')}, "
            if 'gravity' in body and body['gravity'] is not None:
                txt += f"Gravity: {body['gravity']:.2f}g, "
            if 'isLandable' in body:
                txt += f"Landable: {'Yes' if body['isLandable'] else 'No'}, "
            if 'atmosphereType' in body and body['atmosphereType']:
                txt += f"Atmosphere: {body['atmosphereType']}"
            else:
                txt += "Atmosphere: -"
            txt = txt.rstrip(', ')
        else:
            txt = "No info for this planet."
        self.planet_info_label.configure(text=txt)

    def _plot_route(self):
        name = self.info_values['system_name'].cget('text')
        if name and name != "-":
            try:
                import pyperclip
                pyperclip.copy(name)
            except Exception:
                pass

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
