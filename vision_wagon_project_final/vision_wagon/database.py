"""
Database operations for Vision Wagon project.
Optimized version with proper async SQLAlchemy usage.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple # Tuple was not used, removed for cleanliness
from contextlib import asynccontextmanager

from sqlalchemy import (
    create_engine, # This was not used directly, create_async_engine is used. Kept for now.
    select,
    delete,
    update,
    func,
    and_,
    or_,
    desc,
    asc
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.dialects.postgresql import insert # Specific to PostgreSQL, ensure DB compatibility or make generic

from .database_models import (
    Base,
    Agent,
    AgentLog,
    Campaign,
    Task,
    Content,
    SecurityEvent,
    SystemMetric,
    AvatarPersonality
)
# Assuming config.py will be created or config_manager adapted
from .config_manager import get_config # Using existing config_manager

logger = logging.getLogger(__name__)
# settings = get_settings() # Replaced with get_config()

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
        self.settings = get_config() # Load settings via existing config_manager

    async def initialize(self):
        """Initialize database engine and session factory."""
        if self._initialized:
            return

        try:
            db_url = self.settings.database.async_url # Get from loaded config
            db_debug_echo = self.settings.system.debug # Get from loaded config

            self.engine = create_async_engine(
                db_url,
                echo=db_debug_echo,
                pool_size=self.settings.database.pool_size or 20, # Use config values or defaults
                max_overflow=self.settings.database.max_overflow or 30,
                pool_pre_ping=True, # Good practice
                pool_recycle=self.settings.database.pool_recycle or 3600,
                pool_timeout=self.settings.database.pool_timeout or 30,
                future=True # future=True is default in SQLAlchemy 2.0, can be omitted
            )

            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self._initialized = True
            logger.info("Database initialized successfully using new DatabaseManager")

        except Exception as e:
            logger.error(f"Failed to initialize database with new DatabaseManager: {e}", exc_info=True)
            raise

    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None # Clear the engine
            self.session_factory = None # Clear the factory
            self._initialized = False
            logger.info("Database connections closed by new DatabaseManager")

    @asynccontextmanager
    async def get_session(self) -> AsyncSession: # Added return type hint
        """Get async database session with proper cleanup."""
        if not self._initialized or not self.session_factory: # Added not self.session_factory check
            # This should ideally not happen if initialize is called correctly at startup
            logger.warning("DatabaseManager not initialized or session_factory is None. Attempting to initialize.")
            await self.initialize()
            if not self.session_factory: # Check again after attempt
                 logger.error("Failed to create session_factory after re-initialization attempt.")
                 raise RuntimeError("Database session factory is not available.")


        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except IntegrityError as e: # Specific handling for IntegrityError
            await session.rollback()
            logger.error(f"Database IntegrityError: {e}", exc_info=True)
            raise
        except SQLAlchemyError as e: # General SQLAlchemy errors
            await session.rollback()
            logger.error(f"Database SQLAlchemyError: {e}", exc_info=True)
            raise
        except Exception as e: # Other unexpected errors
            await session.rollback()
            logger.error(f"Generic database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()

db_manager = DatabaseManager()

# Agent Operations
async def get_agents(
    status: Optional[str] = None,
    agent_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Agent]:
    """Get agents with optional filtering and pagination."""
    async with db_manager.get_session() as session:
        stmt = select(Agent)
        if status:
            stmt = stmt.where(Agent.status == status)
        if agent_type:
            stmt = stmt.where(Agent.agent_type == agent_type)

        stmt = stmt.order_by(desc(Agent.created_at)) # Explicit desc

        if offset is not None: # Check for None explicitly
            stmt = stmt.offset(offset)
        if limit is not None: # Check for None explicitly
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

async def get_agent_by_id(agent_id: str) -> Optional[Agent]:
    """Get agent by ID."""
    async with db_manager.get_session() as session:
        # In Agent model, agent_id is the unique human-readable ID, not the UUID 'id' field.
        stmt = select(Agent).where(Agent.agent_id == agent_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

async def create_agent(agent_data: Dict[str, Any]) -> Agent:
    """Create a new agent."""
    async with db_manager.get_session() as session:
        agent = Agent(**agent_data)
        session.add(agent)
        # Commit is handled by context manager, flush and refresh are good for getting generated values
        await session.flush()
        await session.refresh(agent)
        return agent

async def update_agent(agent_id: str, updates: Dict[str, Any]) -> Optional[Agent]:
    """Update an existing agent."""
    async with db_manager.get_session() as session:
        # In Agent model, agent_id is the unique human-readable ID.
        stmt = select(Agent).where(Agent.agent_id == agent_id)
        result = await session.execute(stmt)
        agent = result.scalar_one_or_none()

        if not agent:
            return None

        for field, value in updates.items():
            if hasattr(agent, field):
                setattr(agent, field, value)

        # agent.updated_at is likely handled by onupdate=datetime.utcnow in model
        # If not, uncomment:
        # agent.updated_at = datetime.utcnow()
        await session.flush()
        await session.refresh(agent)
        return agent

# Agent Log Operations
async def get_agent_logs(
    agent_id: Optional[str] = None,
    level: Optional[str] = None,
    action: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[AgentLog]:
    async with db_manager.get_session() as session:
        stmt = select(AgentLog).options(joinedload(AgentLog.agent))
        conditions = []
        if agent_id:
            conditions.append(AgentLog.agent_id == agent_id) # agent_id is string in AgentLog
        if level:
            conditions.append(AgentLog.level == level)
        if action:
            conditions.append(AgentLog.action == action)
        if start_time:
            conditions.append(AgentLog.timestamp >= start_time)
        if end_time:
            conditions.append(AgentLog.timestamp <= end_time)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(AgentLog.timestamp))

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

async def create_agent_log(log_data: Dict[str, Any]) -> AgentLog:
    async with db_manager.get_session() as session:
        log_entry = AgentLog(**log_data)
        session.add(log_entry)
        await session.flush()
        await session.refresh(log_entry)
        return log_entry

async def cleanup_old_logs(days_to_keep: int = 30) -> int:
    async with db_manager.get_session() as session:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        stmt = delete(AgentLog).where(AgentLog.timestamp < cutoff_date)
        result = await session.execute(stmt)
        deleted_count = result.rowcount
        logger.info(f"Cleaned up {deleted_count} old agent log entries")
        return deleted_count

# Campaign Operations
async def get_campaigns(
    status: Optional[str] = None,
    campaign_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Campaign]:
    async with db_manager.get_session() as session:
        stmt = select(Campaign)
        if status:
            stmt = stmt.where(Campaign.status == status)
        if campaign_type:
            stmt = stmt.where(Campaign.campaign_type == campaign_type)
        stmt = stmt.order_by(desc(Campaign.created_at))
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

async def get_campaign_by_id(campaign_id: str) -> Optional[Campaign]: # campaign_id is UUID in model
    async with db_manager.get_session() as session:
        stmt = select(Campaign).options(
            selectinload(Campaign.tasks),
            selectinload(Campaign.contents) # contents, not content per model
        ).where(Campaign.id == campaign_id) # Use 'id' for UUID PK
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

async def create_campaign(campaign_data: Dict[str, Any]) -> Campaign:
    async with db_manager.get_session() as session:
        campaign = Campaign(**campaign_data)
        session.add(campaign)
        await session.flush()
        await session.refresh(campaign)
        return campaign

# Task Operations
async def get_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    agent_id: Optional[str] = None, # agent_id is string in Task model
    campaign_id: Optional[str] = None, # campaign_id is UUID in Task model
    priority: Optional[int] = None, # priority is int in Task model
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Task]:
    async with db_manager.get_session() as session:
        stmt = select(Task).options(
            joinedload(Task.agent),
            joinedload(Task.campaign)
        )
        conditions = []
        if status:
            conditions.append(Task.status == status)
        if task_type:
            conditions.append(Task.task_type == task_type)
        if agent_id:
            conditions.append(Task.agent_id == agent_id)
        if campaign_id:
            conditions.append(Task.campaign_id == campaign_id)
        if priority is not None: # Priority can be 0
            conditions.append(Task.priority == priority)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(
            desc(Task.priority), # Higher priority first
            desc(Task.created_at)
        )

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

async def get_task_by_id(task_id: str) -> Optional[Task]: # task_id is UUID in model
    async with db_manager.get_session() as session:
        stmt = select(Task).options(
            joinedload(Task.agent),
            joinedload(Task.campaign)
        ).where(Task.id == task_id) # Use 'id' for UUID PK
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

async def create_task(task_data: Dict[str, Any]) -> Task:
    async with db_manager.get_session() as session:
        task = Task(**task_data)
        session.add(task)
        await session.flush()
        await session.refresh(task)
        return task

async def update_task_status(task_id: str, status: str, task_result: Optional[Dict[str, Any]] = None) -> Optional[Task]: # task_id is UUID
    async with db_manager.get_session() as session:
        stmt = select(Task).where(Task.id == task_id) # Use 'id' for UUID PK
        result_obj = await session.execute(stmt)
        task = result_obj.scalar_one_or_none()

        if not task:
            return None

        task.status = status
        # task.updated_at handled by onupdate in model

        if task_result is not None: # Check for None explicitly
            task.output_data = task_result # Assuming result goes into output_data

        if status in ['COMPLETED', 'FAILED', 'CANCELLED']: # String values from Enum
            task.completed_at = datetime.utcnow()

        await session.flush()
        await session.refresh(task)
        return task

# Content Operations
async def get_content_list( # Renamed from get_content to avoid conflict with single get_content_by_id
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    campaign_id: Optional[str] = None, # campaign_id is UUID
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Content]:
    async with db_manager.get_session() as session:
        stmt = select(Content).options(joinedload(Content.campaign))
        conditions = []
        if content_type:
            conditions.append(Content.content_type == content_type)
        if status:
            conditions.append(Content.status == status)
        if campaign_id:
            conditions.append(Content.campaign_id == campaign_id)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(Content.created_at))

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

async def get_content_by_id(content_id: str) -> Optional[Content]: # content_id is UUID
    """Get content by ID."""
    async with db_manager.get_session() as session:
        stmt = select(Content).where(Content.id == content_id) # Use 'id' for UUID PK
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

async def create_content(content_data: Dict[str, Any]) -> Content:
    async with db_manager.get_session() as session:
        content = Content(**content_data)
        session.add(content)
        await session.flush()
        await session.refresh(content)
        return content

async def update_content(content_id: str, updates: Dict[str, Any]) -> Optional[Content]: # content_id is UUID
    async with db_manager.get_session() as session:
        stmt = select(Content).where(Content.id == content_id) # Use 'id' for UUID PK
        result = await session.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            return None

        for field, value in updates.items():
            if field == 'content_metadata' and content.content_metadata and isinstance(value, dict):
                merged_metadata = {**content.content_metadata, **value}
                setattr(content, field, merged_metadata)
            elif hasattr(content, field):
                setattr(content, field, value)

        # content.updated_at handled by onupdate
        await session.flush()
        await session.refresh(content)
        return content

# Security Event Operations
async def get_security_events(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[SecurityEvent]:
    async with db_manager.get_session() as session:
        stmt = select(SecurityEvent)
        conditions = []
        if event_type:
            conditions.append(SecurityEvent.event_type == event_type)
        if severity:
            conditions.append(SecurityEvent.severity == severity)
        if start_time:
            conditions.append(SecurityEvent.timestamp >= start_time)
        if end_time:
            conditions.append(SecurityEvent.timestamp <= end_time)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(SecurityEvent.timestamp))

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

async def create_security_event(event_data: Dict[str, Any]) -> SecurityEvent:
    async with db_manager.get_session() as session:
        event = SecurityEvent(**event_data)
        session.add(event)
        await session.flush()
        await session.refresh(event)
        return event

# Metrics Operations
async def get_metrics(
    metric_name: Optional[str] = None,
    metric_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[SystemMetric]:
    async with db_manager.get_session() as session:
        stmt = select(SystemMetric)
        conditions = []
        if metric_name:
            conditions.append(SystemMetric.metric_name == metric_name)
        if metric_type:
            conditions.append(SystemMetric.metric_type == metric_type)
        if start_time:
            conditions.append(SystemMetric.timestamp >= start_time)
        if end_time:
            conditions.append(SystemMetric.timestamp <= end_time)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(SystemMetric.timestamp))

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

async def create_metric(metric_data: Dict[str, Any]) -> SystemMetric:
    async with db_manager.get_session() as session:
        metric = SystemMetric(**metric_data)
        session.add(metric)
        await session.flush()
        await session.refresh(metric)
        return metric

# Optimized System Stats
async def get_system_stats() -> Dict[str, Any]:
    async with db_manager.get_session() as session:
        agent_stats_stmt = select(Agent.status, func.count(Agent.id).label('count')).group_by(Agent.status) # Use Agent.id
        agent_result = await session.execute(agent_stats_stmt)
        agent_stats = {row.status: row.count for row in agent_result.all()} # Use .all() for named tuples

        task_stats_stmt = select(Task.status, func.count(Task.id).label('count')).group_by(Task.status) # Use Task.id
        task_result = await session.execute(task_stats_stmt)
        task_stats = {row.status: row.count for row in task_result.all()}

        campaign_stats_stmt = select(Campaign.status, func.count(Campaign.id).label('count')).group_by(Campaign.status) # Use Campaign.id
        campaign_result = await session.execute(campaign_stats_stmt)
        campaign_stats = {row.status: row.count for row in campaign_result.all()}

        content_stats_stmt = select(Content.status, func.count(Content.id).label('count')).group_by(Content.status) # Use Content.id
        content_result = await session.execute(content_stats_stmt)
        content_stats = {row.status: row.count for row in content_result.all()}

        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        security_stats_stmt = select(
            SecurityEvent.severity, func.count(SecurityEvent.id).label('count') # Use SecurityEvent.id
        ).where(SecurityEvent.timestamp >= cutoff_time).group_by(SecurityEvent.severity)
        security_result = await session.execute(security_stats_stmt)
        security_stats = {row.severity: row.count for row in security_result.all()}

        return {
            'agents': agent_stats,
            'tasks': task_stats,
            'campaigns': campaign_stats,
            'content': content_stats,
            'security_events_24h': security_stats,
            'timestamp': datetime.utcnow().isoformat()
        }

# Avatar Personality Operations
async def get_avatar_personality(avatar_id: str) -> Optional[AvatarPersonality]:
    async with db_manager.get_session() as session:
        stmt = select(AvatarPersonality).where(AvatarPersonality.avatar_id == avatar_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

async def update_avatar_personality(avatar_id: str, updates: Dict[str, Any]) -> Optional[AvatarPersonality]:
    async with db_manager.get_session() as session:
        stmt = select(AvatarPersonality).where(AvatarPersonality.avatar_id == avatar_id)
        result = await session.execute(stmt)
        personality = result.scalar_one_or_none()

        if not personality:
            # Create new if not exists, ensuring avatar_id is part of updates or passed explicitly
            personality_data = {'avatar_id': avatar_id, **updates.get('personality_profile', {})}
            if 'personality_profile' not in personality_data: # ensure key exists
                 personality_data['personality_profile'] = updates
            # personality = AvatarPersonality(**personality_data) # This might fail if updates dont match model
            personality = AvatarPersonality(avatar_id=avatar_id, personality_profile=updates.get('personality_profile', {}))

            session.add(personality)
        else:
            if 'personality_profile' in updates:
                 personality.personality_profile = updates['personality_profile']
            # personality.updated_at handled by onupdate

        await session.flush()
        await session.refresh(personality)
        return personality

# Health Check Operations
async def health_check() -> Dict[str, Any]:
    try:
        async with db_manager.get_session() as session:
            stmt = select(func.count()).select_from(Agent) # Simpler count
            result = await session.execute(stmt)
            agent_count = result.scalar_one() # scalar_one as we expect one row

            return {
                'status': 'healthy',
                'agent_count': agent_count,
                'timestamp': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

# Utility Functions
async def bulk_insert_metrics(metrics_data: List[Dict[str, Any]]) -> int:
    if not metrics_data:
        return 0
    async with db_manager.get_session() as session:
        # For PostgreSQL, on_conflict_do_nothing is efficient.
        # For other DBs, this might need adjustment or be less performant.
        # Ensure your SystemMetric model has appropriate unique constraints for conflict to work.
        stmt = insert(SystemMetric).values(metrics_data)
        # Assuming a unique constraint on (metric_name, timestamp, source, tags_hash_if_any)
        # For simplicity, if no such constraint, remove on_conflict or handle per DB.
        # For generic solution, might need to query existence first or catch IntegrityError per row (slow).
        # The provided model does not show unique constraints that would make on_conflict_do_nothing always safe.
        # We will assume it's intended to insert new rows only.
        # result = await session.execute(stmt.on_conflict_do_nothing()) # Potentially problematic without right constraints

        # Safer generic approach: just insert. If duplicates are an issue, handle at application level or with constraints.
        await session.execute(stmt) # Removed on_conflict_do_nothing for broader compatibility / if no conflict target
        # rowcount for bulk insert with 'values' might not be directly available or behave differently across backends
        # For inserts, rowcount is often -1 with some drivers when not returning.
        # We'll return the number of items attempted to insert as a proxy.
        return len(metrics_data)


async def get_task_queue_size() -> int:
    async with db_manager.get_session() as session:
        # Count tasks in 'PENDING' or 'RETRY' status, or any status considered active in queue
        stmt = select(func.count(Task.id)).where(Task.status == 'pending') # Use Task.id
        result = await session.execute(stmt)
        return result.scalar_one() or 0

async def get_active_agents_count() -> int:
    async with db_manager.get_session() as session:
        stmt = select(func.count(Agent.id)).where(Agent.status == 'active') # Use Agent.id and 'active'
        result = await session.execute(stmt)
        return result.scalar_one() or 0

# Initialize database on module import - this should be called at application startup
async def init_db():
    """Initialize database on startup."""
    await db_manager.initialize()

# Cleanup function for graceful shutdown - to be called at application shutdown
async def cleanup_db():
    """Cleanup database connections on shutdown."""
    await db_manager.close()
