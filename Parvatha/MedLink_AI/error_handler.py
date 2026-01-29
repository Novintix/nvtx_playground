# error_handler.py
import logging
from typing import Optional
from config import ERROR_MESSAGES

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def handle_error(error: Exception, context: Optional[str] = None) -> str:
    """
    Enhanced error handler with logging and user-friendly messages
    """
    error_msg = str(error).lower()
    error_type = type(error).__name__
    
    # Log the error
    logger.error(f"Error in {context or 'unknown'}: {error_type} - {error}")
    
    # NCBI/Network errors
    if any(x in error_msg for x in ["ncbi", "entrez", "network", "connection"]):
        return ERROR_MESSAGES["ncbi_connection"]
    
    # FAISS errors
    if "faiss" in error_msg or "index" in error_msg:
        return ERROR_MESSAGES["faiss_error"]
    
    # Model loading errors
    if any(x in error_msg for x in ["cuda", "torch", "model", "memory"]):
        return ERROR_MESSAGES["model_error"]
    
    # Generation errors
    if any(x in error_msg for x in ["generate", "decode", "token"]):
        return ERROR_MESSAGES["generation_error"]
    
    # Generic fallback
    return f"⚠️ Error: {error_type}. Please try again or contact support."


def log_info(message: str):
    """Log info message"""
    logger.info(message)


def log_warning(message: str):
    """Log warning message"""
    logger.warning(message)


def log_error(message: str):
    """Log error message"""
    logger.error(message)