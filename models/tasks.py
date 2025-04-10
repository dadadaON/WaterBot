from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from models.base import Base

class CheckedTask(Base):
    __tablename__ = 'checked_tasks'

    task_id = Column(String, primary_key=True)
    checked_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<CheckedTask(task_id={self.task_id})>" 