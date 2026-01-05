from loguru import logger
from src.config import settings
import sys

def setup_logger():
    """Configure logging for the application"""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.langgraph_log_level
    )
    
    # Add file handler
    logger.add(
        "logs/agentic_automation.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level="DEBUG",
        rotation="500 MB",
        retention="7 days"
    )
    
    return logger

logger = setup_logger()
