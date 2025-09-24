"""
Agent API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_async_db
from app.repositories.agent import (
    AgentRepository,
    AgentExecutionRepository,
    AgentDependencyRepository,
    AgentMemoryRepository,
)
from app.services.agent import (
    AgentService,
    AgentExecutionService,
    AgentMemoryService,
)
from app.schemas.agent import (
    Agent,
    AgentCreate,
    AgentUpdate,
    AgentWithDetails,
    AgentExecution,
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentMemory,
    AgentMemoryCreate,
    AgentMemoryUpdate,
)

router = APIRouter()


def get_agent_service(db: AsyncSession = Depends(get_async_db)) -> AgentService:
    """Get agent service with all repositories."""
    agent_repo = AgentRepository(db)
    execution_repo = AgentExecutionRepository(db)
    dependency_repo = AgentDependencyRepository(db)
    memory_repo = AgentMemoryRepository(db)
    
    service = AgentService(agent_repo)
    service.set_repositories(execution_repo, dependency_repo, memory_repo)
    return service


def get_execution_service(db: AsyncSession = Depends(get_async_db)) -> AgentExecutionService:
    """Get execution service."""
    execution_repo = AgentExecutionRepository(db)
    return AgentExecutionService(execution_repo)


def get_memory_service(db: AsyncSession = Depends(get_async_db)) -> AgentMemoryService:
    """Get memory service."""
    memory_repo = AgentMemoryRepository(db)
    return AgentMemoryService(memory_repo)


@router.get("/", response_model=List[Agent])
async def get_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_type: Optional[str] = None,
    active_only: bool = Query(False),
    service: AgentService = Depends(get_agent_service),
):
    """Get all agents."""
    if agent_type:
        return await service.get_by_type(agent_type)
    elif active_only:
        return await service.get_active_agents()
    else:
        return await service.get_multi(skip, limit)


@router.get("/{agent_id}", response_model=AgentWithDetails)
async def get_agent(
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
):
    """Get agent by ID."""
    agent = await service.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    return agent


@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_in: AgentCreate,
    service: AgentService = Depends(get_agent_service),
):
    """Create new agent."""
    try:
        return await service.create(agent_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: UUID,
    agent_in: AgentUpdate,
    service: AgentService = Depends(get_agent_service),
):
    """Update agent."""
    try:
        agent = await service.update(agent_id, agent_in)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        return agent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
):
    """Delete agent."""
    success = await service.delete(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )


@router.patch("/{agent_id}/status", response_model=Agent)
async def update_agent_status(
    agent_id: UUID,
    status: str,
    service: AgentService = Depends(get_agent_service),
):
    """Update agent status."""
    agent = await service.update_status(agent_id, status)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    return agent


@router.get("/{agent_id}/dependencies")
async def get_agent_dependencies(
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
):
    """Get agent dependencies."""
    dependencies = await service.get_dependencies(agent_id)
    return {"dependencies": dependencies}


@router.post("/{agent_id}/dependencies")
async def add_agent_dependency(
    agent_id: UUID,
    depends_on_agent_id: UUID,
    dependency_type: str = "required",
    service: AgentService = Depends(get_agent_service),
):
    """Add dependency to agent."""
    try:
        success = await service.add_dependency(agent_id, depends_on_agent_id, dependency_type)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dependency already exists"
            )
        return {"message": "Dependency added successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{agent_id}/dependencies/{depends_on_agent_id}")
async def remove_agent_dependency(
    agent_id: UUID,
    depends_on_agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
):
    """Remove dependency from agent."""
    success = await service.remove_dependency(agent_id, depends_on_agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found"
        )
    return {"message": "Dependency removed successfully"}


@router.post("/{agent_id}/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    agent_id: UUID,
    request: AgentExecutionRequest,
    execution_service: AgentExecutionService = Depends(get_execution_service),
):
    """Execute an agent."""
    # Override agent_id from URL
    request.agent_id = agent_id
    
    try:
        return await execution_service.execute_agent(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )


@router.get("/{agent_id}/executions", response_model=List[AgentExecution])
async def get_agent_executions(
    agent_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    execution_service: AgentExecutionService = Depends(get_execution_service),
):
    """Get agent execution history."""
    return await execution_service.get_by_agent(agent_id, skip, limit)


@router.get("/{agent_id}/memory", response_model=List[AgentMemory])
async def get_agent_memory(
    agent_id: UUID,
    memory_service: AgentMemoryService = Depends(get_memory_service),
):
    """Get agent memory."""
    return await memory_service.get_by_agent(agent_id)


@router.post("/{agent_id}/memory", response_model=AgentMemory)
async def set_agent_memory(
    agent_id: UUID,
    memory_in: AgentMemoryCreate,
    memory_service: AgentMemoryService = Depends(get_memory_service),
):
    """Set agent memory."""
    # Override agent_id from URL
    memory_in.agent_id = agent_id
    return await memory_service.create(memory_in)


@router.get("/{agent_id}/memory/{memory_key}")
async def get_agent_memory_by_key(
    agent_id: UUID,
    memory_key: str,
    memory_service: AgentMemoryService = Depends(get_memory_service),
):
    """Get specific memory by key."""
    memory = await memory_service.get_by_key(agent_id, memory_key)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    return memory


@router.put("/{agent_id}/memory/{memory_key}")
async def update_agent_memory(
    agent_id: UUID,
    memory_key: str,
    memory_value: dict,
    memory_type: str = "episodic",
    memory_service: AgentMemoryService = Depends(get_memory_service),
):
    """Update agent memory."""
    memory = await memory_service.set_memory(agent_id, memory_key, memory_value, memory_type)
    return memory


@router.delete("/{agent_id}/memory/{memory_key}")
async def delete_agent_memory(
    agent_id: UUID,
    memory_key: str,
    memory_service: AgentMemoryService = Depends(get_memory_service),
):
    """Delete agent memory."""
    memory = await memory_service.get_by_key(agent_id, memory_key)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    success = await memory_service.delete(memory.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )
    
    return {"message": "Memory deleted successfully"}
