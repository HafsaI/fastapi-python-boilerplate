from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from datetime import datetime

from app.core.base import BaseRepository
from app.models.customer_session import CustomerSession
from app.models.product_request import ProductRequest
from app.schemas.customer_session import CustomerSessionCreate, CustomerSessionUpdate

class ChatRepository(BaseRepository[CustomerSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.model = CustomerSession
    
    async def get(self, id: int) -> Optional[CustomerSession]:
        result = await self.db.execute(
            select(CustomerSession).where(CustomerSession.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[CustomerSession]:
        result = await self.db.execute(
            select(CustomerSession)
            .offset(skip)
            .limit(limit)
            .order_by(CustomerSession.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_customer_session(self, thread_id: str, customer_id: int = None) -> Optional[CustomerSession]:
        result = await self.db.execute(
            select(CustomerSession).where(CustomerSession.thread_id == thread_id, CustomerSession.customer_id == customer_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_customer_id(self, customer_id: int) -> List[CustomerSession]:
        result = await self.db.execute(
            select(CustomerSession)
            .where(CustomerSession.customer_id == customer_id)
            .order_by(CustomerSession.created_at.desc())
        )
        return result.scalars().all()
    
    async def create(self, obj_in: CustomerSessionCreate) -> CustomerSession:
        db_obj = CustomerSession(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def insert_session(self, session_status: int = 1, thread_id: str = None, customer_id: int = None) -> CustomerSession:
        db_obj = CustomerSession(
            session_status=session_status,
            thread_id=thread_id,
            customer_id=customer_id,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: int, obj_in: CustomerSessionUpdate) -> Optional[CustomerSession]:
        update_data = obj_in.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await self.db.execute(
                update(CustomerSession)
                .where(CustomerSession.id == id)
                .values(**update_data)
            )
            await self.db.commit()
        return await self.get(id)
    
    async def delete(self, id: int) -> bool:
        result = await self.db.execute(
            delete(CustomerSession).where(CustomerSession.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def insert_message(self, session_id: int, messages: str = None, session_status: int = 1) -> bool:
        """Insert a message into the messages JSONB column for a session."""
        try:
            if session_status is not None:
                 await self.db.execute(
                update(CustomerSession)
                .where(CustomerSession.id == session_id)
                .values(messages=messages, session_status=session_status, updated_at=datetime.utcnow())
            )
            else:
                await self.db.execute(
                update(CustomerSession)
                .where(CustomerSession.id == session_id)
                .values(messages=messages, updated_at=datetime.utcnow())
            )
           
            await self.db.commit()
            
            print(f"Message inserted for session_id: {session_id}")
            return True
            
        except Exception as e:
            print(f"Error inserting message: {e}")
            await self.db.rollback()
            return False
    
    async def create_multiple_product_requests(self, product_requests: List[Dict[str, Any]]) -> List[ProductRequest]:
        """Create multiple product requests in a single transaction."""
        try:
            db_objects = []
            for pr_data in product_requests:
                db_obj = ProductRequest(
                    customer_session_id=pr_data.get("customer_session_id"),
                    product_name=pr_data.get("product_name"),
                    quantity=pr_data.get("quantity", 0),
                    country=pr_data.get("country")
                )
                db_objects.append(db_obj)
            
            self.db.add_all(db_objects)
            await self.db.commit()
            for obj in db_objects:
                await self.db.refresh(obj)
            return db_objects
            
        except Exception as e:
            print(f"Error creating product requests: {e}")
            await self.db.rollback()
            return []
    
    async def get_product_requests_by_session_id(self, customer_session_id: int) -> List[ProductRequest]:
        """Get all product requests for a specific customer session."""
        result = await self.db.execute(
            select(ProductRequest)
            .where(ProductRequest.customer_session_id == customer_session_id)
            .order_by(ProductRequest.created_at.desc())
        )
        return result.scalars().all()