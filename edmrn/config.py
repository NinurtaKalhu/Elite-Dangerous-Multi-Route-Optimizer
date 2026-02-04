import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
@dataclass
class AppConfig:
    appearance_mode: str = 'Dark'
    color_theme: str = 'green'
    overlay_opacity: int = 80
    overlay_size: str = 'Medium'
    auto_start_overlay_when_ready: bool = True
    journal_path: str = ''
    selected_commander: str = 'Auto'
    autosave_interval: str = '5 minutes'
    ship_jump_range: str = '70.0'
    current_theme: str = 'elite_dangerous'
    window_geometry: str = '1100x800+100+100'
    borderless_mode: bool = True
    log_columns: list = None
    @classmethod
    def get_app_data_path(cls):
        try:
            home = Path.home()
            documents = home / "Documents"
            if not documents.exists():
                documents = home
            app_data = documents / "EDMRN_Route_Data"
            app_data.mkdir(parents=True, exist_ok=True)
            return str(app_data)
        except Exception:
            app_data = Path.cwd() / 'EDMRN_Route_Data'
            app_data.mkdir(parents=True, exist_ok=True)
            return str(app_data)
    @classmethod
    def get_settings_file(cls):
        app_data = cls.get_app_data_path()
        return str(Path(app_data) / 'settings.json')
    @classmethod
    def load(cls):
        settings_file = cls.get_settings_file()
        if Path(settings_file).exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception:
                pass
        return cls()
    def save(self):
        settings_file = self.get_settings_file()
        try:
            Path(settings_file).parent.mkdir(parents=True, exist_ok=True)
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False
class Paths:
    @staticmethod
    def get_app_data_dir():
        return AppConfig.get_app_data_path()
    @staticmethod
    def get_backup_folder():
        backup_dir = Path(AppConfig.get_app_data_path()) / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        return str(backup_dir)
    @staticmethod
    def get_backup_subfolder(timestamp_str: str):
        subfolder = Path(Paths.get_backup_folder()) / timestamp_str
        subfolder.mkdir(parents=True, exist_ok=True)
        return str(subfolder)
    @staticmethod
    def get_last_csv_file():
        return str(Path(AppConfig.get_app_data_path()) / 'last_output.txt')
    @staticmethod
    def get_assets_dir():
        assets_dir = Path.cwd() / 'assets'
        assets_dir.mkdir(exist_ok=True)
        return str(assets_dir)
