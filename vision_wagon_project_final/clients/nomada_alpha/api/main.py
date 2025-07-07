from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pika
import json
import os
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Nómada Alpha API", version="0.1.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
VISION_WAGON_URL = os.getenv("VISION_WAGON_URL", "http://vision_wagon:8000")

# Modelos Pydantic
class CampaignRequest(BaseModel):
    name: str
    description: Optional[str] = None
    campaign_type: Optional[str] = None
    target_audience: Optional[str] = None
    budget: Optional[int] = None
    config: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    campaign_id: int
    action_type: str
    context: Optional[Dict[str, Any]] = None

class EventMessage(BaseModel):
    event_type: str
    data: Dict[str, Any]
    timestamp: str

# Variables globales para conexiones
rabbitmq_connection = None
rabbitmq_channel = None

@app.on_event("startup")
async def startup_event():
    """Inicializar conexiones al arrancar la aplicación"""
    global rabbitmq_connection, rabbitmq_channel
    
    try:
        # Configurar RabbitMQ
        rabbitmq_connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        rabbitmq_channel = rabbitmq_connection.channel()
        
        # Declarar colas
        rabbitmq_channel.queue_declare(queue="nomada_events", durable=True)
        rabbitmq_channel.queue_declare(queue="campaign_tasks", durable=True)
        
        logger.info("Connected to RabbitMQ successfully")
        
        # Iniciar consumidor de eventos en background
        asyncio.create_task(start_event_consumer())
        
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones al apagar la aplicación"""
    global rabbitmq_connection
    if rabbitmq_connection and not rabbitmq_connection.is_closed:
        rabbitmq_connection.close()
        logger.info("RabbitMQ connection closed")

# Endpoints básicos
@app.get("/")
async def root():
    return {
        "service": "Nómada Alpha API",
        "version": "0.1.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "running",
            "rabbitmq": "connected" if rabbitmq_connection and not rabbitmq_connection.is_closed else "disconnected",
            "vision_wagon": "unknown"
        }
    }
    
    # Verificar conexión con Vision Wagon Core
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{VISION_WAGON_URL}/health", timeout=5.0)
            health_status["services"]["vision_wagon"] = "connected" if response.status_code == 200 else "error"
    except Exception:
        health_status["services"]["vision_wagon"] = "disconnected"
    
    return health_status

# Endpoints de campañas
@app.post("/campaigns")
async def create_campaign(campaign: CampaignRequest):
    """Crear una nueva campaña a través de Vision Wagon Core"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VISION_WAGON_URL}/campaigns",
                json=campaign.dict(),
                timeout=30.0
            )
            
            if response.status_code == 200:
                campaign_data = response.json()
                
                # Publicar evento de campaña creada
                await publish_event({
                    "event_type": "campaign_created",
                    "data": campaign_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return campaign_data
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Vision Wagon Core: {e}")
        raise HTTPException(status_code=503, detail="Vision Wagon Core unavailable")

@app.get("/campaigns")
async def list_campaigns():
    """Obtener lista de campañas"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{VISION_WAGON_URL}/campaigns", timeout=30.0)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Vision Wagon Core: {e}")
        raise HTTPException(status_code=503, detail="Vision Wagon Core unavailable")

@app.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: int):
    """Obtener detalles de una campaña específica"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{VISION_WAGON_URL}/campaigns/{campaign_id}", timeout=30.0)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Campaign not found")
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Vision Wagon Core: {e}")
        raise HTTPException(status_code=503, detail="Vision Wagon Core unavailable")

# Endpoints de tareas
@app.post("/tasks")
async def create_task(task: TaskRequest, background_tasks: BackgroundTasks):
    """Crear una nueva tarea y enviarla a la cola"""
    try:
        # Enviar tarea a RabbitMQ
        task_message = {
            "campaign_id": task.campaign_id,
            "action_type": task.action_type,
            "context": task.context or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        background_tasks.add_task(publish_task, task_message)
        
        return {
            "status": "task_queued",
            "task": task_message,
            "message": "Task has been queued for processing"
        }
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@app.post("/tasks/execute")
async def execute_task(task: TaskRequest):
    """Ejecutar una tarea directamente a través de Vision Wagon Core"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VISION_WAGON_URL}/tasks/execute",
                json=task.dict(),
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Publicar evento de tarea ejecutada
                await publish_event({
                    "event_type": "task_executed",
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return result
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Vision Wagon Core: {e}")
        raise HTTPException(status_code=503, detail="Vision Wagon Core unavailable")

# Endpoints de eventos
@app.get("/events")
async def get_recent_events():
    """Obtener eventos recientes (simulado)"""
    # En una implementación real, esto vendría de una base de datos o cache
    return {
        "events": [
            {
                "id": 1,
                "event_type": "campaign_created",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {"campaign_id": 1, "name": "Test Campaign"}
            }
        ],
        "total": 1
    }

# Funciones auxiliares
async def publish_event(event_data: Dict[str, Any]):
    """Publicar un evento a RabbitMQ"""
    try:
        if rabbitmq_channel:
            rabbitmq_channel.basic_publish(
                exchange='',
                routing_key='nomada_events',
                body=json.dumps(event_data),
                properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
            )
            logger.info(f"Event published: {event_data['event_type']}")
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")

async def publish_task(task_data: Dict[str, Any]):
    """Publicar una tarea a RabbitMQ"""
    try:
        if rabbitmq_channel:
            rabbitmq_channel.basic_publish(
                exchange='',
                routing_key='campaign_tasks',
                body=json.dumps(task_data),
                properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
            )
            logger.info(f"Task published: {task_data}")
    except Exception as e:
        logger.error(f"Failed to publish task: {e}")

async def start_event_consumer():
    """Iniciar consumidor de eventos (placeholder)"""
    # En una implementación real, aquí se configuraría el consumidor de RabbitMQ
    logger.info("Event consumer started (placeholder)")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

