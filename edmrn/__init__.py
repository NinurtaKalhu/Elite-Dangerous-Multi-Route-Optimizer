__version__ = "3.2.0"
__author__ = "Ninurta Kalhu"
__email__ = "ninurtakalhu@gmail.com"
__all__ = [
    'EDMRN_App',
    'AppConfig',
    'setup_logging',
    'EDMRN_Error'
]
def __getattr__(name: str):
    if name == 'EDMRN_App':
        from edmrn.app import EDMRN_App
        return EDMRN_App
    if name == 'AppConfig':
        from edmrn.config import AppConfig
        return AppConfig
    if name == 'setup_logging':
        from edmrn.logger import setup_logging
        return setup_logging
    if name == 'EDMRN_Error':
        from edmrn.exceptions import EDMRN_Error
        return EDMRN_Error
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
