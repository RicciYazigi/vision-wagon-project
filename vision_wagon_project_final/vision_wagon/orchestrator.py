"""
Orchestrator - Vision Wagon
Coordinador central que gestiona la ejecución de agentes y flujos de trabajo.
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import traceback

from .agents.core.base_agent import BaseAgent, AgentResult
from .config_manager import get_config
from .database import db_manager
from .database_models import Content
from .security_validator import get_security_validator

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Estados de las tareas"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskPriority(Enum):
    """Prioridades de las tareas"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """Representación de una tarea en el sistema"""
    task_id: str
    task_type: str
    agent_id: str
    context: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[AgentResult] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 300.0
    dependencies: List[str] = field(default_factory=list)
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowStep:
    """Paso en un flujo de trabajo"""
    step_id: str
    agent_id: str
    task_type: str
    context: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    condition: Optional[Callable] = None
    on_success: Optional[Callable] = None
    on_failure: Optional[Callable] = None

@dataclass
class Workflow:
    """Flujo de trabajo completo"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class Orchestrator:
    """
    Orquestador central del sistema Vision Wagon.
    Responsable de:
    - Gestión de agentes
    - Ejecución de tareas
    - Coordinación de flujos de trabajo
    - Monitoreo de rendimiento
    - Manejo de errores y reintentos
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el orquestador.
        
        Args:
            config: Configuración del orquestador
        """
        self.config_manager = get_config()
        self.security_validator = get_security_validator()
        
        # Configuración
        orchestrator_config = self.config_manager.orchestrator
        self.max_concurrent_tasks = orchestrator_config.max_concurrent_tasks
        self.task_timeout = orchestrator_config.task_timeout
        self.retry_delay = orchestrator_config.retry_delay
        self.health_check_interval = orchestrator_config.health_check_interval
        
        # Registro de agentes
        self.registered_agents: Dict[str, BaseAgent] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        
        # Gestión de tareas
        self.task_queue = asyncio.PriorityQueue() # Stores (priority, time, task_obj)
        self.pending_tasks_by_id: Dict[str, Task] = {} # For quick lookup of tasks in queue
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {} # Includes successfully completed tasks
        self.failed_tasks: Dict[str, Task] = {} # Includes failed and cancelled tasks
        
        # Gestión de workflows
        self.workflows: Dict[str, Workflow] = {}
        self.workflow_templates: Dict[str, Workflow] = {}
        
        # Métricas y monitoreo
        self.metrics = {
            'tasks_executed': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'average_execution_time': 0.0,
            'agent_utilization': defaultdict(float),
            'error_rates': defaultdict(float)
        }
        
        # Control de ejecución
        self.is_running = False
        self.worker_tasks = []
        self.health_check_task = None
        
        # Eventos y callbacks
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        logger.info("Orchestrator inicializado")

    async def start(self) -> None:
        """Inicia el orquestador"""
        if self.is_running:
            logger.warning("Orchestrator ya está ejecutándose")
            return
        
        try:
            self.is_running = True
            
            # Inicializar base de datos
            if not await db_manager.test_connection_async():
                raise Exception("No se pudo conectar a la base de datos")
            
            # Iniciar workers para procesamiento de tareas
            for i in range(self.max_concurrent_tasks):
                worker = asyncio.create_task(self._task_worker(f"worker_{i}"))
                self.worker_tasks.append(worker)
            
            # Iniciar monitoreo de salud
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            # Cargar workflows predefinidos
            await self._load_workflow_templates()
            
            logger.info(f"Orchestrator iniciado con {len(self.worker_tasks)} workers")
            
        except Exception as e:
            logger.error(f"Error iniciando Orchestrator: {str(e)}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Detiene el orquestador"""
        if not self.is_running:
            return
        
        logger.info("Deteniendo Orchestrator...")
        self.is_running = False
        
        # Cancelar workers
        for worker in self.worker_tasks:
            worker.cancel()
        
        # Cancelar health check
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Esperar a que terminen las tareas
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        if self.health_check_task:
            await asyncio.gather(self.health_check_task, return_exceptions=True)
        
        # Limpiar agentes registrados
        for agent in self.registered_agents.values():
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Error limpiando agente {agent.agent_id}: {str(e)}")
        
        logger.info("Orchestrator detenido")

    async def register_agent(self, agent: BaseAgent) -> None:
        """
        Registra un agente en el orquestador.
        
        Args:
            agent: Agente a registrar
        """
        try:
            # Inicializar agente si no está inicializado
            if not agent.is_initialized:
                await agent.initialize()
            
            # Registrar agente
            self.registered_agents[agent.agent_id] = agent
            
            # Obtener capacidades del agente
            capabilities = getattr(agent, 'capabilities', [])
            self.agent_capabilities[agent.agent_id] = capabilities
            
            logger.info(f"Agente registrado: {agent.agent_id} ({agent.agent_type})")
            
            # Emitir evento
            await self._emit_event('agent_registered', {
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type,
                'capabilities': capabilities
            })
            
        except Exception as e:
            logger.error(f"Error registrando agente {agent.agent_id}: {str(e)}")
            raise

    async def unregister_agent(self, agent_id: str) -> None:
        """
        Desregistra un agente del orquestador.
        
        Args:
            agent_id: ID del agente a desregistrar
        """
        if agent_id in self.registered_agents:
            agent = self.registered_agents[agent_id]
            
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Error limpiando agente {agent_id}: {str(e)}")
            
            del self.registered_agents[agent_id]
            del self.agent_capabilities[agent_id]
            
            logger.info(f"Agente desregistrado: {agent_id}")
            
            # Emitir evento
            await self._emit_event('agent_unregistered', {'agent_id': agent_id})

    async def submit_task(self, task_type: str, agent_id: str, context: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.NORMAL,
                         timeout: float = None, max_retries: int = None,
                         dependencies: List[str] = None,
                         callback: Callable = None,
                         metadata: Dict[str, Any] = None) -> str:
        """
        Envía una tarea para ejecución.
        
        Args:
            task_type: Tipo de tarea
            agent_id: ID del agente que ejecutará la tarea
            context: Contexto de la tarea
            priority: Prioridad de la tarea
            timeout: Timeout en segundos
            max_retries: Máximo número de reintentos
            dependencies: Lista de IDs de tareas dependientes
            callback: Función callback para cuando complete
            metadata: Metadatos adicionales
            
        Returns:
            ID de la tarea creada
        """
        # Validar agente
        if agent_id not in self.registered_agents:
            raise ValueError(f"Agente no registrado: {agent_id}")
        
        # Crear tarea
        task = Task(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            agent_id=agent_id,
            context=context,
            priority=priority,
            timeout=timeout or self.task_timeout,
            max_retries=max_retries or 3,
            dependencies=dependencies or [],
            callback=callback,
            metadata=metadata or {}
        )
        
        # Validar dependencias
        await self._validate_task_dependencies(task)
        
        # Agregar a cola con prioridad
        priority_value = priority.value
        await self.task_queue.put((priority_value, task.created_at, task))
        self.pending_tasks_by_id[task.task_id] = task # Add to lookup dict
        
        logger.info(f"Tarea enviada: {task.task_id} ({task_type}) -> {agent_id}")
        
        # Emitir evento
        await self._emit_event('task_submitted', {
            'task_id': task.task_id,
            'task_type': task_type,
            'agent_id': agent_id,
            'priority': priority.name
        })
        
        return task.task_id

    async def _validate_task_dependencies(self, task: Task) -> None:
        """Valida las dependencias de una tarea"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                # Verificar si la dependencia está en ejecución o pendiente
                if dep_id not in self.running_tasks and dep_id not in self.pending_tasks_by_id:
                    raise ValueError(f"Dependencia no encontrada o no en estado válido: {dep_id}")

    async def _task_worker(self, worker_id: str) -> None:
        """Worker que procesa tareas de la cola"""
        logger.info(f"Worker {worker_id} iniciado")
        
        while self.is_running:
            try:
                # Obtener tarea de la cola con timeout
                try:
                    priority, created_at, task = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue # Continue to next iteration of while loop to check self.is_running

                # Task dequeued, remove from pending_tasks_by_id
                if task.task_id in self.pending_tasks_by_id:
                    del self.pending_tasks_by_id[task.task_id]
                
                # Verificar dependencias y estado de la tarea antes de procesar
                if task.status == TaskStatus.CANCELLED:
                    logger.info(f"Worker {worker_id}: Tarea {task.task_id} ya estaba cancelada, descartando.")
                    # Asegurarse de que esté en failed_tasks si se canceló mientras estaba en la cola
                    if task.task_id not in self.failed_tasks:
                         self.failed_tasks[task.task_id] = task
                    continue

                if not await self._check_task_dependencies(task):
                    # Re-enqueue if dependencies are not met
                    logger.debug(f"Dependencias no listas para tarea {task.task_id}, re-encolando.")
                    await self.task_queue.put((priority, created_at, task))
                    self.pending_tasks_by_id[task.task_id] = task # Add back to lookup
                    await asyncio.sleep(1) # Avoid busy-looping
                    continue
                
                # Ejecutar tarea
                await self._process_single_task(task, worker_id)
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelado.")
                break # Exit the while loop
            except Exception as e:
                logger.error(f"Error en worker {worker_id}: {str(e)}", exc_info=True)
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_id} detenido")

    async def _check_task_dependencies(self, task: Task) -> bool:
        """Verifica si las dependencias de una tarea están completadas"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        return True

    async def _process_single_task(self, task: Task, worker_id: str) -> None:
        """
        Procesa una única tarea: la ejecuta, maneja su resultado (éxito/fallo),
        y actualiza su estado y las métricas.
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        self.running_tasks[task.task_id] = task
        
        logger.info(f"Worker {worker_id}: Iniciando tarea {task.task_id} ({task.task_type}) por agente {task.agent_id}")
        
        try:
            await self._emit_event('task_started', {'task_id': task.task_id, 'worker_id': worker_id, 'agent_id': task.agent_id})
            
            agent = self.registered_agents[task.agent_id]
            result = await asyncio.wait_for(
                agent.process(task.context),
                timeout=task.timeout
            )
            
            task.result = result
            task.completed_at = datetime.utcnow()
            
            if result.success:
                await self._handle_task_success(task)
            else:
                task.error = result.error
                await self._handle_task_failure(task, worker_id)
        
        except asyncio.TimeoutError:
            task.error = f"Timeout ({task.timeout}s) ejecutando tarea {task.task_id}"
            logger.warning(task.error)
            await self._handle_task_failure(task, worker_id)
        except Exception as e:
            task.error = f"Excepción ejecutando tarea {task.task_id}: {str(e)}"
            logger.error(task.error, exc_info=True)
            await self._handle_task_failure(task, worker_id)
        
        finally:
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
            await self._update_task_metrics(task)

    async def _handle_task_success(self, task: Task) -> None:
        """Maneja la finalización exitosa de una tarea."""
        task.status = TaskStatus.COMPLETED
        self.completed_tasks[task.task_id] = task

        logger.info(f"Tarea {task.task_id} completada exitosamente.")

        if task.callback:
            try:
                await task.callback(task, task.result)
            except Exception as e:
                logger.error(f"Error en callback de tarea {task.task_id}: {str(e)}", exc_info=True)

        await self._emit_event('task_completed', {
            'task_id': task.task_id,
            'execution_time': (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else 0,
            'result': task.result.data if task.result and hasattr(task.result, 'data') else None
        })

    async def _handle_task_failure(self, task: Task, worker_id: str) -> None:
        """Maneja el fallo de una tarea, incluyendo lógica de reintentos."""
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            logger.warning(f"Worker {worker_id}: Fallo en tarea {task.task_id} (intento {task.retry_count}/{task.max_retries}). Error: {task.error}. Reintentando...")
            task.status = TaskStatus.PENDING
            task.started_at = None # Reset start time for retry
            
            await asyncio.sleep(self.retry_delay)
            
            priority_value = task.priority.value
            await self.task_queue.put((priority_value, task.created_at, task)) # Re-enqueue
            self.pending_tasks_by_id[task.task_id] = task # Add back to lookup
            
            await self._emit_event('task_retry', {'task_id': task.task_id, 'retry_count': task.retry_count, 'error': task.error})
        else:
            logger.error(f"Worker {worker_id}: Tarea {task.task_id} falló definitivamente después de {task.retry_count} intentos. Error: {task.error}")
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow() # Mark completion time for failed task
            self.failed_tasks[task.task_id] = task
            
            await self._emit_event('task_failed', {'task_id': task.task_id, 'error': task.error, 'retry_count': task.retry_count})

    async def _update_task_metrics(self, task: Task) -> None:
        """Actualiza las métricas relacionadas con la ejecución de una tarea."""
        self.metrics['tasks_executed'] += 1
        
        if task.status == TaskStatus.COMPLETED:
            self.metrics['tasks_completed'] += 1
            
            # Tiempo de ejecución
            if task.started_at and task.completed_at:
                execution_time = (task.completed_at - task.started_at).total_seconds()
                current_avg = self.metrics['average_execution_time']
                total_completed = self.metrics['tasks_completed']
                
                # Actualizar promedio
                self.metrics['average_execution_time'] = (
                    (current_avg * (total_completed - 1) + execution_time) / total_completed
                )
        
        elif task.status == TaskStatus.FAILED:
            self.metrics['tasks_failed'] += 1
            
            # Tasa de error por agente
            agent_id = task.agent_id
            total_agent_tasks = sum(1 for t in list(self.completed_tasks.values()) + list(self.failed_tasks.values()) 
                                  if t.agent_id == agent_id)
            failed_agent_tasks = sum(1 for t in self.failed_tasks.values() if t.agent_id == agent_id)
            
            if total_agent_tasks > 0:
                self.metrics['error_rates'][agent_id] = failed_agent_tasks / total_agent_tasks

    async def _health_check_loop(self) -> None:
        """Loop de verificación de salud del sistema"""
        logger.info("Health check iniciado")
        
        while self.is_running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error en health check: {str(e)}")
                await asyncio.sleep(self.health_check_interval)
        
        logger.info("Health check detenido")

    async def _perform_health_check(self) -> None:
        """Realiza verificación de salud del sistema, incluyendo agentes en paralelo."""

        async def check_agent_health(agent_id: str, agent: BaseAgent) -> Optional[str]:
            """Chequea la salud de un único agente y retorna su ID si no está saludable."""
            try:
                health_context = {'operation': 'health_check'}
                # Asumiendo que BaseAgent.process es una corutina
                result = await asyncio.wait_for(agent.process(health_context), timeout=5.0)
                if not result.success:
                    logger.warning(f"Agente {agent_id} reportó health check no exitoso: {result.error}")
                    return agent_id
            except asyncio.TimeoutError:
                logger.warning(f"Agente {agent_id} timed out durante health check.")
                return agent_id
            except Exception as e:
                logger.warning(f"Excepción durante health check del agente {agent_id}: {str(e)}")
                return agent_id
            return None

        # Verificar agentes en paralelo
        agent_checks = [check_agent_health(agent_id, agent) for agent_id, agent in self.registered_agents.items()]
        results = await asyncio.gather(*agent_checks)
        unhealthy_agents = [agent_id for agent_id in results if agent_id is not None]

        # Verificar base de datos
        db_healthy = await db_manager.test_connection_async()
        
        # Verificar cola de tareas
        queue_size = self.task_queue.qsize()
        running_tasks_count = len(self.running_tasks)
        
        # Log de estado
        if unhealthy_agents or not db_healthy or queue_size > 100:
            logger.warning(f"Health check - Agentes no saludables: {unhealthy_agents}, "
                         f"DB: {'OK' if db_healthy else 'FAIL'}, "
                         f"Cola: {queue_size}, Ejecutando: {running_tasks_count}")
        else:
            logger.debug(f"Health check OK - Cola: {queue_size}, Ejecutando: {running_tasks_count}")

    # Gestión de Workflows
    
    async def create_workflow(self, name: str, description: str, steps: List[Dict[str, Any]]) -> str:
        """
        Crea un nuevo workflow.
        
        Args:
            name: Nombre del workflow
            description: Descripción del workflow
            steps: Lista de pasos del workflow
            
        Returns:
            ID del workflow creado
        """
        workflow_id = str(uuid.uuid4())
        
        # Convertir pasos a objetos WorkflowStep
        workflow_steps = []
        for step_data in steps:
            step = WorkflowStep(
                step_id=step_data['step_id'],
                agent_id=step_data['agent_id'],
                task_type=step_data['task_type'],
                context=step_data.get('context', {}),
                dependencies=step_data.get('dependencies', [])
            )
            workflow_steps.append(step)
        
        # Crear workflow
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            steps=workflow_steps
        )
        
        self.workflows[workflow_id] = workflow
        
        logger.info(f"Workflow creado: {workflow_id} ({name})")
        
        return workflow_id

    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> str:
        """
        Ejecuta un workflow.
        
        Args:
            workflow_id: ID del workflow a ejecutar
            context: Contexto global del workflow
            
        Returns:
            ID de ejecución del workflow
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow no encontrado: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        workflow.status = TaskStatus.RUNNING
        workflow.started_at = datetime.utcnow()
        workflow.context = context or {}
        
        execution_id = f"{workflow_id}_{int(datetime.utcnow().timestamp())}"
        
        logger.info(f"Ejecutando workflow: {workflow.name} (ID: {execution_id})")
        
        try:
            # Crear tareas para cada paso
            step_tasks = {}
            
            for step in workflow.steps:
                # Combinar contexto del workflow con contexto del paso
                step_context = {**workflow.context, **step.context}
                
                # Crear tarea
                task_id = await self.submit_task(
                    task_type=step.task_type,
                    agent_id=step.agent_id,
                    context=step_context,
                    dependencies=[step_tasks[dep] for dep in step.dependencies if dep in step_tasks],
                    metadata={'workflow_id': workflow_id, 'execution_id': execution_id, 'step_id': step.step_id}
                )
                
                step_tasks[step.step_id] = task_id
            
            # Emitir evento
            await self._emit_event('workflow_started', {
                'workflow_id': workflow_id,
                'execution_id': execution_id,
                'steps_count': len(workflow.steps)
            })
            
            return execution_id
            
        except Exception as e:
            workflow.status = TaskStatus.FAILED
            logger.error(f"Error ejecutando workflow {workflow_id}: {str(e)}")
            raise

    async def _load_workflow_templates(self) -> None:
        """Carga plantillas de workflows predefinidos"""
        # Workflow de ejemplo: Análisis completo de campaña
        campaign_analysis_steps = [
            {
                'step_id': 'data_collection',
                'agent_id': 'intelligence_agent',
                'task_type': 'collect_campaign_data',
                'context': {'analysis_type': 'campaign_performance'},
                'dependencies': []
            },
            {
                'step_id': 'security_check',
                'agent_id': 'security_agent',
                'task_type': 'security_audit',
                'context': {'audit_type': 'campaign_security'},
                'dependencies': []
            },
            {
                'step_id': 'performance_analysis',
                'agent_id': 'intelligence_agent',
                'task_type': 'analyze_performance',
                'context': {'include_visualizations': True},
                'dependencies': ['data_collection']
            },
            {
                'step_id': 'generate_report',
                'agent_id': 'intelligence_agent',
                'task_type': 'generate_report',
                'context': {'report_type': 'comprehensive'},
                'dependencies': ['performance_analysis', 'security_check']
            }
        ]
        
        await self.create_workflow(
            name="Análisis Completo de Campaña",
            description="Workflow completo para análisis de rendimiento y seguridad de campañas",
            steps=campaign_analysis_steps
        )
        
        logger.info("Plantillas de workflow cargadas")

    # Eventos y Callbacks
    
    def on(self, event: str, handler: Callable) -> None:
        """
        Registra un manejador de eventos.
        
        Args:
            event: Nombre del evento
            handler: Función manejadora
        """
        self.event_handlers[event].append(handler)

    async def _emit_event(self, event: str, data: Dict[str, Any]) -> None:
        """
        Emite un evento a todos los manejadores registrados.
        
        Args:
            event: Nombre del evento
            data: Datos del evento
        """
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event, data)
                    else:
                        handler(event, data)
                except Exception as e:
                    logger.error(f"Error en manejador de evento {event}: {str(e)}")

    # Métodos de consulta y estado
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de una tarea"""
        # Buscar en tareas en ejecución
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return self._task_to_dict(task)
        
        # Buscar en tareas completadas
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return self._task_to_dict(task)
        
        # Buscar en tareas fallidas
        if task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            return self._task_to_dict(task)
        
        return None

    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Convierte una tarea a diccionario"""
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'agent_id': task.agent_id,
            'status': task.status.value,
            'priority': task.priority.name,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'retry_count': task.retry_count,
            'error': task.error,
            'result': task.result.__dict__ if task.result else None,
            'metadata': task.metadata
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado general del sistema"""
        return {
            'is_running': self.is_running,
            'registered_agents': list(self.registered_agents.keys()),
            'queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'workflows': len(self.workflows),
            'metrics': self.metrics,
            'workers': len(self.worker_tasks)
        }

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de un agente específico"""
        if agent_id not in self.registered_agents:
            return None
        
        agent = self.registered_agents[agent_id]
        
        # Contar tareas por estado para este agente
        agent_running = sum(1 for t in self.running_tasks.values() if t.agent_id == agent_id)
        agent_completed = sum(1 for t in self.completed_tasks.values() if t.agent_id == agent_id)
        agent_failed = sum(1 for t in self.failed_tasks.values() if t.agent_id == agent_id)
        
        return {
            'agent_id': agent_id,
            'agent_type': agent.agent_type,
            'is_initialized': agent.is_initialized,
            'capabilities': self.agent_capabilities.get(agent_id, []),
            'tasks_running': agent_running,
            'tasks_completed': agent_completed,
            'tasks_failed': agent_failed,
            'error_rate': self.metrics['error_rates'].get(agent_id, 0.0),
            'last_activity': agent.last_activity.isoformat() if hasattr(agent, 'last_activity') else None
        }

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancela una tarea.
        
        Args:
            task_id: ID de la tarea a cancelar
            
        Returns:
            True si se canceló exitosamente
        """
        # Buscar en tareas en ejecución
        if task_id in self.running_tasks:
            task_to_cancel = self.running_tasks[task_id]
            task_to_cancel.status = TaskStatus.CANCELLED
            task_to_cancel.completed_at = datetime.utcnow()
            # Consider how to signal the running task to stop, if it's long-running.
            # For now, we just mark it and it will be cleaned up by its worker.
            # Or, if agent.process supports cancellation, call it here.
            logger.info(f"Marcando tarea en ejecución {task_id} como cancelada.")
            # No la movemos a failed_tasks aquí, _process_single_task lo hará si la tarea termina por cancelación.
            # O si queremos forzarlo:
            if task_id in self.running_tasks: del self.running_tasks[task_id] # remove from running
            self.failed_tasks[task_id] = task_to_cancel # move to failed explicitly
            await self._emit_event('task_cancelled', {'task_id': task_id})
            return True

        # Buscar en tareas pendientes (en cola)
        if task_id in self.pending_tasks_by_id:
            task_to_cancel = self.pending_tasks_by_id[task_id]
            task_to_cancel.status = TaskStatus.CANCELLED
            task_to_cancel.completed_at = datetime.utcnow()
            
            # Eliminar de pending_tasks_by_id
            del self.pending_tasks_by_id[task_id]
            
            # Mover a failed_tasks
            self.failed_tasks[task_id] = task_to_cancel
            
            logger.info(f"Tarea pendiente {task_id} cancelada y removida de la cola.")
            await self._emit_event('task_cancelled', {'task_id': task_id})
            # Nota: La tarea todavía está en self.task_queue. El worker la descartará
            # cuando la obtenga y vea su estado CANCELLED o si ya no está en pending_tasks_by_id.
            # Para una eliminación más limpia de la PriorityQueue, se necesitaría una implementación de PQ que soporte remove.
            return True
            
        logger.warning(f"Intento de cancelar tarea {task_id} no encontrada en ejecución ni pendiente.")
        return False

    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pausa un workflow"""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow.status = TaskStatus.PAUSED
            
            logger.info(f"Workflow pausado: {workflow_id}")
            await self._emit_event('workflow_paused', {'workflow_id': workflow_id})
            
            return True
        
        return False

    async def resume_workflow(self, workflow_id: str) -> bool:
        """Reanuda un workflow pausado"""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            if workflow.status == TaskStatus.PAUSED:
                workflow.status = TaskStatus.RUNNING
                
                logger.info(f"Workflow reanudado: {workflow_id}")
                await self._emit_event('workflow_resumed', {'workflow_id': workflow_id})
                
                return True
        
        return False

# Instancia global del orquestador
orchestrator = Orchestrator()

# Funciones de conveniencia
async def start_orchestrator():
    """Inicia el orquestador global"""
    await orchestrator.start()

async def stop_orchestrator():
    """Detiene el orquestador global"""
    await orchestrator.stop()

def get_orchestrator() -> Orchestrator:
    """Obtiene la instancia global del orquestador"""
    return orchestrator

