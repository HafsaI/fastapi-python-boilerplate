from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ProductRequestBase(BaseModel):
    customer_session_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: int = Field(default=0, ge=0)
    country: Optional[str] = None

class ProductRequestCreate(ProductRequestBase):
    pass

class ProductRequestUpdate(BaseModel):
    customer_session_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    country: Optional[str] = None
    deleted_at: Optional[datetime] = None

class ProductRequest(ProductRequestBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
