"""
CLI - Vision Wagon Command Line Interface
Interfaz de línea de comandos para administrar y operar Vision Wagon.
"""

import asyncio
import click
import json
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path
import yaml

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision_wagon.config.config_manager import get_config
from vision_wagon.database.database import db_manager, init_database
from vision_wagon.orchestrator.orchestrator import get_orchestrator
from vision_wagon.constructor.constructor import get_constructor
from vision_wagon.core.shared_enums import ContentType
from vision_wagon.security.security_validator import get_security_validator

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
@click.option('--config', '-c', help='Archivo de configuración')
@click.option('--verbose', '-v', is_flag=True, help='Modo verbose')
@click.pass_context
def cli(ctx, config, verbose):
    """Vision Wagon - Sistema de IA Generativa y Automatización"""
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config
    ctx.obj['verbose'] = verbose
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    click.echo("🚀 Vision Wagon CLI")
    click.echo("=" * 50)

# Comandos de Sistema
@cli.group()
def system():
    """Comandos de administración del sistema"""
    pass

@system.command()
@click.option('--force', is_flag=True, help='Forzar inicialización')
def init(force):
    """Inicializa el sistema Vision Wagon"""
    async def _init():
        try:
            click.echo("Inicializando Vision Wagon...")
            
            # Inicializar base de datos
            click.echo("📊 Inicializando base de datos...")
            await init_database()
            click.echo("✅ Base de datos inicializada")
            
            # Verificar configuración
            config_manager = get_config()
            click.echo("⚙️ Verificando configuración...")
            
            # Mostrar configuración básica
            click.echo(f"   - Entorno: {config_manager.system.environment}")
            click.echo(f"   - Debug: {config_manager.system.debug}")
            click.echo(f"   - Host: {config_manager.system.host}:{config_manager.system.port}")
            
            # Verificar APIs
            constructor = get_constructor()
            await constructor.initialize()
            click.echo(f"   - APIs disponibles: {constructor.available_apis}")
            
            click.echo("✅ Sistema inicializado correctamente")
            
        except Exception as e:
            click.echo(f"❌ Error inicializando sistema: {str(e)}", err=True)
            sys.exit(1)
    
    asyncio.run(_init())

@system.command()
def status():
    """Muestra el estado del sistema"""
    async def _status():
        try:
            click.echo("📊 Estado del Sistema Vision Wagon")
            click.echo("-" * 40)
            
            # Estado de la base de datos
            db_status = await db_manager.test_connection_async()
            click.echo(f"Base de datos: {'🟢 Conectada' if db_status else '🔴 Desconectada'}")
            
            # Estado del orquestador
            orchestrator = get_orchestrator()
            system_status = orchestrator.get_system_status()
            
            click.echo(f"Orquestador: {'🟢 Activo' if system_status['is_running'] else '🔴 Inactivo'}")
            click.echo(f"Agentes registrados: {len(system_status['registered_agents'])}")
            click.echo(f"Tareas en cola: {system_status['queue_size']}")
            click.echo(f"Tareas ejecutándose: {system_status['running_tasks']}")
            click.echo(f"Tareas completadas: {system_status['completed_tasks']}")
            click.echo(f"Tareas fallidas: {system_status['failed_tasks']}")
            
            # Estado del constructor
            constructor = get_constructor()
            constructor_metrics = constructor.get_metrics()
            
            click.echo(f"Constructor: 🟢 Activo")
            click.echo(f"Contenido generado: {constructor_metrics['content_generated']}")
            click.echo(f"APIs disponibles: {len(constructor_metrics['available_apis'])}")
            
            # Estado de seguridad
            security_validator = get_security_validator()
            security_summary = security_validator.get_security_summary()
            
            click.echo(f"Seguridad: 🟢 Activa")
            click.echo(f"Eventos de seguridad: {security_summary['total_events']}")
            
        except Exception as e:
            click.echo(f"❌ Error obteniendo estado: {str(e)}", err=True)
    
    asyncio.run(_status())

@system.command()
@click.option('--output', '-o', default='config_backup.yaml', help='Archivo de salida')
def backup_config(output):
    """Respalda la configuración actual"""
    try:
        config_manager = get_config()
        config_manager.save_config(output)
        click.echo(f"✅ Configuración respaldada en: {output}")
    except Exception as e:
        click.echo(f"❌ Error respaldando configuración: {str(e)}", err=True)

