import os
import json
import hashlib
import threading
import logging
from collections import Counter
from edmrn.codex_translation import codex_translation

logger = logging.getLogger('ExobioManager')


class ExobioManager:
    def __init__(self, section):
        self.section = section
        self._onfoot_bio_samples = []
        self._last_body = None
        self._incomplete_exobio = []
        self._last_edsm_exobio_samples = []
        self._bio_update_queue = None
        self._bio_summary_scheduled = False
        self._pending_bio_summary = None
        self._bio_tooltip = None
        self._bio_tooltip_widget = None
        self._last_bio_summary_hash = None
        self._start_bio_update_poller()

    def _get_history_path(self):
        from edmrn.config import Paths
        return os.path.join(os.path.dirname(Paths.get_backup_folder()), 'visited_systems_history.json')

    def _start_bio_update_poller(self):
        try:
            bio_card = getattr(self.section, 'bio_card', None)
            if bio_card:
                bio_card.after(100, self._process_bio_update_queue)
        except Exception:
            pass

    def _process_bio_update_queue(self):
        try:
            if self._bio_update_queue is None:
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
                self._bio_summary_scheduled = False
            except Exception:
                pass
            try:
                bio_card = getattr(self.section, 'bio_card', None)
                if bio_card:
                    bio_card.after(100, self._process_bio_update_queue)
            except Exception:
                pass

    def _enqueue_bio_update(self, exobio_samples, system=None, body=None):
        try:
            if self._bio_update_queue is None:
                import queue
                self._bio_update_queue = queue.Queue()
            self._bio_update_queue.put((exobio_samples, system, body))
            if not self._bio_summary_scheduled:
                self._bio_summary_scheduled = True
                try:
                    parent = getattr(self.section, 'parent', None)
                    if parent and hasattr(parent, 'after'):
                        parent.after(0, self._process_bio_update_queue)
                    else:
                        bio_card = getattr(self.section, 'bio_card', None)
                        if bio_card:
                            bio_card.after(0, self._process_bio_update_queue)
                except Exception:
                    self._bio_summary_scheduled = False
        except Exception:
            pass

    def add_onfoot_bio_sample(self, genus, body=None, system=None, geo=False, completed=False):
        logger.info(f"[DEBUG] add_onfoot_bio_sample called: genus={genus}, body={body}, system={system}, geo={geo}, completed={completed}")
        if body is not None and self._last_body is not None and body != self._last_body:
            logger.info(f"[DEBUG] Body changed from {self._last_body} to {body}, resetting samples")
            self._onfoot_bio_samples = []
        if body is not None:
            self._last_body = body
        if genus:
            self._onfoot_bio_samples.append(genus)
            if body and system:
                self._save_exobio_to_history(genus, body, system, geo, completed)
            exobio_samples = list(getattr(self, '_last_edsm_exobio_samples', []))
            exobio_samples += self._onfoot_bio_samples
            self._enqueue_bio_update(exobio_samples, system, body)
        self._load_current_system_exobio(system)

    def _save_exobio_to_history(self, genus, body, system, geo, completed):
        history_path = self._get_history_path()
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
            for k in ('first_visit', 'last_visit', 'visit_count', 'source_files'):
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
            logger.warning(f"Could not add exobio record to json: {e}")
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
            logger.warning(f"Could not add exobio/geo record to central source: {e}")

    def _load_current_system_exobio(self, system):
        try:
            history_path = self._get_history_path()
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

    def _load_incomplete_exobio(self, system=None):
        def read_history():
            try:
                history_path = self._get_history_path()
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
                parent = getattr(self.section, 'parent', None)
                if parent and hasattr(parent, 'after') and parent.winfo_exists():
                    parent.after(0, lambda: setattr(self, '_incomplete_exobio', result))
                else:
                    self._incomplete_exobio = result
            except Exception:
                self._incomplete_exobio = result
        threading.Thread(target=read_history, daemon=True).start()

    def update_bio_summary(self, exobio_samples, system=None, body=None):
        import threading
        try:
            if threading.current_thread() is not threading.main_thread():
                if self._bio_summary_scheduled:
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
                    bio_card = getattr(self.section, 'bio_card', None)
                    if bio_card:
                        bio_card.after(0, _run_on_main)
                except Exception:
                    pass
                return
        except Exception:
            pass
        try:
            bio_card = getattr(self.section, 'bio_card', None)
            bio_summary_label = getattr(self.section, 'bio_summary_label', None)
            bio_title_label = getattr(self.section, 'bio_title_label', None)
            colors = getattr(self.section, 'colors', {})
            if not bio_card or not bio_summary_label:
                return
            children = []
            try:
                children = list(bio_card.winfo_children())
            except Exception:
                return
            for widget in children:
                if widget not in (bio_title_label, bio_summary_label):
                    try:
                        widget.destroy()
                    except Exception:
                        pass
            logger.info(f"[DEBUG] update_bio_summary called: exobio_samples={exobio_samples}, system={system}, body={body}")

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
                        genus_code = rec.get('genus', '?')
                        genus_name = codex_translation.get(genus_code, genus_code)
                        incomplete_lines.append(f"[{status}] {rec.get('system', '?')} / {rec.get('body', '?')}: {genus_name}")

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
                children_now = list(bio_card.winfo_children()) if bio_card else []
            except Exception:
                children_now = []
            has_rendered_widgets = len([w for w in children_now if w not in (bio_title_label, bio_summary_label)]) > 0
            if hasattr(self, '_last_bio_summary_hash') and self._last_bio_summary_hash == state_hash and has_rendered_widgets:
                return

            app = getattr(self.section, 'app', None)
            if app is not None and hasattr(app, '_overlay_exobio_species'):
                try:
                    app._overlay_exobio_species = species_list
                except Exception:
                    pass
                if hasattr(app, 'overlay_enabled') and app.overlay_enabled and hasattr(app, 'overlay_manager') and hasattr(app.overlay_manager, '_instance') and app.overlay_manager._instance:
                    def safe_update_async():
                        def _do_update():
                            try:
                                self.app.overlay_manager._instance.update_display()
                            except Exception:
                                pass
                        threading.Thread(target=_do_update, daemon=True).start()
                    if threading.current_thread() is threading.main_thread():
                        safe_update_async()
                    else:
                        try:
                            app.root.after(0, safe_update_async)
                        except Exception:
                            pass
            self._last_bio_summary_hash = state_hash
            summary_text = "\n".join(incomplete_lines) + ("\n" if incomplete_lines else "")
            try:
                bio_summary_label.configure(text=summary_text)
            except Exception:
                pass
            if not species_list and not incomplete_lines:
                try:
                    bio_summary_label.configure(text="-")
                except Exception:
                    pass
                return

            import tkinter as tk
            try:
                row_frame = tk.Frame(bio_card, bg=colors.get('background', '#1a1a1a'))
                row_frame.pack(anchor="w", padx=12, pady=(0, 8), fill="x")
            except Exception:
                return

            use_canvas = len(species_list) <= 5
            logger.info(f"[DEBUG] Rendering {len(species_list)} species, use_canvas={use_canvas}")

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
                    row = tk.Frame(row_frame, bg=colors.get('background', '#1a1a1a'))
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
                    icon_label = tk.Label(row, text=icon, font=("Segoe UI", 13), bg=colors.get('background', '#1a1a1a'), fg="#4FC3F7")
                    icon_label.pack(side="left", padx=(0, 4))
                    make_tooltip(icon_label, icon_text)
                except Exception:
                    pass
                try:
                    if use_canvas:
                        name_label = tk.Label(row, text=species, font=("Segoe UI", 12, "bold"), bg=colors.get('background', '#1a1a1a'), fg=colors.get('accent', '#FFD700'))
                    else:
                        name_label = tk.Label(row, text=f"{species} [{count}/3]", font=("Segoe UI", 11), bg=colors.get('background', '#1a1a1a'), fg=colors.get('accent', '#FFD700'))
                    name_label.pack(side="left", padx=(0, 8))
                except Exception:
                    pass
                if use_canvas:
                    for j in range(3):
                        try:
                            color = "#4FC3F7" if j < count and count < 3 else ("#A3FFB0" if j < count else "#888")
                            circle = tk.Canvas(row, width=16, height=16, bg=colors.get('background', '#1a1a1a'), highlightthickness=0)
                            circle.create_oval(2, 2, 14, 14, fill=color, outline="#333")
                            circle.pack(side="left", padx=1)
                            make_tooltip(circle, f"Sample {j+1} {'scanned' if j < count else 'not scanned'}")
                        except Exception:
                            pass
                try:
                    import webbrowser
                    wiki_url = f"https://elite-dangerous.fandom.com/wiki/{species.replace(' ', '_')}"
                    def open_link(url=wiki_url):
                        try:
                            webbrowser.open(url)
                        except Exception:
                            pass
                    link_btn = tk.Label(row, text="🔗", font=("Segoe UI", 12), fg="#4FC3F7", bg=colors.get('background', '#1a1a1a'), cursor="hand2")
                    link_btn.pack(side="left", padx=(6, 0))
                    if use_canvas:
                        make_tooltip(link_btn, "Open wiki page")
                    link_btn.bind("<Button-1>", lambda e, url=wiki_url: open_link(url))
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"update_bio_summary crash-proofed: {e}")
