import asyncio
from datetime import datetime
from sqlalchemy import select

from utils.google_tasks import GoogleTasksManager
from models.tasks import CheckedTask
from models.database import async_session
from utils.logger import logger

class TasksChecker:
    def __init__(self, bot):
        self.bot = bot
        self.tasks_manager = GoogleTasksManager()
        self.check_interval = 300  # 5 хвилин

    async def get_new_tasks(self):
        """Отримує нові завдання, які ще не були перевірені"""
        try:
            # Отримуємо всі завдання з Google Tasks
            all_tasks = await self.tasks_manager.list_tasks()
            
            async with async_session() as session:
                # Отримуємо всі перевірені task_id з бази даних
                result = await session.execute(select(CheckedTask.task_id))
                checked_task_ids = {row[0] for row in result}
                
                # Фільтруємо нові завдання
                new_tasks = [
                    task for task in all_tasks 
                    if task['id'] not in checked_task_ids
                ]
                
                # Зберігаємо нові завдання як перевірені
                for task in new_tasks:
                    checked_task = CheckedTask(task_id=task['id'])
                    session.add(checked_task)
                
                await session.commit()
                
                return new_tasks
        except Exception as e:
            logger.error(f"Помилка при перевірці нових завдань: {e}")
            return []

    async def notify_about_new_tasks(self, tasks):
        """Відправляє сповіщення про нові завдання"""
        if not tasks:
            return

        message = "📋 Нові завдання:\n\n"
        for task in tasks:
            message += f"• {task['title']}\n"
            if task.get('notes'):
                message += f"  Деталі: {task['notes']}\n"
            message += "\n"

        # TODO: Замініть ADMIN_CHAT_ID на реальний ID чату адміністратора
        try:
            await self.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
        except Exception as e:
            logger.error(f"Помилка при відправці сповіщення: {e}")

    async def check_loop(self):
        """Головний цикл перевірки завдань"""
        while True:
            try:
                new_tasks = await self.get_new_tasks()
                if new_tasks:
                    await self.notify_about_new_tasks(new_tasks)
            except Exception as e:
                logger.error(f"Помилка в циклі перевірки: {e}")
            
            await asyncio.sleep(self.check_interval) 