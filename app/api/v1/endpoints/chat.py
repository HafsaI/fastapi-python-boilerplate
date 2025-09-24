"""
Chat API endpoints.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from typing import List
import uuid, random
import json

from app.schemas.chat import ChatRequest, ChatResponse, WebSocketChatRequest
from app.schemas.customer_session import CustomerSession
from app.services.chat import ChatService
from app.repositories.chat import ChatRepository
from app.core.database import get_async_db
from app.core.logging import logger

router = APIRouter()

connections = {}

def get_chat_service(db = Depends(get_async_db)) -> ChatService:
    """Get ChatService with repository dependency."""
    chat_repository = ChatRepository(db)
    return ChatService(chat_repository=chat_repository)

async def get_chat_service_async() -> ChatService:
    """Get ChatService with repository for async contexts (like WebSocket)."""
    async for db in get_async_db():
        chat_repository = ChatRepository(db)
        return ChatService(chat_repository=chat_repository)

@router.post("/chat", response_model=ChatResponse)
def chat_with_bot(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    """
    Process a customer message through the LangGraph workflow.
    """
    try:
        result = chat_service.process_message(
            message=request.message,
            thread_id=request.thread_id,
            customer_id=request.customer_id
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/sessions", response_model=List[CustomerSession])
async def get_all_sessions(
    customer_id: str = None,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get customer sessions with optional filtering by customer_id and pagination.
    """
    try:
        sessions = await chat_service.get_all_sessions(
            customer_id=customer_id,
        )
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")

@router.get("/sessions/{session_id}", response_model=CustomerSession)
async def get_session_by_id(
    session_id: int, 
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get a specific session by ID with all fields including messages as array of objects.
    """
    try:
        session = await chat_service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()    
    chat_service = await get_chat_service_async()
    
    initial_thread_id = chat_service.create_openai_thread()
    connections[websocket] = {
        "thread_id": initial_thread_id, 
    }

    error_message = {
        "status": "error",
        "message": "Let us fix the issue. Please try after some time.",
    }

    try:
        while True:
            # Receive message from frontend
            raw_data = await websocket.receive_text()
            
            try:
                # Parse as JSON into native python object
                data = json.loads(raw_data)
                
                # Validate the structure + if initial set initial thread id
                if isinstance(data, dict) and "message" in data and "customer_id" in data:
                    message = data["message"]
                    thread_id = data.get("thread_id", initial_thread_id)
                    customer_id = data.get("customer_id")
                    is_initial = data.get("is_initial", False)
                    
                    # Update connection info 
                    connections[websocket]["thread_id"] = thread_id
                    connections[websocket]["customer_id"] = customer_id
                        
                else:
                    await websocket.send_json(error_message)
                    await websocket.close(code=1000, reason="Conversation Error")
                    
            except json.JSONDecodeError:

                await websocket.send_json(error_message)
                await websocket.close(code=1000, reason="Conversation Error")
           
            # Process with ChatService
            result = await chat_service.process_customer_message(
                message=message,
                thread_id=thread_id,
                customer_id=customer_id,
                is_initial=is_initial
            )    
            await websocket.send_json(result)    
            
            # Check if conversation is complete
            if result.get("is_complete", False):
                completion_message = {
                    "status": "complete",
                    "message": "Conversation completed successfully! Connection will be closed.",
                    "data": result["extracted_data"],
                    "thread_id": thread_id,
                    "customer_id": customer_id
                }
                await websocket.send_json(completion_message)                
                await websocket.close(code=1000, reason="Conversation completed")
                break  

    except WebSocketDisconnect:
        if websocket in connections:
            del connections[websocket]
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in connections:
            del connections[websocket]