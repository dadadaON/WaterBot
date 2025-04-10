import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from utils.logger import logger
from handlers.tasks import router as tasks_router
from utils.google_tasks import GoogleTasksManager
from models.base import Base
from models.database import async_engine

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    logger.info("Starting bot")
    logger.debug(f"Bot token: {BOT_TOKEN[:5]}...")
    
    try:
        # Створюємо таблиці при запуску
        await create_tables()
        
        # Ініціалізація бота та диспетчера
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Аутентифікація Google Tasks
        logger.info("Authenticating Google Tasks")
        tasks_manager = GoogleTasksManager()
        await tasks_manager.authenticate()
        logger.info("Google Tasks authenticated successfully")
        
        # Реєстрація роутерів
        dp.include_router(tasks_router)
        logger.info("Routers registered successfully")
        
        # Видалення всіх попередніх оновлень
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted, updates dropped")
        
        logger.info("Bot started")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        logger.exception("Full error traceback:")
        raise
    finally:
        await bot.session.close()
        logger.info("Bot session closed")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped") 