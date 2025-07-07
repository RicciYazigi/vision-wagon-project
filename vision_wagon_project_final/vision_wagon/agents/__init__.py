"""
Vision Wagon Agents Package
Contiene todos los agentes del sistema Vision Wagon.
"""

from .core.base_agent import BaseAgent, AgentResult
from .assembly_agent import AssemblyAgent
from .coaching_agent import CoachingAgent
from .moderation_agent import ModerationAgent
from .narrativearchitect_agent import NarrativeArchitectAgent

__all__ = [
    'BaseAgent',
    'AgentResult',
    'AssemblyAgent',
    'CoachingAgent',
    'ModerationAgent',
    'NarrativeArchitectAgent'
]

