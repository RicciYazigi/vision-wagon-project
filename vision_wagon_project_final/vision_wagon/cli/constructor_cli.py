#!/usr/bin/env python3
"""
constructor.py - CLI Interface para ConstructorAgent
Vision Wagon - Automatización SDLC

Uso:
    python constructor.py init
    python constructor.py build --blueprint blueprints/agents.yml --target SecurityAgent
    python constructor.py status
    python constructor.py task --name scaffold_agent --agent-name TestAgent --agent-type operational
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any
import logging

# Importar ConstructorAgent (asumiendo que está en el mismo directorio o instalado)
from constructor_agent import ConstructorAgent, ConstructorCLI, BlueprintParser, AgentSpec

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VisionWagonCLI:
    """CLI Principal de Vision Wagon ConstructorAgent"""
    
    def __init__(self):
        self.constructor_cli = ConstructorCLI()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Crea el parser de argumentos"""
        parser = argparse.ArgumentParser(
            description="Vision Wagon ConstructorAgent - Automatización SDLC",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos:
  %(prog)s init                                    # Inicializar proyecto
  %(prog)s build --blueprint agents.yml           # Construir desde blueprint
  %(prog)s build --target SecurityAgent           # Construir agente específico
  %(prog)s task --name init_project_structure     # Ejecutar tarea específica
  %(prog)s status                                  # Ver estado del proyecto
  %(prog)s validate --blueprint agents.yml        # Validar blueprint
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
        
        # Comando init
        init_parser = subparsers.add_parser('init', help='Inicializar estructura del proyecto')
        init_parser.add_argument(
            '--project-root',
            type=str,
            default='.',
            help='Directorio raíz del proyecto (default: directorio actual)'
        )
        
        # Comando build
        build_parser = subparsers.add_parser('build', help='Construir desde blueprint')
        build_parser.add_argument(
            '--blueprint',
            type=str,
            help='Ruta al archivo blueprint YAML'
        )
        build_parser.add_argument(
            '--target',
            type=str,
            help='Objetivo específico a construir (agente, módulo, etc.)'
        )
        build_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular ejecución sin realizar cambios'
        )
        
        # Comando status
        status_parser = subparsers.add_parser('status', help='Ver estado del proyecto')
        status_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Mostrar información detallada'
        )
        
        # Comando task
        task_parser = subparsers.add_parser('task', help='Ejecutar tarea específica')
        task_parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Nombre de la tarea a ejecutar'
        )
        task_parser.add_argument(
            '--agent-name',
            type=str,
            help='Nombre del agente (para tareas de agentes)'
        )
        task_parser.add_argument(
            '--agent-type',
            type=str,
            choices=['executive', 'operational'],
            default='operational',
            help='Tipo de agente'
        )
        task_parser.add_argument(
            '--params',
            type=str,
            help='Parámetros adicionales en formato JSON'
        )
        
        # Comando validate
        validate_parser = subparsers.add_parser('validate', help='Validar blueprint')
        validate_parser.add_argument(
            '--blueprint',
            type=str,
            required=True,
            help='Ruta al archivo blueprint a validar'
        )
        
        # Comando generate
        generate_parser = subparsers.ad