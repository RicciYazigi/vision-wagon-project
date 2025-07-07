"""
Vision Wagon - Main Application
Sistema de IA Generativa y Automatización para el ecosistema Nómada Alpha.
"""

import asyncio
import logging
import signal
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/vision_wagon.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Importar componentes principales
from .config_manager import get_config
from .database import db_manager, init_database
from .orchestrator import get_orchestrator
from .constructor.constructor import get_constructor
from .security_validator import get_security_validator

# Importar agentes
from .agents.assembly_agent import AssemblyAgent
from .agents.coaching_agent import CoachingAgent
from .agents.moderation_agent import ModerationAgent
from .agents.narrativearchitect_agent import NarrativeArchitectAgent

class VisionWagon:
    """
    Clase principal del sistema Vision Wagon.
    Coordina todos los componentes y agentes del sistema.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa Vision Wagon.
        
        Args:
            config_file: Archivo de configuración opcional
        """
        self.config_file = config_file
        self.is_running = False
        self.components = {}
        self.agents = {}
        
        # Configurar manejadores de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Vision Wagon inicializado")

    def _signal_handler(self, signum, frame):
        """Manejador de señales para cierre graceful"""
        logger.info(f"Señal recibida: {signum}")
        asyncio.create_task(self.shutdown())

    async def initialize(self) -> None:
        """Inicializa todos los componentes del sistema"""
        try:
            logger.info("🚀 Iniciando Vision Wagon...")
            
            # 1. Cargar configuración
            await self._initialize_config()
            
            # 2. Configurar logging según configuración
            await self._setup_logging()
            
            # 3. Inicializar base de datos
            await self._initialize_database()
            
            # 4. Inicializar componentes principales
            await self._initialize_components()
            
            # 5. Registrar agentes
            await self._register_agents()
            
            # 6. Iniciar orquestador
            await self._start_orchestrator()
            
            # 7. Verificar sistema
            await self._verify_system()
            
            self.is_running = True
            logger.info("✅ Vision Wagon iniciado exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Vision Wagon: {str(e)}")
            await self.shutdown()
            raise

    async def _initialize_config(self) -> None:
        """Inicializa la configuración del sistema"""
        logger.info("⚙️ Inicializando configuración...")
        
        config_manager = get_config()
        
        # Configurar logging según configuración
        config_manager.setup_logging()
        
        logger.info(f"Configuración cargada - Entorno: {config_manager.system.environment}")

    async def _setup_logging(self) -> None:
        """Configura el sistema de logging"""
        # Crear directorio de logs si no existe
        os.makedirs('logs', exist_ok=True)
        
        config_manager = get_config()
        
        # El logging ya fue configurado por el config_manager
        logger.info("📝 Sistema de logging configurado")

    async def _initialize_database(self) -> None:
        """Inicializa la base de datos"""
        logger.info("📊 Inicializando base de datos...")
        
        # Verificar conexión
        if not await db_manager.test_connection_async():
            raise Exception("No se pudo conectar a la base de datos")
        
        # Crear tablas si no existen
        await init_database()
        
        logger.info("✅ Base de datos inicializada")

    async def _initialize_components(self) -> None:
        """Inicializa los componentes principales"""
        logger.info("🔧 Inicializando componentes...")
        
        # Constructor
        constructor = get_constructor()
        await constructor.initialize()
        self.components['constructor'] = constructor
        logger.info("✅ Constructor inicializado")
        
        # Security Validator
        security_validator = get_security_validator()
        self.components['security'] = security_validator
        logger.info("✅ Security Validator inicializado")
        
        logger.info("✅ Componentes principales inicializados")

    async def _register_agents(self) -> None:
        """Registra todos los agentes en el orquestador"""
        logger.info("🤖 Registrando agentes...")
        
        orchestrator = get_orchestrator()
        
        # Intelligence Agent
        intelligence_agent = IntelligenceAgent()
        await orchestrator.register_agent(intelligence_agent)
        self.agents['intelligence'] = intelligence_agent
        logger.info("✅ Intelligence Agent registrado")
        
        # Security Agent
        security_agent = SecurityAgent()
        await orchestrator.register_agent(security_agent)
        self.agents['security'] = security_agent
        logger.info("✅ Security Agent registrado")
        
        logger.info(f"✅ {len(self.agents)} agentes registrados")

    async def _start_orchestrator(self) -> None:
        """Inicia el orquestador"""
        logger.info("🎭 Iniciando orquestador...")
        
        orchestrator = get_orchestrator()
        await orchestrator.start()
        self.components['orchestrator'] = orchestrator
        
        logger.info("✅ Orquestador iniciado")

    async def _verify_system(self) -> None:
        """Verifica que todos los sistemas estén funcionando"""
        logger.info("🔍 Verificando sistema...")
        
        # Verificar base de datos
        if not await db_manager.test_connection_async():
            raise Exception("Verificación de base de datos fallida")
        
        # Verificar orquestador
        orchestrator = get_orchestrator()
        system_status = orchestrator.get_system_status()
        if not system_status['is_running']:
            raise Exception("Verificación del orquestador fallida")
        
        # Verificar agentes
        registered_agents = system_status['registered_agents']
        if len(registered_agents) != len(self.agents):
            raise Exception("No todos los agentes están registrados")
        
        logger.info("✅ Verificación del sistema completada")

    async def run(self) -> None:
        """Ejecuta el bucle principal del sistema"""
        if not self.is_running:
            await self.initialize()
        
        logger.info("🔄 Vision Wagon ejecutándose...")
        logger.info("Presiona Ctrl+C para detener el sistema")
        
        try:
            # Bucle principal - mantener el sistema vivo
            while self.is_running:
                await asyncio.sleep(1)
                
                # Aquí se pueden agregar verificaciones periódicas
                # Por ejemplo, health checks, métricas, etc.
                
        except KeyboardInterrupt:
            logger.info("Interrupción de teclado recibida")
        except Exception as e:
            logger.error(f"Error en bucle principal: {str(e)}")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Cierra el sistema de forma graceful"""
        if not self.is_running:
            return
        
        logger.info("🛑 Cerrando Vision Wagon...")
        self.is_running = False
        
        try:
            # Detener orquestador
            if 'orchestrator' in self.components:
                await self.components['orchestrator'].stop()
                logger.info("✅ Orquestador detenido")
            
            # Limpiar constructor
            if 'constructor' in self.components:
                await self.components['constructor'].cleanup()
                logger.info("✅ Constructor limpiado")
            
            # Limpiar agentes
            for agent_name, agent in self.agents.items():
                try:
                    await agent.cleanup()
                    logger.info(f"✅ {agent_name} limpiado")
                except Exception as e:
                    logger.error(f"Error limpiando {agent_name}: {str(e)}")
            
            logger.info("👋 Vision Wagon cerrado exitosamente")
            
        except Exception as e:
            logger.error(f"Error durante el cierre: {str(e)}")

    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información del sistema"""
        info = {
            'name': 'Vision Wagon',
            'version': '1.0.0',
            'status': 'running' if self.is_running else 'stopped',
            'started_at': datetime.utcnow().isoformat(),
            'components': list(self.components.keys()),
            'agents': list(self.agents.keys())
        }
        
        if self.is_running and 'orchestrator' in self.components:
            orchestrator_status = self.components['orchestrator'].get_system_status()
            info.update({
                'orchestrator_status': orchestrator_status,
                'tasks_in_queue': orchestrator_status.get('queue_size', 0),
                'running_tasks': orchestrator_status.get('running_tasks', 0)
            })
        
        return info

    # Métodos de conveniencia para interactuar con el sistema
    
    async def submit_task(self, task_type: str, agent_id: str, context: Dict[str, Any]) -> str:
        """Envía una tarea al sistema"""
        if not self.is_running:
            raise Exception("Sistema no está ejecutándose")
        
        orchestrator = self.components.get('orchestrator')
        if not orchestrator:
            raise Exception("Orquestador no disponible")
        
        return await orchestrator.submit_task(task_type, agent_id, context)

    async def generate_content(self, content_type: str, prompt: str, **kwargs) -> str:
        """Genera contenido usando el constructor"""
        if not self.is_running:
            raise Exception("Sistema no está ejecutándose")
        
        constructor = self.components.get('constructor')
        if not constructor:
            raise Exception("Constructor no disponible")
        
        from constructor.constructor import ContentType
        content_type_enum = ContentType(content_type)
        
        return await constructor.generate_content(content_type_enum, prompt, **kwargs)

    def get_security_status(self) -> Dict[str, Any]:
        """Obtiene estado de seguridad"""
        if not self.is_running:
            return {'status': 'system_not_running'}
        
        security_validator = self.components.get('security')
        if not security_validator:
            return {'status': 'security_not_available'}
        
        return security_validator.get_security_summary()

# Función principal
async def main():
    """Función principal del sistema"""
    try:
        # Crear instancia de Vision Wagon
        vision_wagon = VisionWagon()
        
        # Ejecutar sistema
        await vision_wagon.run()
        
    except KeyboardInterrupt:
        logger.info("Interrupción de teclado - cerrando sistema")
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Verificar Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 o superior requerido")
        sys.exit(1)
    
    # Crear directorios necesarios
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    os.makedirs('generated_content', exist_ok=True)
    
    # Ejecutar sistema
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Vision Wagon cerrado por el usuario")
    except Exception as e:
        print(f"❌ Error fatal: {str(e)}")
        sys.exit(1)

