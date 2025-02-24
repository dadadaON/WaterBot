import os
import sys
import subprocess
from pathlib import Path

def create_venv():
    """Створення віртуального середовища"""
    print("Створення віртуального середовища...")
    subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
    
    if sys.platform == 'win32':
        python_path = '.\\venv\\Scripts\\python.exe'
        pip_cmd = f'{python_path} -m pip'
    else:
        pip_cmd = './venv/bin/pip'
    
    print("Встановлення залежностей...")
    subprocess.run(f'{pip_cmd} install --upgrade pip', shell=True, check=True)
    subprocess.run(f'{pip_cmd} install -r requirements.txt', shell=True, check=True)

def create_structure():
    """Створення базової структури проекту"""
    print("Створення структури проекту...")
    
    # Створюємо основні директорії
    directories = ['handlers', 'utils', 'models']
    for dir_name in directories:
        os.makedirs(dir_name, exist_ok=True)
        # Створюємо __init__.py в кожній директорії
        with open(os.path.join(dir_name, '__init__.py'), 'w') as f:
            pass

def main():
    try:
        # Створюємо віртуальне середовище
        create_venv()
        
        # Створюємо структуру проекту
        create_structure()
        
        print("\nНалаштування завершено!")
        print("\nДля запуску бота виконайте:")
        if sys.platform == 'win32':
            print("1. .\\venv\\Scripts\\activate")
        else:
            print("1. source venv/bin/activate")
        print("2. python bot.py")
        
    except subprocess.CalledProcessError as e:
        print(f"Помилка: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неочікувана помилка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 