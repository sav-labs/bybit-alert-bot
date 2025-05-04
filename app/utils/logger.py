import sys
from loguru import logger
from app.settings import LOG_LEVEL, LOG_FILE

def setup_logger():
    """Configure logger."""
    # Remove default handlers
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file handler
    logger.add(
        LOG_FILE,
        rotation="10 MB",
        retention="1 week",
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    logger.info(f"Logger initialized with level {LOG_LEVEL}")
    
    return logger 