# Comandos de Agentes
@cli.group()
def agents():
    """Comandos para gestión de agentes"""
    pass

@agents.command()
def list():
    """Lista todos los agentes registrados"""
    async def _list():
        try:
            orchestrator = get_orchestrator()
            system_status = orchestrator.get_system_status()
            
            if not system_status['registered_agents']:
                click.echo("No hay agentes registrados")
                return
            
            click.echo("🤖 Agentes Registrados")
            click.echo("-" * 30)
            
            for agent_id in system_status['registered_agents']:
                agent_status = orchestrator.get_agent_status(agent_id)
                if agent_status:
                    status_icon = "🟢" if agent_status['is_initialized'] else "🔴"
                    click.echo(f"{status_icon} {agent_id} ({agent_status['agent_type']})")
                    click.echo(f"   Tareas completadas: {agent_status['tasks_completed']}")
                    click.echo(f"   Tareas fallidas: {agent_status['tasks_failed']}")
                    click.echo(f"   Tasa de error: {agent_status['error_rate']:.2%}")
                    click.echo()
        
        except Exception as e:
            click.echo(f"❌ Error listando agentes: {str(e)}", err=True)
    
    asyncio.run(_list())

@agents.command()
@click.argument('agent_id')
def info(agent_id):
    """Muestra información detallada de un agente"""
    async def _info():
        try:
            orchestrator = get_orchestrator()
            agent_status = orchestrator.get_agent_status(agent_id)
            
            if not agent_status:
                click.echo(f"❌ Agente no encontrado: {agent_id}")
                return
            
            click.echo(f"🤖 Información del Agente: {agent_id}")
            click.echo("-" * 40)
            click.echo(f"Tipo: {agent_status['agent_type']}")
            click.echo(f"Estado: {'🟢 Inicializado' if agent_status['is_initialized'] else '🔴 No inicializado'}")
            click.echo(f"Capacidades: {', '.join(agent_status['capabilities'])}")
            click.echo(f"Tareas ejecutándose: {agent_status['tasks_running']}")
            click.echo(f"Tareas completadas: {agent_status['tasks_completed']}")
            click.echo(f"Tareas fallidas: {agent_status['tasks_failed']}")
            click.echo(f"Tasa de error: {agent_status['error_rate']:.2%}")
            
            if agent_status['last_activity']:
                click.echo(f"Última actividad: {agent_status['last_activity']}")
        
        except Exception as e:
            click.echo(f"❌ Error obteniendo información del agente: {str(e)}", err=True)
    
    asyncio.run(_info())

# Comandos de Tareas
@cli.group()
def tasks():
    """Comandos para gestión de tareas"""
    pass

@tasks.command()
@click.argument('task_type')
@click.argument('agent_id')
@click.option('--context', '-c', help='Contexto JSON para la tarea')
@click.option('--priority', '-p', default='normal', type=click.Choice(['low', 'normal', 'high', 'critical']))
@click.option('--timeout', '-t', type=float, help='Timeout en segundos')
def submit(task_type, agent_id, context, priority, timeout):
    """Envía una tarea para ejecución"""
    async def _submit():
        try:
            orchestrator = get_orchestrator()
            
            # Parsear contexto
            task_context = {}
            if context:
                try:
                    task_context = json.loads(context)
                except json.JSONDecodeError:
                    click.echo("❌ Contexto JSON inválido", err=True)
                    return
            
            # Convertir prioridad
            from orchestrator.orchestrator import TaskPriority
            priority_map = {
                'low': TaskPriority.LOW,
                'normal': TaskPriority.NORMAL,
                'high': TaskPriority.HIGH,
                'critical': TaskPriority.CRITICAL
            }
            
            task_priority = priority_map[priority]
            
            # Enviar tarea
            task_id = await orchestrator.submit_task(
                task_type=task_type,
                agent_id=agent_id,
                context=task_context,
                priority=task_priority,
                timeout=timeout
            )
            
            click.echo(f"✅ Tarea enviada: {task_id}")
            click.echo(f"   Tipo: {task_type}")
            click.echo(f"   Agente: {agent_id}")
            click.echo(f"   Prioridad: {priority}")
        
        except Exception as e:
            click.echo(f"❌ Error enviando tarea: {str(e)}", err=True)
    
    asyncio.run(_submit())

