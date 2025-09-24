"""
Agent Pydantic schemas for API serialization.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class AgentBase(BaseModel):
    """Base agent schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    agent_type: str = Field(..., min_length=1, max_length=100)
    config: Optional[Dict[str, Any]] = None


class AgentCreate(AgentBase):
    """Schema for creating an agent."""
    pass


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    agent_type: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class AgentInDB(AgentBase):
    """Schema for agent in database."""
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class Agent(AgentInDB):
    """Schema for agent response."""
    pass


class AgentExecutionBase(BaseModel):
    """Base agent execution schema."""
    input_data: Optional[Dict[str, Any]] = None


class AgentExecutionCreate(AgentExecutionBase):
    """Schema for creating an agent execution."""
    agent_id: UUID


class AgentExecutionUpdate(BaseModel):
    """Schema for updating an agent execution."""
    output_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[int] = None
    completed_at: Optional[datetime] = None


class AgentExecutionInDB(AgentExecutionBase):
    """Schema for agent execution in database."""
    id: UUID
    agent_id: UUID
    output_data: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    execution_time: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AgentExecution(AgentExecutionInDB):
    """Schema for agent execution response."""
    pass


class AgentDependencyBase(BaseModel):
    """Base agent dependency schema."""
    depends_on_agent_id: UUID
    dependency_type: str = Field(default="required")


class AgentDependencyCreate(AgentDependencyBase):
    """Schema for creating an agent dependency."""
    agent_id: UUID


class AgentDependencyInDB(AgentDependencyBase):
    """Schema for agent dependency in database."""
    id: UUID
    agent_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentDependency(AgentDependencyInDB):
    """Schema for agent dependency response."""
    pass


class AgentMemoryBase(BaseModel):
    """Base agent memory schema."""
    memory_key: str = Field(..., min_length=1, max_length=255)
    memory_value: Optional[Dict[str, Any]] = None
    memory_type: str = Field(default="episodic")


class AgentMemoryCreate(AgentMemoryBase):
    """Schema for creating agent memory."""
    agent_id: UUID
    expires_at: Optional[datetime] = None


class AgentMemoryUpdate(BaseModel):
    """Schema for updating agent memory."""
    memory_value: Optional[Dict[str, Any]] = None
    memory_type: Optional[str] = None
    expires_at: Optional[datetime] = None


class AgentMemoryInDB(AgentMemoryBase):
    """Schema for agent memory in database."""
    id: UUID
    agent_id: UUID
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AgentMemory(AgentMemoryInDB):
    """Schema for agent memory response."""
    pass


class AgentWithDetails(Agent):
    """Schema for agent with related data."""
    executions: List[AgentExecution] = []
    dependencies: List[AgentDependency] = []


class AgentExecutionRequest(BaseModel):
    """Schema for agent execution request."""
    agent_id: UUID
    input_data: Dict[str, Any]
    timeout: Optional[int] = None


class AgentExecutionResponse(BaseModel):
    """Schema for agent execution response."""
    execution_id: UUID
    status: str
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[int] = None
