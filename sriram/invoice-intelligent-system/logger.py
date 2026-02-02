"""
Centralized logging - file only, no print statements.
"""

import logging
from config import LOG_FILE, LOG_LEVEL

def setup_logger(name: str) -> logging.Logger:
    """Create logger instance for a module."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(getattr(logging, LOG_LEVEL))
        
        file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    return logger
