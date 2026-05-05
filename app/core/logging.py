import sys
from loguru import logger
from app.core.config import settings

'''Logging setup with loguru, setup console and file handlers'''

def setup_logging() -> None:
    logger.remove()

    #Console
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    #File
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )