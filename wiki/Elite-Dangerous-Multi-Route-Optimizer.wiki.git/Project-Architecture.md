<h1>Project Architecture</h1>


EDMRN uses a modular architecture designed to separate UI, routing, journal processing, navigation and data services.

The project contains 35+ functional modules and a larger set of supporting components.

```text
EDMRN_v3.3/
|--- edmrn/
|   |--- app.py
|   |--- app_window.py
|   |--- galaxy_handler.py
|   |--- journal_handler.py
|   |--- custom_route.py
|   |--- fuel_tracker.py
|   |--- exobiology.py
|   |--- journal_cache.py
|   |--- log_viewer.py
|   |--- system_info_section.py
|   |--- optimizer.py
|   |--- tracker.py
|   |--- minimap.py
|   |--- overlay.py
|   |--- journal.py
|   |--- journal_operations.py
|   |--- logger.py
|   |--- backup.py
|   |--- autosave.py
|   |--- platform_detector.py
|   |--- exceptions.py
|   |--- utils.py
|   |--- config.py
|   |--- gui.py
|   |--- ui_components.py
|   |--- theme_manager.py
|   |--- theme_editor.py
|   |--- ed_theme.py
|   |--- route_management.py
|   |--- settings_manager.py
|   |--- neutron_manager.py
|   |--- neutron.py
|   |--- galaxy_plotter.py
|   |--- file_operations.py
|   |--- system_autocomplete.py
|   |--- autocomplete_entry.py
|   |--- edmrn_sheet.py
|   |--- column_display_names.py
|   |--- codex_translation.py
|   |--- slef_store.py
|   |--- icons.py
|   |--- updater.py
|   |--- visit_history.py
|   |--- visit_history_dialog.py
|   |--- themes/
|   |   |--- elite_dangerous.json
|   |   |--- aisling_duval.json
|   |   |--- archon_delaine.json
|   |   |--- arissa_lavigny_duval.json
|   |   |--- denton_patreus.json
|   |   |--- edmund_mahon.json
|   |   |--- felicia_winters.json
|   |   |--- li_yong_rui.json
|   |   |--- pranav_antal.json
|   |   |--- zachary_hudson.json
|   |   `--- zemina_torval.json
|   `--- __init__.py
|--- assets/
|   |--- explorer_icon.ico
|   `--- explorer_icon.png
|--- main.py
|--- run.py
|--- setup.py
|--- edmrn.spec
|--- build_clean.bat
|--- requirements.txt
|--- LICENSE
`--- README.md
```

---
