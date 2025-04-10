import logging
import sys
from pathlib import Path
import shutil
from datetime import datetime
import os

from config import BASE_DIR

# Створюємо директорію для логів якщо її немає
logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(exist_ok=True)

# Налаштування форматування
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Функція для ротації логів
def rotate_logs():
    current_log = logs_dir / "log.txt"
    old_log = logs_dir / "log.old"
    
    try:
        if current_log.exists():
            # Перевіряємо, чи файл не використовується
            try:
                with open(current_log, 'a') as f:
                    pass
            except IOError:
                # Якщо файл використовується, пропускаємо ротацію
                return
                
            if old_log.exists():
                try:
                    old_log.unlink()  # Видаляємо старий log.old
                except Exception:
                    pass  # Ігноруємо помилки при видаленні старого файлу
                    
            try:
                shutil.move(current_log, old_log)  # Переміщуємо поточний лог в log.old
            except Exception:
                pass  # Ігноруємо помилки при переміщенні
    except Exception as e:
        print(f"Помилка при ротації логів: {e}")

# Ротація логів при старті
rotate_logs()

# Налаштування файлового обробника для поточного логу
current_file_handler = logging.FileHandler(
    logs_dir / "log.txt",
    encoding='utf-8'
)
current_file_handler.setFormatter(log_format)
current_file_handler.setLevel(logging.DEBUG)

# Налаштування консольного обробника
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
console_handler.setLevel(logging.DEBUG)

# Створюємо логер
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)
logger.addHandler(current_file_handler)
logger.addHandler(console_handler)

# Додаємо заголовок до нового логу
logger.info("="*50)
logger.info(f"Новий сеанс логування почався {datetime.now()}")
logger.info("="*50) 