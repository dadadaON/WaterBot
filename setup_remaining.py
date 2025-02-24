import os
import subprocess
from pathlib import Path
import asyncio
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

def create_alembic_env():
    """Створення env.py для Alembic"""
    env_content = '''import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Додаємо шлях до проекту
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Імпортуємо моделі
from models.base import Base
from models.user import User

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_sync_migrations():
    """Run migrations in 'online' mode."""
    asyncio.run(run_migrations_online())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_sync_migrations()
'''
    migrations_dir = Path('migrations')
    migrations_dir.mkdir(exist_ok=True)
    env_file = migrations_dir / 'env.py'
    env_file.write_text(env_content)

def create_directory_structure():
    """Створення структури директорій"""
    directories = [
        'logs',
        'migrations',
        'models',
        'handlers',
        'utils'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        init_file = Path(directory) / '__init__.py'
        init_file.touch(exist_ok=True)

def check_required_files():
    """Перевірка наявності необхідних файлів"""
    required_files = [
        'requirements.txt',
        '.env',
        'config.py',
        'alembic.ini'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("Відсутні необхідні файли:")
        for file in missing_files:
            print(f"- {file}")
        return False
    return True

def initialize_alembic():
    """Ініціалізація та налаштування Alembic"""
    print("Налаштування Alembic...")
    create_alembic_env()
    
    try:
        subprocess.run(['alembic', 'revision', '--autogenerate', '-m', 'Initial migration'], check=True)
        subprocess.run(['alembic', 'upgrade', 'head'], check=True)
        print("Міграції успішно створені та застосовані")
    except subprocess.CalledProcessError as e:
        print(f"Помилка при виконанні міграцій: {e}")
        return False
    return True

def main():
    print("Налаштування проекту...")
    
    if not check_required_files():
        return
    
    create_directory_structure()
    
    if not initialize_alembic():
        return
    
    print("Налаштування успішно завершено!")

if __name__ == '__main__':
    main() 