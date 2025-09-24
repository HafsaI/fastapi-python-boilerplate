from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
import json

class CustomerSessionBase(BaseModel):
    thread_id: Optional[str] = None
    customer_id: Optional[int] = None
    session_status: int = Field(default=1, ge=1, le=2)
    messages: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class CustomerSessionCreate(CustomerSessionBase):
    pass

class CustomerSessionUpdate(BaseModel):
    thread_id: Optional[str] = None
    customer_id: Optional[int] = None
    session_status: Optional[int] = Field(None, ge=1, le=2)
    messages: Optional[List[Dict[str, Any]]] = None
    deleted_at: Optional[datetime] = None

class CustomerSession(CustomerSessionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @validator('messages', pre=True)
    def parse_messages(cls, v):
        """Parse messages field from string to list if needed."""
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        if isinstance(v, list):
            return v
        return []

    class Config:
        from_attributes = True