@tasks.command()
@click.argument('task_id')
def status(task_id):
    """Muestra el estado de una tarea"""
    orchestrator = get_orchestrator()
    task_status = orchestrator.get_task_status(task_id)
    
    if not task_status:
        click.echo(f"❌ Tarea no encontrada: {task_id}")
        return
    
    click.echo(f"📋 Estado de la Tarea: {task_id}")
    click.echo("-" * 40)
    click.echo(f"Tipo: {task_status['task_type']}")
    click.echo(f"Agente: {task_status['agent_id']}")
    click.echo(f"Estado: {task_status['status']}")
    click.echo(f"Prioridad: {task_status['priority']}")
    click.echo(f"Creada: {task_status['created_at']}")
    
    if task_status['started_at']:
        click.echo(f"Iniciada: {task_status['started_at']}")
    
    if task_status['completed_at']:
        click.echo(f"Completada: {task_status['completed_at']}")
    
    if task_status['error']:
        click.echo(f"Error: {task_status['error']}")
    
    click.echo(f"Reintentos: {task_status['retry_count']}")

@tasks.command()
@click.option('--status', '-s', help='Filtrar por estado')
@click.option('--agent', '-a', help='Filtrar por agente')
@click.option('--limit', '-l', default=20, help='Límite de resultados')
def list(status, agent, limit):
    """Lista tareas con filtros opcionales"""
    orchestrator = get_orchestrator()
    system_status = orchestrator.get_system_status()
    
    click.echo("📋 Lista de Tareas")
    click.echo("-" * 30)
    
    # Mostrar tareas en ejecución
    if system_status['running_tasks'] > 0:
        click.echo(f"🔄 Tareas ejecutándose: {system_status['running_tasks']}")
    
    # Mostrar tareas completadas
    if system_status['completed_tasks'] > 0:
        click.echo(f"✅ Tareas completadas: {system_status['completed_tasks']}")
    
    # Mostrar tareas fallidas
    if system_status['failed_tasks'] > 0:
        click.echo(f"❌ Tareas fallidas: {system_status['failed_tasks']}")
    
    click.echo(f"⏳ Tareas en cola: {system_status['queue_size']}")

# Comandos de Contenido
@cli.group()
def content():
    """Comandos para generación de contenido"""
    pass

@content.command()
@click.argument('content_type', type=click.Choice(['text', 'image', 'audio', 'document', 'social_post']))
@click.argument('prompt')
@click.option('--output', '-o', help='Archivo de salida')
@click.option('--params', '-p', help='Parámetros JSON adicionales')
def generate(content_type, prompt, output, params):
    """Genera contenido usando IA"""
    async def _generate():
        try:
            constructor = get_constructor()
            
            # Parsear parámetros
            parameters = {}
            if params:
                try:
                    parameters = json.loads(params)
                except json.JSONDecodeError:
                    click.echo("❌ Parámetros JSON inválidos", err=True)
                    return
            
            # Generar contenido
            click.echo(f"🎨 Generando {content_type}...")
            click.echo(f"Prompt: {prompt}")
            
            content_type_enum = ContentType(content_type)
            request_id = await constructor.generate_content(
                content_type=content_type_enum,
                prompt=prompt,
                parameters=parameters
            )
            
            click.echo(f"✅ Solicitud enviada: {request_id}")
            
            # Esperar resultado
            import time
            max_wait = 60  # 60 segundos máximo
            waited = 0
            
            while waited < max_wait:
                status = constructor.get_generation_status(request_id)
                if status and status['status'] == 'completed':
                    click.echo("✅ Contenido generado exitosamente")
                    
                    if status['result']:
                        result = status['result']
                        click.echo(f"ID del contenido: {result.get('content_id')}")
                        
                        if result.get('file_path'):
                            click.echo(f"Archivo guardado: {result['file_path']}")
                            
                            # Copiar a archivo de salida si se especificó
                            if output:
                                import shutil
                                shutil.copy2(result['file_path'], output)
                                click.echo(f"Copiado a: {output}")
                    
                    break
                elif status and status['status'] == 'failed':
                    click.echo(f"❌ Error generando contenido: {status.get('error')}")
                    break
                
                time.sleep(2)
                waited += 2
                click.echo(".", nl=False)
            
            if waited >= max_wait:
                click.echo(f"\n⏰ Timeout esperando resultado. ID de solicitud: {request_id}")
        
        except Exception as e:
            click.echo(f"❌ Error generando contenido: {str(e)}", err=True)
    
    asyncio.run(_generate())

