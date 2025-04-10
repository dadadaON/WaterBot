from sqlalchemy import text
from models.database import async_engine

async def migrate():
    async with async_engine.begin() as conn:
        # Додаємо нову колонку
        await conn.execute(
            text("ALTER TABLE service_requests ADD COLUMN question TEXT;")
        ) 