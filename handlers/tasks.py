from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import asyncio

from utils.google_tasks import GoogleTasksManager
from utils.logger import logger
from models.database import get_session
from models.request import ServiceRequest

router = Router()
tasks_manager = GoogleTasksManager()

# Додайте константи для назв списків на початку файлу
TASK_LISTS = {
    'install': 'Встановлення обладнання',
    'maintenance': 'Техобслуговування обладнання',
    'repair': 'Ремонт обладнання',
    'question': 'Питання'
}

class TaskStates(StatesGroup):
    waiting_for_service_type = State()
    waiting_for_full_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_title = State()  # Додано
    waiting_for_description = State()
    waiting_for_due_date = State()
    waiting_for_confirmation = State()
    waiting_for_completion = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привіт! Виберіть послугу:\n"
        "/install - Встановлення обладнання\n"
        "/maintenance - Техобслуговування обладнання\n"
        "/repair - Ремонт обладнання\n"
        "/question - Задати питання"
    )

@router.message(Command("install"))
async def cmd_install(message: Message, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_full_name)
    await state.update_data(service_type='install')
    await message.answer("Введіть ваше ПІБ:")

@router.message(Command("maintenance"))
async def cmd_maintenance(message: Message, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_full_name)
    await state.update_data(service_type='maintenance')
    await message.answer("Введіть ваше ПІБ:")

@router.message(Command("repair"))
async def cmd_repair(message: Message, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_full_name)
    await state.update_data(service_type='repair')
    await message.answer("Введіть ваше ПІБ:")

@router.message(Command("question"))
async def cmd_question(message: Message, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_full_name)
    await state.update_data(service_type='question')
    await message.answer("Введіть ваше ПІБ:")

