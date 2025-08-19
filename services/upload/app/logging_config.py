import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging():
    """Configure logging for the upload server with separate log files."""
    
    # Create logs directory
    log_dir = Path("/home/ubuntu/file-uploader/services/upload/logs")
    log_dir.mkdir(exist_ok=True)
    
    # Define log files
    server_log = log_dir / "server.log"
    access_log = log_dir / "access.log"
    activity_log = log_dir / "activity.log"
    error_log = log_dir / "error.log"
    
    # Common formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Detailed formatter for activity logs
    activity_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Clear any existing handlers
    logging.getLogger().handlers.clear()
    
    # 1. Server Status Logger
    server_logger = logging.getLogger('server')
    server_logger.setLevel(logging.INFO)
    server_handler = logging.handlers.RotatingFileHandler(
        server_log, maxBytes=10*1024*1024, backupCount=5
    )
    server_handler.setFormatter(formatter)
    server_logger.addHandler(server_handler)
    
    # 2. Access Logger (HTTP requests)
    access_logger = logging.getLogger('access')
    access_logger.setLevel(logging.INFO)
    access_handler = logging.handlers.RotatingFileHandler(
        access_log, maxBytes=10*1024*1024, backupCount=5
    )
    access_handler.setFormatter(activity_formatter)
    access_logger.addHandler(access_handler)
    
    # 3. Activity Logger (uploads/downloads)
    activity_logger = logging.getLogger('activity')
    activity_logger.setLevel(logging.INFO)
    activity_handler = logging.handlers.RotatingFileHandler(
        activity_log, maxBytes=10*1024*1024, backupCount=5
    )
    activity_handler.setFormatter(activity_formatter)
    activity_logger.addHandler(activity_handler)
    
    # 4. Error Logger
    error_logger = logging.getLogger('error')
    error_logger.setLevel(logging.ERROR)
    error_handler = logging.handlers.RotatingFileHandler(
        error_log, maxBytes=10*1024*1024, backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)
    
    # 5. Root logger for general app logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return {
        'server': server_logger,
        'access': access_logger, 
        'activity': activity_logger,
        'error': error_logger
    }

# Get loggers
loggers = setup_logging()

# Export individual loggers for easy import
server_logger = loggers['server']
access_logger = loggers['access']
activity_logger = loggers['activity']
error_logger = loggers['error']
