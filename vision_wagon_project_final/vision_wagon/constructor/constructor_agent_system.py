# ConstructorAgent v1.1 - Sistema Completo
# Vision Wagon - Automatización SDLC

import os
import json
import yaml
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import subprocess
import tempfile
import shutil

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== MODELOS DE DATOS ==========

@dataclass
class TaskResult:
    """Resultado de una tarea ejecutada"""
    task_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    artifacts_created: List[str] = field(default_factory=list)

@dataclass
class BuildContext:
    """Contexto de construcción con toda la información necesaria"""
    project_root: Path
    blueprint_path: Path
    target_module: Optional[str] = None
    target_agent: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentSpec:
    """Especificación de un agente"""
    name: str
    type: str  # 'executive' | 'operational'
    description: str
    dependencies: List[str] = field(default_factory=list)
    methods: List[Dict[str, Any]] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)

# ========== PLANTILLAS DE CÓDIGO ==========

class CodeTemplates:
    """Plantillas de código reutilizables"""
    
    @staticmethod
    def agent_base_template(agent_spec: AgentSpec) -> str:
        """Plantilla base para agentes"""
        return f'''"""
{agent_spec.name} - Vision Wagon Agent
Tipo: {agent_spec.type.title()}
Descripción: {agent_spec.description}
Generado automáticamente por ConstructorAgent
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..core.base_agent import BaseAgent
from ..database.database_models import AgentLog, Campaign

logger = logging.getLogger(__name__)

class {agent_spec.name}(BaseAgent):
    """
    {agent_spec.description}
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_id="{agent_spec.name.lower()}",
            agent_type="{agent_spec.type}",
            config=config or {{}}
        )
        self.dependencies = {json.dumps(agent_spec.dependencies)}
        
    async def initialize(self) -> bool:
        """Inicializa el agente y sus dependencias"""
        try:
            logger.info(f"Inicializando {{self.agent_id}}")
            # TODO: Implementar inicialización específica
            return True
        except Exception as e:
            logger.error(f"Error inicializando {{self.agent_id}}: {{e}}")
            return False
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa la tarea principal del agente"""
        try:
            # Log de inicio
            await self.log_action("process_start", context)
            
            # TODO: Implementar lógica de procesamiento
            result = {{
                "status": "completed",
                "agent": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {{}}
            }}
            
            # Log de finalización
            await self.log_action("process_complete", result)
            return result
            
        except Exception as e:
            error_result = {{
                "status": "error",
                "agent": self.agent_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }}
            await self.log_action("process_error", error_result)
            return error_result
    
    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Valida los datos de entrada"""
        # TODO: Implementar validación específica
        return True
        
    async def cleanup(self) -> None:
        """Limpieza de recursos"""
        logger.info(f"Limpiando recursos de {{self.agent_id}}")
        # TODO: Implementar limpieza específica
'''

    @staticmethod
    def database_model_template(model_name: str, fields: List[Dict[str, Any]]) -> str:
        """Plantilla para modelos de base de datos"""
        field_definitions = []
        relationships = []
        
        for field_info in fields:
            field_name = field_info['name']
            field_type = field_info['type']
            field_options = field_info.get('options', {})
            
            if field_info.get('is_relationship', False):
                relationships.append(f"    {field_name} = relationship(\"{field_info['related_model']}\")")
            else:
                options_str = ", ".join([f"{k}={v}" for k, v in field_options.items()])
                if options_str:
                    field_definitions.append(f"    {field_name} = Column({field_type}, {options_str})")
                else:
                    field_definitions.append(f"    {field_name} = Column({field_type})")
        
        fields_code = "\n".join(field_definitions)
        relationships_code = "\n".join(relationships) if relationships else ""
        
        return f'''from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class {model_name}(Base):
    """
    Modelo {model_name} - Generado por ConstructorAgent
    """
    __tablename__ = '{model_name.lower()}s'
    
{fields_code}
{relationships_code}
    
    def __repr__(self):
        return f"<{model_name}(id={{self.id}})>"
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {{c.name: getattr(self, c.name) for c in self.__table__.columns}}
'''

    @staticmethod
    def api_endpoint_template(endpoint_spec: Dict[str, Any]) -> str:
        """Plantilla para endpoints de API"""
        method = endpoint_spec['method'].upper()
        path = endpoint_spec['path']
        function_name = endpoint_spec['function_name']
        description = endpoint_spec.get('description', '')
        
        return f'''@app.{method.lower()}("{path}")
async def {function_name}(
    # TODO: Añadir parámetros según especificación
):
    """
    {description}
    """
    try:
        # TODO: Implementar lógica del endpoint
        return {{"status": "success", "message": "Endpoint implementado"}}
    except Exception as e:
        logger.error(f"Error en {function_name}: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))
'''

