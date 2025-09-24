"""
Agent service layer for business logic.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncio
import time

from app.core.base import BaseService
from app.repositories.agent import (
    AgentRepository,
    AgentExecutionRepository,
    AgentDependencyRepository,
    AgentMemoryRepository,
)
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentExecutionCreate,
    AgentExecutionUpdate,
    AgentMemoryCreate,
    AgentMemoryUpdate,
    AgentExecutionRequest,
    AgentExecutionResponse,
)
from app.models.agent import Agent, AgentExecution
from app.core.logging import logger


class AgentService(BaseService[Agent]):
    """Service for Agent business logic."""
    
    def __init__(self, agent_repo: AgentRepository):
        super().__init__(agent_repo)
        self.agent_repo = agent_repo
        self.execution_repo = None
        self.dependency_repo = None
        self.memory_repo = None
    
    def set_repositories(
        self,
        execution_repo: AgentExecutionRepository,
        dependency_repo: AgentDependencyRepository,
        memory_repo: AgentMemoryRepository,
    ):
        """Set additional repositories."""
        self.execution_repo = execution_repo
        self.dependency_repo = dependency_repo
        self.memory_repo = memory_repo
    
    async def get(self, id: UUID) -> Optional[Agent]:
        """Get agent by ID."""
        return await self.agent_repo.get(id)
    
    async def get_by_name(self, name: str) -> Optional[Agent]:
        """Get agent by name."""
        return await self.agent_repo.get_by_name(name)
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Get multiple agents."""
        return await self.agent_repo.get_multi(skip, limit)
    
    async def get_active_agents(self) -> List[Agent]:
        """Get all active agents."""
        return await self.agent_repo.get_active_agents()
    
    async def get_by_type(self, agent_type: str) -> List[Agent]:
        """Get agents by type."""
        return await self.agent_repo.get_by_type(agent_type)
    
    async def create(self, obj_in: AgentCreate) -> Agent:
        """Create new agent."""
        # Check if agent with same name already exists
        existing_agent = await self.agent_repo.get_by_name(obj_in.name)
        if existing_agent:
            raise ValueError(f"Agent with name '{obj_in.name}' already exists")
        
        agent = await self.agent_repo.create(obj_in)
        logger.info(f"Created agent: {agent.name} ({agent.id})")
        return agent
    
    async def update(self, id: UUID, obj_in: AgentUpdate) -> Optional[Agent]:
        """Update agent."""
        # Check if name is being updated and if it conflicts
        if obj_in.name:
            existing_agent = await self.agent_repo.get_by_name(obj_in.name)
            if existing_agent and existing_agent.id != id:
                raise ValueError(f"Agent with name '{obj_in.name}' already exists")
        
        agent = await self.agent_repo.update(id, obj_in)
        if agent:
            logger.info(f"Updated agent: {agent.name} ({agent.id})")
        return agent
    
    async def delete(self, id: UUID) -> bool:
        """Delete agent."""
        agent = await self.agent_repo.get(id)
        if not agent:
            return False
        
        # Delete related data
        if self.execution_repo:
            executions = await self.execution_repo.get_by_agent(id)
            for execution in executions:
                await self.execution_repo.delete(execution.id)
        
        if self.dependency_repo:
            dependencies = await self.dependency_repo.get_by_agent(id)
            for dependency in dependencies:
                await self.dependency_repo.delete(dependency.id)
        
        if self.memory_repo:
            memories = await self.memory_repo.get_by_agent(id)
            for memory in memories:
                await self.memory_repo.delete(memory.id)
        
        success = await self.agent_repo.delete(id)
        if success:
            logger.info(f"Deleted agent: {agent.name} ({agent.id})")
        return success
    
    async def update_status(self, id: UUID, status: str) -> Optional[Agent]:
        """Update agent status."""
        agent = await self.agent_repo.update_status(id, status)
        if agent:
            logger.info(f"Updated agent status: {agent.name} -> {status}")
        return agent
    
    async def add_dependency(self, agent_id: UUID, depends_on_agent_id: UUID, dependency_type: str = "required") -> bool:
        """Add dependency between agents."""
        if not self.dependency_repo:
            raise ValueError("Dependency repository not set")
        
        # Check if dependency already exists
        dependencies = await self.dependency_repo.get_by_agent(agent_id)
        for dep in dependencies:
            if dep.depends_on_agent_id == depends_on_agent_id:
                return False
        
        # Check for circular dependencies
        if await self._check_circular_dependency(agent_id, depends_on_agent_id):
            raise ValueError("Circular dependency detected")
        
        from app.schemas.agent import AgentDependencyCreate
        dependency_data = AgentDependencyCreate(
            agent_id=agent_id,
            depends_on_agent_id=depends_on_agent_id,
            dependency_type=dependency_type,
        )
        
        await self.dependency_repo.create(dependency_data)
        logger.info(f"Added dependency: {agent_id} -> {depends_on_agent_id}")
        return True
    
    async def remove_dependency(self, agent_id: UUID, depends_on_agent_id: UUID) -> bool:
        """Remove dependency between agents."""
        if not self.dependency_repo:
            raise ValueError("Dependency repository not set")
        
        dependencies = await self.dependency_repo.get_by_agent(agent_id)
        for dep in dependencies:
            if dep.depends_on_agent_id == depends_on_agent_id:
                success = await self.dependency_repo.delete(dep.id)
                if success:
                    logger.info(f"Removed dependency: {agent_id} -> {depends_on_agent_id}")
                return success
        return False
    
    async def get_dependencies(self, agent_id: UUID) -> List[Dict[str, Any]]:
        """Get agent dependencies."""
        if not self.dependency_repo:
            return []
        
        dependencies = await self.dependency_repo.get_by_agent(agent_id)
        return [
            {
                "id": str(dep.id),
                "depends_on_agent_id": str(dep.depends_on_agent_id),
                "dependency_type": dep.dependency_type,
                "created_at": dep.created_at.isoformat(),
            }
            for dep in dependencies
        ]
    
    async def _check_circular_dependency(self, agent_id: UUID, depends_on_agent_id: UUID) -> bool:
        """Check for circular dependencies."""
        if agent_id == depends_on_agent_id:
            return True
        
        # Get dependencies of the target agent
        target_dependencies = await self.dependency_repo.get_by_agent(depends_on_agent_id)
        for dep in target_dependencies:
            if dep.depends_on_agent_id == agent_id:
                return True
            # Recursive check
            if await self._check_circular_dependency(agent_id, dep.depends_on_agent_id):
                return True
        
        return False


