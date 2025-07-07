"""
Database Models - Vision Wagon
Modelos de base de datos para el sistema Vision Wagon usando SQLAlchemy.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Agent(Base):
    """Modelo para agentes registrados en el sistema"""
    __tablename__ = 'agents'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(100), unique=True, nullable=False, index=True)
    agent_type = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), default='inactive', index=True)  # active, inactive, error
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_execution = Column(DateTime)
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    average_execution_time = Column(Float, default=0.0)

    # Relaciones
    logs = relationship("AgentLog", back_populates="agent", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="agent")

    def __repr__(self):
        return f"<Agent(id={self.agent_id}, type={self.agent_type}, status={self.status})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'config': self.config,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'average_execution_time': self.average_execution_time
        }

class AgentLog(Base):
    """Modelo para logs de agentes"""
    __tablename__ = 'agent_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey('agents.agent_id'), nullable=False, index=True)
    execution_id = Column(String(100), index=True)
    action = Column(String(100), nullable=False, index=True)
    level = Column(String(20), default='info', index=True)  # debug, info, warning, error
    message = Column(Text)
    data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    execution_time = Column(Float)
    success = Column(Boolean)

    # Relaciones
    agent = relationship("Agent", back_populates="logs")

    def __repr__(self):
        return f"<AgentLog(agent={self.agent_id}, action={self.action}, level={self.level})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'agent_id': self.agent_id,
            'execution_id': self.execution_id,
            'action': self.action,
            'level': self.level,
            'message': self.message,
            'data': self.data,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'execution_time': self.execution_time,
            'success': self.success
        }

class Campaign(Base):
    """Modelo para campañas de marketing/contenido"""
    __tablename__ = 'campaigns'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    campaign_type = Column(String(50), nullable=False, index=True)  # marketing, content, analysis
    status = Column(String(20), default='draft', index=True)  # draft, active, paused, completed, cancelled
    config = Column(JSON)
    target_audience = Column(JSON)
    metrics = Column(JSON)
    budget = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

    # Relaciones
    tasks = relationship("Task", back_populates="campaign")
    contents = relationship("Content", back_populates="campaign")

    def __repr__(self):
        return f"<Campaign(name={self.name}, type={self.campaign_type}, status={self.status})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'campaign_type': self.campaign_type,
            'status': self.status,
            'config': self.config,
            'target_audience': self.target_audience,
            'metrics': self.metrics,
            'budget': self.budget,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }

class Task(Base):
    """Modelo para tareas del sistema"""
    __tablename__ = 'tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), default='pending', index=True)  # pending, running, completed, failed, cancelled
    priority = Column(Integer, default=5, index=True)  # 1-10, 10 = highest
    agent_id = Column(String(100), ForeignKey('agents.agent_id'), index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id'), index=True)
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    progress = Column(Float, default=0.0)  # 0.0 - 1.0
    estimated_duration = Column(Integer)  # seconds
    actual_duration = Column(Integer)  # seconds
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    agent = relationship("Agent", back_populates="tasks")
    campaign = relationship("Campaign", back_populates="tasks")

    def __repr__(self):
        return f"<Task(title={self.title}, status={self.status}, agent={self.agent_id})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'task_type': self.task_type,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'agent_id': self.agent_id,
            'campaign_id': str(self.campaign_id) if self.campaign_id else None,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_message': self.error_message,
            'progress': self.progress,
            'estimated_duration': self.estimated_duration,
            'actual_duration': self.actual_duration,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Content(Base):
    """Modelo para contenido generado"""
    __tablename__ = 'contents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    content_type = Column(String(50), nullable=False, index=True)  # text, image, video, audio
    format = Column(String(20))  # html, markdown, jpg, mp4, etc.
    content = Column(Text)  # Para texto o URL para multimedia
    content_metadata = Column(JSON)
    tags = Column(JSON)
    is_flagged = Column(Boolean, default=False)
    moderation_categories = Column(JSON)
    moderated_by = Column(String(100))
    moderated_at = Column(DateTime)
    status = Column(String(20), default='draft', index=True)  # draft, published, archived
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id'), index=True)
    generated_by = Column(String(100)) # agent_id que generó el contenido
    quality_score = Column(Float)  # 0.0 - 1.0
    engagement_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)

    # Relaciones
    campaign = relationship("Campaign", back_populates="contents")

    def __repr__(self):
        return f"<Content(title={self.title}, type={self.content_type}, status={self.status})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'content_type': self.content_type,
            'format': self.format,
            'content': self.content,
            'metadata': self.metadata,
            'tags': self.tags,
            'status': self.status,
            'campaign_id': str(self.campaign_id) if self.campaign_id else None,
            'generated_by': self.generated_by,
            'quality_score': self.quality_score,
            'engagement_metrics': self.engagement_metrics,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }

class SecurityEvent(Base):
    """Modelo para eventos de seguridad"""
    __tablename__ = 'security_events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)  # authentication, authorization, data_access, etc.
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    source = Column(String(100), nullable=False)  # agent_id, user_id, system
    target = Column(String(100))  # what was accessed/affected
    action = Column(String(100), nullable=False)
    description = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    additional_data = Column(JSON)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<SecurityEvent(type={self.event_type}, severity={self.severity}, source={self.source})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'event_type': self.event_type,
            'severity': self.severity,
            'source': self.source,
            'target': self.target,
            'action': self.action,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'additional_data': self.additional_data,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class SystemMetric(Base):
    """Modelo para métricas del sistema"""
    __tablename__ = 'system_metrics'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # counter, gauge, histogram
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    tags = Column(JSON)  # Para filtros y agrupaciones
    source = Column(String(100))  # agent_id, system component
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<SystemMetric(name={self.metric_name}, value={self.value}, source={self.source})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'metric_name': self.metric_name,
            'metric_type': self.metric_type,
            'value': self.value,
            'unit': self.unit,
            'tags': self.tags,
            'source': self.source,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }



class AvatarPersonality(Base):
    """Modelo para el perfil de personalidad de un avatar de IA"""
    __tablename__ = 'avatar_personalities'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    avatar_id = Column(String(100), unique=True, nullable=False, index=True)
    personality_profile = Column(JSON)  # JSON con rasgos, tono, etc.
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AvatarPersonality(avatar_id={self.avatar_id})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'avatar_id': self.avatar_id,
            'personality_profile': self.personality_profile,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


