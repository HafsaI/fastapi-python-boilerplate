"""
Pydantic schemas for the AI Agents platform.
"""
from app.schemas.agent import (
    Agent,
    AgentCreate,
    AgentUpdate,
    AgentInDB,
    AgentExecution,
    AgentExecutionCreate,
    AgentExecutionUpdate,
    AgentExecutionInDB,
    AgentDependency,
    AgentDependencyCreate,
    AgentDependencyInDB,
    AgentMemory,
    AgentMemoryCreate,
    AgentMemoryUpdate,
    AgentMemoryInDB,
    AgentWithDetails,
    AgentExecutionRequest,
    AgentExecutionResponse,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from app.schemas.customer_session import (
    CustomerSession,
    CustomerSessionCreate,
    CustomerSessionUpdate,
)
from app.schemas.product_request import (
    ProductRequest,
    ProductRequestCreate,
    ProductRequestUpdate,
)

__all__ = [
    "Agent",
    "AgentCreate",
    "AgentUpdate",
    "AgentInDB",
    "AgentExecution",
    "AgentExecutionCreate",
    "AgentExecutionUpdate",
    "AgentExecutionInDB",
    "AgentDependency",
    "AgentDependencyCreate",
    "AgentDependencyInDB",
    "AgentMemory",
    "AgentMemoryCreate",
    "AgentMemoryUpdate",
    "AgentMemoryInDB",
    "AgentWithDetails",
    "AgentExecutionRequest",
    "AgentExecutionResponse",
    "ChatRequest",
    "ChatResponse",
    "CustomerSession",
    "CustomerSessionCreate",
    "CustomerSessionUpdate",
    "ProductRequest",
    "ProductRequestCreate",
    "ProductRequestUpdate",
]
