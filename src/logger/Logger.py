import os
import sys
import logging
import logging.handlers as handlers
from pathlib import Path


class Logger:
    """
    Singleton Logger class that provides comprehensive logging functionality.
    
    Logs are saved to a dedicated '/logs' directory within the project root.
    The directory is automatically created if it does not exist.
    
    Features:
    - Automatic log directory creation
    - Console output (stdout)
    - File output with daily rotation
    - Configurable backup retention (default: 15 days)
    - Consistent log formatting across all handlers
    """
    
    LOG_FORMAT = "%(asctime)-15s %(name)s %(levelname)-8s %(message)s"
    LOG_DIR_NAME = "logs"
    DEFAULT_LOG_FILE = "logs.txt"
    _instance = None
    _initialized = False

    def __new__(cls, log_name: str = None):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_name: str = None):
        if Logger._initialized:
            return
        Logger._initialized = True
        
        # Determine project root directory (parent of 'src' directory)
        project_root = self._get_project_root()
        
        # Create logs directory if it doesn't exist
        logs_dir = project_root / self.LOG_DIR_NAME
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up log file path
        log_file_name = log_name if log_name else self.DEFAULT_LOG_FILE
        log_file_path = logs_dir / log_file_name
        
        # Configure logger
        logger_name = os.uname().nodename
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter
        
        # Prevent duplicate handlers if logger already has handlers
        if logger.handlers:
            logger.handlers.clear()
        
        # Console handler - outputs to stdout for real-time monitoring
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        logger.addHandler(console_handler)
        
        # File handler with timed rotation - rotates at midnight, keeps 15 days of backups
        file_handler = handlers.TimedRotatingFileHandler(
            str(log_file_path),
            when='midnight',
            backupCount=15,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Capture all levels in file
        file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        logger.addHandler(file_handler)
        
        self.log = logger
        self.log_dir = logs_dir
        self.log_file_path = log_file_path
        
        # Log initialization message
        logger.info(f"Logger initialized. Log directory: {logs_dir}")

    @staticmethod
    def _get_project_root() -> Path:
        """
        Determine the project root directory.
        
        Looks for the project root by finding the parent directory of 'src'.
        Falls back to current working directory if 'src' is not found.
        
        Returns:
            Path: The project root directory path
        """
        # Start from the Logger.py file location and find project root
        current_file = Path(__file__).resolve()
        
        # Navigate up to find the project root (parent of 'src' directory)
        for parent in current_file.parents:
            if (parent / 'src').is_dir() and (parent / 'app.py').exists():
                return parent
        
        # Fallback to current working directory
        return Path.cwd()


# Create a single logger instance at module level
_logger_instance = Logger()
log = _logger_instance.log
