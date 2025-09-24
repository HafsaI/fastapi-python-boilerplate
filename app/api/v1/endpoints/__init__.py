"""
API endpoints for the AI Agents platform.
"""
from app.api.v1.endpoints.agents import router as agents_router
from app.api.v1.endpoints.chat import router as chat_router

__all__ = ["agents_router", "chat_router"]
