from .core.base_agent import BaseAgent, AgentResult
from ..database import db_manager
from ..database_models import Content # Assuming Content might be used for storing profiles or logs
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class CoachingAgent(BaseAgent):
    agent_id: str = "coaching"
    agent_type: str = "operational"
    description: str = "Aplica las directrices del usuario al perfil de personalidad del avatar de IA."
    capabilities: list = [] # Define las capacidades específicas de este agente

    async def initialize(self) -> None:
        # Lógica de inicialización específica para CoachingAgent
        logger.info(f"Inicializando {self.agent_id}Agent...")
        await super().initialize()

    async def process(self, context: Dict[str, Any]) -> AgentResult:
        operation_name = context.get("operation", "N/A")
        logger.info(f"{self.agent_id}Agent procesando solicitud: {operation_name}")

        avatar_id = context.get("avatar_id")
        guidelines = context.get("guidelines")

        if not avatar_id or not guidelines:
            return AgentResult(success=False, error="Missing avatar_id or guidelines in context.")

        try:
            # Retrieve current personality profile (simulated)
            current_profile = await db_manager.get_avatar_personality(avatar_id)
            if not current_profile:
                current_profile = {"traits": [], "tone": "neutral"}

            # Apply guidelines (simulated logic)
            updated_profile = self._apply_guidelines(current_profile, guidelines)

            # Save updated personality profile
            await db_manager.update_avatar_personality(avatar_id, updated_profile)

            return AgentResult(success=True, data={
                "avatar_id": avatar_id,
                "updated_profile": updated_profile
            })

        except Exception as e:
            logger.error(f"Error en CoachingAgent al procesar {avatar_id}: {str(e)}")
            return AgentResult(success=False, error=f"Error procesando coaching: {str(e)}")

    def _apply_guidelines(self, current_profile: Dict[str, Any], guidelines: Dict[str, Any]) -> Dict[str, Any]:
        # Simple logic to apply guidelines. In a real scenario, this would be more complex.
        updated_profile = current_profile.copy()

        if "add_traits" in guidelines:
            for trait in guidelines["add_traits"]:
                if trait not in updated_profile["traits"]:
                    updated_profile["traits"].append(trait)
        
        if "remove_traits" in guidelines:
            for trait in guidelines["remove_traits"]:
                if trait in updated_profile["traits"]:
                    updated_profile["traits"].remove(trait)

        if "set_tone" in guidelines:
            updated_profile["tone"] = guidelines["set_tone"]

        return updated_profile

    async def cleanup(self) -> None:
        # Lógica de limpieza específica para CoachingAgent
        logger.info(f"Limpiando {self.agent_id}Agent...")
        await super().cleanup()
