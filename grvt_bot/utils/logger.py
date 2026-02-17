"""
Logging utilities for GRVT Bot.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str = "grvt_bot",
    log_file: Optional[str] = "grvt_bot.log",
    level: int = logging.INFO,
    console: bool = True,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
    quiet_third_party: bool = True,
) -> logging.Logger:
    """
    Setup a logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file (None to disable file logging)
        level: Logging level
        console: Whether to log to console
        max_bytes: Max size for each log file before rotation
        backup_count: Number of rotated files to keep
        quiet_third_party: Reduce noisy third-party/root logs in terminal
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Format
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8',
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    if quiet_third_party:
        # Prevent implicit basicConfig output like "ERROR:root:..."
        # while keeping our own logger output readable.
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            root_logger.addHandler(logging.NullHandler())
        root_logger.setLevel(logging.CRITICAL)

        for noisy_name in ("urllib3", "requests", "pysdk", "asyncio"):
            logging.getLogger(noisy_name).setLevel(logging.WARNING)

    return logger
