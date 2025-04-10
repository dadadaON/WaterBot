@echo off
echo Запуск WaterBot...

:: Перехід в директорію скрипта
cd /d "%~dp0"

:: Активація віртуального середовища
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Помилка: Віртуальне середовище не знайдено!
    echo Будь ласка, запустіть setup_windows.bat для налаштування
    pause
    exit /b 1
)

:: Перевірка наявності Python
python --version > nul 2>&1
if errorlevel 1 (
    echo Помилка: Python не знайдено!
    pause
    exit /b 1
)

:: Запуск бота
echo Запуск бота...
python bot.py

:: Якщо бот зупинився, чекаємо натискання клавіші
pause 