@content.command()
@click.option('--type', '-t', help='Filtrar por tipo de contenido')
@click.option('--limit', '-l', default=10, help='Límite de resultados')
def list(type, limit):
    """Lista contenido generado"""
    constructor = get_constructor()
    
    content_type_filter = None
    if type:
        try:
            content_type_filter = ContentType(type)
        except ValueError:
            click.echo(f"❌ Tipo de contenido inválido: {type}")
            return
    
    contents = constructor.list_generated_content(
        content_type=content_type_filter,
        limit=limit
    )
    
    if not contents:
        click.echo("No se encontró contenido generado")
        return
    
    click.echo("🎨 Contenido Generado")
    click.echo("-" * 30)
    
    for content in contents:
        click.echo(f"📄 {content['content_id']}")
        click.echo(f"   Tipo: {content['content_type']}")
        click.echo(f"   Título: {content['title']}")
        click.echo(f"   Creado: {content['created_at']}")
        if content['file_path']:
            click.echo(f"   Archivo: {content['file_path']}")
        click.echo()

# Comandos de Seguridad
@cli.group()
def security():
    """Comandos de seguridad y auditoría"""
    pass

@security.command()
def scan():
    """Ejecuta escaneo de vulnerabilidades"""
    async def _scan():
        try:
            click.echo("🔒 Ejecutando escaneo de seguridad...")
            
            # Aquí se integraría con el SecurityAgent
            # Por ahora, mostrar información básica
            security_validator = get_security_validator()
            summary = security_validator.get_security_summary()
            
            click.echo("📊 Resumen de Seguridad")
            click.echo("-" * 30)
            click.echo(f"Total de eventos: {summary['total_events']}")
            click.echo(f"Rate limiting: {'🟢 Activo' if summary['rate_limiting_enabled'] else '🔴 Inactivo'}")
            click.echo(f"IPs bloqueadas: {summary['blocked_ips_count']}")
            
            if summary['events_by_severity']:
                click.echo("\nEventos por severidad:")
                for severity, count in summary['events_by_severity'].items():
                    icon = {"low": "🟡", "medium": "🟠", "high": "🔴", "critical": "🚨"}.get(severity, "⚪")
                    click.echo(f"  {icon} {severity}: {count}")
        
        except Exception as e:
            click.echo(f"❌ Error en escaneo de seguridad: {str(e)}", err=True)
    
    asyncio.run(_scan())

@security.command()
@click.option('--severity', '-s', help='Filtrar por severidad')
@click.option('--limit', '-l', default=20, help='Límite de resultados')
def events(severity, limit):
    """Muestra eventos de seguridad"""
    security_validator = get_security_validator()
    events = security_validator.get_security_events(
        severity=severity,
        limit=limit
    )
    
    if not events:
        click.echo("No se encontraron eventos de seguridad")
        return
    
    click.echo("🔒 Eventos de Seguridad")
    click.echo("-" * 30)
    
    for event in events:
        severity_icon = {
            "low": "🟡",
            "medium": "🟠", 
            "high": "🔴",
            "critical": "🚨"
        }.get(event.severity, "⚪")
        
        click.echo(f"{severity_icon} {event.event_type} ({event.severity})")
        click.echo(f"   Fuente: {event.source}")
        click.echo(f"   Acción: {event.action}")
        click.echo(f"   Descripción: {event.description}")
        click.echo(f"   Timestamp: {event.timestamp}")
        click.echo()

# Comandos de Configuración
@cli.group()
def config():
    """Comandos de configuración"""
    pass

@config.command()
def show():
    """Muestra la configuración actual"""
    config_manager = get_config()
    config_dict = config_manager.get_all_config()
    
    click.echo("⚙️ Configuración Actual")
    click.echo("-" * 30)
    
    for section, values in config_dict.items():
        click.echo(f"\n[{section.upper()}]")
        for key, value in values.items():
            # Ocultar claves sensibles
            if 'key' in key.lower() or 'secret' in key.lower():
                value = "***" if value else "No configurado"
            click.echo(f"  {key}: {value}")

@config.command()
@click.argument('section')
@click.argument('key')
@click.argument('value')
def set(section, key, value):
    """Establece un valor de configuración"""
    try:
        config_manager = get_config()
        
        # Convertir tipos básicos
        if value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '').isdigit():
            value = float(value)
        
        config_manager.update_config(section, key, value)
        click.echo(f"✅ Configuración actualizada: {section}.{key} = {value}")
    
    except Exception as e:
        click.echo(f"❌ Error actualizando configuración: {str(e)}", err=True)

