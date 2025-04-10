from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///bot.db"

# Створюємо асинхронний двигун
async_engine = create_async_engine(
    DATABASE_URL,
    echo=True  # Для відображення SQL запитів в консолі
)

# Створюємо фабрику сесій
async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    async with async_session() as session:
        yield session 