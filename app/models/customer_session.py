from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base

class CustomerSession(Base):
    __tablename__ = "customer_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(255), nullable=True)
    customer_id = Column(Integer, nullable=True)
    session_status = Column(Integer, default=1, nullable=True)
    messages = Column(JSONB, default='[]', nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)