@router.message(TaskStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(TaskStates.waiting_for_phone)
    await message.answer("Введіть ваш телефон:")

@router.message(TaskStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(TaskStates.waiting_for_address)
    await message.answer("Введіть вашу адресу:")

@router.message(TaskStates.waiting_for_address)
async def process_address_service(message: Message, state: FSMContext):
    data = await state.get_data()
    full_name = data['full_name']
    phone = data['phone']
    address = message.text
    service_type = data.get('service_type', 'install')  # За замовчуванням "install"
    
    try:
        # Зберігаємо в базу даних
        async for session in get_session():
            new_request = ServiceRequest(
                full_name=full_name,
                phone=phone,
                address=address,
                service_type=TASK_LISTS[service_type]
            )
            session.add(new_request)
            await session.commit()

        # Перевіряємо аутентифікацію Google Tasks
        if not tasks_manager.service:
            await tasks_manager.authenticate()
        
        # Отримуємо або створюємо відповідний список
        list_id = await get_or_create_task_list(TASK_LISTS[service_type])
        
        # Створюємо завдання
        task_title = f"Клієнт: {full_name}"
        task_description = f"Телефон: {phone}\nАдреса: {address}"
        
        await tasks_manager.create_task(list_id, task_title, task_description)
        
        await message.answer(
            f"✅ Заявка на {TASK_LISTS[service_type]} прийнята!\n"
            "Ми зв'яжемося з вами найближчим часом."
        )
    except Exception as e:
        logger.error(f"Error processing service request: {str(e)}")
        await message.answer("❌ Виникла помилка. Спробуйте пізніше.")
    finally:
        await state.clear()

@router.message(Command("add"))
async def cmd_add_task(message: Message, state: FSMContext):
    try:
        logger.info(f"User {message.from_user.id} starting task creation")
        await state.set_state(TaskStates.waiting_for_title)
        await message.answer("Введіть назву завдання:")
    except Exception as e:
        logger.error(f"Error in add command: {str(e)}")
        await message.answer("Помилка при створенні завдання. Спробуйте пізніше.")

@router.message(TaskStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(TaskStates.waiting_for_description)
    await message.answer("Введіть опис завдання (або /skip для пропуску):")

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступні команди:\n"
        "/start - Почати роботу з ботом\n"
        "/add - Додати нове завдання\n"
        "/help - Переглянути доступні команди"
    )

@router.message(Command("skip"))
async def cmd_skip(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state == TaskStates.waiting_for_description:
        await state.update_data(description="")
        await state.set_state(TaskStates.waiting_for_due_date)
        await message.answer("Введіть дату завершення завдання (у форматі YYYY-MM-DD) або /skip для пропуску:")
    
    elif current_state == TaskStates.waiting_for_due_date:
        await state.update_data(due_date=None)
        data = await state.get_data()
        confirmation_text = (
            "Перевірте введені дані:\n"
            f"Назва: {data['title']}\n"
            f"Опис: {data.get('description', '')}\n"
            f"Дата завершення: не вказано\n\n"
            "Для підтвердження напишіть 'так'"
        )
        await state.set_state(TaskStates.waiting_for_confirmation)
        await message.answer(confirmation_text)

@router.message(TaskStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(TaskStates.waiting_for_due_date)
    await message.answer("Введіть дату завершення завдання (або /skip для пропуску):")

@router.message(TaskStates.waiting_for_due_date)
async def process_due_date(message: Message, state: FSMContext):
    await state.update_data(due_date=message.text)
    await state.set_state(TaskStates.waiting_for_confirmation)
    await message.answer("Перевірте введені дані:\n"
                       "Назва: {title}\n"
                       "Опис: {description}\n"
                       "Дата завершення: {due_date}")

@router.message(TaskStates.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext):
    logger.info(f"Processing confirmation from user {message.from_user.id}")
    
    data = await state.get_data()
    title = data.get('title')
    description = data.get('description', '')
    due_date = data.get('due_date', None)
    
    # Форматуємо повідомлення для підтвердження
    confirmation_text = (
        "Перевірте введені дані:\n"
        f"Назва: {title}\n"
        f"Опис: {description}\n"
        f"Дата завершення: {due_date}\n\n"
        "Для підтвердження напишіть 'так'"
    )
    
    if message.text.lower() == "так":
        try:
            logger.info(f"Creating task with title: {title}")
            
            # Перевіряємо аутентифікацію
            if not tasks_manager.service:
                logger.info("Authenticating Google Tasks")
                await tasks_manager.authenticate()
            
            # Створюємо список завдань
            task_list = await tasks_manager.create_task_list("Мої завдання")
            list_id = task_list.get('id')
            
            # Створюємо завдання
            await tasks_manager.create_task(list_id, title, description, due_date)
            await message.answer("✅ Завдання успішно створено!")
            
            await state.clear()
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            await message.answer("❌ Помилка при створенні завдання. Спробуйте ще раз.")
    else:
        await state.set_state(TaskStates.waiting_for_description)
        await message.answer("Введіть опис завдання:")

@router.message(TaskStates.waiting_for_completion)
async def process_completion(message: Message, state: FSMContext):
    await state.update_data(completed=True)
    await state.set_state(TaskStates.waiting_for_confirmation)
    await message.answer("Завдання завершено!")

@router.message(Command("list"))
async def cmd_list_tasks(message: Message):
    tasks = tasks_manager.get_tasks()
    if not tasks:
        await message.answer("У вас немає жодного завдання.")
    else:
        task_list = "\n".join([f"{task['title']} - {task['dueDate']}" for task in tasks])
        await message.answer(f"Ваші завдання:\n{task_list}")

@router.message(Command("delete"))
async def cmd_delete_task(message: Message):
    try:
        logger.info(f"User {message.from_user.id} trying to delete task")
        # Логіка видалення завдання
        pass
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        await message.answer("Не вдалося видалити завдання. Спробуйте пізніше.")

@router.message(Command("complete"))
async def cmd_complete_task(message: Message):
    try:
        logger.info(f"User {message.from_user.id} trying to complete task")
        # Логіка завершення завдання
        pass
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}")
        await message.answer("Не вдалося завершити завдання. Спробуйте пізніше.")

@router.message(Command("test"))
async def cmd_test(message: Message):
    try:
        logger.info("Testing Google Tasks connection")
        result = await tasks_manager.test_connection()
        if result:
            await message.answer("З'єднання з Google Tasks успішне!")
        else:
            await message.answer("Помилка з'єднання з Google Tasks")
    except Exception as e:
        logger.error(f"Test command error: {str(e)}")
        await message.answer("Помилка при тестуванні з'єднання")

async def get_or_create_task_list(list_name: str) -> str:
    """Отримує ID списку завдань або створює новий"""
    try:
        # Спробуємо знайти існуючий список
        loop = asyncio.get_event_loop()
        lists = await loop.run_in_executor(
            None, 
            tasks_manager.service.tasklists().list().execute
        )
        
        # Шукаємо список за назвою
        for task_list in lists.get('items', []):
            if task_list['title'] == list_name:
                return task_list['id']
        
        # Якщо список не знайдено, створюємо новий
        new_list = await tasks_manager.create_task_list(list_name)
        return new_list['id']
    except Exception as e:
        logger.error(f"Error getting/creating task list: {str(e)}")
        raise 