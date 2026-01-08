import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from edmrn.config import AppConfig
_logging_initialized = False
def setup_logging():
    global _logging_initialized
    if _logging_initialized:
        return
    try:
        app_data_dir = Path(AppConfig.get_app_data_path())
        log_dir = app_data_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"edmrn_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        root_logger.setLevel(logging.INFO)
        _logging_initialized = True
    except Exception as e:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        _logging_initialized = True
def get_logger(name):
    if not _logging_initialized:
        setup_logging()
    return logging.getLogger(f'EDMRN.{name}')
