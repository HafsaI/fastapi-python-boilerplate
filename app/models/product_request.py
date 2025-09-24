from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class ProductRequest(Base):
    __tablename__ = "product_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_session_id = Column(Integer, ForeignKey("customer_sessions.id"), nullable=True)
    product_name = Column(String(255), nullable=True)
    quantity = Column(Integer, default=0, nullable=False)
    country = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
