import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'file_key'):
            log_entry['file_key'] = record.file_key
        if hasattr(record, 'file_size'):
            log_entry['file_size'] = record.file_size
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        
        return json.dumps(log_entry)


class LoggerSetup:
    """Configure structured logging for the upload server."""
    
    def __init__(self, log_dir: str = "/var/log/upload-server"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure log directory permissions
        os.chmod(self.log_dir, 0o755)
        
    def setup_loggers(self):
        """Set up all loggers with appropriate handlers."""
        
        # Main application logger
        self.setup_app_logger()
        
        # Access logger (HTTP requests)
        self.setup_access_logger()
        
        # Security logger (auth events)
        self.setup_security_logger()
        
        # Activity logger (uploads/downloads)
        self.setup_activity_logger()
        
        # Error logger (errors and exceptions)
        self.setup_error_logger()
    
    def setup_app_logger(self):
        """Main application logger."""
        logger = logging.getLogger("upload_server")
        logger.setLevel(logging.INFO)
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "app.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)
        
        return logger
    
    def setup_access_logger(self):
        """HTTP access logger."""
        logger = logging.getLogger("access")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "access.log",
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=30
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
        return logger
    
    def setup_security_logger(self):
        """Security events logger."""
        logger = logging.getLogger("security")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "security.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=20
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
        return logger
    
    def setup_activity_logger(self):
        """File operations logger."""
        logger = logging.getLogger("activity")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "activity.log",
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=50
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
        return logger
    
    def setup_error_logger(self):
        """Error and exception logger."""
        logger = logging.getLogger("errors")
        logger.setLevel(logging.WARNING)
        logger.propagate = False
        
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "errors.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=20
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
        return logger


# Activity logging helpers
def log_upload_start(user_id: str, filename: str, file_size: int, ip_address: str):
    """Log upload initiation."""
    logger = logging.getLogger("activity")
    logger.info("Upload started", extra={
        'operation': 'upload_start',
        'user_id': user_id,
        'filename': filename,
        'file_size': file_size,
        'ip_address': ip_address
    })


def log_upload_complete(user_id: str, file_key: str, filename: str, file_size: int, ip_address: str):
    """Log successful upload completion."""
    logger = logging.getLogger("activity")
    logger.info("Upload completed", extra={
        'operation': 'upload_complete',
        'user_id': user_id,
        'file_key': file_key,
        'filename': filename,
        'file_size': file_size,
        'ip_address': ip_address
    })


def log_upload_failed(user_id: str, filename: str, error: str, ip_address: str):
    """Log failed upload."""
    logger = logging.getLogger("activity")
    logger.warning("Upload failed", extra={
        'operation': 'upload_failed',
        'user_id': user_id,
        'filename': filename,
        'error_type': error,
        'ip_address': ip_address
    })


def log_download(user_id: str, file_key: str, ip_address: str, user_agent: str = None):
    """Log file download/access."""
    logger = logging.getLogger("activity")
    logger.info("File accessed", extra={
        'operation': 'download',
        'user_id': user_id,
        'file_key': file_key,
        'ip_address': ip_address,
        'user_agent': user_agent
    })


def log_file_delete(user_id: str, file_key: str, ip_address: str):
    """Log file deletion."""
    logger = logging.getLogger("activity")
    logger.info("File deleted", extra={
        'operation': 'delete',
        'user_id': user_id,
        'file_key': file_key,
        'ip_address': ip_address
    })


def log_auth_success(user_id: str, auth_type: str, ip_address: str):
    """Log successful authentication."""
    logger = logging.getLogger("security")
    logger.info("Authentication successful", extra={
        'operation': 'auth_success',
        'user_id': user_id,
        'auth_type': auth_type,
        'ip_address': ip_address
    })


def log_auth_failed(auth_type: str, reason: str, ip_address: str):
    """Log failed authentication."""
    logger = logging.getLogger("security")
    logger.warning("Authentication failed", extra={
        'operation': 'auth_failed',
        'auth_type': auth_type,
        'error_type': reason,
        'ip_address': ip_address
    })


def log_access(method: str, path: str, status_code: int, response_time: float, ip_address: str, user_agent: str = None):
    """Log HTTP access."""
    logger = logging.getLogger("access")
    logger.info(f"{method} {path}", extra={
        'operation': 'http_request',
        'method': method,
        'path': path,
        'status_code': status_code,
        'response_time': response_time,
        'ip_address': ip_address,
        'user_agent': user_agent
    })


# Initialize logging
logger_setup = LoggerSetup()
logger_setup.setup_loggers()

# Export main loggers
app_logger = logging.getLogger("upload_server")
access_logger = logging.getLogger("access")
security_logger = logging.getLogger("security")
activity_logger = logging.getLogger("activity")
error_logger = logging.getLogger("errors")
