import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error.log")


os.makedirs(LOG_DIR, exist_ok=True)


logger = logging.getLogger("flask_app")
logger.setLevel(logging.INFO)

# File handler (rotates logs at 5MB, keeps 5 backups) - for ALL logs
file_handler = RotatingFileHandler(APP_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=10)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

# Error handler (rotates logs at 5MB, keeps 5 backups) - ONLY ERROR logs
error_handler = RotatingFileHandler(ERROR_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=10)
error_handler.setLevel(logging.ERROR)  # Only logs ERROR and above
error_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))


console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)
