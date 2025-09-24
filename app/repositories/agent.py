"""
Agent repository for database operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime

from app.core.base import BaseRepository
from app.models.agent import Agent, AgentExecution, AgentDependency, AgentMemory
from app.schemas.agent import (
    AgentCreate, 
    AgentUpdate, 
    AgentExecutionCreate, 
    AgentExecutionUpdate,
    AgentDependencyCreate,
    AgentMemoryCreate,
    AgentMemoryUpdate
)


class AgentRepository(BaseRepository[Agent]):
    """Repository for Agent model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.model = Agent
    
    async def get(self, id: UUID) -> Optional[Agent]:
        """Get agent by ID."""
        result = await self.db.execute(
            select(Agent)
            .options(selectinload(Agent.executions), selectinload(Agent.dependencies))
            .where(Agent.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Agent]:
        """Get agent by name."""
        result = await self.db.execute(
            select(Agent).where(Agent.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Get multiple agents."""
        result = await self.db.execute(
            select(Agent)
            .offset(skip)
            .limit(limit)
            .order_by(Agent.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_active_agents(self) -> List[Agent]:
        """Get all active agents."""
        result = await self.db.execute(
            select(Agent).where(Agent.is_active == True)
        )
        return result.scalars().all()
    
    async def get_by_type(self, agent_type: str) -> List[Agent]:
        """Get agents by type."""
        result = await self.db.execute(
            select(Agent).where(Agent.agent_type == agent_type)
        )
        return result.scalars().all()
    
    async def create(self, obj_in: AgentCreate) -> Agent:
        """Create new agent."""
        db_obj = Agent(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: UUID, obj_in: AgentUpdate) -> Optional[Agent]:
        """Update agent."""
        update_data = obj_in.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await self.db.execute(
                update(Agent)
                .where(Agent.id == id)
                .values(**update_data)
            )
            await self.db.commit()
        return await self.get(id)
    
    async def delete(self, id: UUID) -> bool:
        """Delete agent."""
        result = await self.db.execute(
            delete(Agent).where(Agent.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def update_status(self, id: UUID, status: str) -> Optional[Agent]:
        """Update agent status."""
        await self.db.execute(
            update(Agent)
            .where(Agent.id == id)
            .values(status=status, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return await self.get(id)


class AgentExecutionRepository(BaseRepository[AgentExecution]):
    """Repository for AgentExecution model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.model = AgentExecution
    
    async def get(self, id: UUID) -> Optional[AgentExecution]:
        """Get execution by ID."""
        result = await self.db.execute(
            select(AgentExecution).where(AgentExecution.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[AgentExecution]:
        """Get multiple executions."""
        result = await self.db.execute(
            select(AgentExecution)
            .offset(skip)
            .limit(limit)
            .order_by(AgentExecution.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_by_agent(self, agent_id: UUID, skip: int = 0, limit: int = 100) -> List[AgentExecution]:
        """Get executions by agent ID."""
        result = await self.db.execute(
            select(AgentExecution)
            .where(AgentExecution.agent_id == agent_id)
            .offset(skip)
            .limit(limit)
            .order_by(AgentExecution.created_at.desc())
        )
        return result.scalars().all()
    
    async def create(self, obj_in: AgentExecutionCreate) -> AgentExecution:
        """Create new execution."""
        db_obj = AgentExecution(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: UUID, obj_in: AgentExecutionUpdate) -> Optional[AgentExecution]:
        """Update execution."""
        update_data = obj_in.dict(exclude_unset=True)
        if update_data:
            await self.db.execute(
                update(AgentExecution)
                .where(AgentExecution.id == id)
                .values(**update_data)
            )
            await self.db.commit()
        return await self.get(id)
    
    async def delete(self, id: UUID) -> bool:
        """Delete execution."""
        result = await self.db.execute(
            delete(AgentExecution).where(AgentExecution.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0


class AgentDependencyRepository(BaseRepository[AgentDependency]):
    """Repository for AgentDependency model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.model = AgentDependency
    
    async def get(self, id: UUID) -> Optional[AgentDependency]:
        """Get dependency by ID."""
        result = await self.db.execute(
            select(AgentDependency).where(AgentDependency.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[AgentDependency]:
        """Get multiple dependencies."""
        result = await self.db.execute(
            select(AgentDependency)
            .offset(skip)
            .limit(limit)
            .order_by(AgentDependency.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_by_agent(self, agent_id: UUID) -> List[AgentDependency]:
        """Get dependencies by agent ID."""
        result = await self.db.execute(
            select(AgentDependency).where(AgentDependency.agent_id == agent_id)
        )
        return result.scalars().all()
    
    async def create(self, obj_in: AgentDependencyCreate) -> AgentDependency:
        """Create new dependency."""
        db_obj = AgentDependency(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: UUID, obj_in: AgentDependencyCreate) -> Optional[AgentDependency]:
        """Update dependency."""
        update_data = obj_in.dict(exclude_unset=True)
        if update_data:
            await self.db.execute(
                update(AgentDependency)
                .where(AgentDependency.id == id)
                .values(**update_data)
            )
            await self.db.commit()
        return await self.get(id)
    
    async def delete(self, id: UUID) -> bool:
        """Delete dependency."""
        result = await self.db.execute(
            delete(AgentDependency).where(AgentDependency.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0


class AgentMemoryRepository(BaseRepository[AgentMemory]):
    """Repository for AgentMemory model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.model = AgentMemory
    
    async def get(self, id: UUID) -> Optional[AgentMemory]:
        """Get memory by ID."""
        result = await self.db.execute(
            select(AgentMemory).where(AgentMemory.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[AgentMemory]:
        """Get multiple memories."""
        result = await self.db.execute(
            select(AgentMemory)
            .offset(skip)
            .limit(limit)
            .order_by(AgentMemory.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_by_agent(self, agent_id: UUID) -> List[AgentMemory]:
        """Get memories by agent ID."""
        result = await self.db.execute(
            select(AgentMemory).where(AgentMemory.agent_id == agent_id)
        )
        return result.scalars().all()
    
    async def get_by_key(self, agent_id: UUID, memory_key: str) -> Optional[AgentMemory]:
        """Get memory by agent ID and key."""
        result = await self.db.execute(
            select(AgentMemory).where(
                and_(
                    AgentMemory.agent_id == agent_id,
                    AgentMemory.memory_key == memory_key
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create(self, obj_in: AgentMemoryCreate) -> AgentMemory:
        """Create new memory."""
        db_obj = AgentMemory(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: UUID, obj_in: AgentMemoryUpdate) -> Optional[AgentMemory]:
        """Update memory."""
        update_data = obj_in.dict(exclude_unset=True)
        if update_data:
            await self.db.execute(
                update(AgentMemory)
                .where(AgentMemory.id == id)
                .values(**update_data)
            )
            await self.db.commit()
        return await self.get(id)
    
    async def delete(self, id: UUID) -> bool:
        """Delete memory."""
        result = await self.db.execute(
            delete(AgentMemory).where(AgentMemory.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
