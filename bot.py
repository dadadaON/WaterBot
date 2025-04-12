import asyncio
import logging
import sys
import pkg_resources
import subprocess
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramAPIError

from config import BOT_TOKEN, NOTIFICATION_GROUP_ID
from utils.logger import logger
from handlers.tasks import router as tasks_router
from utils.google_tasks import GoogleTasksManager
from utils.excel_sync import ExcelSync
from models.base import Base
from models.database import async_engine

# Додаємо більше логування
logger.debug(f"Initial BOT_TOKEN: {BOT_TOKEN}")
logger.info(f"Notification group ID: {NOTIFICATION_GROUP_ID}")

def check_requirements():
    """Перевіряє та встановлює всі необхідні бібліотеки з requirements.txt"""
    requirements_path = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_path.exists():
        logger.error("Файл requirements.txt не знайдено!")
        sys.exit(1)
    
    try:
        with open(requirements_path, 'r', encoding='utf-8') as f:
            requirements = f.readlines()
    except Exception as e:
        logger.error(f"Помилка при читанні requirements.txt: {e}")
        sys.exit(1)
    
    missing_packages = []
    for requirement in requirements:
        # Пропускаємо порожні рядки та коментарі
        requirement = requirement.strip()
        if not requirement or requirement.startswith('#'):
            continue
            
        try:
            pkg_resources.require(requirement)
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            missing_packages.append(requirement)
    
    if missing_packages:
        logger.info("Встановлення відсутніх бібліотек...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])
            logger.info("Всі бібліотеки успішно встановлено!")
        except subprocess.CalledProcessError as e:
            logger.error(f"Помилка при встановленні бібліотек: {e}")
            sys.exit(1)

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    # Перевіряємо наявність всіх необхідних бібліотек
    check_requirements()
    
    logger.info("Starting bot")
    logger.debug(f"Bot token before initialization: {BOT_TOKEN}")
    
    try:
        # Створюємо таблиці при запуску
        await create_tables()
        
        # Створюємо таблиці при запуску
        await create_tables()
        
        # Ініціалізація бота та диспетчера
        logger.debug(f"Creating bot with token: {BOT_TOKEN}")
        bot = Bot(token=BOT_TOKEN)
        logger.debug(f"Bot created with token: {bot.token}")
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Аутентифікація Google Tasks
        logger.info("Authenticating Google Tasks")
        tasks_manager = GoogleTasksManager()
        await tasks_manager.authenticate()
        logger.info("Google Tasks authenticated successfully")
        
        # Ініціалізація синхронізації з Excel
        excel_sync = ExcelSync()
        # Запускаємо автоматичну синхронізацію в фоновому режимі
        asyncio.create_task(excel_sync.start_auto_sync(interval_minutes=5))
        logger.info("Excel sync started")
        
        # Реєстрація роутерів
        dp.include_router(tasks_router)
        logger.info("Routers registered successfully")
        
        # Видалення всіх попередніх оновлень
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted, updates dropped")
        
        logger.info("Bot started")
        
        # Запускаємо polling з явно вказаними дозволеними оновленнями
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "callback_query",
                "chat_member",
                "my_chat_member"
            ],
            handle_signals=True
        )
    except TelegramAPIError as telegram_error:
        logger.error(f"Telegram API Error: {telegram_error}")
        if "Conflict" in str(telegram_error):
            logger.error("Multiple bot instances detected! Please make sure only one instance is running.")
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        logger.exception("Full error traceback:")
        raise
    finally:
        if 'bot' in locals():
            await bot.session.close()
            logger.info("Bot session closed")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.exception("Full error traceback:") 