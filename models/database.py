from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///database.db"

# Створюємо асинхронний двигун
async_engine = create_async_engine(
    DATABASE_URL,
    echo=True  # Для відображення SQL запитів в консолі
)

# Створюємо фабрику сесій
async_session = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Функція для отримання сесії
def get_session():
    return async_session() 