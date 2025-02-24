import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from config import BASE_DIR

# Створюємо директорію для логів якщо її немає
logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(exist_ok=True)

# Налаштування форматування
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Налаштування файлового обробника
file_handler = RotatingFileHandler(
    logs_dir / "bot.log",
    maxBytes=5242880,  # 5MB
    backupCount=3,
    encoding='utf-8'
)
file_handler.setFormatter(log_format)
file_handler.setLevel(logging.DEBUG)

# Налаштування консольного обробника
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
console_handler.setLevel(logging.DEBUG)

# Створюємо логер
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler) 