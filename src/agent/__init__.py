"""Agent module for Legal Document Assistant"""

from .legal_agent import LegalDocumentAgent
from .config import AgentConfig
from .instructions import AGENT_INSTRUCTIONS

__all__ = ["LegalDocumentAgent", "AgentConfig", "AGENT_INSTRUCTIONS"]
