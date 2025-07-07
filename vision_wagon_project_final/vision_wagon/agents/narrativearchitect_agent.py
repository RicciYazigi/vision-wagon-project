from .core.base_agent import BaseAgent, AgentResult
from ..database import db_manager
from ..database_models import Content
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class NarrativeArchitectAgent(BaseAgent):
    agent_id: str = "narrativearchitect"
    agent_type: str = "operational"
    description: str = "Diseña los arcos narrativos, tramas y diálogos, asistido por IA y considerando directrices de coaching."
    capabilities: list = ["narrative_generation", "character_development", "dialogue_creation", "plot_structuring"]

    async def initialize(self) -> None:
        # Lógica de inicialización específica para NarrativeArchitectAgent
        logger.info(f"Inicializando {self.agent_id}Agent...")
        await super().initialize()

    async def process(self, context: Dict[str, Any]) -> AgentResult:
        logger.info(f"{self.agent_id}Agent procesando solicitud: {context.get('operation', 'N/A')}")
        
        operation = context.get("operation")
        
        try:
            if operation == "generate_narrative":
                return await self._generate_narrative(context)
            elif operation == "develop_character":
                return await self._develop_character(context)
            elif operation == "create_dialogue":
                return await self._create_dialogue(context)
            elif operation == "structure_plot":
                return await self._structure_plot(context)
            else:
                return AgentResult(success=False, error=f"Operación no soportada: {operation}")
                
        except Exception as e:
            logger.error(f"Error en NarrativeArchitectAgent: {str(e)}")
            return AgentResult(success=False, error=f"Error procesando narrativa: {str(e)}")

    async def _generate_narrative(self, context: Dict[str, Any]) -> AgentResult:
        """Genera una narrativa considerando las directrices de coaching de avatares."""
        prompt = context.get("prompt", "")
        avatar_id = context.get("avatar_id")
        campaign_id = context.get("campaign_id")
        
        if not prompt:
            return AgentResult(success=False, error="Prompt requerido para generar narrativa")
        
        # Obtener perfil de personalidad del avatar si está disponible
        avatar_personality = None
        if avatar_id:
            avatar_personality = await db_manager.get_avatar_personality(avatar_id)
        
        # Generar narrativa considerando la personalidad del avatar
        narrative_content = await self._create_narrative_content(prompt, avatar_personality)
        
        # Crear contenido en la base de datos para moderación
        content_data = {
            "content_type": "narrative",
            "content": narrative_content,
            "content_metadata": {
                "prompt": prompt,
                "avatar_id": avatar_id,
                "personality_applied": avatar_personality is not None
            },
            "generated_by": self.agent_id,
            "campaign_id": campaign_id,
            "status": "draft"  # Será moderado antes de publicación
        }
        
        content = await db_manager.create_content(content_data)
        
        return AgentResult(success=True, data={
            "content_id": str(content.id),
            "narrative": narrative_content,
            "avatar_personality_applied": avatar_personality is not None,
            "status": "pending_moderation"
        })

    async def _develop_character(self, context: Dict[str, Any]) -> AgentResult:
        """Desarrolla un personaje basado en directrices de coaching."""
        character_name = context.get("character_name", "")
        avatar_id = context.get("avatar_id")
        traits = context.get("traits", [])
        
        if not character_name:
            return AgentResult(success=False, error="Nombre del personaje requerido")
        
        # Obtener perfil de personalidad del avatar
        avatar_personality = None
        if avatar_id:
            avatar_personality = await db_manager.get_avatar_personality(avatar_id)
        
        # Desarrollar personaje considerando la personalidad del avatar
        character_profile = await self._create_character_profile(character_name, traits, avatar_personality)
        
        return AgentResult(success=True, data={
            "character_name": character_name,
            "character_profile": character_profile,
            "avatar_influence": avatar_personality is not None
        })

    async def _create_dialogue(self, context: Dict[str, Any]) -> AgentResult:
        """Crea diálogos considerando la personalidad del avatar."""
        scene_context = context.get("scene_context", "")
        characters = context.get("characters", [])
        avatar_id = context.get("avatar_id")
        
        if not scene_context or not characters:
            return AgentResult(success=False, error="Contexto de escena y personajes requeridos")
        
        # Obtener perfil de personalidad del avatar
        avatar_personality = None
        if avatar_id:
            avatar_personality = await db_manager.get_avatar_personality(avatar_id)
        
        # Crear diálogos considerando la personalidad
        dialogue = await self._generate_dialogue(scene_context, characters, avatar_personality)
        
        return AgentResult(success=True, data={
            "scene_context": scene_context,
            "dialogue": dialogue,
            "personality_influenced": avatar_personality is not None
        })

    async def _structure_plot(self, context: Dict[str, Any]) -> AgentResult:
        """Estructura una trama considerando directrices narrativas."""
        theme = context.get("theme", "")
        genre = context.get("genre", "")
        target_length = context.get("target_length", "medium")
        
        if not theme:
            return AgentResult(success=False, error="Tema requerido para estructurar trama")
        
        # Estructurar trama
        plot_structure = await self._create_plot_structure(theme, genre, target_length)
        
        return AgentResult(success=True, data={
            "theme": theme,
            "genre": genre,
            "plot_structure": plot_structure
        })

    async def _create_narrative_content(self, prompt: str, avatar_personality: Optional[Dict[str, Any]]) -> str:
        """Crea contenido narrativo considerando la personalidad del avatar."""
        # Simulación de generación de narrativa
        base_narrative = f"Basándose en '{prompt}', se desarrolla una historia..."
        
        if avatar_personality:
            traits = avatar_personality.get("traits", [])
            tone = avatar_personality.get("tone", "neutral")
            
            # Aplicar personalidad a la narrativa
            personality_influence = f" [Influenciado por rasgos: {', '.join(traits)} con tono {tone}]"
            base_narrative += personality_influence
        
        return base_narrative

    async def _create_character_profile(self, name: str, traits: List[str], avatar_personality: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Crea un perfil de personaje."""
        profile = {
            "name": name,
            "base_traits": traits,
            "background": f"Personaje desarrollado para la narrativa: {name}",
            "motivations": ["Objetivo principal del personaje"],
            "conflicts": ["Conflicto interno o externo"]
        }
        
        if avatar_personality:
            # Influenciar el perfil con la personalidad del avatar
            avatar_traits = avatar_personality.get("traits", [])
            profile["avatar_influenced_traits"] = avatar_traits
            profile["personality_tone"] = avatar_personality.get("tone", "neutral")
        
        return profile

    async def _generate_dialogue(self, scene_context: str, characters: List[str], avatar_personality: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Genera diálogos para una escena."""
        dialogue = []
        
        for i, character in enumerate(characters):
            line = f"Línea de diálogo para {character} en el contexto: {scene_context}"
            
            if avatar_personality and i == 0:  # Aplicar personalidad al primer personaje
                tone = avatar_personality.get("tone", "neutral")
                line += f" [Tono: {tone}]"
            
            dialogue.append({
                "character": character,
                "line": line,
                "emotion": "neutral"
            })
        
        return dialogue

    async def _create_plot_structure(self, theme: str, genre: str, target_length: str) -> Dict[str, Any]:
        """Crea una estructura de trama."""
        structure = {
            "theme": theme,
            "genre": genre,
            "target_length": target_length,
            "acts": [
                {
                    "act": 1,
                    "title": "Introducción",
                    "description": f"Establecimiento del mundo y personajes para el tema: {theme}",
                    "key_events": ["Presentación del protagonista", "Incidente incitante"]
                },
                {
                    "act": 2,
                    "title": "Desarrollo",
                    "description": "Desarrollo del conflicto principal",
                    "key_events": ["Escalada del conflicto", "Punto de giro"]
                },
                {
                    "act": 3,
                    "title": "Resolución",
                    "description": "Clímax y resolución de la historia",
                    "key_events": ["Clímax", "Resolución", "Desenlace"]
                }
            ]
        }
        
        return structure

    async def cleanup(self) -> None:
        # Lógica de limpieza específica para NarrativeArchitectAgent
        logger.info(f"Limpiando {self.agent_id}Agent...")
        await super().cleanup()