# Comandos de Desarrollo y Testing
@cli.group()
def dev():
    """Comandos de desarrollo y testing"""
    pass

@dev.command()
def test():
    """Ejecuta tests básicos del sistema"""
    async def _test():
        click.echo("🧪 Ejecutando tests del sistema...")
        
        tests_passed = 0
        tests_total = 0
        
        # Test 1: Conexión a base de datos
        tests_total += 1
        try:
            db_status = await db_manager.test_connection_async()
            if db_status:
                click.echo("✅ Test DB: Conexión exitosa")
                tests_passed += 1
            else:
                click.echo("❌ Test DB: Conexión fallida")
        except Exception as e:
            click.echo(f"❌ Test DB: Error - {str(e)}")
        
        # Test 2: Configuración
        tests_total += 1
        try:
            config_manager = get_config()
            if config_manager.system.environment:
                click.echo("✅ Test Config: Configuración cargada")
                tests_passed += 1
            else:
                click.echo("❌ Test Config: Configuración incompleta")
        except Exception as e:
            click.echo(f"❌ Test Config: Error - {str(e)}")
        
        # Test 3: Constructor
        tests_total += 1
        try:
            constructor = get_constructor()
            await constructor.initialize()
            click.echo("✅ Test Constructor: Inicialización exitosa")
            tests_passed += 1
        except Exception as e:
            click.echo(f"❌ Test Constructor: Error - {str(e)}")
        
        # Resumen
        click.echo(f"\n📊 Resumen: {tests_passed}/{tests_total} tests pasaron")
        
        if tests_passed == tests_total:
            click.echo("🎉 Todos los tests pasaron!")
        else:
            click.echo("⚠️ Algunos tests fallaron")
            sys.exit(1)
    
    asyncio.run(_test())

@dev.command()
@click.option('--port', '-p', default=8000, help='Puerto del servidor')
@click.option('--host', '-h', default='0.0.0.0', help='Host del servidor')
def serve(port, host):
    """Inicia servidor de desarrollo"""
    click.echo(f"🚀 Iniciando servidor de desarrollo en {host}:{port}")
    click.echo("Presiona Ctrl+C para detener")
    
    # Aquí se iniciaría el servidor web/API
    # Por ahora, solo simular
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\n👋 Servidor detenido")

# Comando principal de ayuda
@cli.command()
def version():
    """Muestra información de versión"""
    click.echo("Vision Wagon v1.0.0")
    click.echo("Sistema de IA Generativa y Automatización")
    click.echo("Desarrollado para el ecosistema Nómada Alpha")

@cli.group()
def constructor():
    """Comandos para construcción de agentes y componentes"""
    pass

@constructor.command()
@click.option("--blueprint", "-b", required=True, help="Ruta al archivo blueprint (YAML)")
def build(blueprint):
    """Construye agentes y componentes a partir de un blueprint"""
    async def _build():
        try:
            constructor_agent = get_constructor()
            click.echo(f"🛠️ Construyendo desde blueprint: {blueprint}")
            
            # Cargar blueprint
            with open(blueprint, 'r', encoding='utf-8') as f:
                blueprint_data = yaml.safe_load(f)
            
            if not blueprint_data or "agents" not in blueprint_data:
                click.echo("❌ Blueprint inválido: no se encontró la sección 'agents'", err=True)
                return
            
            for agent_data in blueprint_data["agents"]:
                agent_id = agent_data.get("name")
                agent_type = agent_data.get("type", "BaseAgent")
                agent_description = agent_data.get("description", "")
                
                click.echo(f"   - Generando esqueleto para agente: {agent_id} ({agent_type})")
                
                await constructor_agent.generate_agent_skeleton(agent_id, agent_type, agent_description)

            click.echo("✅ Construcción completada")
            
        except FileNotFoundError:
            click.echo(f"❌ Error: Archivo blueprint no encontrado en {blueprint}", err=True)
        except yaml.YAMLError as e:
            click.echo(f"❌ Error parseando blueprint YAML: {str(e)}", err=True)
        except Exception as e:
            click.echo(f"❌ Error construyendo agentes: {str(e)}", err=True)
    
    asyncio.run(_build())

if __name__ == '__main__':
    cli()
