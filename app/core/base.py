"""
Base classes for the AI Agents platform.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.core.database import Base

# Type variables
T = TypeVar('T', bound=Base)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class BaseModelMixin(Base):
    """Base model mixin with common fields."""
    __abstract__ = True
    
    id = None  # Will be defined in subclasses
    created_at = None
    updated_at = None
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Add common fields to subclasses
        if not hasattr(cls, 'id'):
            cls.id = None  # Will be properly defined in subclasses
        if not hasattr(cls, 'created_at'):
            cls.created_at = None
        if not hasattr(cls, 'updated_at'):
            cls.updated_at = None


class BaseRepository(ABC, Generic[T]):
    """Base repository class for database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get multiple entities."""
        pass
    
    @abstractmethod
    async def create(self, obj_in: CreateSchemaType) -> T:
        """Create new entity."""
        pass
    
    @abstractmethod
    async def update(self, id: Any, obj_in: UpdateSchemaType) -> Optional[T]:
        """Update entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete entity."""
        pass


class BaseService(ABC, Generic[T]):
    """Base service class for business logic."""
    
    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository
    
    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get multiple entities."""
        pass
    
    @abstractmethod
    async def create(self, obj_in: CreateSchemaType) -> T:
        """Create new entity."""
        pass
    
    @abstractmethod
    async def update(self, id: Any, obj_in: UpdateSchemaType) -> Optional[T]:
        """Update entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete entity."""
        pass


class BaseController(ABC):
    """Base controller class for API endpoints."""
    
    def __init__(self, service: BaseService):
        self.service = service
    
    @abstractmethod
    async def get(self, id: Any) -> Any:
        """Get entity endpoint."""
        pass
    
    @abstractmethod
    async def get_multi(self, skip: int = 0, limit: int = 100) -> Any:
        """Get multiple entities endpoint."""
        pass
    
    @abstractmethod
    async def create(self, obj_in: Any) -> Any:
        """Create entity endpoint."""
        pass
    
    @abstractmethod
    async def update(self, id: Any, obj_in: Any) -> Any:
        """Update entity endpoint."""
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> Any:
        """Delete entity endpoint."""
        pass


class AgentBase(ABC):
    """Base class for AI agents."""
    
    def __init__(self, agent_id: str, name: str, description: str = ""):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.status = "idle"
        self.created_at = datetime.utcnow()
        self.dependencies: List[str] = []
        self.memory: Dict[str, Any] = {}
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main functionality."""
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "dependencies": self.dependencies,
        }
    
    async def add_dependency(self, agent_id: str):
        """Add a dependency to another agent."""
        if agent_id not in self.dependencies:
            self.dependencies.append(agent_id)
    
    async def remove_dependency(self, agent_id: str):
        """Remove a dependency."""
        if agent_id in self.dependencies:
            self.dependencies.remove(agent_id)
