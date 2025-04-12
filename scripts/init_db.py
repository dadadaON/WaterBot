import asyncio
import sys
import os

# Додаємо кореневу директорію проекту в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import Base
from models.database import async_engine
from models.request import ServiceRequest  # Додаємо імпорт моделі

async def init_db():
    print("Creating database tables...")
    async with async_engine.begin() as conn:
        # Видаляємо всі існуючі таблиці
        await conn.run_sync(Base.metadata.drop_all)
        # Створюємо таблиці заново
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")
    
    # Виводимо список створених таблиць
    print("\nCreated tables:")
    for table in Base.metadata.tables:
        print(f"- {table}")

if __name__ == "__main__":
    asyncio.run(init_db()) 