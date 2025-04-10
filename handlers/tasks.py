from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import asyncio
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import html # Додаємо імпорт для санітизації

from utils.google_tasks import GoogleTasksManager
from utils.excel_sync import ExcelSync
from utils.logger import logger
from models.database import get_session
from models.request import ServiceRequest
from config import NOTIFICATION_GROUP_ID, ADMINS

router = Router()
tasks_manager = GoogleTasksManager()
excel_sync = ExcelSync()

# Додайте константи для назв списків на початку файлу
TASK_LISTS = {
    'install': 'Встановлення обладнання',
    'maintenance': 'Техобслуговування обладнання',
    'repair': 'Ремонт обладнання',
    'question': 'Питання'
}

# Оновлюємо константи для кнопок
SERVICES = {
    'install': '🔧 Встановлення обладнання',
    'maintenance': '🔄 Техобслуговування',
    'repair': '🛠 Ремонт обладнання',
    'question': '❓ Задати питання'
}

# Контактна інформація
CONTACT_PHONE = "@Complete_System"
CONTACT_EMAIL = ""
CONTACT_ADDRESS = ""
CONTACT_NUMBER = "+390738390983"

class TaskStates(StatesGroup):
    waiting_for_service_type = State()
    waiting_for_full_name = State()
    waiting_for_phone = State()
    waiting_for_settlement = State()
    waiting_for_street = State()
    waiting_for_building = State()
    waiting_for_apartment = State()
    waiting_for_question = State()
    waiting_for_confirmation = State()

def get_services_keyboard() -> InlineKeyboardMarkup:
    """Створює клавіатуру з кнопками послуг"""
    builder = InlineKeyboardBuilder()
    for service_id, service_name in SERVICES.items():
        builder.button(text=service_name, callback_data=f"service:{service_id}")
    builder.button(text="❌ Скасувати заявку", callback_data="cancel")
    builder.adjust(1)  # По одній кнопці в рядку
    return builder.as_markup()

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Створює клавіатуру для підтвердження"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Підтвердити", callback_data="confirm:yes")
    builder.button(text="❌ Скасувати", callback_data="confirm:no")
    builder.adjust(2)
    return builder.as_markup()

