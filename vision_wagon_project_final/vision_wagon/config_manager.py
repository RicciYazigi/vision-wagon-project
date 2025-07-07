"""
Config Manager - Vision Wagon
Gestor centralizado de configuración para el sistema Vision Wagon.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    url: str = "sqlite:///./vision_wagon.db"
    async_url: str = "sqlite+aiosqlite:///./vision_wagon.db"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600

@dataclass
class AgentConfig:
    """Configuración base para agentes"""
    max_retries: int = 3
    timeout: float = 30.0
    debug_mode: bool = False
    log_level: str = "INFO"
    custom_settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    enable_authentication: bool = True
    enable_authorization: bool = True
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 100
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    enable_https_only: bool = False

@dataclass
class APIConfig:
    """Configuración de APIs externas"""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    stability_api_key: str = ""
    elevenlabs_api_key: str = ""
    replicate_api_key: str = ""
    timeout: float = 60.0
    max_retries: int = 3

@dataclass
class LoggingConfig:
    """Configuración de logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "logs/vision_wagon.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    console_enabled: bool = True

@dataclass
class OrchestratorConfig:
    """Configuración del orquestador"""
    max_concurrent_tasks: int = 10
    task_timeout: float = 300.0
    retry_delay: float = 5.0
    health_check_interval: float = 60.0
    enable_task_queue: bool = True
    queue_backend: str = "memory"  # memory, redis, rabbitmq

@dataclass
class SystemConfig:
    """Configuración del sistema"""
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = True
    data_directory: str = "data"
    temp_directory: str = "temp"
    max_upload_size: int = 104857600  # 100MB

