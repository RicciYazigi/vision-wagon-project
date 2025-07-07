"""
BaseAgent - Clase base para todos los agentes de Vision Wagon
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Clase base abstracta para todos los agentes"""
    
    def __init__(self, agent_id: str, agent_type: str, config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}
        self.status = "inactive"
        self.created_at = datetime.utcnow()
        self.last_activity = None
        self.execution_count = 0
        
        # Configurar logging específico del agente
        self.logger = logging.getLogger(f"agent.{agent_id}")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Inicializa el agente - debe ser implementado por cada agente"""
        pass
    
    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una tarea - debe ser implementado por cada agente"""
        pass
    
    @abstractmethod
    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Valida datos de entrada - debe ser implementado por cada agente"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Limpia recursos - debe ser implementado por cada agente"""
        pass
    
    async def log_action(self, action: str, data: Dict[str, Any]) -> None:
        """Registra una acción del agente"""
        self.logger.info(f"Acción {action}: {data}")
        self.last_activity = datetime.utcnow()
        
        # TODO: Integrar con base de datos para logging persistente
        # await self._save_log_to_db(action, data)
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del agente"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "execution_count": self.execution_count,
            "config": self.config
        }
    
    async def start(self) -> bool:
        """Inicia el agente"""
        try:
            self.logger.info(f"Iniciando agente {self.agent_id}")
            
            if await self.initialize():
                self.status = "active"
                await self.log_action("agent_started", {"agent_id": self.agent_id})
                return True
            else:
                self.status = "error"
                return False
                
        except Exception as e:
            self.logger.error(f"Error iniciando agente {self.agent_id}: {e}")
            self.status = "error"
            return False
    
    async def stop(self) -> None:
        """Detiene el agente"""
        try:
            self.logger.info(f"Deteniendo agente {self.agent_id}")
            self.status = "stopping"
            
            await self.cleanup()
            
            self.status = "inactive"
            await self.log_action("agent_stopped", {"agent_id": self.agent_id})
            
        except Exception as e:
            self.logger.error(f"Error deteniendo agente {self.agent_id}: {e}")
            self.status = "error"
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el procesamiento principal del agente"""
        if self.status != "active":
            return {
                "status": "error",
                "error": f"Agente {self.agent_id} no está activo",
                "agent_status": self.status
            }
        
        try:
            # Validar entrada
            if not await self.validate_input(context):
                return {
                    "status": "error",
                    "error": "Validación de entrada falló",
                    "agent_id": self.agent_id
                }
            
            # Procesar
            self.execution_count += 1
            result = await self.process(context)
            
            await self.log_action("execution_completed", {
                "execution_count": self.execution_count,
                "result_status": result.get("status", "unknown")
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error ejecutando agente {self.agent_id}: {e}")
            await self.log_action("execution_error", {"error": str(e)})
            
            return {
                "status": "error",
                "error": str(e),
                "agent_id": self.agent_id
            }

