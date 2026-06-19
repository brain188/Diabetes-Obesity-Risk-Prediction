"""
Base repository class with common CRUD operations.
All repositories inherit from this base class.
"""

import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.database import Base
from app.core.exceptions import DatabaseError, NotFoundError

# Set up logger
logger = logging.getLogger(__name__)

# Generic type for model
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.
    
    Attributes:
        model: SQLAlchemy model class
        session: Async database session
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository with model and session.
        
        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session
    
    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record.
        
        Args:
            **kwargs: Model field values
            
        Returns:
            Created model instance
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            logger.debug(f"Created {self.model.__name__} with id={getattr(instance, 'id', None)}")
            return instance
        except Exception as e:
            logger.error(f"Failed to create {self.model.__name__}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to create {self.model.__name__}",
                detail={"error": str(e)}
            )
    
    async def get_by_id(self, id: str, id_column: str = None) -> Optional[ModelType]:
        """
        Get record by ID.
        
        Args:
            id: Record identifier
            id_column: Column name for ID (defaults to '{model_name}_id')
            
        Returns:
            Model instance or None if not found
        """
        if id_column is None:
            primary_key = self.model.__mapper__.primary_key
            if primary_key:
                id_column = primary_key[0].key
            else:
                raise DatabaseError(
                    message=f"Failed to determine primary key for {self.model.__name__}"
                )
        
        try:
            stmt = select(self.model).where(getattr(self.model, id_column) == id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get {self.model.__name__} by id {id}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to retrieve {self.model.__name__}",
                detail={"error": str(e)}
            )
    
    async def get_by_id_or_fail(self, id: str, id_column: str = None) -> ModelType:
        """
        Get record by ID or raise NotFoundError.
        
        Args:
            id: Record identifier
            id_column: Column name for ID
            
        Returns:
            Model instance
            
        Raises:
            NotFoundError: If record not found
        """
        instance = await self.get_by_id(id, id_column)
        if not instance:
            raise NotFoundError(
                resource=self.model.__name__,
                identifier=id
            )
        return instance
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
        descending: bool = False,
        **filters
    ) -> List[ModelType]:
        """
        Get all records with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            order_by: Column name to order by
            descending: Whether to order descending
            **filters: Field-value pairs for filtering
            
        Returns:
            List of model instances
        """
        try:
            stmt = select(self.model)
            
            # Apply filters
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)
            
            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                if descending:
                    stmt = stmt.order_by(order_column.desc())
                else:
                    stmt = stmt.order_by(order_column)
            
            # Apply pagination
            stmt = stmt.offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get {self.model.__name__} list: {str(e)}")
            raise DatabaseError(
                message=f"Failed to retrieve {self.model.__name__} list",
                detail={"error": str(e)}
            )
    
    async def count(self, **filters) -> int:
        """
        Count records matching filters.
        
        Args:
            **filters: Field-value pairs for filtering
            
        Returns:
            Total count
        """
        try:
            stmt = select(func.count()).select_from(self.model)
            
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)
            
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to count {self.model.__name__}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to count {self.model.__name__}",
                detail={"error": str(e)}
            )
    
    async def update(self, id: str, id_column: str = None, **kwargs) -> ModelType:
        """
        Update a record by ID.
        
        Args:
            id: Record identifier
            id_column: Column name for ID
            **kwargs: Field-value pairs to update
            
        Returns:
            Updated model instance
            
        Raises:
            NotFoundError: If record not found
        """
        if id_column is None:
            primary_key = self.model.__mapper__.primary_key
            if primary_key:
                id_column = primary_key[0].key
            else:
                id_column = f"{self.model.__tablename__.rstrip('s')}_id"
        
        try:
            # First get the instance
            instance = await self.get_by_id_or_fail(id, id_column)
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(instance, key) and value is not None:
                    setattr(instance, key, value)
            
            await self.session.flush()
            await self.session.refresh(instance)
            
            logger.debug(f"Updated {self.model.__name__} with id={id}")
            return instance
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update {self.model.__name__} {id}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to update {self.model.__name__}",
                detail={"error": str(e)}
            )
    
    async def delete(self, id: str, id_column: str = None) -> bool:
        """
        Delete a record by ID.
        
        Args:
            id: Record identifier
            id_column: Column name for ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseError: If deletion fails
        """
        if id_column is None:
            primary_key = self.model.__mapper__.primary_key
            if primary_key:
                id_column = primary_key[0].key
            else:
                id_column = f"{self.model.__tablename__.rstrip('s')}_id"
        
        try:
            stmt = delete(self.model).where(getattr(self.model, id_column) == id)
            result = await self.session.execute(stmt)
            await self.session.flush()
            
            deleted = result.rowcount > 0
            if deleted:
                logger.debug(f"Deleted {self.model.__name__} with id={id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete {self.model.__name__} {id}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to delete {self.model.__name__}",
                detail={"error": str(e)}
            )
    
    async def exists(self, **filters) -> bool:
        """
        Check if a record exists matching filters.
        
        Args:
            **filters: Field-value pairs for filtering
            
        Returns:
            True if exists, False otherwise
        """
        count = await self.count(**filters)
        return count > 0
    
    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in bulk.
        
        Args:
            items: List of dictionaries with field values
            
        Returns:
            List of created model instances
        """
        instances = []
        try:
            for item in items:
                instance = self.model(**item)
                self.session.add(instance)
                instances.append(instance)
            
            await self.session.flush()
            logger.debug(f"Bulk created {len(instances)} {self.model.__name__} records")
            return instances
        except Exception as e:
            logger.error(f"Failed to bulk create {self.model.__name__}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to bulk create {self.model.__name__}",
                detail={"error": str(e)}
            )