class ConfigManager:
    """Gestor centralizado de configuración"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_file: Ruta al archivo de configuración (YAML o JSON)
        """
        self.config_file = config_file or os.getenv("VISION_WAGON_CONFIG", os.path.join(os.path.dirname(__file__), "config.yaml"))
        self.config_data: Dict[str, Any] = {}
        
        # Configuraciones por defecto
        self.database = DatabaseConfig()
        self.agent = AgentConfig()
        self.security = SecurityConfig()
        self.api = APIConfig()
        self.logging = LoggingConfig()
        self.orchestrator = OrchestratorConfig()
        self.system = SystemConfig()
        
        # Cargar configuración
        self._load_config()
        self._load_environment_variables()
        self._validate_config()
        
        logger.info(f"ConfigManager inicializado con archivo: {self.config_file}")

    def _load_config(self) -> None:
        """Carga la configuración desde archivo"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"Archivo de configuración no encontrado: {self.config_file}")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    self.config_data = yaml.safe_load(f) or {}
                elif config_path.suffix.lower() == '.json':
                    self.config_data = json.load(f)
                else:
                    logger.error(f"Formato de archivo no soportado: {config_path.suffix}")
                    return
            
            # Aplicar configuración cargada
            self._apply_config(self.config_data)
            logger.info("Configuración cargada exitosamente desde archivo")
            
        except Exception as e:
            logger.error(f"Error cargando configuración: {str(e)}")

    def _load_environment_variables(self) -> None:
        """Carga configuración desde variables de entorno"""
        env_mappings = {
            # Database
            'DATABASE_URL': ('database', 'url'),
            'ASYNC_DATABASE_URL': ('database', 'async_url'),
            
            # Security
            'JWT_SECRET_KEY': ('security', 'jwt_secret_key'),
            'ENABLE_AUTHENTICATION': ('security', 'enable_authentication'),
            
            # APIs
            'OPENAI_API_KEY': ('api', 'openai_api_key'),
            'ANTHROPIC_API_KEY': ('api', 'anthropic_api_key'),
            'STABILITY_API_KEY': ('api', 'stability_api_key'),
            'ELEVENLABS_API_KEY': ('api', 'elevenlabs_api_key'),
            'REPLICATE_API_KEY': ('api', 'replicate_api_key'),
            
            # System
            'ENVIRONMENT': ('system', 'environment'),
            'DEBUG': ('system', 'debug'),
            'HOST': ('system', 'host'),
            'PORT': ('system', 'port'),
            
            # Logging
            'LOG_LEVEL': ('logging', 'level'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convertir tipos según sea necesario
                if key in ['enable_authentication', 'debug']:
                    value = value.lower() in ['true', '1', 'yes', 'on']
                elif key == 'port':
                    value = int(value)
                
                # Aplicar valor
                config_obj = getattr(self, section)
                if hasattr(config_obj, key):
                    setattr(config_obj, key, value)
                    logger.debug(f"Variable de entorno aplicada: {env_var} -> {section}.{key}")

    def _apply_config(self, config_data: Dict[str, Any]) -> None:
        """Aplica la configuración cargada a los objetos de configuración"""
        for section_name, section_data in config_data.items():
            if hasattr(self, section_name) and isinstance(section_data, dict):
                config_obj = getattr(self, section_name)
                for key, value in section_data.items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)

    def _validate_config(self) -> None:
        """Valida la configuración cargada"""
        errors = []
        
        # Validar configuración de seguridad
        if self.security.enable_authentication and not self.security.jwt_secret_key:
            errors.append("JWT secret key es requerido cuando la autenticación está habilitada")
        
        # Validar configuración de base de datos
        if not self.database.url:
            errors.append("URL de base de datos es requerida")
        
        # Validar configuración del sistema
        if self.system.port < 1 or self.system.port > 65535:
            errors.append("Puerto debe estar entre 1 y 65535")
        
        if errors:
            error_msg = "Errores de configuración encontrados:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

    def get_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """
        Obtiene la configuración específica de un agente.
        
        Args:
            agent_id: ID del agente
            
        Returns:
            Configuración del agente
        """
        # Configuración base
        base_config = {
            'max_retries': self.agent.max_retries,
            'timeout': self.agent.timeout,
            'debug_mode': self.agent.debug_mode,
            'log_level': self.agent.log_level,
        }
        
        # Configuración específica del agente desde archivo
        agent_configs = self.config_data.get('agents', {})
        agent_specific = agent_configs.get(agent_id, {})
        
        # Combinar configuraciones
        final_config = {**base_config, **agent_specific, **self.agent.custom_settings}
        
        return final_config

    def get_database_url(self, async_mode: bool = False) -> str:
        """
        Obtiene la URL de conexión a la base de datos.
        
        Args:
            async_mode: Si True, devuelve la URL asíncrona
            
        Returns:
            URL de conexión
        """
        return self.database.async_url if async_mode else self.database.url

    def get_api_config(self, service: str) -> Dict[str, Any]:
        """
        Obtiene la configuración de una API externa.
        
        Args:
            service: Nombre del servicio (openai, anthropic, etc.)
            
        Returns:
            Configuración de la API
        """
        api_key_map = {
            'openai': self.api.openai_api_key,
            'anthropic': self.api.anthropic_api_key,
            'stability': self.api.stability_api_key,
            'elevenlabs': self.api.elevenlabs_api_key,
            'replicate': self.api.replicate_api_key,
        }
        
        return {
            'api_key': api_key_map.get(service, ''),
            'timeout': self.api.timeout,
            'max_retries': self.api.max_retries,
        }

    def update_config(self, section: str, key: str, value: Any) -> None:
        """
        Actualiza un valor de configuración.
        
        Args:
            section: Sección de configuración
            key: Clave a actualizar
            value: Nuevo valor
        """
        if hasattr(self, section):
            config_obj = getattr(self, section)
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
                logger.info(f"Configuración actualizada: {section}.{key} = {value}")
            else:
                logger.warning(f"Clave no encontrada: {section}.{key}")
        else:
            logger.warning(f"Sección no encontrada: {section}")

    def save_config(self, file_path: Optional[str] = None) -> None:
        """
        Guarda la configuración actual a archivo.
        
        Args:
            file_path: Ruta donde guardar (opcional)
        """
        save_path = file_path or self.config_file
        
        # Construir diccionario de configuración
        config_dict = {
            'database': {
                'url': self.database.url,
                'async_url': self.database.async_url,
                'pool_size': self.database.pool_size,
                'max_overflow': self.database.max_overflow,
                'pool_timeout': self.database.pool_timeout,
                'pool_recycle': self.database.pool_recycle,
            },
            'agent': {
                'max_retries': self.agent.max_retries,
                'timeout': self.agent.timeout,
                'debug_mode': self.agent.debug_mode,
                'log_level': self.agent.log_level,
                'custom_settings': self.agent.custom_settings,
            },
            'security': {
                'enable_authentication': self.security.enable_authentication,
                'enable_authorization': self.security.enable_authorization,
                'jwt_algorithm': self.security.jwt_algorithm,
                'jwt_expiration_hours': self.security.jwt_expiration_hours,
                'rate_limiting_enabled': self.security.rate_limiting_enabled,
                'max_requests_per_minute': self.security.max_requests_per_minute,
                'allowed_origins': self.security.allowed_origins,
                'enable_https_only': self.security.enable_https_only,
            },
            'api': {
                'timeout': self.api.timeout,
                'max_retries': self.api.max_retries,
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_enabled': self.logging.file_enabled,
                'file_path': self.logging.file_path,
                'max_file_size': self.logging.max_file_size,
                'backup_count': self.logging.backup_count,
                'console_enabled': self.logging.console_enabled,
            },
            'orchestrator': {
                'max_concurrent_tasks': self.orchestrator.max_concurrent_tasks,
                'task_timeout': self.orchestrator.task_timeout,
                'retry_delay': self.orchestrator.retry_delay,
                'health_check_interval': self.orchestrator.health_check_interval,
                'enable_task_queue': self.orchestrator.enable_task_queue,
                'queue_backend': self.orchestrator.queue_backend,
            },
            'system': {
                'environment': self.system.environment,
                'debug': self.system.debug,
                'host': self.system.host,
                'port': self.system.port,
                'workers': self.system.workers,
                'reload': self.system.reload,
                'data_directory': self.system.data_directory,
                'temp_directory': self.system.temp_directory,
                'max_upload_size': self.system.max_upload_size,
            }
        }
        
        try:
            # Crear directorio si no existe
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar como YAML
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Configuración guardada en: {save_path}")
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {str(e)}")
            raise

    def get_all_config(self) -> Dict[str, Any]:
        """Obtiene toda la configuración como diccionario"""
        return {
            'database': self.database.__dict__,
            'agent': self.agent.__dict__,
            'security': {k: v for k, v in self.security.__dict__.items() if k != 'jwt_secret_key'},
            'api': {k: v for k, v in self.api.__dict__.items() if 'key' not in k.lower()},
            'logging': self.logging.__dict__,
            'orchestrator': self.orchestrator.__dict__,
            'system': self.system.__dict__,
        }

    def setup_logging(self) -> None:
        """Configura el sistema de logging según la configuración"""
        import logging.handlers
        
        # Configurar nivel de logging
        numeric_level = getattr(logging, self.logging.level.upper(), logging.INFO)
        
        # Configurar formato
        formatter = logging.Formatter(self.logging.format)
        
        # Logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # Limpiar handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Handler de consola
        if self.logging.console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Handler de archivo
        if self.logging.file_enabled:
            # Crear directorio de logs si no existe
            log_path = Path(self.logging.file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                self.logging.file_path,
                maxBytes=self.logging.max_file_size,
                backupCount=self.logging.backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

# Instancia global del gestor de configuración
config_manager = ConfigManager()

# Funciones de conveniencia
def get_config() -> ConfigManager:
    """Obtiene la instancia global del gestor de configuración"""
    return config_manager

def get_agent_config(agent_id: str) -> Dict[str, Any]:
    """Obtiene la configuración de un agente específico"""
    return config_manager.get_agent_config(agent_id)

def get_database_url(async_mode: bool = False) -> str:
    """Obtiene la URL de la base de datos"""
    return config_manager.get_database_url(async_mode)

def get_api_config(service: str) -> Dict[str, Any]:
    """Obtiene la configuración de una API externa"""
    return config_manager.get_api_config(service)

