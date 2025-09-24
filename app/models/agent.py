"""
Agent database models.
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Agent(Base):
    """Agent model."""
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    agent_type = Column(String(100), nullable=False)  # e.g., "llm", "tool", "workflow"
    status = Column(String(50), default="idle")  # idle, running, error, completed
    config = Column(JSON)  # Agent-specific configuration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")
    dependencies = relationship("AgentDependency", back_populates="agent", cascade="all, delete-orphan", foreign_keys="AgentDependency.agent_id")


class AgentExecution(Base):
    """Agent execution history."""
    __tablename__ = "agent_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String(50), default="running")  # running, completed, failed
    error_message = Column(Text)
    execution_time = Column(Integer)  # in milliseconds
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    agent = relationship("Agent", back_populates="executions")


class AgentDependency(Base):
    """Agent dependencies."""
    __tablename__ = "agent_dependencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    depends_on_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    dependency_type = Column(String(50), default="required")  # required, optional
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", back_populates="dependencies", foreign_keys=[agent_id])
    depends_on_agent = relationship("Agent", foreign_keys=[depends_on_agent_id])


class AgentMemory(Base):
    """Agent memory storage."""
    __tablename__ = "agent_memory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    memory_key = Column(String(255), nullable=False)
    memory_value = Column(JSON)
    memory_type = Column(String(50), default="episodic")  # episodic, semantic, procedural
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relationships
    agent = relationship("Agent")