# Створюємо клавіатуру для головного меню
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Створює головну клавіатуру"""
    keyboard = [
        [KeyboardButton(text="📝 Створити заявку")],
        [KeyboardButton(text="ℹ️ Інформація"), KeyboardButton(text="📞 Контакти")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

@router.message(Command("start"))
async def cmd_start(message: Message):
    # Спочатку показуємо головне меню
    await message.answer(
        "👋 Вітаю!\n"
        "Я допоможу вам оформити заявку на обслуговування.",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "📝 Створити заявку")
async def handle_create_request(message: Message):
    await message.answer(
        "📝 Оберіть, будь ласка, тип послуги:",
        reply_markup=get_services_keyboard()
    )

@router.message(F.text == "ℹ️ Інформація")
async def handle_info(message: Message):
    await message.answer(
        "ℹ️ Про нас:\n\n"
        "Ми надаємо послуги з встановлення та обслуговування обладнання.\n"
        "Працюємо щодня з 9:00 до 18:00."
    )

@router.message(F.text == "📞 Контакти")
async def handle_contacts(message: Message):
    await message.answer(
        "📞 Наші контакти:\n\n"
        f"👤 {CONTACT_PHONE}\n"
        f"📱 {CONTACT_NUMBER}"
    )

@router.callback_query(lambda c: c.data == "cancel")
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Запис скасовано.\n"
        "Щоб почати спочатку, натисніть /start"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith('service:'))
async def process_service_selection(callback: CallbackQuery, state: FSMContext):
    try:
        service_id = callback.data.split(':')[1]
        logger.info(f"Selected service: {service_id}")
        
        await state.update_data(service_type=service_id)
        logger.debug(f"State updated with service_type: {service_id}")
        
        # Різні повідомлення для різних типів послуг
        if service_id == 'question':
            await callback.message.edit_text(
                "Будь ласка, введіть ваше ім'я:"
            )
        else:
            await callback.message.edit_text(
                f"Ви обрали: {SERVICES[service_id]}\n"
                "Будь ласка, введіть ваше ім'я:"
            )
        await state.set_state(TaskStates.waiting_for_full_name)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error processing service selection: {str(e)}")
        await callback.message.edit_text(
            "❌ Помилка при виборі послуги. Спробуйте ще раз:",
            reply_markup=get_services_keyboard()
        )
        await callback.answer()

@router.message(TaskStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    # Валідація імені (приклад простої перевірки)
    if not all(x.isalpha() or x.isspace() for x in message.text):
        await message.answer(
            "❌ Ім'я має містити лише літери та пробіли.\n"
            "Будь ласка, спробуйте ще раз:"
        )
        return
    
    await state.update_data(full_name=message.text)
    await state.set_state(TaskStates.waiting_for_phone)
    await message.answer(
        "Введіть, будь ласка, ваш номер телефону у форматі:\n"
        "(___) ___-__-__"
    )

@router.message(TaskStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    # Валідація номера телефону
    phone = message.text.strip()
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) != 10:
        await message.answer(
            "❌ Некоректний формат номера телефону.\n"
            "Будь ласка, введіть номер у форматі (___) ___-__-__"
        )
        return
    
    formatted_phone = f"({digits[:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:]}"
    await state.update_data(phone=formatted_phone)
    
    # Перевіряємо тип послуги
    data = await state.get_data()
    if data['service_type'] == 'question':
        await state.set_state(TaskStates.waiting_for_question)
        await message.answer("Опишіть, будь ласка, ваше питання:")
    else:
        await state.set_state(TaskStates.waiting_for_settlement)
        await message.answer("Введіть, будь ласка, назву населеного пункту:")

@router.message(TaskStates.waiting_for_settlement)
async def process_settlement(message: Message, state: FSMContext):
    settlement = message.text.strip()
    if not settlement:
        await message.answer(
            "❌ Будь ласка, введіть назву населеного пункту:"
        )
        return
    
    await state.update_data(settlement=settlement)
    await state.set_state(TaskStates.waiting_for_street)
    await message.answer("Введіть, будь ласка, назву вулиці:")

@router.message(TaskStates.waiting_for_street)
async def process_street(message: Message, state: FSMContext):
    street = message.text.strip()
    if len(street) < 2:
        await message.answer(
            "❌ Назва вулиці занадто коротка.\n"
            "Будь ласка, введіть коректну назву вулиці:"
        )
        return
    
    await state.update_data(street=street)
    await state.set_state(TaskStates.waiting_for_building)
    await message.answer("Введіть, будь ласка, номер будинку:")

@router.message(TaskStates.waiting_for_building)
async def process_building(message: Message, state: FSMContext):
    building = message.text.strip()
    if not building:
        await message.answer(
            "❌ Будь ласка, введіть номер будинку:"
        )
        return
    
    await state.update_data(building=building)
    await state.set_state(TaskStates.waiting_for_apartment)
    await message.answer("Введіть, будь ласка, номер квартири:")

@router.message(TaskStates.waiting_for_apartment)
async def process_apartment(message: Message, state: FSMContext):
    apartment = message.text.strip()
    if not apartment:
        await message.answer(
            "❌ Будь ласка, введіть номер квартири:"
        )
        return
    
    data = await state.get_data()
    
    # Формуємо повну адресу з квартирою
    address = f"вул. {data['street']}, буд. {data['building']}, кв. {apartment}"
    await state.update_data(address=address)
    
    # Формуємо повідомлення для підтвердження
    confirmation_text = (
        "📋 Перевірте, будь ласка, введені дані:\n\n"
        f"Послуга: {SERVICES[data['service_type']]}\n"
        f"Ім'я: {data['full_name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Населений пункт: {data['settlement']}\n"
        f"Адреса: {address}\n\n"
        "Все правильно?"
    )
    
    await state.set_state(TaskStates.waiting_for_confirmation)
    await message.answer(confirmation_text, reply_markup=get_confirm_keyboard())

@router.message(Command("help"))
async def cmd_help(message: Message):
    # Базова довідка для всіх користувачів
    help_text = (
        "🔍 Доступні команди:\n\n"
        "/start - Почати оформлення заявки\n"
        "/cancel - Скасувати поточну дію\n"
        "/help - Показати це повідомлення\n"
    )
    
    # Додаткові команди для адміністраторів
    if str(message.from_user.id) in ADMINS:
        help_text += (
            "\n👑 Команди адміністратора:\n"
            "/sync - Синхронізувати дані з Excel\n"
            "/test - Перевірити з'єднання з Google Tasks\n"
        )
    
    help_text += (
        "\nДля оформлення заявки просто натисніть /start "
        "та дотримуйтесь інструкцій."
    )
    
    await message.answer(help_text)

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

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔄 Дію скасовано. Оберіть послугу:",
        reply_markup=get_services_keyboard()
    )

async def get_or_create_task_list(list_name: str) -> str:
    """Отримує ID списку завдань або створює новий"""
    try:
        # Перевіряємо, чи сервіс ініціалізований
        if not tasks_manager.service:
            logger.info("Authenticating Google Tasks before creating task list")
            await tasks_manager.authenticate()
            
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

@router.callback_query(lambda c: c.data.startswith('confirm:'))
async def process_confirmation_callback(callback: CallbackQuery, state: FSMContext):
    try:
        confirmation = callback.data.split(':')[1]
        data = await state.get_data()
        
        if confirmation == 'yes':
            # Перевіряємо автентифікацію перед створенням завдання
            if not tasks_manager.service:
                logger.info("Authenticating Google Tasks before creating task")
                await tasks_manager.authenticate()
                
            # Перевіряємо наявність всіх обов'язкових полів
            required_fields = ['full_name', 'phone', 'service_type']
            if data['service_type'] != 'question':
                required_fields.append('settlement')
                
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
                
            # Отримуємо або створюємо список завдань
            list_name = TASK_LISTS.get(data['service_type'])
            list_id = await get_or_create_task_list(list_name)
            
            # Формуємо заголовок та опис завдання
            title = f"{SERVICES[data['service_type']]} - {data['full_name']}"
            notes = f"Ім'я: {data['full_name']}\n"
            notes += f"Телефон: {data['phone']}\n"
            
            if data['service_type'] == 'question':
                notes += f"Питання: {data['question']}"
            else:
                if 'settlement' in data:
                    notes += f"Населений пункт: {data['settlement']}\n"
                if 'address' in data:
                    notes += f"Адреса: {data['address']}"
            
            # Створюємо завдання
            try:
                task = await tasks_manager.create_task(list_id, title, notes)
                if task:
                    logger.info(f"Task created successfully: {task.get('id')}")
                    
                    # --- Початок: Надсилання сповіщення ---
                    try:
                        # Санітизуємо назву завдання перед надсиланням
                        sanitized_title = html.escape(title) 
                        notification_text = f"✅ Створено нове завдання: {sanitized_title}"
                        
                        await callback.bot.send_message(
                            chat_id=NOTIFICATION_GROUP_ID,
                            text=notification_text,
                            parse_mode=None  # Надсилаємо як звичайний текст
                        )
                        logger.info(f"Sent notification for task '{task.get('id')}' to group {NOTIFICATION_GROUP_ID}")
                    except Exception as notify_e:
                        logger.error(f"Failed to send notification to group {NOTIFICATION_GROUP_ID}: {notify_e}")
                    # --- Кінець: Надсилання сповіщення ---

                    # Зберігаємо запит в базі даних
                    async with get_session() as session:
                        new_request = ServiceRequest(
                            full_name=data['full_name'],
                            phone=data['phone'],
                            service_type=data['service_type'],
                            settlement=data['settlement']
                        )
                        
                        if data['service_type'] == 'question':
                            new_request.question = data['question']
                        else:
                            new_request.address = data['address']
                            
                        session.add(new_request)
                        await session.commit()
                    
                    await callback.message.edit_text(
                        f"✅ Заявка на {SERVICES[data['service_type']]} прийнята!\n"
                        "Ми зв'яжемося з вами найближчим часом."
                    )
                    await state.clear()
                else:
                    await callback.message.edit_text(
                        "❌ Помилка при створенні завдання. Спробуйте ще раз:",
                        reply_markup=get_services_keyboard()
                    )
                    await state.clear()
            except Exception as e:
                logger.error(f"Error creating task: {str(e)}")
                await callback.message.edit_text(
                    "❌ Помилка при створенні завдання. Спробуйте ще раз:",
                    reply_markup=get_services_keyboard()
                )
                await state.clear()
                
        elif confirmation == 'no':
            await callback.message.edit_text(
                "❌ Заявку скасовано.\n"
                "Щоб створити нову заявку, натисніть /start"
            )
            await state.clear()
            
        # Відповідаємо на callback
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error processing confirmation callback: {str(e)}")
        logger.exception("Full error traceback:")
        await callback.message.edit_text(
            "❌ Виникла помилка. Спробуйте ще раз:",
            reply_markup=get_services_keyboard()
        )
        await state.clear()
        await callback.answer()

@router.callback_query(lambda c: c.data == "action:create")
async def create_request(callback: CallbackQuery):
    await cmd_start(callback.message)
    await callback.answer()

@router.callback_query(lambda c: c.data == "action:info")
async def show_info(callback: CallbackQuery):
    await callback.message.answer(
        "📞 Наші контакти:\n\n"
        f"👤 {CONTACT_PHONE}"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "action:contacts")
async def show_contacts(callback: CallbackQuery):
    await callback.message.answer(
        "📞 Наші контакти:\n\n"
        f"👤 {CONTACT_PHONE}\n"
        f"📱 {CONTACT_NUMBER}"
    )
    await callback.answer()

@router.message(TaskStates.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Формуємо повідомлення для підтвердження
    confirmation_text = (
        "📋 Перевірте, будь ласка, введені дані:\n\n"
        f"Послуга: {SERVICES[data['service_type']]}\n"
        f"Ім'я: {data['full_name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Питання: {message.text}\n\n"
        "Все правильно?"
    )
    
    await state.update_data(question=message.text)
    await state.set_state(TaskStates.waiting_for_confirmation)
    await message.answer(confirmation_text, reply_markup=get_confirm_keyboard())

@router.message(Command("sync"))
async def cmd_sync(message: Message):
    """Команда для ручної синхронізації з Excel"""
    # Перевіряємо, чи користувач є адміністратором
    if str(message.from_user.id) not in ADMINS:
        await message.answer("❌ У вас немає прав для виконання цієї команди.")
        return
        
    try:
        # Показуємо повідомлення про початок синхронізації
        status_message = await message.answer("🔄 Синхронізація з Excel...")
        
        # Запускаємо синхронізацію
        if await excel_sync.export_to_excel():
            await status_message.edit_text("✅ Дані успішно експортовано в Excel!")
        else:
            await status_message.edit_text("❌ Помилка при експорті даних.")
    except Exception as e:
        logger.error(f"Error in sync command: {str(e)}")
        await message.answer("❌ Сталася помилка при синхронізації.") 