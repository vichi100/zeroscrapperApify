import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def get_logger(name, log_file="app.log", level=logging.INFO):
    """
    Configures and returns a logger instance with both console and file handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if the logger is re-used
    if not logger.handlers:
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler (Rotating)
        # Ensure logs directory exists if a path is provided
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Default app-level logger
logger = get_logger("housing_scraper", log_file="logs/housing_scraper.log")
