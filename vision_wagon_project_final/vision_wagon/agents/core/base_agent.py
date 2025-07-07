
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentResult:
    """Resultado de la ejecución de un agente"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BaseAgent:
    """
    Clase base para todos los agentes en Vision Wagon.
    Define la interfaz común y funcionalidades básicas.
    """
    agent_id: str = "base_agent"
    agent_type: str = "base"
    description: str = "Agente base del sistema Vision Wagon."
    capabilities: list = []

    def __init__(self):
        self.is_initialized = False
        self.last_activity: Optional[datetime] = None
        logger.info(f"Agente {self.agent_id} inicializado (no configurado)")

    async def initialize(self) -> None:
        """
        Inicializa el agente. Debe ser sobrescrito por agentes específicos.
        Realiza tareas de configuración, carga de modelos, etc.
        """
        logger.info(f"Inicializando agente {self.agent_id}...")
        self.is_initialized = True
        self.last_activity = datetime.utcnow()
        logger.info(f"Agente {self.agent_id} inicializado exitosamente.")

    async def process(self, context: Dict[str, Any]) -> AgentResult:
        """
        Procesa una solicitud o tarea. Debe ser sobrescrito por agentes específicos.
        
        Args:
            context: Diccionario con los datos de entrada para el procesamiento.
            
        Returns:
            AgentResult: Objeto con el resultado de la operación (éxito/fallo, datos, error).
        """
        self.last_activity = datetime.utcnow()
        operation_name = context.get("operation", "N/A")
        logger.info(f"Agente {self.agent_id} procesando solicitud: {operation_name}")
        return AgentResult(success=False, error="Método process no implementado en el agente base.")

    async def cleanup(self) -> None:
        """
        Realiza tareas de limpieza al detener o desregistrar el agente.
        Debe ser sobrescrito por agentes específicos.
        """
        logger.info(f"Limpiando agente {self.agent_id}...")
        self.is_initialized = False
        logger.info(f"Agente {self.agent_id} limpiado exitosamente.")

    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del agente.
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "is_initialized": self.is_initialized,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "description": self.description,
            "capabilities": self.capabilities
        }



