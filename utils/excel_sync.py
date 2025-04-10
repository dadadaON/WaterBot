import pandas as pd
from datetime import datetime
import asyncio
from sqlalchemy import select
from models.database import get_session
from models.request import ServiceRequest
from utils.logger import logger

class ExcelSync:
    def __init__(self, excel_path="database.xlsx"):
        self.excel_path = excel_path
        
    async def export_to_excel(self):
        """Експортує дані з БД в Excel файл"""
        try:
            logger.info("Starting export to Excel")
            async with get_session() as session:
                # Отримуємо всі записи з БД
                query = select(ServiceRequest)
                result = await session.execute(query)
                requests = result.scalars().all()
                
                # Конвертуємо в список словників
                data = []
                for request in requests:
                    data.append({
                        'ID': request.id,
                        'Ім\'я': request.full_name,
                        'Телефон': request.phone,
                        'Тип послуги': request.service_type,
                        'Населений пункт': request.settlement,
                        'Адреса': request.address if request.address else '',
                        'Питання': request.question if request.question else '',
                        'Створено': request.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                # Створюємо DataFrame
                df = pd.DataFrame(data)
                
                # Зберігаємо в Excel з форматуванням
                with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Заявки')
                    # Отримуємо об'єкт worksheet
                    worksheet = writer.sheets['Заявки']
                    
                    # Налаштовуємо ширину стовпців
                    for idx, col in enumerate(df.columns):
                        max_length = max(
                            df[col].astype(str).apply(len).max(),
                            len(str(col))
                        )
                        worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
                
                logger.info(f"Data exported to {self.excel_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            logger.exception("Full error traceback:")
            return False
    
    async def start_auto_sync(self, interval_minutes=5):
        """Запускає автоматичну синхронізацію з заданим інтервалом"""
        logger.info(f"Starting auto-sync with {interval_minutes} minutes interval")
        while True:
            try:
                await self.export_to_excel()
                await asyncio.sleep(interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in auto-sync: {str(e)}")
                await asyncio.sleep(60)  # Чекаємо хвилину перед повторною спробою 