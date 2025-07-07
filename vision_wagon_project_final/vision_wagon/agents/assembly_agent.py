from .core.base_agent import BaseAgent, AgentResult
from ..database import db_manager
from ..database_models import Content
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AssemblyAgent(BaseAgent):
    agent_id: str = "assembly"
    agent_type: str = "operational"
    description: str = "Ensambla los activos generados (texto, imagen) en productos finales (episodios), considerando moderación de contenido."
    capabilities: list = ["content_assembly", "episode_creation", "asset_integration", "quality_control"]

    async def initialize(self) -> None:
        # Lógica de inicialización específica para AssemblyAgent
        logger.info(f"Inicializando {self.agent_id}Agent...")
        await super().initialize()

    async def process(self, context: Dict[str, Any]) -> AgentResult:
        logger.info(f"{self.agent_id}Agent procesando solicitud: {context.get('operation', 'N/A')}")
        
        operation = context.get("operation")
        
        try:
            if operation == "assemble_episode":
                return await self._assemble_episode(context)
            elif operation == "integrate_assets":
                return await self._integrate_assets(context)
            elif operation == "validate_content":
                return await self._validate_content(context)
            elif operation == "finalize_production":
                return await self._finalize_production(context)
            else:
                return AgentResult(success=False, error=f"Operación no soportada: {operation}")
                
        except Exception as e:
            logger.error(f"Error en AssemblyAgent: {str(e)}")
            return AgentResult(success=False, error=f"Error ensamblando contenido: {str(e)}")

    async def _assemble_episode(self, context: Dict[str, Any]) -> AgentResult:
        """Ensambla un episodio completo a partir de contenidos moderados."""
        episode_title = context.get("episode_title", "")
        content_ids = context.get("content_ids", [])
        campaign_id = context.get("campaign_id")
        
        if not episode_title or not content_ids:
            return AgentResult(success=False, error="Título del episodio y IDs de contenido requeridos")
        
        # Verificar que todos los contenidos estén aprobados por moderación
        approved_contents = []
        for content_id in content_ids:
            content = await db_manager.get_content(content_id)
            if not content:
                return AgentResult(success=False, error=f"Contenido {content_id} no encontrado")
            
            if content.is_flagged or content.moderation_status != "approved":
                return AgentResult(success=False, error=f"Contenido {content_id} no ha sido aprobado por moderación")
            
            approved_contents.append(content)
        
        # Ensamblar episodio
        episode_data = await self._create_episode_structure(episode_title, approved_contents)
        
        # Crear el episodio como contenido final
        final_episode_data = {
            "content_type": "episode",
            "content": json.dumps(episode_data),
            "content_metadata": {
                "episode_title": episode_title,
                "source_content_ids": content_ids,
                "assembly_timestamp": datetime.utcnow().isoformat()
            },
            "generated_by": self.agent_id,
            "campaign_id": campaign_id,
            "status": "published",  # Ya está moderado
            "moderation_status": "approved"
        }
        
        final_episode = await db_manager.create_content(final_episode_data)
        
        return AgentResult(success=True, data={
            "episode_id": str(final_episode.id),
            "episode_title": episode_title,
            "assembled_contents": len(approved_contents),
            "status": "published"
        })

    async def _integrate_assets(self, context: Dict[str, Any]) -> AgentResult:
        """Integra diferentes tipos de activos (texto, imagen, audio) en un formato cohesivo."""
        assets = context.get("assets", [])
        integration_type = context.get("integration_type", "multimedia")
        
        if not assets:
            return AgentResult(success=False, error="Activos requeridos para integración")
        
        # Verificar que todos los activos estén aprobados
        approved_assets = []
        for asset in assets:
            if asset.get("moderation_status") != "approved":
                return AgentResult(success=False, error=f"Activo {asset.get('id', 'unknown')} no aprobado")
            approved_assets.append(asset)
        
        # Integrar activos
        integrated_content = await self._perform_asset_integration(approved_assets, integration_type)
        
        return AgentResult(success=True, data={
            "integrated_content": integrated_content,
            "assets_count": len(approved_assets),
            "integration_type": integration_type
        })

    async def _validate_content(self, context: Dict[str, Any]) -> AgentResult:
        """Valida la calidad y coherencia del contenido ensamblado."""
        content_id = context.get("content_id")
        validation_criteria = context.get("validation_criteria", ["coherence", "quality", "moderation_compliance"])
        
        if not content_id:
            return AgentResult(success=False, error="ID de contenido requerido para validación")
        
        content = await db_manager.get_content(content_id)
        if not content:
            return AgentResult(success=False, error="Contenido no encontrado")
        
        # Realizar validación
        validation_results = await self._perform_content_validation(content, validation_criteria)
        
        return AgentResult(success=True, data={
            "content_id": content_id,
            "validation_results": validation_results,
            "is_valid": validation_results.get("overall_score", 0) >= 0.8
        })

    async def _finalize_production(self, context: Dict[str, Any]) -> AgentResult:
        """Finaliza la producción de un episodio o contenido."""
        content_id = context.get("content_id")
        production_notes = context.get("production_notes", "")
        
        if not content_id:
            return AgentResult(success=False, error="ID de contenido requerido para finalización")
        
        # Actualizar estado del contenido
        update_data = {
            "status": "finalized",
            "content_metadata": {
                "production_finalized": True,
                "finalization_timestamp": datetime.utcnow().isoformat(),
                "production_notes": production_notes
            }
        }
        
        updated_content = await db_manager.update_content(content_id, update_data)
        
        if not updated_content:
            return AgentResult(success=False, error="Error actualizando contenido")
        
        return AgentResult(success=True, data={
            "content_id": content_id,
            "status": "finalized",
            "finalization_timestamp": datetime.utcnow().isoformat()
        })

    async def _create_episode_structure(self, title: str, contents: List[Content]) -> Dict[str, Any]:
        """Crea la estructura de un episodio a partir de contenidos aprobados."""
        episode_structure = {
            "title": title,
            "creation_timestamp": datetime.utcnow().isoformat(),
            "segments": [],
            "metadata": {
                "total_contents": len(contents),
                "content_types": list(set([content.content_type for content in contents])),
                "assembly_agent": self.agent_id
            }
        }
        
        # Organizar contenidos en segmentos
        for i, content in enumerate(contents):
            segment = {
                "segment_id": i + 1,
                "content_id": str(content.id),
                "content_type": content.content_type,
                "content": content.content,
                "generated_by": content.generated_by,
                "metadata": content.content_metadata
            }
            episode_structure["segments"].append(segment)
        
        return episode_structure

    async def _perform_asset_integration(self, assets: List[Dict[str, Any]], integration_type: str) -> Dict[str, Any]:
        """Realiza la integración de activos."""
        integrated_content = {
            "integration_type": integration_type,
            "timestamp": datetime.utcnow().isoformat(),
            "assets": assets,
            "integration_metadata": {
                "total_assets": len(assets),
                "asset_types": list(set([asset.get("type", "unknown") for asset in assets]))
            }
        }
        
        if integration_type == "multimedia":
            # Lógica específica para integración multimedia
            integrated_content["multimedia_layout"] = self._create_multimedia_layout(assets)
        elif integration_type == "narrative":
            # Lógica específica para integración narrativa
            integrated_content["narrative_flow"] = self._create_narrative_flow(assets)
        
        return integrated_content

    async def _perform_content_validation(self, content: Content, criteria: List[str]) -> Dict[str, Any]:
        """Realiza validación de contenido según criterios especificados."""
        validation_results = {
            "content_id": str(content.id),
            "validation_timestamp": datetime.utcnow().isoformat(),
            "criteria_results": {},
            "overall_score": 0.0
        }
        
        total_score = 0.0
        
        for criterion in criteria:
            if criterion == "coherence":
                score = self._validate_coherence(content)
            elif criterion == "quality":
                score = self._validate_quality(content)
            elif criterion == "moderation_compliance":
                score = self._validate_moderation_compliance(content)
            else:
                score = 0.5  # Criterio desconocido
            
            validation_results["criteria_results"][criterion] = score
            total_score += score
        
        validation_results["overall_score"] = total_score / len(criteria) if criteria else 0.0
        
        return validation_results

    def _create_multimedia_layout(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crea un layout multimedia para los activos."""
        return {
            "layout_type": "multimedia",
            "sections": [
                {
                    "section_id": i + 1,
                    "asset_id": asset.get("id"),
                    "asset_type": asset.get("type"),
                    "position": f"section_{i + 1}"
                }
                for i, asset in enumerate(assets)
            ]
        }

    def _create_narrative_flow(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crea un flujo narrativo para los activos."""
        return {
            "flow_type": "narrative",
            "sequence": [
                {
                    "sequence_id": i + 1,
                    "asset_id": asset.get("id"),
                    "narrative_function": asset.get("narrative_function", "content"),
                    "transition": "smooth" if i < len(assets) - 1 else "conclusion"
                }
                for i, asset in enumerate(assets)
            ]
        }

    def _validate_coherence(self, content: Content) -> float:
        """Valida la coherencia del contenido."""
        # Simulación de validación de coherencia
        if content.content and len(content.content) > 10:
            return 0.9
        return 0.5

    def _validate_quality(self, content: Content) -> float:
        """Valida la calidad del contenido."""
        # Simulación de validación de calidad
        if content.content_metadata and content.generated_by:
            return 0.85
        return 0.6

    def _validate_moderation_compliance(self, content: Content) -> float:
        """Valida el cumplimiento de moderación."""
        if content.moderation_status == "approved" and not content.is_flagged:
            return 1.0
        elif content.moderation_status == "pending":
            return 0.5
        return 0.0

    async def cleanup(self) -> None:
        # Lógica de limpieza específica para AssemblyAgent
        logger.info(f"Limpiando {self.agent_id}Agent...")
        await super().cleanup()