class AgentExecutionService(BaseService[AgentExecution]):
    """Service for AgentExecution business logic."""
    
    def __init__(self, execution_repo: AgentExecutionRepository):
        super().__init__(execution_repo)
        self.execution_repo = execution_repo
    
    async def get(self, id: UUID) -> Optional[AgentExecution]:
        """Get execution by ID."""
        return await self.execution_repo.get(id)
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[AgentExecution]:
        """Get multiple executions."""
        return await self.execution_repo.get_multi(skip, limit)
    
    async def get_by_agent(self, agent_id: UUID, skip: int = 0, limit: int = 100) -> List[AgentExecution]:
        """Get executions by agent ID."""
        return await self.execution_repo.get_by_agent(agent_id, skip, limit)
    
    async def create(self, obj_in: AgentExecutionCreate) -> AgentExecution:
        """Create new execution."""
        execution = await self.execution_repo.create(obj_in)
        logger.info(f"Created execution: {execution.id} for agent {execution.agent_id}")
        return execution
    
    async def update(self, id: UUID, obj_in: AgentExecutionUpdate) -> Optional[AgentExecution]:
        """Update execution."""
        execution = await self.execution_repo.update(id, obj_in)
        if execution:
            logger.info(f"Updated execution: {execution.id}")
        return execution
    
    async def delete(self, id: UUID) -> bool:
        """Delete execution."""
        success = await self.execution_repo.delete(id)
        if success:
            logger.info(f"Deleted execution: {id}")
        return success
    
    async def execute_agent(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        """Execute an agent with input data."""
        # Create execution record
        execution_data = AgentExecutionCreate(
            agent_id=request.agent_id,
            input_data=request.input_data,
            status="running",
        )
        execution = await self.create(execution_data)
        
        start_time = time.time()
        
        try:
            # Here you would implement the actual agent execution logic
            # This is a placeholder for the agent execution
            await asyncio.sleep(0.1)  # Simulate processing
            
            # Update execution with success
            execution_time = int((time.time() - start_time) * 1000)
            update_data = AgentExecutionUpdate(
                output_data={"result": "Agent executed successfully"},
                status="completed",
                execution_time=execution_time,
                completed_at=datetime.utcnow(),
            )
            execution = await self.update(execution.id, update_data)
            
            return AgentExecutionResponse(
                execution_id=execution.id,
                status=execution.status,
                output_data=execution.output_data,
                execution_time=execution.execution_time,
            )
            
        except Exception as e:
            # Update execution with error
            execution_time = int((time.time() - start_time) * 1000)
            update_data = AgentExecutionUpdate(
                status="failed",
                error_message=str(e),
                execution_time=execution_time,
                completed_at=datetime.utcnow(),
            )
            execution = await self.update(execution.id, update_data)
            
            logger.error(f"Agent execution failed: {execution.id} - {str(e)}")
            
            return AgentExecutionResponse(
                execution_id=execution.id,
                status=execution.status,
                error_message=execution.error_message,
                execution_time=execution.execution_time,
            )


class AgentMemoryService(BaseService):
    """Service for AgentMemory business logic."""
    
    def __init__(self, memory_repo: AgentMemoryRepository):
        super().__init__(memory_repo)
        self.memory_repo = memory_repo
    
    async def get(self, id: UUID) -> Optional[Any]:
        """Get memory by ID."""
        return await self.memory_repo.get(id)
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get multiple memories."""
        return await self.memory_repo.get_multi(skip, limit)
    
    async def get_by_agent(self, agent_id: UUID) -> List[Any]:
        """Get memories by agent ID."""
        return await self.memory_repo.get_by_agent(agent_id)
    
    async def get_by_key(self, agent_id: UUID, memory_key: str) -> Optional[Any]:
        """Get memory by agent ID and key."""
        return await self.memory_repo.get_by_key(agent_id, memory_key)
    
    async def create(self, obj_in: AgentMemoryCreate) -> Any:
        """Create new memory."""
        memory = await self.memory_repo.create(obj_in)
        logger.info(f"Created memory: {memory.memory_key} for agent {memory.agent_id}")
        return memory
    
    async def update(self, id: UUID, obj_in: AgentMemoryUpdate) -> Optional[Any]:
        """Update memory."""
        memory = await self.memory_repo.update(id, obj_in)
        if memory:
            logger.info(f"Updated memory: {memory.id}")
        return memory
    
    async def delete(self, id: UUID) -> bool:
        """Delete memory."""
        success = await self.memory_repo.delete(id)
        if success:
            logger.info(f"Deleted memory: {id}")
        return success
    
    async def set_memory(self, agent_id: UUID, memory_key: str, memory_value: Dict[str, Any], memory_type: str = "episodic", expires_at: Optional[datetime] = None) -> Any:
        """Set memory for an agent."""
        # Check if memory already exists
        existing_memory = await self.get_by_key(agent_id, memory_key)
        
        if existing_memory:
            # Update existing memory
            update_data = AgentMemoryUpdate(
                memory_value=memory_value,
                memory_type=memory_type,
                expires_at=expires_at,
            )
            return await self.update(existing_memory.id, update_data)
        else:
            # Create new memory
            memory_data = AgentMemoryCreate(
                agent_id=agent_id,
                memory_key=memory_key,
                memory_value=memory_value,
                memory_type=memory_type,
                expires_at=expires_at,
            )
            return await self.create(memory_data)
    
    async def get_memory(self, agent_id: UUID, memory_key: str) -> Optional[Dict[str, Any]]:
        """Get memory value for an agent."""
        memory = await self.get_by_key(agent_id, memory_key)
        if memory:
            # Check if memory has expired
            if memory.expires_at and memory.expires_at < datetime.utcnow():
                await self.delete(memory.id)
                return None
            return memory.memory_value
        return None