# ========== TAREAS DE CONSTRUCCIÓN ==========

class BuildTask(ABC):
    """Clase base para tareas de construcción"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, context: BuildContext) -> TaskResult:
        """Ejecuta la tarea"""
        pass

class InitProjectStructureTask(BuildTask):
    """Tarea para inicializar la estructura del proyecto"""
    
    def __init__(self):
        super().__init__(
            "init_project_structure",
            "Crea la estructura de directorios base del proyecto"
        )
    
    async def execute(self, context: BuildContext) -> TaskResult:
        """Crea la estructura de directorios"""
        start_time = datetime.now()
        artifacts = []
        
        try:
            directories = [
                "agents/executive",
                "agents/operational", 
                "agents/core",
                "database",
                "api",
                "orchestrator",
                "tests/agents",
                "tests/api",
                "tests/database",
                "config",
                "blueprints",
                "logs",
                "docs"
            ]
            
            for dir_path in directories:
                full_path = context.project_root / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                
                # Crear __init__.py en directorios Python
                if any(dir_path.startswith(prefix) for prefix in ["agents", "database", "api", "orchestrator"]):
                    init_file = full_path / "__init__.py"
                    init_file.write_text('"""Vision Wagon - Generado por ConstructorAgent"""')
                    artifacts.append(str(init_file))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TaskResult(
                task_name=self.name,
                success=True,
                output=f"Creados {len(directories)} directorios",
                execution_time=execution_time,
                artifacts_created=artifacts
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                task_name=self.name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )

class GenerateConfigFilesTask(BuildTask):
    """Tarea para generar archivos de configuración"""
    
    def __init__(self):
        super().__init__(
            "generate_config_files",
            "Genera archivos de configuración del proyecto"
        )
    
    async def execute(self, context: BuildContext) -> TaskResult:
        start_time = datetime.now()
        artifacts = []
        
        try:
            # requirements.txt
            requirements = [
                "fastapi==0.104.1",
                "uvicorn==0.24.0",
                "sqlalchemy==2.0.23",
                "pydantic==2.5.0",
                "python-dotenv==1.0.0",
                "asyncio==3.4.3",
                "pytest==7.4.3",
                "pytest-asyncio==0.21.1",
                "httpx==0.25.2",
                "pyyaml==6.0.1",
                "aiofiles==23.2.1"
            ]
            
            req_file = context.project_root / "requirements.txt"
            req_file.write_text("\n".join(requirements))
            artifacts.append(str(req_file))
            
            # .env.example
            env_example = """# Vision Wagon - Configuración de Entorno
DATABASE_URL=sqlite:///./vision_wagon.db
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
LLM_API_KEY=your_llm_api_key_here
LLM_API_URL=https://api.your-llm-provider.com
ENVIRONMENT=development
"""
            
            env_file = context.project_root / ".env.example"
            env_file.write_text(env_example)
            artifacts.append(str(env_file))
            
            # .gitignore
            gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env
.env.local

# Database
*.db
*.sqlite3

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Vision Wagon específico
blueprints/*.local.yml
config/*.local.*
"""
            
            git_file = context.project_root / ".gitignore"
            git_file.write_text(gitignore)
            artifacts.append(str(git_file))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TaskResult(
                task_name=self.name,
                success=True,
                output=f"Generados {len(artifacts)} archivos de configuración",
                execution_time=execution_time,
                artifacts_created=artifacts
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                task_name=self.name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )

class ScaffoldAgentTask(BuildTask):
    """Tarea para crear el esqueleto de un agente"""
    
    def __init__(self, agent_spec: AgentSpec):
        super().__init__(
            "scaffold_agent",
            f"Crea el esqueleto del agente {agent_spec.name}"
        )
        self.agent_spec = agent_spec
    
    async def execute(self, context: BuildContext) -> TaskResult:
        start_time = datetime.now()
        
        try:
            # Determinar la ruta del archivo
            agent_type_dir = "executive" if self.agent_spec.type == "executive" else "operational"
            agent_file = context.project_root / "agents" / agent_type_dir / f"{self.agent_spec.name.lower()}.py"
            
            # Generar código del agente
            agent_code = CodeTemplates.agent_base_template(self.agent_spec)
            
            # Escribir archivo
            agent_file.write_text(agent_code)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TaskResult(
                task_name=self.name,
                success=True,
                output=f"Agente {self.agent_spec.name} creado en {agent_file}",
                execution_time=execution_time,
                artifacts_created=[str(agent_file)]
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                task_name=self.name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )

