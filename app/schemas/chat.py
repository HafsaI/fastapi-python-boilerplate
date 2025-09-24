"""
Chat Pydantic schemas for API serialization.
"""
from typing import Optional, Dict, Any, Literal, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(..., min_length=1, max_length=10000)
    thread_id: Optional[str] = None
    customer_id: Optional[str] = None
    is_initial: Optional[bool] = False


class ChatResponse(BaseModel):
    """Schema for chat response."""
    message: str
    thread_id: str
    customer_id: str
    extracted_data: Optional[Dict[str, Any]] = None
    #extracted_products: Optional[List[Dict[str, Any]]] = None
    response: str
    #is_complete: Optional[bool] = None


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""
    type: Literal["message", "response", "error", "status"]
    data: Dict[str, Any]
    thread_id: Optional[str] = None
    customer_id: Optional[str] = None


class WebSocketChatRequest(BaseModel):
    """Schema for WebSocket chat request."""
    message: str = Field(..., min_length=1, max_length=10000)
    thread_id: Optional[str] = None
    customer_id: Optional[str] = None
    is_initial: Optional[bool] = False
