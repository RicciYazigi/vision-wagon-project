#!/usr/bin/env python3
"""
Prueba básica del sistema Vision Wagon
"""

import sys
import os
import asyncio
import logging

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vision_wagon'))

# Configurar logging para las pruebas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_imports():
    """Prueba que todos los agentes se puedan importar correctamente"""
    try:
        from vision_wagon.agents.core.base_agent import BaseAgent, AgentResult
        from vision_wagon.agents.assembly_agent import AssemblyAgent
        from vision_wagon.agents.coaching_agent import CoachingAgent
        from vision_wagon.agents.moderation_agent import ModerationAgent
        from vision_wagon.agents.narrativearchitect_agent import NarrativeArchitectAgent
        
        logger.info("✓ Todos los agentes se importaron correctamente")
        return True
    except Exception as e:
        logger.error(f"✗ Error importando agentes: {e}")
        return False

async def test_agent_initialization():
    """Prueba que los agentes se puedan inicializar"""
    try:
        from vision_wagon.agents.assembly_agent import AssemblyAgent
        from vision_wagon.agents.coaching_agent import CoachingAgent
        from vision_wagon.agents.moderation_agent import ModerationAgent
        from vision_wagon.agents.narrativearchitect_agent import NarrativeArchitectAgent
        
        # Crear instancias de los agentes
        assembly_agent = AssemblyAgent()
        coaching_agent = CoachingAgent()
        moderation_agent = ModerationAgent()
        narrative_agent = NarrativeArchitectAgent()
        
        # Verificar que tienen los atributos esperados
        agents = [assembly_agent, coaching_agent, moderation_agent, narrative_agent]
        
        for agent in agents:
            assert hasattr(agent, 'agent_id'), f"Agente {agent.__class__.__name__} no tiene agent_id"
            assert hasattr(agent, 'agent_type'), f"Agente {agent.__class__.__name__} no tiene agent_type"
            assert hasattr(agent, 'description'), f"Agente {agent.__class__.__name__} no tiene description"
            assert hasattr(agent, 'capabilities'), f"Agente {agent.__class__.__name__} no tiene capabilities"
        
        logger.info("✓ Todos los agentes se inicializaron correctamente")
        return True
    except Exception as e:
        logger.error(f"✗ Error inicializando agentes: {e}")
        return False

async def test_agent_basic_functionality():
    """Prueba funcionalidad básica de los agentes"""
    try:
        from vision_wagon.agents.assembly_agent import AssemblyAgent
        
        # Crear y inicializar un agente
        agent = AssemblyAgent()
        await agent.initialize()
        
        # Verificar que se inicializó correctamente
        assert agent.is_initialized, "El agente no se marcó como inicializado"
        assert agent.last_activity is not None, "El agente no registró actividad"
        
        logger.info("✓ Funcionalidad básica de agentes funciona correctamente")
        return True
    except Exception as e:
        logger.error(f"✗ Error en funcionalidad básica: {e}")
        return False

async def test_config_loading():
    """Prueba que la configuración se pueda cargar"""
    try:
        # Verificar que el archivo de configuración existe
        config_path = os.path.join(os.path.dirname(__file__), 'vision_wagon', 'config.yaml')
        assert os.path.exists(config_path), f"Archivo de configuración no encontrado: {config_path}"
        
        logger.info("✓ Archivo de configuración encontrado")
        return True
    except Exception as e:
        logger.error(f"✗ Error cargando configuración: {e}")
        return False

async def run_all_tests():
    """Ejecuta todas las pruebas"""
    logger.info("=== Iniciando pruebas básicas de Vision Wagon ===")
    
    tests = [
        ("Importación de agentes", test_agent_imports),
        ("Inicialización de agentes", test_agent_initialization),
        ("Funcionalidad básica", test_agent_basic_functionality),
        ("Carga de configuración", test_config_loading),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Ejecutando: {test_name} ---")
        result = await test_func()
        results.append((test_name, result))
    
    # Resumen de resultados
    logger.info("\n=== Resumen de Pruebas ===")
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\nTotal: {len(results)} pruebas")
    logger.info(f"Pasaron: {passed}")
    logger.info(f"Fallaron: {failed}")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