# ========== ANALIZADOR DE BLUEPRINTS ==========

class BlueprintParser:
    """Analizador de archivos blueprint YAML"""
    
    @staticmethod
    def parse_blueprint(blueprint_path: Path) -> Dict[str, Any]:
        """Parsea un archivo blueprint"""
        try:
            with open(blueprint_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error parseando blueprint {blueprint_path}: {e}")
            return {}
    
    @staticmethod
    def extract_agent_specs(blueprint_data: Dict[str, Any]) -> List[AgentSpec]:
        """Extrae especificaciones de agentes del blueprint"""
        agents = []
        
        if 'agents' in blueprint_data:
            for agent_data in blueprint_data['agents']:
                agent_spec = AgentSpec(
                    name=agent_data.get('name', ''),
                    type=agent_data.get('type', 'operational'),
                    description=agent_data.get('description', ''),
                    dependencies=agent_data.get('dependencies', []),
                    methods=agent_data.get('methods', []),
                    config=agent_data.get('config', {})
                )
                agents.append(agent_spec)
        
        return agents

# ========== CONSTRUCTOR AGENT PRINCIPAL ==========

class ConstructorAgent:
    """
    Agente Constructor Principal - Vision Wagon
    Automatiza el ciclo completo de desarrollo de software
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.tasks_registry: Dict[str, BuildTask] = {}
        self.execution_history: List[TaskResult] = []
        
        # Registrar tareas disponibles
        self._register_core_tasks()
        
        logger.info(f"ConstructorAgent inicializado en {self.project_root}")
    
    def _register_core_tasks(self):
        """Registra las tareas principales"""
        self.tasks_registry.update({
            "init_project_structure": InitProjectStructureTask(),
            "generate_config_files": GenerateConfigFilesTask(),
        })
    
    async def build_from_blueprint(self, blueprint_path: Path, target: Optional[str] = None) -> List[TaskResult]:
        """Construye el proyecto basándose en un blueprint"""
        logger.info(f"Iniciando construcción desde blueprint: {blueprint_path}")
        
        # Parsear blueprint
        blueprint_data = BlueprintParser.parse_blueprint(blueprint_path)
        if not blueprint_data:
            return [TaskResult("parse_blueprint", False, error="No se pudo parsear el blueprint")]
        
        # Crear contexto de construcción
        context = BuildContext(
            project_root=self.project_root,
            blueprint_path=blueprint_path,
            target_module=target,
            config=blueprint_data.get('config', {}),
            metadata=blueprint_data.get('metadata', {})
        )
        
        # Determinar tareas a ejecutar
        tasks_to_execute = self._plan_execution(blueprint_data, target)
        
        # Ejecutar tareas
        results = []
        for task_name in tasks_to_execute:
            if task_name in self.tasks_registry:
                logger.info(f"Ejecutando tarea: {task_name}")
                result = await self.tasks_registry[task_name].execute(context)
                results.append(result)
                self.execution_history.append(result)
                
                if not result.success:
                    logger.error(f"Tarea {task_name} falló: {result.error}")
                    break
            else:
                logger.warning(f"Tarea no encontrada: {task_name}")
        
        return results
    
    def _plan_execution(self, blueprint_data: Dict[str, Any], target: Optional[str] = None) -> List[str]:
        """Planifica qué tareas ejecutar basándose en el blueprint"""
        planned_tasks = []
        
        # Siempre inicializar estructura si no existe
        if not (self.project_root / "agents").exists():
            planned_tasks.append("init_project_structure")
            planned_tasks.append("generate_config_files")
        
        # Añadir tareas específicas según el blueprint
        if 'agents' in blueprint_data:
            agent_specs = BlueprintParser.extract_agent_specs(blueprint_data)
            for agent_spec in agent_specs:
                if not target or target == agent_spec.name:
                    # Registrar tarea específica para este agente
                    task_name = f"scaffold_agent_{agent_spec.name.lower()}"
                    self.tasks_registry[task_name] = ScaffoldAgentTask(agent_spec)
                    planned_tasks.append(task_name)
        
        return planned_tasks
    
    async def execute_task(self, task_name: str, context: Optional[BuildContext] = None) -> TaskResult:
        """Ejecuta una tarea específica"""
        if task_name not in self.tasks_registry:
            return TaskResult(task_name, False, error=f"Tarea {task_name} no encontrada")
        
        if not context:
            context = BuildContext(
                project_root=self.project_root,
                blueprint_path=self.project_root / "blueprints" / "default.yml"
            )
        
        result = await self.tasks_registry[task_name].execute(context)
        self.execution_history.append(result)
        return result
    
    def generate_execution_report(self) -> Dict[str, Any]:
        """Genera un reporte de la ejecución"""
        total_tasks = len(self.execution_history)
        successful_tasks = sum(1 for result in self.execution_history if result.success)
        failed_tasks = total_tasks - successful_tasks
        total_time = sum(result.execution_time for result in self.execution_history)
        
        return {
            "summary": {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": f"{(successful_tasks/total_tasks)*100:.1f}%" if total_tasks > 0 else "0%",
                "total_execution_time": f"{total_time:.2f}s"
            },
            "tasks": [
                {
                    "name": result.task_name,
                    "success": result.success,
                    "execution_time": f"{result.execution_time:.2f}s",
                    "artifacts_created": len(result.artifacts_created),
                    "error": result.error if not result.success else None
                }
                for result in self.execution_history
            ]
        }

# ========== CLI INTERFACE ==========

class ConstructorCLI:
    """Interfaz de línea de comandos para ConstructorAgent"""
    
    def __init__(self):
        self.constructor = ConstructorAgent()
    
    async def run_command(self, command: str, **kwargs):
        """Ejecuta un comando específico"""
        if command == "build":
            return await self._handle_build_command(**kwargs)
        elif command == "init":
            return await self._handle_init_command(**kwargs)
        elif command == "status":
            return await self._handle_status_command(**kwargs)
        else:
            return {"error": f"Comando no reconocido: {command}"}
    
    async def _handle_build_command(self, blueprint: str = None, target: str = None, **kwargs):
        """Maneja el comando build"""
        blueprint_path = Path(blueprint) if blueprint else Path("blueprints/default.yml")
        
        if not blueprint_path.exists():
            return {"error": f"Blueprint no encontrado: {blueprint_path}"}
        
        results = await self.constructor.build_from_blueprint(blueprint_path, target)
        report = self.constructor.generate_execution_report()
        
        return {
            "command": "build",
            "blueprint": str(blueprint_path),
            "target": target,
            "results": report
        }
    
    async def _handle_init_command(self, **kwargs):
        """Maneja el comando init"""
        context = BuildContext(
            project_root=self.constructor.project_root,
            blueprint_path=Path("blueprints/default.yml")
        )
        
        init_result = await self.constructor.execute_task("init_project_structure", context)
        config_result = await self.constructor.execute_task("generate_config_files", context)
        
        return {
            "command": "init",
            "results": [init_result, config_result]
        }
    
    async def _handle_status_command(self, **kwargs):
        """Maneja el comando status"""
        return {
            "command": "status",
            "project_root": str(self.constructor.project_root),
            "execution_history": self.constructor.generate_execution_report()
        }

# ========== PUNTO DE ENTRADA ==========

async def main():
    """Función principal para pruebas"""
    # Ejemplo de uso
    constructor = ConstructorAgent(Path("./vision_wagon_project"))
    
    # Crear blueprint de ejemplo
    example_blueprint = {
        "metadata": {
            "name": "Vision Wagon Core",
            "version": "1.0.0",
            "description": "Sistema base de Vision Wagon"
        },
        "config": {
            "database_type": "sqlite",
            "api_port": 8000
        },
        "agents": [
            {
                "name": "SecurityAgent",
                "type": "executive",
                "description": "Agente de seguridad y validación",
                "dependencies": ["database"],
                "methods": [
                    {
                        "name": "validate_security",
                        "description": "Valida aspectos de seguridad"
                    }
                ]
            },
            {
                "name": "CopywriterAgent",
                "type": "operational",
                "description": "Agente de generación de contenido",
                "dependencies": ["psychology_agent"],
                "config": {
                    "llm_model": "gpt-4"
                }
            }
        ]
    }
    
    # Crear directorio de blueprints si no existe
    blueprints_dir = constructor.project_root / "blueprints"
    blueprints_dir.mkdir(exist_ok=True)
    
    # Guardar blueprint de ejemplo
    blueprint_path = blueprints_dir / "example.yml"
    with open(blueprint_path, 'w', encoding='utf-8') as f:
        yaml.dump(example_blueprint, f, default_flow_style=False, allow_unicode=True)
    
    # Ejecutar construcción
    results = await constructor.build_from_blueprint(blueprint_path)
    
    # Mostrar reporte
    report = constructor.generate_execution_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
