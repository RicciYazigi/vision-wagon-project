"""
Database Module - Vision Wagon
Manejo de conexiones y operaciones de base de datos usando SQLAlchemy.
"""

import os
import logging
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio

from .database_models import Base, Agent, AgentLog, Campaign, Task, Content, SecurityEvent, SystemMetric

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor de base de datos para Vision Wagon"""
    
    def __init__(self, database_url: Optional[str] = None, async_url: Optional[str] = None):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            database_url: URL de conexión síncrona
            async_url: URL de conexión asíncrona
        """
        # URLs por defecto (SQLite para desarrollo)
        self.database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'sqlite:///./vision_wagon.db'
        )
        
        self.async_database_url = async_url or os.getenv(
            'ASYNC_DATABASE_URL',
            'sqlite+aiosqlite:///./vision_wagon.db'
        )
        
        # Configuración del engine
        engine_kwargs = {}
        if 'sqlite' in self.database_url:
            engine_kwargs.update({
                'poolclass': StaticPool,
                'connect_args': {'check_same_thread': False}
            })
        
        # Engines
        self.engine = create_engine(self.database_url, **engine_kwargs)
        self.async_engine = create_async_engine(self.async_database_url, **engine_kwargs)
        
        # Session makers
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.AsyncSessionLocal = async_sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.async_engine,
            class_=AsyncSession
        )
        
        logger.info(f"DatabaseManager inicializado con URL: {self.database_url}")

    def create_tables(self) -> None:
        """Crea todas las tablas en la base de datos"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tablas creadas exitosamente")
        except Exception as e:
            logger.error(f"Error creando tablas: {str(e)}")
            raise

    async def create_tables_async(self) -> None:
        """Crea todas las tablas de forma asíncrona"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Tablas creadas exitosamente (async)")
        except Exception as e:
            logger.error(f"Error creando tablas (async): {str(e)}")
            raise

    def drop_tables(self) -> None:
        """Elimina todas las tablas de la base de datos"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Tablas eliminadas exitosamente")
        except Exception as e:
            logger.error(f"Error eliminando tablas: {str(e)}")
            raise

    @contextmanager
    def get_session(self):
        """Context manager para sesiones síncronas"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en sesión de base de datos: {str(e)}")
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self):
        """Context manager para sesiones asíncronas"""
        session = self.AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Error en sesión asíncrona de base de datos: {str(e)}")
            raise
        finally:
            await session.close()

    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("Conexión a base de datos exitosa")
            return True
        except Exception as e:
            logger.error(f"Error de conexión a base de datos: {str(e)}")
            return False

    async def test_connection_async(self) -> bool:
        """Prueba la conexión asíncrona a la base de datos"""
        try:
            async with self.get_async_session() as session:
                await session.execute(text("SELECT 1"))
            logger.info("Conexión asíncrona a base de datos exitosa")
            return True
        except Exception as e:
            logger.error(f"Error de conexión asíncrona a base de datos: {str(e)}")
            return False

    # Métodos CRUD para Agent
    async def create_agent(self, agent_data: Dict[str, Any]) -> Agent:
        """Crea un nuevo agente en la base de datos"""
        async with self.get_async_session() as session:
            agent = Agent(**agent_data)
            session.add(agent)
            await session.flush()
            await session.refresh(agent)
            return agent

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Obtiene un agente por su ID"""
        async with self.get_async_session() as session:
            result = await session.get(Agent, agent_id)
            return result

    async def get_agents(self, agent_type: Optional[str] = None, status: Optional[str] = None) -> List[Agent]:
        """Obtiene lista de agentes con filtros opcionales"""
        async with self.get_async_session() as session:
            query = session.query(Agent)
            
            if agent_type:
                query = query.filter(Agent.agent_type == agent_type)
            if status:
                query = query.filter(Agent.status == status)
                
            result = await query.all()
            return result

    async def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Optional[Agent]:
        """Actualiza un agente"""
        async with self.get_async_session() as session:
            agent = await session.get(Agent, agent_id)
            if agent:
                for key, value in update_data.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)
                await session.flush()
                await session.refresh(agent)
            return agent

    async def delete_agent(self, agent_id: str) -> bool:
        """Elimina un agente"""
        async with self.get_async_session() as session:
            agent = await session.get(Agent, agent_id)
            if agent:
                await session.delete(agent)
                return True
            return False

    # Métodos CRUD para AgentLog
    async def create_agent_log(self, log_data: Dict[str, Any]) -> AgentLog:
        """Crea un nuevo log de agente"""
        async with self.get_async_session() as session:
            log = AgentLog(**log_data)
            session.add(log)
            await session.flush()
            await session.refresh(log)
            return log

    async def get_agent_logs(self, agent_id: str, limit: int = 100) -> List[AgentLog]:
        """Obtiene logs de un agente"""
        async with self.get_async_session() as session:
            result = await session.query(AgentLog)\
                .filter(AgentLog.agent_id == agent_id)\
                .order_by(AgentLog.timestamp.desc())\
                .limit(limit)\
                .all()
            return result

    # Métodos CRUD para Campaign
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Campaign:
        """Crea una nueva campaña"""
        async with self.get_async_session() as session:
            campaign = Campaign(**campaign_data)
            session.add(campaign)
            await session.flush()
            await session.refresh(campaign)
            return campaign

    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Obtiene una campaña por su ID"""
        async with self.get_async_session() as session:
            result = await session.get(Campaign, campaign_id)
            return result

    async def get_campaigns(self, status: Optional[str] = None, campaign_type: Optional[str] = None) -> List[Campaign]:
        """Obtiene lista de campañas con filtros opcionales"""
        async with self.get_async_session() as session:
            query = session.query(Campaign)
            
            if status:
                query = query.filter(Campaign.status == status)
            if campaign_type:
                query = query.filter(Campaign.campaign_type == campaign_type)
                
            result = await query.all()
            return result

    # Métodos CRUD para Task
    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        """Crea una nueva tarea"""
        async with self.get_async_session() as session:
            task = Task(**task_data)
            session.add(task)
            await session.flush()
            await session.refresh(task)
            return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Obtiene una tarea por su ID"""
        async with self.get_async_session() as session:
            result = await session.get(Task, task_id)
            return result

    async def get_tasks(self, status: Optional[str] = None, agent_id: Optional[str] = None) -> List[Task]:
        """Obtiene lista de tareas con filtros opcionales"""
        async with self.get_async_session() as session:
            query = session.query(Task)
            
            if status:
                query = query.filter(Task.status == status)
            if agent_id:
                query = query.filter(Task.agent_id == agent_id)
                
            result = await query.all()
            return result

    async def update_task_status(self, task_id: str, status: str, progress: Optional[float] = None) -> Optional[Task]:
        """Actualiza el estado de una tarea"""
        async with self.get_async_session() as session:
            task = await session.get(Task, task_id)
            if task:
                task.status = status
                if progress is not None:
                    task.progress = progress
                await session.flush()
                await session.refresh(task)
            return task

    # Métodos para SecurityEvent
    async def create_security_event(self, event_data: Dict[str, Any]) -> SecurityEvent:
        """Crea un nuevo evento de seguridad"""
        async with self.get_async_session() as session:
            event = SecurityEvent(**event_data)
            session.add(event)
            await session.flush()
            await session.refresh(event)
            return event

    async def get_security_events(self, severity: Optional[str] = None, resolved: Optional[bool] = None, limit: int = 100) -> List[SecurityEvent]:
        """Obtiene eventos de seguridad con filtros"""
        async with self.get_async_session() as session:
            query = session.query(SecurityEvent)
            
            if severity:
                query = query.filter(SecurityEvent.severity == severity)
            if resolved is not None:
                query = query.filter(SecurityEvent.resolved == resolved)
                
            result = await query.order_by(SecurityEvent.timestamp.desc()).limit(limit).all()
            return result

    # Métodos para SystemMetric
    async def create_metric(self, metric_data: Dict[str, Any]) -> SystemMetric:
        """Crea una nueva métrica del sistema"""
        async with self.get_async_session() as session:
            metric = SystemMetric(**metric_data)
            session.add(metric)
            await session.flush()
            await session.refresh(metric)
            return metric

    async def get_metrics(self, metric_name: Optional[str] = None, source: Optional[str] = None, limit: int = 1000) -> List[SystemMetric]:
        """Obtiene métricas del sistema"""
        async with self.get_async_session() as session:
            query = session.query(SystemMetric)
            
            if metric_name:
                query = query.filter(SystemMetric.metric_name == metric_name)
            if source:
                query = query.filter(SystemMetric.source == source)
                
            result = await query.order_by(SystemMetric.timestamp.desc()).limit(limit).all()
            return result

    async def cleanup_old_logs(self, days: int = 30) -> int:
        """Limpia logs antiguos"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with self.get_async_session() as session:
            result = await session.query(AgentLog)\
                .filter(AgentLog.timestamp < cutoff_date)\
                .delete()
            return result

    async def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales del sistema"""
        async with self.get_async_session() as session:
            # Contar agentes por estado
            agent_stats = {}
            agents = await session.query(Agent).all()
            for agent in agents:
                status = agent.status
                agent_stats[status] = agent_stats.get(status, 0) + 1

            # Contar tareas por estado
            task_stats = {}
            tasks = await session.query(Task).all()
            for task in tasks:
                status = task.status
                task_stats[status] = task_stats.get(status, 0) + 1

            # Contar campañas por estado
            campaign_stats = {}
            campaigns = await session.query(Campaign).all()
            for campaign in campaigns:
                status = campaign.status
                campaign_stats[status] = campaign_stats.get(status, 0) + 1

            return {
                'agents': agent_stats,
                'tasks': task_stats,
                'campaigns': campaign_stats,
                'total_agents': len(agents),
                'total_tasks': len(tasks),
                'total_campaigns': len(campaigns)
            }

# Instancia global del gestor de base de datos
db_manager = DatabaseManager()

# Funciones de conveniencia
async def init_database():
    """Inicializa la base de datos"""
    await db_manager.create_tables_async()
    logger.info("Base de datos inicializada")

async def get_db_session():
    """Obtiene una sesión de base de datos asíncrona"""
    async with db_manager.get_async_session() as session:
        yield session



    async def update_content_moderation_status(self, content_id: str, is_flagged: bool, moderation_categories: Dict[str, Any], moderated_by: str) -> Optional[Content]:
        """Actualiza el estado de moderación de un contenido."""
        async with self.get_async_session() as session:
            content = await session.get(Content, content_id)
            if content:
                content.is_flagged = is_flagged
                content.moderation_categories = moderation_categories
                content.moderated_by = moderated_by
                content.moderated_at = datetime.utcnow()
                await session.flush()
                await session.refresh(content)
            return content




    async def get_avatar_personality(self, avatar_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el perfil de personalidad de un avatar por su ID."""
        async with self.get_async_session() as session:
            result = await session.query(AvatarPersonality).filter(AvatarPersonality.avatar_id == avatar_id).first()
            if result:
                return result.personality_profile
            return None

    async def update_avatar_personality(self, avatar_id: str, personality_profile: Dict[str, Any]) -> AvatarPersonality:
        """Actualiza o crea el perfil de personalidad de un avatar."""
        async with self.get_async_session() as session:
            avatar_personality = await session.query(AvatarPersonality).filter(AvatarPersonality.avatar_id == avatar_id).first()
            if avatar_personality:
                avatar_personality.personality_profile = personality_profile
                avatar_personality.updated_at = datetime.utcnow()
            else:
                avatar_personality = AvatarPersonality(avatar_id=avatar_id, personality_profile=personality_profile)
                session.add(avatar_personality)
            await session.flush()
            await session.refresh(avatar_personality)
            return avatar_personality


