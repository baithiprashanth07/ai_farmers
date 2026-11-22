"""Centralized logging configuration."""
import sys
from loguru import logger as _logger
from app.config import get_settings

settings = get_settings()

# Remove default handler
_logger.remove()

# Add console handler with rich formatting
_logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True,
)

# Add file handler for production
_logger.add(
    "logs/ai_farmer.log",
    rotation="10 MB",
    retention="30 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

logger = _logger
