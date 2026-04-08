import os
import logging 
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.core.config import settings


def get_logger(
    name: str = "vehicle_manual_rag",
    level: str = "INFO",
    log_file_path: str = "logs/vehicle_manual_rag.log",
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel( getattr(logging, level.upper(), logging.INFO) )

    # Avoid Duplicate handelrs
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        '[%(levelname)s][%(asctime)s][%(name)s][%(filename)s:%(lineno)d]- %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # StreamHandler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel( getattr(logging, level.upper(), logging.INFO) )
    logger.addHandler(stream_handler)

    # FileHandelr
    if log_file_path:
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            log_file_path, 
            when="midnight", 
            encoding="utf-8",
            interval=2,
            utc=False,
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel( getattr(logging, level.upper(), logging.INFO) )
        logger.addHandler(file_handler)

    return logger

LOG_LEVEL = getattr(settings, "LOG_LEVEL", "INFO")
LOG_FILE_PATH = getattr(settings, "LOG_FILE_PATH", "logs/vehicle_manual_rag.log")

logger = get_logger(name="vehicle_manual_rag",level=LOG_LEVEL, log_file_path=LOG_FILE_PATH)