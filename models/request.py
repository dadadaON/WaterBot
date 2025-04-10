from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from .base import Base

class ServiceRequest(Base):
    __tablename__ = 'service_requests'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)  # Формат: (___)___-__-__
    settlement = Column(String, nullable=False)  # Населений пункт
    address = Column(String, nullable=True)
    service_type = Column(String, nullable=False)
    question = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow) 