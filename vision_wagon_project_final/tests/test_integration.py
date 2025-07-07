#!/usr/bin/env python3
"""
Script de pruebas de integración para Nómada v4.3
Valida la integración completa de moderación y coaching
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Añadir el directorio de Vision Wagon al path
sys.path.append('/home/ubuntu/vision_wagon')

from vision_wagon.config.config_manager import get_config
from vision_wagon.database.database import db_manager, init_database
from vision_wagon.orchestrator.orchestrator import get_orchestrator
from vision_wagon.agents.operational.moderation_agent import ModerationAgent
from vision_wagon.agents.operational.coaching_agent import CoachingAgent
from vision_wagon.agents.operational.narrativearchitect_agent import NarrativeArchitectAgent
from vision_wagon.agents.operational.assembly_agent import AssemblyAgent

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTester:
    def __init__(self):
        self.config = None
        self.orchestrator = None
        self.test_results = []

    async def setup(self):
        """Configuración inicial para las pruebas."""
        logger.info("🔧 Configurando entorno de pruebas...")
        
        try:
            # Cargar configuración
            self.config = get_config()
            logger.info("✅ Configuración cargada")
            
            # Inicializar base de datos
            await init_database()
            logger.info("✅ Base de datos inicializada")
            
            # Obtener orchestrator
            self.orchestrator = get_orchestrator()
            logger.info("✅ Orchestrator inicializado")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error en setup: {str(e)}")
            return False

    async def test_moderation_agent(self):
        """Prueba el ModerationAgent."""
        logger.info("🧪 Probando ModerationAgent...")
        
        try:
            agent = ModerationAgent()
            await agent.initialize()
            
            # Crear contenido de prueba
            test_content = {
                "content_id": "test_content_001",
                "content": "Este es un comentario de prueba para moderación.",
                "content_type": "comment",
                "user_id": "test_user_001"
            }
            
            # Probar moderación
            context = {
                "operation": "moderate_content",
                "content": test_content
            }
            
            result = await agent.process(context)
            
            if result.success:
                logger.info("✅ ModerationAgent funcionando correctamente")
                self.test_results.append({"test": "ModerationAgent", "status": "PASS", "details": result.data})
                return True
            else:
                logger.error(f"❌ ModerationAgent falló: {result.error}")
                self.test_results.append({"test": "ModerationAgent", "status": "FAIL", "error": result.error})
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando ModerationAgent: {str(e)}")
            self.test_results.append({"test": "ModerationAgent", "status": "ERROR", "error": str(e)})
            return False

    async def test_coaching_agent(self):
        """Prueba el CoachingAgent."""
        logger.info("🧪 Probando CoachingAgent...")
        
        try:
            agent = CoachingAgent()
            await agent.initialize()
            
            # Probar actualización de personalidad
            context = {
                "operation": "update_personality",
                "avatar_id": "avatar_test_001",
                "personality_data": {
                    "traits": ["empática", "creativa"],
                    "tone": "cálido y acogedor",
                    "style_preferences": ["narrativa descriptiva", "diálogos emotivos"]
                }
            }
            
            result = await agent.process(context)
            
            if result.success:
                logger.info("✅ CoachingAgent funcionando correctamente")
                self.test_results.append({"test": "CoachingAgent", "status": "PASS", "details": result.data})
                return True
            else:
                logger.error(f"❌ CoachingAgent falló: {result.error}")
                self.test_results.append({"test": "CoachingAgent", "status": "FAIL", "error": result.error})
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando CoachingAgent: {str(e)}")
            self.test_results.append({"test": "CoachingAgent", "status": "ERROR", "error": str(e)})
            return False

    async def test_narrative_architect_integration(self):
        """Prueba la integración del NarrativeArchitect con coaching."""
        logger.info("🧪 Probando integración NarrativeArchitect + Coaching...")
        
        try:
            agent = NarrativeArchitectAgent()
            await agent.initialize()
            
            # Probar generación de narrativa con avatar
            context = {
                "operation": "generate_narrative",
                "prompt": "Una aventura épica en un mundo fantástico",
                "avatar_id": "avatar_test_001",
                "campaign_id": "campaign_test_001"
            }
            
            result = await agent.process(context)
            
            if result.success:
                logger.info("✅ NarrativeArchitect + Coaching funcionando correctamente")
                self.test_results.append({"test": "NarrativeArchitect_Integration", "status": "PASS", "details": result.data})
                return True
            else:
                logger.error(f"❌ NarrativeArchitect + Coaching falló: {result.error}")
                self.test_results.append({"test": "NarrativeArchitect_Integration", "status": "FAIL", "error": result.error})
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando NarrativeArchitect + Coaching: {str(e)}")
            self.test_results.append({"test": "NarrativeArchitect_Integration", "status": "ERROR", "error": str(e)})
            return False

    async def test_assembly_agent_integration(self):
        """Prueba la integración del AssemblyAgent con moderación."""
        logger.info("🧪 Probando integración AssemblyAgent + Moderación...")
        
        try:
            agent = AssemblyAgent()
            await agent.initialize()
            
            # Probar validación de contenido
            context = {
                "operation": "validate_content",
                "content_id": "test_content_001",
                "validation_criteria": ["coherence", "quality", "moderation_compliance"]
            }
            
            result = await agent.process(context)
            
            if result.success:
                logger.info("✅ AssemblyAgent + Moderación funcionando correctamente")
                self.test_results.append({"test": "AssemblyAgent_Integration", "status": "PASS", "details": result.data})
                return True
            else:
                logger.error(f"❌ AssemblyAgent + Moderación falló: {result.error}")
                self.test_results.append({"test": "AssemblyAgent_Integration", "status": "FAIL", "error": result.error})
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando AssemblyAgent + Moderación: {str(e)}")
            self.test_results.append({"test": "AssemblyAgent_Integration", "status": "ERROR", "error": str(e)})
            return False

    async def test_database_operations(self):
        """Prueba las operaciones de base de datos."""
        logger.info("🧪 Probando operaciones de base de datos...")
        
        try:
            # Probar creación de contenido
            content_data = {
                "content_type": "test",
                "content": "Contenido de prueba",
                "content_metadata": {"test": True},
                "generated_by": "integration_test",
                "status": "draft"
            }
            
            content = await db_manager.create_content(content_data)
            
            if content:
                logger.info("✅ Operaciones de base de datos funcionando correctamente")
                self.test_results.append({"test": "Database_Operations", "status": "PASS", "content_id": str(content.id)})
                return True
            else:
                logger.error("❌ Error creando contenido en base de datos")
                self.test_results.append({"test": "Database_Operations", "status": "FAIL", "error": "No se pudo crear contenido"})
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando base de datos: {str(e)}")
            self.test_results.append({"test": "Database_Operations", "status": "ERROR", "error": str(e)})
            return False

    async def run_all_tests(self):
        """Ejecuta todas las pruebas de integración."""
        logger.info("🚀 Iniciando pruebas de integración de Nómada v4.3")
        
        # Setup
        if not await self.setup():
            logger.error("❌ Fallo en configuración inicial")
            return False
        
        # Ejecutar pruebas
        tests = [
            self.test_database_operations,
            self.test_moderation_agent,
            self.test_coaching_agent,
            self.test_narrative_architect_integration,
            self.test_assembly_agent_integration
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if await test():
                passed += 1
        
        # Resumen
        logger.info(f"\n📊 RESUMEN DE PRUEBAS:")
        logger.info(f"✅ Pasaron: {passed}/{total}")
        logger.info(f"❌ Fallaron: {total - passed}/{total}")
        
        if passed == total:
            logger.info("🎉 ¡Todas las pruebas pasaron! Sistema integrado correctamente.")
            return True
        else:
            logger.warning("⚠️ Algunas pruebas fallaron. Revisar logs para detalles.")
            return False

    def generate_report(self):
        """Genera un reporte detallado de las pruebas."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": len(self.test_results),
            "passed": len([r for r in self.test_results if r["status"] == "PASS"]),
            "failed": len([r for r in self.test_results if r["status"] in ["FAIL", "ERROR"]]),
            "results": self.test_results
        }
        
        return report

async def main():
    """Función principal."""
    tester = IntegrationTester()
    success = await tester.run_all_tests()
    
    # Generar reporte
    report = tester.generate_report()
    
    # Guardar reporte
    import json
    with open('/home/ubuntu/integration_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"📄 Reporte guardado en: /home/ubuntu/integration_test_report.json")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

