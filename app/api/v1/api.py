"""
API v1 router configuration.
"""
from fastapi import APIRouter
from app.api.v1.endpoints.chat import router as chat_router

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(chat_router, tags=["chat"])
