import logging
import os
from fastAPI.config import LOG_DIR

class RequestIdFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', request_id=''):
        super().__init__(fmt, datefmt, style)
        self.request_id = request_id

    def format(self, record):
        formatted = super().format(record)
        parts = formatted.split(' - ', 1)
        if len(parts) > 1:
            return f"{parts[0]} - [{self.request_id}] - {parts[1]}"
        return formatted

def setup_logger(request_id: str, member_id: str, font_id: str, font_name: str):
    short_id = request_id[:6]
    log_filename = f"{short_id}_{member_id}_{font_id}_{font_name}.log"
    log_file_path = os.path.join(LOG_DIR, log_filename)
    
    logger = logging.getLogger(request_id)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    file_handler = logging.FileHandler(log_file_path)
    file_formatter = RequestIdFormatter('%(asctime)s - %(levelname)s - %(message)s', request_id=short_id)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_formatter = RequestIdFormatter('%(asctime)s - %(levelname)s - %(message)s', request_id=short_id)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger, log_file_path