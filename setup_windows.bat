@echo off
echo Налаштування проекту...

:: Видаляємо старе віртуальне середовище
if exist venv (
    rmdir /s /q venv
)

:: Створюємо нове віртуальне середовище
python -m venv venv

:: Активуємо віртуальне середовище та встановлюємо залежності
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Запускаємо Python скрипт для подальшого налаштування
python setup_remaining.py

echo Налаштування завершено!
echo.
echo Для запуску бота виконайте:
echo venv\Scripts\activate
echo python bot.py
pause 