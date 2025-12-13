class EDMRN_Error(Exception):
    pass

class ConfigError(EDMRN_Error):
    pass

class RouteError(EDMRN_Error):
    pass

class CSVError(EDMRN_Error):
    pass

class JournalError(EDMRN_Error):
    pass

class OverlayError(EDMRN_Error):
    pass

class OptimizationError(EDMRN_Error):
    pass

class BackupError(EDMRN_Error):
    pass

def handle_error(error, context=""):
    from edmrn.logger import get_logger
    logger = get_logger('ErrorHandler')
    
    error_msg = f"{context}: {error}" if context else str(error)
    logger.error(error_msg)
    
    return error_msg