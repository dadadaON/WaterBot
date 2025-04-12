import asyncio
from migrations.add_question_column import migrate

async def run_migrations():
    await migrate()

if __name__ == "__main__":
    asyncio.run(run_migrations()) 