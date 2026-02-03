import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(config):
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO').upper()
    log_path = log_config.get('path', 'logs')
    log_filename = log_config.get('filename', 'agent.log')

    os.makedirs(log_path, exist_ok=True)
    
    log_file = os.path.join(log_path, log_filename)

    logger = logging.getLogger("AgentClient")
    logger.setLevel(log_level)

    # Prevent adding multiple handlers if called more than once
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

if __name__ == '__main__':
    from config import load_config
    config_data = load_config()
    logger = setup_logging(config_data)
    logger.info("Logging setup complete.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning.")
    logger.error("This is an error.")
